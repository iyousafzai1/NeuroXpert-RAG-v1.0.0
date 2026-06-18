"""Build verified NeuroXpert-RAG KB artifacts from semantic verifier outputs."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


def load_rows(path: Path, model_label: str) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["model_label"] = model_label
    return rows


def row_key(row: Dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("pmid") or "",
        row.get("extracted_feature_type") or "",
        row.get("extracted_phenotype") or "",
        row.get("supporting_sentence") or "",
    )


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    n = len(rows)
    return {
        "n_rows": n,
        "models": dict(Counter(row.get("model_label") for row in rows)),
        "decision": dict(Counter(row.get("verifier_decision") for row in rows)),
        "support_score": dict(Counter(row.get("verifier_support_score") for row in rows)),
        "feature_type": dict(Counter(row.get("extracted_feature_type") for row in rows).most_common()),
        "phenotype": dict(Counter(row.get("extracted_phenotype") for row in rows).most_common()),
        "direction": dict(Counter(row.get("extracted_direction") for row in rows).most_common()),
        "directness": dict(Counter(row.get("extracted_directness") for row in rows).most_common()),
    }


def build_consensus(rows: Iterable[Dict[str, str]], min_models: int) -> List[Dict[str, str]]:
    grouped: Dict[tuple[str, str, str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("verifier_decision") not in {"keep", "revise"}:
            continue
        grouped[row_key(row)].append(row)

    consensus: List[Dict[str, str]] = []
    for key, group in grouped.items():
        models = sorted({row.get("model_label") or "" for row in group})
        if len(models) < min_models:
            continue
        best = sorted(
            group,
            key=lambda row: (
                int(row.get("verifier_support_score") or 0),
                1 if row.get("verifier_decision") == "keep" else 0,
            ),
            reverse=True,
        )[0]
        out = dict(best)
        out["consensus_models"] = ";".join(models)
        out["consensus_model_count"] = str(len(models))
        consensus.append(out)
    return consensus


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", nargs=2, metavar=("MODEL_LABEL", "CSV"), required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--consensus-min-models", type=int, default=2)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    all_rows: List[Dict[str, str]] = []
    summary: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs": {},
    }

    for model_label, raw_path in args.run:
        rows = load_rows(Path(raw_path), model_label)
        all_rows.extend(rows)
        keep = [row for row in rows if row.get("verifier_decision") == "keep"]
        useful = [row for row in rows if row.get("verifier_decision") in {"keep", "revise"}]

        safe_label = model_label.lower().replace(" ", "_").replace(".", "").replace("-", "_")
        write_csv(out_dir / f"{safe_label}_verified_keep_only.csv", keep)
        write_csv(out_dir / f"{safe_label}_verified_keep_or_revise.csv", useful)

        summary["runs"][model_label] = {
            "all": summarize(rows),
            "keep_only": summarize(keep),
            "keep_or_revise": summarize(useful),
        }

    combined_keep = [row for row in all_rows if row.get("verifier_decision") == "keep"]
    combined_useful = [row for row in all_rows if row.get("verifier_decision") in {"keep", "revise"}]
    consensus = build_consensus(all_rows, min_models=args.consensus_min_models)

    write_csv(out_dir / "combined_verified_keep_only.csv", combined_keep)
    write_csv(out_dir / "combined_verified_keep_or_revise.csv", combined_useful)
    write_csv(out_dir / f"consensus_min{args.consensus_min_models}_verified_kb.csv", consensus)

    summary["combined_keep_only"] = summarize(combined_keep)
    summary["combined_keep_or_revise"] = summarize(combined_useful)
    summary[f"consensus_min{args.consensus_min_models}"] = summarize(consensus)

    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "verified_kb_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Saved verified KB artifacts to {out_dir}")
    print(json.dumps(summary, ensure_ascii=False, indent=2)[:4000])


if __name__ == "__main__":
    main()
