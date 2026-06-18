"""LLM-based semantic verifier for NeuroXpert-RAG extracted KB rows.

The extractor proposes a structured claim. This verifier judges whether the
quoted evidence sentence actually supports that claim. It is intentionally a
separate stage so the paper can report extraction quality before and after
semantic verification.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List

from neuroxpert_rag.llm.ollama_client import OllamaClient
from neuroxpert_rag.llm.openai_compat_client import OpenAICompatClient
from neuroxpert_rag.llm.structured_extract import extract_single_json_object


VERIFIER_FIELDS = [
    "verifier_model",
    "verifier_support_score",
    "verifier_decision",
    "verifier_phenotype_supported",
    "verifier_feature_supported",
    "verifier_relationship_supported",
    "verifier_direction_supported",
    "verifier_directness_supported",
    "verifier_overclaiming",
    "verifier_corrected_phenotype",
    "verifier_corrected_feature_type",
    "verifier_corrected_direction",
    "verifier_rationale",
    "verifier_error",
]


def build_verifier_prompt(row: Dict[str, str]) -> str:
    claim = {
        "phenotype": row.get("extracted_phenotype"),
        "feature_type": row.get("extracted_feature_type"),
        "relationship": row.get("extracted_relationship"),
        "direction": row.get("extracted_direction"),
        "directness": row.get("extracted_directness"),
        "brain_system": row.get("extracted_brain_system"),
        "diagnostic_context": row.get("extracted_diagnostic_context"),
        "mechanism": row.get("extracted_mechanism"),
    }
    skeleton = {
        "support_score": None,
        "decision": None,
        "phenotype_supported": None,
        "feature_supported": None,
        "relationship_supported": None,
        "direction_supported": None,
        "directness_supported": None,
        "overclaiming": None,
        "corrected_phenotype": None,
        "corrected_feature_type": None,
        "corrected_direction": None,
        "rationale": None,
    }
    return "\n".join(
        [
            "You are a conservative biomedical evidence verifier.",
            "Judge ONLY whether the evidence sentence supports the extracted structured claim.",
            "Do not use outside knowledge. Do not reward a claim merely because it sounds plausible.",
            "",
            "Support score:",
            "2 = the sentence clearly supports the phenotype, feature, relationship, and direction/directness when stated.",
            "1 = the sentence partially supports the claim but needs revision or is indirect.",
            "0 = the sentence does not support the structured claim.",
            "",
            "Decision:",
            "keep = acceptable without correction.",
            "revise = useful evidence but one or more fields should be corrected or made less specific.",
            "drop = unsupported, background-only, or overclaimed.",
            "",
            "Rules:",
            "- If direction is mixed in the sentence, mark direction_supported=false unless the extracted direction captures the relevant part exactly.",
            "- If the sentence mentions a group difference but not a phenotype-feature association, mark overclaiming=true.",
            "- If directness='direct' but the sentence does not name both phenotype and feature, mark directness_supported=false.",
            "- Use null for corrected fields when no correction is needed or no correction is possible.",
            "- Output exactly one JSON object and no markdown.",
            "",
            "Paper metadata:",
            f"PMID: {row.get('pmid')}",
            f"Title: {row.get('title')}",
            f"Year: {row.get('year')}",
            "",
            "Extracted claim:",
            json.dumps(claim, ensure_ascii=False),
            "",
            "Evidence sentence:",
            row.get("supporting_sentence") or "",
            "",
            "Return JSON matching this skeleton:",
            json.dumps(skeleton, ensure_ascii=False),
        ]
    )


def normalize_verdict(obj: Dict[str, Any]) -> Dict[str, str]:
    score = obj.get("support_score")
    try:
        score_int = int(score)
    except Exception:
        score_int = 0
    if score_int not in (0, 1, 2):
        score_int = 0

    decision = str(obj.get("decision") or "").strip().lower()
    if decision not in {"keep", "revise", "drop"}:
        decision = "keep" if score_int == 2 else "revise" if score_int == 1 else "drop"

    def yn(value: Any) -> str:
        if value is True:
            return "yes"
        if value is False:
            return "no"
        text = str(value).strip().lower()
        if text in {"yes", "true", "1"}:
            return "yes"
        if text in {"no", "false", "0"}:
            return "no"
        return "unclear"

    return {
        "verifier_support_score": str(score_int),
        "verifier_decision": decision,
        "verifier_phenotype_supported": yn(obj.get("phenotype_supported")),
        "verifier_feature_supported": yn(obj.get("feature_supported")),
        "verifier_relationship_supported": yn(obj.get("relationship_supported")),
        "verifier_direction_supported": yn(obj.get("direction_supported")),
        "verifier_directness_supported": yn(obj.get("directness_supported")),
        "verifier_overclaiming": yn(obj.get("overclaiming")),
        "verifier_corrected_phenotype": obj.get("corrected_phenotype") or "",
        "verifier_corrected_feature_type": obj.get("corrected_feature_type") or "",
        "verifier_corrected_direction": obj.get("corrected_direction") or "",
        "verifier_rationale": obj.get("rationale") or "",
        "verifier_error": "",
    }


def make_client(args: argparse.Namespace) -> Any:
    if args.backend == "vllm":
        return OpenAICompatClient(
            base_url=args.base_url,
            timeout_s=args.timeout_s,
            max_retries=args.max_retries,
        )
    return OllamaClient(
        base_url=args.base_url,
        timeout_s=args.timeout_s,
        max_retries=args.max_retries,
    )


def summarize(rows: List[Dict[str, str]], args: argparse.Namespace) -> Dict[str, Any]:
    n = len(rows)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": args.in_path,
        "model": args.model,
        "backend": args.backend,
        "n_rows": n,
        "support_score": dict(Counter(r.get("verifier_support_score") for r in rows)),
        "decision": dict(Counter(r.get("verifier_decision") for r in rows)),
        "overclaiming": dict(Counter(r.get("verifier_overclaiming") for r in rows)),
        "errors": sum(1 for r in rows if r.get("verifier_error")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", required=True, help="semantic_audit_sheet.csv")
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary-out", default=None)
    parser.add_argument("--backend", choices=["vllm", "ollama"], default="vllm")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout-s", type=int, default=180)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--only-decisions", default=None, help="Optional comma list from existing review_decision values.")
    parser.add_argument("--num-predict", type=int, default=350)
    args = parser.parse_args()

    with open(args.in_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])

    if args.only_decisions:
        allowed = {x.strip() for x in args.only_decisions.split(",") if x.strip()}
        rows = [row for row in rows if row.get("review_decision") in allowed]
    if args.max_rows is not None:
        rows = rows[: args.max_rows]

    for field in VERIFIER_FIELDS:
        if field not in fields:
            fields.append(field)

    client = make_client(args)
    verified: List[Dict[str, str]] = []
    for idx, row in enumerate(rows, start=1):
        pmid = row.get("pmid") or "unknown"
        print(f"[semantic_verifier] {idx}/{len(rows)} PMID={pmid}", file=sys.stderr, flush=True)
        row = dict(row)
        row["verifier_model"] = args.model
        try:
            prompt = build_verifier_prompt(row)
            resp = client.generate(
                model=args.model,
                prompt=prompt,
                options={"temperature": 0.0, "top_p": 0.9, "num_predict": args.num_predict},
            )
            obj = extract_single_json_object(resp.get("response") or "")
            row.update(normalize_verdict(obj))
        except Exception as e:
            row.update({field: "" for field in VERIFIER_FIELDS if field not in {"verifier_model", "verifier_error"}})
            row["verifier_error"] = f"{type(e).__name__}: {e}"
        verified.append(row)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(verified)

    summary = summarize(verified, args)
    if args.summary_out:
        with open(args.summary_out, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Saved LLM semantic verification to {args.out} (n={len(verified)})")
    if args.summary_out:
        print(f"Saved summary to {args.summary_out}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
