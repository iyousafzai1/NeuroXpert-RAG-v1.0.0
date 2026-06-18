"""Prepare a semantic audit sheet for NeuroXpert-RAG KB records.

Mechanical grounding checks can verify that a PMID exists and that a quoted
sentence appears in the abstract. This audit sheet is for the next question:
does the quoted sentence *actually support* the extracted structured claim?
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from neuroxpert_rag.pilot.kb_audit import audit_record, load_pubmed_corpus_jsonl
from neuroxpert_rag.pilot.schemas import validate_kb_record


AUDIT_FIELDS: List[str] = [
    "record_id",
    "pmid",
    "title",
    "year",
    "journal",
    "query",
    "extracted_brain_system",
    "extracted_feature_type",
    "extracted_phenotype",
    "extracted_diagnostic_context",
    "extracted_relationship",
    "extracted_direction",
    "extracted_mechanism",
    "extracted_directness",
    "evidence_strength",
    "supporting_sentence",
    "schema_valid",
    "schema_issues",
    "citation_valid",
    "sentence_present",
    "sentence_anchored",
    "semantic_support_score",
    "phenotype_correct",
    "feature_type_correct",
    "relationship_correct",
    "direction_correct",
    "overclaiming_flag",
    "hallucination_flag",
    "review_decision",
    "review_notes",
]


RUBRIC = """# NeuroXpert-RAG Semantic Audit Rubric

Use this sheet to judge whether each extracted KB row is scientifically supported.

## Scores

`semantic_support_score`
- `0`: not supported by the quoted sentence.
- `1`: weak or indirect support.
- `2`: clearly supported by the quoted sentence.

Boolean fields should use `yes`, `no`, or `unclear`:
- `phenotype_correct`
- `feature_type_correct`
- `relationship_correct`
- `direction_correct`
- `overclaiming_flag`
- `hallucination_flag`

`review_decision`
- `keep`: acceptable for the strict KB.
- `revise`: conceptually useful but needs field correction.
- `drop`: unsupported, hallucinated, or too indirect.

## Review principle

Judge the extracted row against the `supporting_sentence`, not against general
background knowledge. A real PMID and an anchored sentence are necessary but not
sufficient for a scientifically valid KB claim.
"""


def _bool_text(value: Optional[bool]) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unclear"


def _load_kb(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def prepare_rows(kb_csv: str, corpus_jsonl: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
    corpus_by_pmid = load_pubmed_corpus_jsonl(corpus_jsonl)
    rows = _load_kb(kb_csv)
    if max_rows is not None:
        rows = rows[:max_rows]

    out: List[Dict[str, Any]] = []
    for idx, rec in enumerate(rows, start=1):
        schema_issues = validate_kb_record(rec)
        aud = audit_record(rec, corpus_by_pmid)
        sentence = (rec.get("supporting_sentence") or "").strip()

        out.append(
            {
                "record_id": idx,
                "pmid": rec.get("citation_id") or rec.get("source_id"),
                "title": rec.get("title"),
                "year": rec.get("year"),
                "journal": rec.get("journal"),
                "query": rec.get("query"),
                "extracted_brain_system": rec.get("brain_system"),
                "extracted_feature_type": rec.get("feature_type"),
                "extracted_phenotype": rec.get("phenotype"),
                "extracted_diagnostic_context": rec.get("diagnostic_context"),
                "extracted_relationship": rec.get("relationship"),
                "extracted_direction": rec.get("direction"),
                "extracted_mechanism": rec.get("mechanism"),
                "extracted_directness": rec.get("directness"),
                "evidence_strength": rec.get("evidence_strength"),
                "supporting_sentence": sentence,
                "schema_valid": _bool_text(not schema_issues),
                "schema_issues": "; ".join(schema_issues),
                "citation_valid": _bool_text(aud.get("citation_valid")),
                "sentence_present": _bool_text(bool(sentence)),
                "sentence_anchored": _bool_text(aud.get("evidence_anchored")),
                "semantic_support_score": "",
                "phenotype_correct": "",
                "feature_type_correct": "",
                "relationship_correct": "",
                "direction_correct": "",
                "overclaiming_flag": "",
                "hallucination_flag": "",
                "review_decision": "",
                "review_notes": "",
            }
        )
    return out


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(rows)
    schema_valid_n = sum(1 for r in rows if r["schema_valid"] == "yes")
    citation_valid_n = sum(1 for r in rows if r["citation_valid"] == "yes")
    sentence_present_n = sum(1 for r in rows if r["sentence_present"] == "yes")
    sentence_anchored_n = sum(1 for r in rows if r["sentence_anchored"] == "yes")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": n,
        "schema_valid_n": schema_valid_n,
        "schema_valid_rate": (schema_valid_n / n) if n else None,
        "citation_valid_n": citation_valid_n,
        "citation_valid_rate": (citation_valid_n / n) if n else None,
        "sentence_present_n": sentence_present_n,
        "sentence_present_rate": (sentence_present_n / n) if n else None,
        "sentence_anchored_n": sentence_anchored_n,
        "sentence_anchored_rate": (sentence_anchored_n / sentence_present_n) if sentence_present_n else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary-out", default=None)
    ap.add_argument("--rubric-out", default=None)
    ap.add_argument("--max-rows", type=int, default=None)
    args = ap.parse_args()

    rows = prepare_rows(args.kb, args.corpus, max_rows=args.max_rows)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows)
    if args.summary_out:
        with open(args.summary_out, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    if args.rubric_out:
        with open(args.rubric_out, "w", encoding="utf-8") as f:
            f.write(RUBRIC)

    print(f"Saved semantic audit sheet to {args.out} (n={len(rows)})")
    if args.summary_out:
        print(f"Saved mechanical summary to {args.summary_out}")
    if args.rubric_out:
        print(f"Saved rubric to {args.rubric_out}")


if __name__ == "__main__":
    main()
