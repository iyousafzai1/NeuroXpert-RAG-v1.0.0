"""Pilot-1b: Convert a PubMed JSONL corpus into a knowledge-base CSV.

For now we use a deterministic placeholder extractor that produces:
- one record per paper
- evidence_strength based on simple heuristics (keyword hits)

Later, we will swap in an LLM extraction backend without changing the IO format.

Usage:

python -m neuroxpert_rag.pilot.extract_triples \
  --corpus neuroxpert_rag/data/pilot/pubmed_corpus.jsonl \
  --out neuroxpert_rag/data/pilot/knowledge_base.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from typing import Dict, Iterable, List, Tuple

from .schemas import empty_kb_record, normalize_kb_record, validate_kb_record, KB_RECORD_FIELDS
from .kb_audit import load_pubmed_corpus_jsonl, audit_record

from neuroxpert_rag.llm.ollama_client import OllamaClient
from neuroxpert_rag.llm.openai_compat_client import OpenAICompatClient
from neuroxpert_rag.llm.prompts import build_extraction_prompt
from neuroxpert_rag.llm.structured_extract import extract_single_json_object


PHENOTYPE_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("nonplanning impulsivity", ["nonplanning", "future", "planning"]),
    ("motor impulsivity", ["motor impuls", "inhib", "response inhibition"]),
    ("attentional impulsivity", ["attention", "attentional", "sustained attention"]),
    ("impulsivity (general)", ["impulsivity", "Barratt", "BIS"]),
]

FEATURE_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("functional connectivity", ["functional connectivity", "connectome", "connectivity"]),
    ("dynamic connectivity", ["dynamic functional connectivity", "time-varying", "sliding window"]),
    ("BOLD variability", ["BOLD variability", "signal variability", "temporal variability", "MSSD", "standard deviation"]),
]

BRAIN_SYSTEM_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("default mode network", ["default mode", "DMN"]),
    ("frontoparietal/control network", ["frontoparietal", "control network", "executive control"]),
    ("salience/ventral attention network", ["salience", "ventral attention"]),
    ("somatomotor network", ["somatomotor", "sensorimotor"]),
]


def _norm_text(s: str) -> str:
    s = s or ""
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _best_match(text: str, patterns: List[Tuple[str, List[str]]]) -> Tuple[str, float]:
    """Return (label, score) where score is in [0,1] based on keyword hits."""
    best_label = "unknown"
    best = 0.0
    for label, kws in patterns:
        hits = sum(1 for kw in kws if kw in text)
        score = hits / max(len(kws), 1)
        if score > best:
            best = score
            best_label = label
    return best_label, min(1.0, best)


def placeholder_extract(paper: Dict) -> Dict:
    title = paper.get("title") or ""
    abstract = paper.get("abstract") or ""
    text = _norm_text(title + "\n" + abstract)

    phenotype, p_score = _best_match(text, PHENOTYPE_KEYWORDS)
    feature_type, f_score = _best_match(text, FEATURE_KEYWORDS)
    brain_system, b_score = _best_match(text, BRAIN_SYSTEM_KEYWORDS)

    # evidence_strength is a conservative heuristic: require multiple signals
    evidence_strength = 0.5 * p_score + 0.3 * f_score + 0.2 * b_score

    rec = empty_kb_record()
    rec.update(
        {
            "source": paper.get("source", "pubmed"),
            "source_id": paper.get("pmid"),
            "query": paper.get("query"),
            "title": title,
            "year": paper.get("year"),
            "journal": paper.get("journal"),
            "brain_system": brain_system,
            "feature_type": feature_type,
            "phenotype": phenotype,
            "diagnostic_context": "unknown",
            "relationship": "associated_with",
            "direction": "unclear",
            "mechanism": None,
            "evidence_strength": float(f"{evidence_strength:.4f}"),
            "supporting_sentence": None,
            "citation_id": paper.get("pmid"),
            "extraction_model": "placeholder-keyword-heuristic",
            "extraction_confidence": "low",
        }
    )
    normalize_kb_record(rec)
    return rec


def ollama_extract(
    paper: Dict,
    *,
    client: OllamaClient | OpenAICompatClient,
    model: str,
    backend_label: str = "ollama",
) -> Dict:
    """LLM-backed extraction via an Ollama-style generate client.

    Returns one KB record per paper.
    """

    prompt = build_extraction_prompt(paper)
    resp = client.generate(
        model=model,
        prompt=prompt,
        # Determinism knobs: keep temperature low.
        options={
            "temperature": 0.1,
            "top_p": 0.9,
            # Larger models sometimes produce fully populated, pretty-printed JSON.
            # Keep enough room for the object to close instead of truncating mid-field.
            "num_predict": 700,
            # Repeat penalty helps reduce babbling.
            "repeat_penalty": 1.1,
        },
    )
    text = resp.get("response", "")
    obj = extract_single_json_object(text)

    # Ensure all keys exist (models sometimes omit a field).
    rec = empty_kb_record()
    rec.update(obj)

    # Normalize: treat empty strings as missing.
    for k, v in list(rec.items()):
        if isinstance(v, str) and not v.strip():
            rec[k] = None

    # Default certain categorical fields to 'unknown' when missing.
    for k in ["brain_system", "feature_type", "phenotype", "diagnostic_context", "relationship", "direction"]:
        if rec.get(k) is None:
            rec[k] = "unknown"
    if rec.get("directness") is None:
        rec["directness"] = "unclear"

    if rec.get("extraction_confidence") is None:
        rec["extraction_confidence"] = "low"
    # Force provenance/citation fields from corpus for safety.
    rec["source"] = paper.get("source", "pubmed")
    rec["source_id"] = paper.get("pmid")
    rec["query"] = paper.get("query")
    rec["title"] = paper.get("title")
    rec["year"] = paper.get("year")
    rec["journal"] = paper.get("journal")
    rec["citation_id"] = paper.get("pmid")
    rec["extraction_model"] = f"{backend_label}:{model}"

    # evidence_strength must be float if present
    if rec.get("evidence_strength") is not None:
        try:
            rec["evidence_strength"] = float(rec["evidence_strength"])
        except Exception:
            rec["evidence_strength"] = None

    normalize_kb_record(rec)
    return rec


def load_jsonl(path: str) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--max-papers",
        type=int,
        default=None,
        help="Optional limit for quick debugging (process first N papers).",
    )
    ap.add_argument(
        "--backend",
        choices=["placeholder", "ollama", "vllm"],
        default="placeholder",
        help="Extraction backend. 'vllm' calls an OpenAI-compatible vLLM server.",
    )
    ap.add_argument(
        "--ollama-model",
        default="llama3.2:3b",
        help="Ollama model name (must be pulled already).",
    )
    ap.add_argument(
        "--ollama-base-url",
        default="http://127.0.0.1:11434",
        help="Ollama server base URL.",
    )
    ap.add_argument(
        "--ollama-timeout-s",
        type=int,
        default=60,
        help="Per-request Ollama timeout in seconds.",
    )
    ap.add_argument(
        "--ollama-max-retries",
        type=int,
        default=0,
        help="Number of retries for each Ollama request.",
    )
    ap.add_argument(
        "--vllm-model",
        default="qwen2.5-7b-instruct",
        help="vLLM served model name.",
    )
    ap.add_argument(
        "--vllm-base-url",
        default="http://127.0.0.1:8000/v1",
        help="vLLM OpenAI-compatible base URL, e.g. http://192.168.22.227:8000/v1.",
    )
    ap.add_argument(
        "--vllm-api-key",
        default=None,
        help="Optional API key for OpenAI-compatible servers. vLLM local serving usually does not need one.",
    )
    ap.add_argument(
        "--strict-grounding",
        action="store_true",
        help="If set (ollama backend only), skip records failing citation/evidence anchoring checks.",
    )
    ap.add_argument(
        "--require-supporting-sentence",
        action="store_true",
        help="If set (ollama backend only), require a non-empty supporting_sentence; otherwise skip.",
    )
    args = ap.parse_args()

    rows: List[Dict] = []
    issues_count = 0

    client = None
    if args.backend == "ollama":
        client = OllamaClient(
            base_url=args.ollama_base_url,
            timeout_s=args.ollama_timeout_s,
            max_retries=args.ollama_max_retries,
        )
        active_model = args.ollama_model
    elif args.backend == "vllm":
        client = OpenAICompatClient(
            base_url=args.vllm_base_url,
            timeout_s=args.ollama_timeout_s,
            max_retries=args.ollama_max_retries,
            api_key=args.vllm_api_key,
        )
        active_model = args.vllm_model
    else:
        active_model = args.ollama_model

    processed = 0
    kept = 0
    skipped = 0

    corpus_by_pmid = None
    if args.backend in ("ollama", "vllm") and (args.strict_grounding or args.require_supporting_sentence):
        # We need corpus for evidence anchoring checks.
        corpus_by_pmid = load_pubmed_corpus_jsonl(args.corpus)

    for paper in load_jsonl(args.corpus):
        if args.max_papers is not None and processed >= args.max_papers:
            break

        pmid = paper.get("pmid") or "unknown"
        print(
            f"[extract_triples] processing paper {processed + 1}"
            f"{f'/{args.max_papers}' if args.max_papers is not None else ''} "
            f"(PMID={pmid}, backend={args.backend})",
            file=sys.stderr,
            flush=True,
        )

        if args.backend in ("ollama", "vllm"):
            assert client is not None
            try:
                rec = ollama_extract(paper, client=client, model=active_model, backend_label=args.backend)
            except Exception as e:
                print(
                    f"[extract_triples] {args.backend} extraction failed for PMID={pmid}: {type(e).__name__}: {e}",
                    file=sys.stderr,
                    flush=True,
                )
                # Keep pipeline running; store failure as a low-confidence record.
                rec = empty_kb_record()
                rec.update(
                    {
                        "source": paper.get("source", "pubmed"),
                        "source_id": paper.get("pmid"),
                        "query": paper.get("query"),
                        "title": paper.get("title"),
                        "year": paper.get("year"),
                        "journal": paper.get("journal"),
                        "citation_id": paper.get("pmid"),
                        "extraction_model": f"{args.backend}:{active_model}",
                        "extraction_confidence": "low",
                        "mechanism": f"EXTRACTION_ERROR: {type(e).__name__}: {e}",
                        "evidence_strength": 0.0,
                    }
                )
                issues_count += 1
        else:
            rec = placeholder_extract(paper)

        # Optional strict enforcement: do not admit ungrounded records.
        if args.backend in ("ollama", "vllm") and (args.strict_grounding or args.require_supporting_sentence):
            assert corpus_by_pmid is not None
            if args.require_supporting_sentence and not (rec.get("supporting_sentence") or "").strip():
                skipped += 1
                processed += 1
                continue

            if args.strict_grounding:
                aud = audit_record(rec, corpus_by_pmid)
                # If supporting_sentence is absent, evidence_anchored is None; in strict mode,
                # we treat that as a failure.
                evidence_ok = aud.get("evidence_anchored") is True
                if not (aud.get("citation_valid") and evidence_ok):
                    skipped += 1
                    processed += 1
                    continue

        issues = validate_kb_record(rec)
        if issues:
            issues_count += 1
        rows.append(rec)
        processed += 1
        kept += 1

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=KB_RECORD_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(
        f"Saved {len(rows)} KB records to {args.out}. "
        f"Records with schema issues: {issues_count}. "
        f"Processed={processed} Kept={kept} Skipped={skipped}"
    )


if __name__ == "__main__":
    main()
