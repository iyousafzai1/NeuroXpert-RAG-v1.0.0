"""Matched-input Track B (Step 3 / Experiment 1).

Runs the Track-B verifier (Llama-3.1-8B-Instruct, production decoding: temperature 0.0, top_p 0.9, max 350 tokens) on
exactly the claim/evidence strings that MiniCheck, AlignScore and DeBERTa received (comparators/data/rows_{120,300}.jsonl):
  premise    = extractor-provided supporting sentence (verbatim)
  hypothesis = frozen rule-based textualisation of the structured claim (verbalize_claim, unchanged)
No PMID, title, year, structured fields, extractor identity or abstract is provided.

Two prompt variants are run so that the effect of the INPUT can be separated from the effect of the PROMPT WORDING:
  native_instr : Track B's own instruction block, rules and JSON skeleton, verbatim; only the input block differs
                 (textual claim instead of structured JSON; no paper metadata).
  minimal      : the reviewer-specified minimal prompt (Claim / Evidence / KEEP-REVISE-DROP definitions), JSON output.
Empty-evidence rows receive the deterministic unsupported output (score 0, drop) without a model call, exactly as every
comparator did under the frozen protocol.
"""
from __future__ import annotations
import argparse, csv, json, sys, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from neuroxpert_rag.llm.openai_compat_client import OpenAICompatClient
from neuroxpert_rag.llm.structured_extract import extract_single_json_object
from neuroxpert_rag.pilot.semantic_llm_verifier import normalize_verdict

NATIVE_HEADER = [
    "You are a conservative biomedical evidence verifier.",
    "Judge ONLY whether the evidence sentence supports the extracted structured claim.",
    "Do not use outside knowledge. Do not reward a claim merely because it sounds plausible.",
    "", "Support score:",
    "2 = the sentence clearly supports the phenotype, feature, relationship, and direction/directness when stated.",
    "1 = the sentence partially supports the claim but needs revision or is indirect.",
    "0 = the sentence does not support the structured claim.",
    "", "Decision:",
    "keep = acceptable without correction.",
    "revise = useful evidence but one or more fields should be corrected or made less specific.",
    "drop = unsupported, background-only, or overclaimed.",
    "", "Rules:",
    "- If direction is mixed in the sentence, mark direction_supported=false unless the extracted direction captures the relevant part exactly.",
    "- If the sentence mentions a group difference but not a phenotype-feature association, mark overclaiming=true.",
    "- If directness='direct' but the sentence does not name both phenotype and feature, mark directness_supported=false.",
    "- Use null for corrected fields when no correction is needed or no correction is possible.",
    "- Output exactly one JSON object and no markdown.",
]
NATIVE_SKELETON = {"support_score": None, "decision": None, "phenotype_supported": None, "feature_supported": None,
                   "relationship_supported": None, "direction_supported": None, "directness_supported": None,
                   "overclaiming": None, "corrected_phenotype": None, "corrected_feature_type": None,
                   "corrected_direction": None, "rationale": None}

def prompt_native_instr(hyp: str, prem: str) -> str:
    return "\n".join(NATIVE_HEADER + ["", "Extracted claim:", hyp, "", "Evidence sentence:", prem, "",
                                      "Return JSON matching this skeleton:", json.dumps(NATIVE_SKELETON)])

def prompt_minimal(hyp: str, prem: str) -> str:
    return "\n".join([
        f"Claim: {hyp}", f"Evidence: {prem}", "",
        "Classify the claim as:",
        "KEEP: fully supported",
        "REVISE: partially supported or requires correction",
        "DROP: unsupported or contradicted",
        "",
        "Also give a support score: 2 = fully supported, 1 = partially supported, 0 = unsupported or contradicted.",
        "Return exactly one JSON object and no markdown: {\"support_score\": 0|1|2, \"decision\": \"KEEP\"|\"REVISE\"|\"DROP\", \"rationale\": \"...\"}",
    ])

VARIANTS = {"native_instr": prompt_native_instr, "minimal": prompt_minimal}
FIELDS = ["id","set","extractor_model","variant","empty_evidence_rule","support_score","decision","overclaiming","rationale",
          "parse_status","raw_response","error"]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", nargs="+", required=True); ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model", default="llama-3.1-8b-instruct"); ap.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    rows = [json.loads(l) for p in a.rows for l in Path(p).open(encoding="utf-8") if l.strip()]
    client = OpenAICompatClient(base_url=a.base_url, timeout_s=300, max_retries=3)
    jobs = [(r, v) for r in rows for v in VARIANTS]

    def work(job):
        r, v = job
        out = {"id": r["id"], "set": r["set"], "extractor_model": r["extractor_model"], "variant": v, "empty_evidence_rule": "no",
               "support_score": "", "decision": "", "overclaiming": "", "rationale": "", "parse_status": "", "raw_response": "", "error": ""}
        prem = (r.get("premise") or "").strip(); hyp = (r.get("hypothesis") or "").strip()
        if not prem:
            out.update(empty_evidence_rule="yes", support_score="0", decision="drop", parse_status="rule"); return out
        try:
            resp = client.generate(model=a.model, prompt=VARIANTS[v](hyp, prem),
                                   options={"temperature": 0.0, "top_p": 0.9, "num_predict": 350})
            raw = resp.get("response") or ""; out["raw_response"] = raw
            try:
                obj = extract_single_json_object(raw); out["parse_status"] = "ok"
            except Exception as exc:  # noqa: BLE001
                obj = {}; out["parse_status"] = f"parse_fail: {type(exc).__name__}"
            nv = normalize_verdict(obj)  # production normalisation: score->{0,1,2}; decision fallback from score
            out.update(support_score=nv["verifier_support_score"], decision=nv["verifier_decision"],
                       overclaiming=nv.get("verifier_overclaiming", ""), rationale=nv.get("verifier_rationale", ""))
        except Exception as exc:  # noqa: BLE001
            out["error"] = f"{type(exc).__name__}: {exc}"; out["parse_status"] = "error"
        return out

    t0 = time.time(); res = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for n, o in enumerate(ex.map(work, jobs), 1):
            res.append(o)
            if n % 100 == 0: print(f"[matched] {n}/{len(jobs)} {time.time()-t0:.0f}s", file=sys.stderr, flush=True)
    od = Path(a.out_dir); od.mkdir(parents=True, exist_ok=True)
    with (od / "matched_input_trackb_rows.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(res)
    summ = {}
    for v in VARIANTS:
        for s in sorted({r["set"] for r in res}):
            sub = [r for r in res if r["variant"] == v and r["set"] == s]
            summ[f"{v}/{s}"] = {"n": len(sub), "decision": dict(Counter(r["decision"] for r in sub)),
                                "parse": dict(Counter(r["parse_status"] for r in sub)), "errors": sum(bool(r["error"]) for r in sub)}
    summ["seconds"] = round(time.time() - t0, 1); summ["model"] = a.model
    (od / "matched_input_trackb_summary.json").write_text(json.dumps(summ, indent=2)); print(json.dumps(summ), flush=True)

if __name__ == "__main__":
    main()
