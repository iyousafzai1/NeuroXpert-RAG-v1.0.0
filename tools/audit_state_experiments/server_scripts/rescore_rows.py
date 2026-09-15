"""Re-score an existing audit-sheet CSV with a chosen verifier (paired crossover, Step 0).

Rows are sent UNCHANGED to the production Track-B prompt (neuroxpert_rag.pilot.semantic_llm_verifier.build_verifier_prompt),
with the production decoding settings (temperature 0.0, top_p 0.9, max 350 tokens). The SHA-256 of the input file is
recorded so the manuscript can state that byte-identical extracted records were verified by each verifier.
Requests are issued concurrently (thread pool) against a vLLM OpenAI-compatible endpoint.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, sys, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from neuroxpert_rag.llm.openai_compat_client import OpenAICompatClient
from neuroxpert_rag.llm.structured_extract import extract_single_json_object
from neuroxpert_rag.pilot.semantic_llm_verifier import build_verifier_prompt, normalize_verdict

VFIELDS = ["verifier_model","verifier_support_score","verifier_decision","verifier_phenotype_supported","verifier_feature_supported",
           "verifier_relationship_supported","verifier_direction_supported","verifier_directness_supported","verifier_overclaiming",
           "verifier_corrected_phenotype","verifier_corrected_feature_type","verifier_corrected_direction","verifier_rationale",
           "verifier_error","verifier_raw_response"]

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-csv", required=True); ap.add_argument("--out-csv", required=True)
    ap.add_argument("--verifier-model", required=True); ap.add_argument("--base-url", required=True)
    ap.add_argument("--workers", type=int, default=16); ap.add_argument("--num-predict", type=int, default=350)
    a = ap.parse_args()
    inp = Path(a.in_csv); rows = list(csv.DictReader(inp.open(encoding="utf-8", newline="")))
    base_fields = [f for f in rows[0].keys() if f not in VFIELDS]
    client = OpenAICompatClient(base_url=a.base_url, timeout_s=300, max_retries=3)

    def work(i_row):
        i, row = i_row
        out = {k: row.get(k, "") for k in base_fields}
        out["verifier_model"] = a.verifier_model
        for f in VFIELDS[1:]: out.setdefault(f, "")
        try:
            resp = client.generate(model=a.verifier_model, prompt=build_verifier_prompt(row),
                                   options={"temperature": 0.0, "top_p": 0.9, "num_predict": a.num_predict})
            raw = resp.get("response") or ""
            out["verifier_raw_response"] = raw
            out.update(normalize_verdict(extract_single_json_object(raw)))
        except Exception as exc:  # noqa: BLE001
            out["verifier_error"] = f"{type(exc).__name__}: {exc}"
        return i, out

    t0 = time.time(); done = [None] * len(rows)
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for n, (i, out) in enumerate(ex.map(work, enumerate(rows)), 1):
            done[i] = out
            if n % 25 == 0: print(f"[rescore] {n}/{len(rows)} {time.time()-t0:.0f}s", file=sys.stderr, flush=True)
    outp = Path(a.out_csv); outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=base_fields + VFIELDS); w.writeheader(); w.writerows(done)
    summary = {"generated_at": datetime.now(timezone.utc).isoformat(), "input_csv": str(inp), "input_sha256": sha256(inp),
               "verifier_model": a.verifier_model, "base_url": a.base_url, "n_rows": len(done),
               "decision": dict(Counter(r["verifier_decision"] for r in done)),
               "overclaiming": dict(Counter(r["verifier_overclaiming"] for r in done)),
               "errors": sum(1 for r in done if r["verifier_error"]), "seconds": round(time.time()-t0, 1)}
    Path(str(outp)[:-4] + "_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), flush=True)

if __name__ == "__main__":
    main()
