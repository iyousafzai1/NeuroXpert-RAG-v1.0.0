"""Pilot-3: Audit a knowledge-base CSV against the retrieved corpus.

This is a key step toward an ESWA-ready *expert system* contribution:
we explicitly validate that extracted knowledge is grounded in retrieved
documents.

Audits performed:
1) citation validity: citation_id must be present in the corpus (PMID match)
2) evidence anchoring: supporting_sentence must be a verbatim substring of the
   corresponding abstract (after whitespace normalization)

Outputs a JSON report with aggregate metrics + per-record failures.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _norm_ws(s: str) -> str:
    s = s or ""
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def load_pubmed_corpus_jsonl(path: str) -> Dict[str, Dict[str, Any]]:
    """Return mapping PMID -> paper dict."""

    by_pmid: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            obj = json.loads(ln)
            pmid = str(obj.get("pmid") or "").strip()
            if pmid:
                by_pmid[pmid] = obj
    return by_pmid


def audit_record(rec: Dict[str, str], corpus_by_pmid: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    citation_id = (rec.get("citation_id") or "").strip()
    supporting_sentence = (rec.get("supporting_sentence") or "").strip()

    citation_valid = bool(citation_id) and citation_id in corpus_by_pmid

    evidence_ok: Optional[bool] = None
    if supporting_sentence:
        if not citation_valid:
            evidence_ok = False
        else:
            abs_text = corpus_by_pmid[citation_id].get("abstract") or ""
            evidence_ok = _norm_ws(supporting_sentence) in _norm_ws(abs_text)

    return {
        "citation_valid": citation_valid,
        "evidence_anchored": evidence_ok,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", required=True, help="knowledge_base.csv")
    ap.add_argument("--corpus", required=True, help="pubmed_corpus.jsonl")
    ap.add_argument("--out", required=True, help="audit report JSON")
    args = ap.parse_args()

    corpus_by_pmid = load_pubmed_corpus_jsonl(args.corpus)

    results: List[Dict[str, Any]] = []
    n = 0
    citation_valid_n = 0
    evidence_present_n = 0
    evidence_anchored_n = 0

    with open(args.kb, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rec in reader:
            n += 1
            audit = audit_record(rec, corpus_by_pmid)
            if audit["citation_valid"]:
                citation_valid_n += 1
            if (rec.get("supporting_sentence") or "").strip():
                evidence_present_n += 1
                if audit["evidence_anchored"]:
                    evidence_anchored_n += 1
            results.append({"record": {"source_id": rec.get("source_id"), "citation_id": rec.get("citation_id")}, "audit": audit})

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kb_path": args.kb,
        "corpus_path": args.corpus,
        "n_records": n,
        "citation_valid_n": citation_valid_n,
        "citation_valid_rate": (citation_valid_n / n) if n else None,
        "evidence_present_n": evidence_present_n,
        "evidence_anchored_n": evidence_anchored_n,
        "evidence_anchored_rate": (evidence_anchored_n / evidence_present_n) if evidence_present_n else None,
        "results": results,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(
        "KB audit saved to {out} | n={n} | citation_valid={cv}/{n} | evidence_anchored={ea}/{ep}".format(
            out=args.out,
            n=n,
            cv=citation_valid_n,
            ea=evidence_anchored_n,
            ep=evidence_present_n,
        )
    )


if __name__ == "__main__":
    main()
