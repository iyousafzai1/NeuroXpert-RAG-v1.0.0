"""Pilot-1: Retrieve a small PubMed corpus using NCBI E-utilities.

This is deliberately lightweight and dependency-minimal (stdlib only).

Outputs JSONL with one record per PMID containing metadata + abstract.

Usage:

python -m neuroxpert_rag.pilot.pubmed_retrieve \
  --out neuroxpert_rag/data/pilot/pubmed_corpus.jsonl \
  --max-per-query 30
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


DEFAULT_QUERIES: List[str] = [
    # impulsivity + neuroimaging
    'Barratt Impulsiveness Scale resting-state fMRI',
    'impulsivity resting-state fMRI functional connectivity',
    'nonplanning impulsivity functional connectivity',
    'attentional impulsivity resting-state fMRI',
    'motor impulsivity resting-state fMRI',
    # diagnoses
    'ADHD impulsivity resting-state fMRI connectivity',
    'bipolar impulsivity resting-state fMRI connectivity',
    'schizophrenia impulsivity resting-state fMRI connectivity',
    # variability
    'BOLD signal variability impulsivity',
    'temporal variability BOLD impulsivity',
    'MSSD BOLD variability impulsivity',
    # networks
    'default mode network impulsivity resting-state',
    'frontoparietal control network impulsivity resting-state',
    'salience network impulsivity resting-state',
    'somatomotor network impulsivity resting-state',
]


@dataclass
class PubMedRecord:
    pmid: str
    title: str
    abstract: str
    journal: Optional[str]
    year: Optional[str]
    query: str

    def to_dict(self) -> Dict:
        return {
            "source": "pubmed",
            "pmid": self.pmid,
            "title": self.title,
            "abstract": self.abstract,
            "journal": self.journal,
            "year": self.year,
            "query": self.query,
        }


def _http_get(url: str, timeout: int = 30, retries: int = 5) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            # Be polite; NCBI rate-limits.
            "User-Agent": "NeuroXpert-RAG-Pilot/0.1 (mailto:unknown@example.com)",
        },
    )
    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            last_error = e
            if attempt >= retries:
                break
            sleep_s = min(2.0 * attempt, 10.0)
            print(
                f"[pubmed_retrieve] request failed ({type(e).__name__}); "
                f"retrying {attempt}/{retries - 1} after {sleep_s:.1f}s",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(sleep_s)
    raise last_error if last_error is not None else RuntimeError("HTTP request failed")


def esearch(query: str, retmax: int = 50) -> List[str]:
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": str(retmax),
        "sort": "relevance",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    raw = _http_get(url)
    data = json.loads(raw.decode("utf-8"))
    return data.get("esearchresult", {}).get("idlist", [])


def efetch(pmids: Iterable[str]) -> bytes:
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    id_str = ",".join(pmids)
    params = {
        "db": "pubmed",
        "id": id_str,
        "retmode": "xml",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    return _http_get(url)


def _text_or_none(elem: Optional[ET.Element]) -> Optional[str]:
    if elem is None:
        return None
    txt = "".join(elem.itertext()).strip()
    return txt if txt else None


def parse_pubmed_xml(xml_bytes: bytes, query: str) -> List[PubMedRecord]:
    root = ET.fromstring(xml_bytes)
    out: List[PubMedRecord] = []

    for article in root.findall(".//PubmedArticle"):
        pmid = _text_or_none(article.find(".//MedlineCitation/PMID"))
        if not pmid:
            continue

        title = _text_or_none(article.find(".//Article/ArticleTitle")) or ""

        abstract_parts = []
        for ab in article.findall(".//Article/Abstract/AbstractText"):
            label = ab.attrib.get("Label")
            part = _text_or_none(ab) or ""
            if label:
                abstract_parts.append(f"{label}: {part}")
            else:
                abstract_parts.append(part)
        abstract = "\n".join([p for p in abstract_parts if p]).strip()

        journal = _text_or_none(article.find(".//Article/Journal/Title"))
        year = _text_or_none(article.find(".//Article/Journal/JournalIssue/PubDate/Year"))
        if year is None:
            # sometimes MedlineDate holds the year
            medline_date = _text_or_none(article.find(".//Article/Journal/JournalIssue/PubDate/MedlineDate"))
            if medline_date:
                year = medline_date.split(" ")[0]

        out.append(
            PubMedRecord(
                pmid=pmid,
                title=title,
                abstract=abstract,
                journal=journal,
                year=year,
                query=query,
            )
        )

    return out


def retrieve_corpus(
    queries: List[str],
    max_per_query: int,
    sleep_s: float = 0.34,
    max_total: Optional[int] = None,
) -> List[PubMedRecord]:
    """Retrieve records for each query and return a de-duplicated list by PMID."""
    by_pmid: Dict[str, PubMedRecord] = {}

    for q in queries:
        print(f"[pubmed_retrieve] searching: {q}", file=sys.stderr, flush=True)
        pmids = esearch(q, retmax=max_per_query)
        if not pmids:
            continue

        # batch efetch to reduce calls
        batch_size = 50
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i : i + batch_size]
            print(
                f"[pubmed_retrieve] fetching {len(batch)} records for query: {q}",
                file=sys.stderr,
                flush=True,
            )
            xml_bytes = efetch(batch)
            recs = parse_pubmed_xml(xml_bytes, query=q)
            for r in recs:
                # prefer first occurrence; store query provenance
                if r.pmid not in by_pmid:
                    by_pmid[r.pmid] = r
                    if max_total is not None and len(by_pmid) >= max_total:
                        return list(by_pmid.values())
            time.sleep(sleep_s)

    return list(by_pmid.values())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output JSONL file")
    ap.add_argument("--max-per-query", type=int, default=30)
    ap.add_argument("--max-total", type=int, default=None, help="Optional cap after PMID de-duplication")
    ap.add_argument("--queries", default=None, help="Optional path to a text file of queries (one per line)")
    args = ap.parse_args()

    if args.queries:
        with open(args.queries, "r", encoding="utf-8") as f:
            queries = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
    else:
        queries = DEFAULT_QUERIES

    records = retrieve_corpus(queries=queries, max_per_query=args.max_per_query, max_total=args.max_total)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

    print(f"Saved {len(records)} PubMed records to {args.out}")


if __name__ == "__main__":
    main()
