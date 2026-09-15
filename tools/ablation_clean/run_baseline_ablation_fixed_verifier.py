"""Run baseline/ablation systems for NeuroXpert-RAG.

CLEAN ABLATION RE-RUN (14 Sep 2026) — identical to pilot/run_baseline_ablation.py except that the semantic verifier
can be served from a separate endpoint (--verifier-base-url) so that a FIXED verifier (Llama-3.1-8B-Instruct) is used for
every extractor, exactly as in the primary 700-abstract evaluation. The original harness defaulted --verifier-model to the
extractor model, which confounded 'gate removal' with a verifier swap. No other logic is changed.


This experiment compares the final gated pipeline against simpler RAG designs
on a fixed PMID subset. It intentionally produces auditable CSV/JSON outputs
for manuscript tables rather than a single prose answer.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from neuroxpert_rag.llm.ollama_client import OllamaClient
from neuroxpert_rag.llm.openai_compat_client import OpenAICompatClient
from neuroxpert_rag.llm.structured_extract import extract_single_json_object
from neuroxpert_rag.pilot.extract_triples import ollama_extract
from neuroxpert_rag.pilot.kb_audit import audit_record, load_pubmed_corpus_jsonl
from neuroxpert_rag.pilot.prepare_semantic_audit import AUDIT_FIELDS, prepare_rows
from neuroxpert_rag.pilot.schemas import KB_RECORD_FIELDS, empty_kb_record, normalize_kb_record, validate_kb_record
from neuroxpert_rag.pilot.semantic_llm_verifier import build_verifier_prompt, normalize_verdict


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_pmids(path: Path, max_pmids: int | None = None) -> list[str]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    pmids = [str(r["pmid"]).strip() for r in rows if str(r.get("pmid") or "").strip()]
    return pmids[:max_pmids] if max_pmids else pmids


def make_client(args: argparse.Namespace) -> Any:
    if args.backend == "vllm":
        return OpenAICompatClient(base_url=args.base_url, timeout_s=args.timeout_s, max_retries=args.max_retries)
    return OllamaClient(base_url=args.base_url, timeout_s=args.timeout_s, max_retries=args.max_retries)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def rate(num: int, den: int) -> float | None:
    return (num / den) if den else None


def naive_prompt(paper: dict[str, Any]) -> str:
    return "\n".join(
        [
            "You are helping with a biomedical literature review.",
            "Read the PubMed abstract and write a short free-form evidence summary about impulsivity and neuroimaging.",
            "Mention the PMID if you use the paper. Do not use JSON.",
            "",
            f"PMID: {paper.get('pmid')}",
            f"Title: {paper.get('title')}",
            f"Year: {paper.get('year')}",
            f"Journal: {paper.get('journal')}",
            "",
            "Abstract:",
            paper.get("abstract") or "",
        ]
    )


def single_stage_prompt(paper: dict[str, Any]) -> str:
    kb = {field: None for field in KB_RECORD_FIELDS}
    verdict = {
        "support_score": None,
        "decision": None,
        "phenotype_supported": None,
        "feature_supported": None,
        "relationship_supported": None,
        "direction_supported": None,
        "directness_supported": None,
        "overclaiming": None,
        "rationale": None,
    }
    skeleton = {"kb_record": kb, "self_verification": verdict}
    return "\n".join(
        [
            "Extract one structured biomedical evidence record from this abstract, then verify your own extraction.",
            "This is a single-stage baseline: do not rely on any external mechanical gate.",
            "The supporting_sentence must be copied from the abstract if possible.",
            "Return exactly one JSON object and no markdown.",
            "",
            f"PMID: {paper.get('pmid')}",
            f"Title: {paper.get('title')}",
            f"Year: {paper.get('year')}",
            f"Journal: {paper.get('journal')}",
            f"Query: {paper.get('query')}",
            "",
            "Abstract:",
            paper.get("abstract") or "",
            "",
            "JSON skeleton:",
            json.dumps(skeleton, ensure_ascii=False),
        ]
    )


def anchored_sentence_from_response(response: str, abstract: str) -> bool:
    norm_abs = re.sub(r"\s+", " ", abstract or "").lower()
    for sentence in re.split(r"(?<=[.!?])\s+", response or ""):
        s = re.sub(r"\s+", " ", sentence).strip().lower()
        if len(s) >= 40 and s in norm_abs:
            return True
    return False


def run_naive(client: Any, args: argparse.Namespace, papers: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for idx, paper in enumerate(papers, start=1):
        pmid = str(paper.get("pmid") or "unknown")
        print(f"[baseline:naive] {idx}/{len(papers)} PMID={pmid}", file=sys.stderr, flush=True)
        error = ""
        text = ""
        try:
            resp = client.generate(
                model=args.model,
                prompt=naive_prompt(paper),
                options={"temperature": 0.1, "top_p": 0.9, "num_predict": args.naive_num_predict},
            )
            text = resp.get("response") or ""
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"
        rows.append(
            {
                "pmid": pmid,
                "title": paper.get("title") or "",
                "response": text,
                "mentions_pmid": str(pmid in text),
                "has_anchored_sentence": str(anchored_sentence_from_response(text, paper.get("abstract") or "")),
                "unparseable_as_schema": "True",
                "error": error,
            }
        )
    write_csv(out_dir / "baseline_a_naive_free_form.csv", rows, list(rows[0].keys()) if rows else [])
    n = len(rows)
    return {
        "system": "baseline_a_naive_free_form_rag",
        "model": args.model,
        "n": n,
        "schema_valid_rate": 0.0,
        "citation_valid_rate": rate(sum(r["mentions_pmid"] == "True" for r in rows), n),
        "quote_anchor_rate": rate(sum(r["has_anchored_sentence"] == "True" for r in rows), n),
        "semantic_keep_rate": None,
        "semantic_revise_rate": None,
        "semantic_drop_rate": None,
        "overclaim_rate": None,
        "useful_evidence_retained_rate": None,
        "unparseable_output_rate": rate(sum(r["unparseable_as_schema"] == "True" for r in rows), n),
        "errors": sum(bool(r["error"]) for r in rows),
    }


def verify_audit_rows(
    client: Any,
    *,
    args: argparse.Namespace,
    audit_rows: list[dict[str, Any]],
    out_csv: Path,
    summary_json: Path,
) -> dict[str, Any]:
    fields = list(AUDIT_FIELDS)
    verifier_fields = [
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
    for field in verifier_fields:
        if field not in fields:
            fields.append(field)
    verified: list[dict[str, Any]] = []
    for idx, row in enumerate(audit_rows, start=1):
        pmid = row.get("pmid") or "unknown"
        print(f"[baseline:verify] {idx}/{len(audit_rows)} PMID={pmid}", file=sys.stderr, flush=True)
        row = dict(row)
        row["verifier_model"] = args.verifier_model
        try:
            prompt = build_verifier_prompt(row)  # type: ignore[arg-type]
            resp = client.generate(
                model=args.verifier_model,
                prompt=prompt,
                options={"temperature": 0.0, "top_p": 0.9, "num_predict": args.verifier_num_predict},
            )
            obj = extract_single_json_object(resp.get("response") or "")
            row.update(normalize_verdict(obj))
        except Exception as exc:  # noqa: BLE001
            for field in verifier_fields:
                row.setdefault(field, "")
            row["verifier_error"] = f"{type(exc).__name__}: {exc}"
        verified.append(row)
    write_csv(out_csv, verified, fields)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": len(verified),
        "decision": dict(Counter(r.get("verifier_decision") for r in verified)),
        "overclaiming": dict(Counter(r.get("verifier_overclaiming") for r in verified)),
        "errors": sum(1 for r in verified if r.get("verifier_error")),
    }
    write_json(summary_json, summary)
    return summary


def audit_kb_rows(kb_rows: list[dict[str, Any]], corpus_path: Path) -> list[dict[str, Any]]:
    temp_kb = corpus_path.parent / "_baseline_temp_kb.csv"
    write_csv(temp_kb, kb_rows, KB_RECORD_FIELDS)
    try:
        return prepare_rows(str(temp_kb), str(corpus_path))
    finally:
        try:
            temp_kb.unlink()
        except FileNotFoundError:
            pass


def summarize_verified(system: str, model: str, audit_rows: list[dict[str, Any]], verifier_summary: dict[str, Any]) -> dict[str, Any]:
    n = len(audit_rows)
    decisions = verifier_summary.get("decision", {})
    over = verifier_summary.get("overclaiming", {})
    return {
        "system": system,
        "model": model,
        "n": n,
        "schema_valid_rate": rate(sum(r.get("schema_valid") == "yes" for r in audit_rows), n),
        "citation_valid_rate": rate(sum(r.get("citation_valid") == "yes" for r in audit_rows), n),
        "quote_anchor_rate": rate(sum(r.get("sentence_anchored") == "yes" for r in audit_rows), n),
        "semantic_keep_rate": rate(int(decisions.get("keep", 0)), n),
        "semantic_revise_rate": rate(int(decisions.get("revise", 0)), n),
        "semantic_drop_rate": rate(int(decisions.get("drop", 0)), n),
        "overclaim_rate": rate(int(over.get("yes", 0)), n),
        "useful_evidence_retained_rate": rate(int(decisions.get("keep", 0)) + int(decisions.get("revise", 0)), n),
        "unparseable_output_rate": 0.0,
        "errors": verifier_summary.get("errors", 0),
    }


def run_structured_no_gate(client: Any, args: argparse.Namespace, papers: list[dict[str, Any]], out_dir: Path, vclient: Any = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for idx, paper in enumerate(papers, start=1):
        pmid = str(paper.get("pmid") or "unknown")
        print(f"[baseline:structured_no_gate] {idx}/{len(papers)} PMID={pmid}", file=sys.stderr, flush=True)
        try:
            rec = ollama_extract(paper, client=client, model=args.model, backend_label=args.backend)
        except Exception as exc:  # noqa: BLE001
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
                    "extraction_model": f"{args.backend}:{args.model}",
                    "extraction_confidence": "low",
                    "mechanism": f"EXTRACTION_ERROR: {type(exc).__name__}: {exc}",
                }
            )
        rows.append(rec)
    write_csv(out_dir / "baseline_b_structured_no_gate_kb.csv", rows, KB_RECORD_FIELDS)
    audit_rows = audit_kb_rows(rows, Path(args.corpus))
    write_csv(out_dir / "baseline_b_structured_no_gate_audit_sheet.csv", audit_rows, AUDIT_FIELDS)
    summary = verify_audit_rows(
        vclient or client,
        args=args,
        audit_rows=audit_rows,
        out_csv=out_dir / "baseline_b_structured_no_gate_verifier.csv",
        summary_json=out_dir / "baseline_b_structured_no_gate_verifier_summary.json",
    )
    return summarize_verified("baseline_b_structured_no_mechanical_gate", args.model, audit_rows, summary)


def run_single_stage(client: Any, args: argparse.Namespace, papers: list[dict[str, Any]], out_dir: Path, vclient: Any = None) -> dict[str, Any]:
    kb_rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    parse_errors = 0
    self_decisions: Counter[str] = Counter()
    for idx, paper in enumerate(papers, start=1):
        pmid = str(paper.get("pmid") or "unknown")
        print(f"[baseline:single_stage] {idx}/{len(papers)} PMID={pmid}", file=sys.stderr, flush=True)
        raw = ""
        err = ""
        rec = empty_kb_record()
        try:
            resp = client.generate(
                model=args.model,
                prompt=single_stage_prompt(paper),
                options={"temperature": 0.1, "top_p": 0.9, "num_predict": args.single_stage_num_predict},
            )
            raw = resp.get("response") or ""
            obj = extract_single_json_object(raw)
            extracted = obj.get("kb_record") if isinstance(obj.get("kb_record"), dict) else obj
            rec.update(extracted)
            verification = obj.get("self_verification") if isinstance(obj.get("self_verification"), dict) else {}
            self_decisions.update([str(verification.get("decision") or "").lower() or "missing"])
        except Exception as exc:  # noqa: BLE001
            parse_errors += 1
            err = f"{type(exc).__name__}: {exc}"
        rec.update(
            {
                "source": paper.get("source", "pubmed"),
                "source_id": paper.get("pmid"),
                "query": paper.get("query"),
                "title": paper.get("title"),
                "year": paper.get("year"),
                "journal": paper.get("journal"),
                "citation_id": paper.get("pmid"),
                "extraction_model": f"single_stage:{args.model}",
            }
        )
        if not rec.get("directness"):
            rec["directness"] = "unclear"
        normalize_kb_record(rec)
        kb_rows.append(rec)
        raw_rows.append({"pmid": pmid, "raw_response": raw, "parse_error": err})
    write_csv(out_dir / "baseline_c_single_stage_raw.csv", raw_rows, ["pmid", "raw_response", "parse_error"])
    write_csv(out_dir / "baseline_c_single_stage_kb.csv", kb_rows, KB_RECORD_FIELDS)
    audit_rows = audit_kb_rows(kb_rows, Path(args.corpus))
    write_csv(out_dir / "baseline_c_single_stage_audit_sheet.csv", audit_rows, AUDIT_FIELDS)
    summary = verify_audit_rows(
        vclient or client,
        args=args,
        audit_rows=audit_rows,
        out_csv=out_dir / "baseline_c_single_stage_external_verifier.csv",
        summary_json=out_dir / "baseline_c_single_stage_external_verifier_summary.json",
    )
    metrics = summarize_verified("baseline_c_single_stage_extract_verify", args.model, audit_rows, summary)
    metrics["unparseable_output_rate"] = rate(parse_errors, len(papers))
    metrics["self_decision_counts"] = dict(self_decisions)
    return metrics


def full_neuroxpert_metrics(args: argparse.Namespace, pmids: set[str], out_dir: Path) -> dict[str, Any] | None:
    if not args.full_run_dir:
        return None
    run_dir = Path(args.full_run_dir)
    sheet = run_dir / "semantic_llm_verifier_all.csv"
    if not sheet.exists():
        return None
    with sheet.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if str(r.get("pmid") or "").strip() in pmids]
    write_csv(out_dir / "full_neuroxpert_subset_verifier.csv", rows, list(rows[0].keys()) if rows else [])
    n = len(rows)
    decisions = Counter(r.get("verifier_decision") for r in rows)
    over = Counter(r.get("verifier_overclaiming") for r in rows)
    return {
        "system": "full_neuroxpert_rag",
        "model": args.model,
        "n": n,
        "schema_valid_rate": rate(sum(r.get("schema_valid") == "yes" for r in rows), n),
        "citation_valid_rate": rate(sum(r.get("citation_valid") == "yes" for r in rows), n),
        "quote_anchor_rate": rate(sum(r.get("sentence_anchored") == "yes" for r in rows), n),
        "semantic_keep_rate": rate(decisions.get("keep", 0), n),
        "semantic_revise_rate": rate(decisions.get("revise", 0), n),
        "semantic_drop_rate": rate(decisions.get("drop", 0), n),
        "overclaim_rate": rate(over.get("yes", 0), n),
        "useful_evidence_retained_rate": rate(decisions.get("keep", 0) + decisions.get("revise", 0), n),
        "unparseable_output_rate": 0.0,
        "errors": sum(bool(r.get("verifier_error")) for r in rows),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--pmids", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--backend", choices=["vllm", "ollama"], default="vllm")
    ap.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--verifier-model", default=None)
    ap.add_argument("--verifier-base-url", default=None, help="separate OpenAI-compatible endpoint serving the fixed verifier")
    ap.add_argument("--full-run-dir", default="")
    ap.add_argument("--max-pmids", type=int, default=100)
    ap.add_argument("--timeout-s", type=int, default=240)
    ap.add_argument("--max-retries", type=int, default=2)
    ap.add_argument("--naive-num-predict", type=int, default=260)
    ap.add_argument("--single-stage-num-predict", type=int, default=900)
    ap.add_argument("--verifier-num-predict", type=int, default=350)
    args = ap.parse_args()
    if args.verifier_model is None:
        args.verifier_model = args.model

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pmid_list = read_pmids(Path(args.pmids), max_pmids=args.max_pmids)
    wanted = set(pmid_list)
    corpus = [r for r in read_jsonl(Path(args.corpus)) if str(r.get("pmid") or "") in wanted]
    order = {pmid: i for i, pmid in enumerate(pmid_list)}
    corpus.sort(key=lambda r: order.get(str(r.get("pmid") or ""), 10**9))
    write_json(out_dir / "baseline_subset_metadata.json", {"n_pmids": len(pmid_list), "n_loaded": len(corpus), "model": args.model, "verifier_model": args.verifier_model, "verifier_base_url": args.verifier_base_url})

    client = make_client(args)
    vclient = OpenAICompatClient(base_url=args.verifier_base_url, timeout_s=args.timeout_s, max_retries=args.max_retries) if args.verifier_base_url else client
    metrics: list[dict[str, Any]] = []
    full = full_neuroxpert_metrics(args, wanted, out_dir)
    if full:
        metrics.append(full)
    metrics.append(run_naive(client, args, corpus, out_dir))
    metrics.append(run_structured_no_gate(client, args, corpus, out_dir, vclient=vclient))
    metrics.append(run_single_stage(client, args, corpus, out_dir, vclient=vclient))

    fields = [
        "system",
        "model",
        "n",
        "schema_valid_rate",
        "citation_valid_rate",
        "quote_anchor_rate",
        "semantic_keep_rate",
        "semantic_revise_rate",
        "semantic_drop_rate",
        "overclaim_rate",
        "useful_evidence_retained_rate",
        "unparseable_output_rate",
        "errors",
        "self_decision_counts",
    ]
    for row in metrics:
        for field in fields:
            row.setdefault(field, "")
    write_csv(out_dir / "baseline_ablation_metrics.csv", metrics, fields)
    write_json(out_dir / "baseline_ablation_metrics.json", metrics)
    print(json.dumps({"out_dir": str(out_dir), "metrics": metrics}, indent=2), flush=True)


if __name__ == "__main__":
    main()
