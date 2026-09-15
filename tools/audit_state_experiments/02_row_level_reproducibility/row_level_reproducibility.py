"""Row-level reproducibility: archived (May 2026, HF/transformers stack) vs clean re-run (Sep 2026, vLLM stack). Step 2 / Analysis 4.

Rows are matched by PMID (one record per PMID in the 100-PMID ablation). For every pair we report
  - exact agreement of each extracted field (case/whitespace-normalised) and all-fields agreement;
  - supporting-sentence agreement: exact (whitespace-normalised), token-Jaccard mean, and same-consensus-key rate
    (pmid + feature type + phenotype + sentence; the manuscript's exact-key consensus key);
  - Track-A pass agreement and kappa; Track-B decision agreement, 3x3 transition matrix and Cohen's kappa;
    overclaim-flag agreement and kappa; joint-state (A x B) agreement;
  - Jaccard similarity of retained record sets (keep-only tier; keep-or-revise tier; each also restricted to Track-A pass).
Pair types
  extraction_repro : archived rows vs clean rows, BOTH verified by the fixed Llama verifier (archived rows re-scored in Step 0),
                     so that the comparison isolates extraction + serving-stack variation from verifier identity.
  verifier_repro   : IDENTICAL rows, same verifier model, archived verdict vs fresh vLLM verdict (verifier determinism across stacks).
  reference_vs_replicate : archived full-pipeline reference rows (700-run subset) vs clean re-extracted two-stage rows (both Llama-verified).
"""
import csv, json, re, collections, pathlib, itertools
B = pathlib.Path(__file__).resolve().parents[1]; X0 = B / "00_paired_crossover"; OUT = pathlib.Path(__file__).parent
CLEAN = B.parent / "ablation_clean/out"
ARCH = pathlib.Path("/Users/irfankhan/Documents/project 4/Egyptial_Informatics_Journal/neuroxpert_rag/results_package_mature_2026_05_29/03_figure_source_data/baseline_ablation_100")
MODELS = ["llama31_8b", "qwen25_7b", "mistral7b"]
FIELDS = ["extracted_phenotype", "extracted_feature_type", "extracted_relationship", "extracted_direction", "extracted_directness",
          "extracted_diagnostic_context", "extracted_brain_system", "extracted_mechanism"]
nz = lambda s: re.sub(r"\s+", " ", (s or "")).strip().lower()
tb = lambda v: str(v).strip().lower() in ("true", "1", "yes", "t")
A_of = lambda r: all(tb(r[k]) for k in ("schema_valid", "citation_valid", "sentence_present", "sentence_anchored"))
load = lambda p: {r["pmid"].strip(): r for r in csv.DictReader(open(p, encoding="utf-8"))}
def kappa(pairs):
    n = len(pairs); cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in cats)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)
def jacc(a, b): return len(a & b) / len(a | b) if (a | b) else 1.0   # two empty sets (e.g. both sentences empty) are identical
def tok(s): return set(re.findall(r"[a-z0-9]+", nz(s)))

def compare(r1, r2, label, ptype, extractor, note):
    common = sorted(set(r1) & set(r2)); n = len(common); res = {"pair": label, "type": ptype, "extractor": extractor, "note": note, "n_matched": n,
                                                                  "n_only_run1": len(set(r1) - set(r2)), "n_only_run2": len(set(r2) - set(r1))}
    if ptype != "verifier_repro":
        for f in FIELDS: res[f"field_exact::{f}"] = round(100 * sum(nz(r1[p][f]) == nz(r2[p][f]) for p in common) / n, 1)
        res["all_fields_exact_pct"] = round(100 * sum(all(nz(r1[p][f]) == nz(r2[p][f]) for f in FIELDS) for p in common) / n, 1)
        res["sentence_exact_pct"] = round(100 * sum(nz(r1[p]["supporting_sentence"]) == nz(r2[p]["supporting_sentence"]) for p in common) / n, 1)
        res["sentence_token_jaccard_mean"] = round(sum(jacc(tok(r1[p]["supporting_sentence"]), tok(r2[p]["supporting_sentence"])) for p in common) / n, 3)
        res["consensus_key_same_pct"] = round(100 * sum((nz(r1[p]["extracted_feature_type"]), nz(r1[p]["extracted_phenotype"]), nz(r1[p]["supporting_sentence"])) ==
                                                        (nz(r2[p]["extracted_feature_type"]), nz(r2[p]["extracted_phenotype"]), nz(r2[p]["supporting_sentence"])) for p in common) / n, 1)
        ap = [(A_of(r1[p]), A_of(r2[p])) for p in common]
        res["trackA_pass_run1"] = sum(a for a, _ in ap); res["trackA_pass_run2"] = sum(b for _, b in ap)
        res["trackA_agreement_pct"] = round(100 * sum(a == b for a, b in ap) / n, 1); res["trackA_kappa"] = round(kappa(ap), 3)
    dp = [(r1[p]["verifier_decision"].strip().lower(), r2[p]["verifier_decision"].strip().lower()) for p in common]
    res["trackB_agreement_pct"] = round(100 * sum(a == b for a, b in dp) / n, 1); res["trackB_kappa"] = round(kappa(dp), 3)
    res["trackB_transition_run1_to_run2"] = {f"{a}->{b}": c for (a, b), c in sorted(collections.Counter(dp).items())}
    op = [(r1[p]["verifier_overclaiming"].strip().lower(), r2[p]["verifier_overclaiming"].strip().lower()) for p in common]
    res["overclaim_yes_run1"] = sum(a == "yes" for a, _ in op); res["overclaim_yes_run2"] = sum(b == "yes" for _, b in op)
    res["overclaim_agreement_pct"] = round(100 * sum(a == b for a, b in op) / n, 1); res["overclaim_kappa"] = round(kappa(op), 3)
    if ptype != "verifier_repro":
        jp = [((A_of(r1[p]), r1[p]["verifier_decision"].strip().lower()), (A_of(r2[p]), r2[p]["verifier_decision"].strip().lower())) for p in common]
        res["joint_state_agreement_pct"] = round(100 * sum(a == b for a, b in jp) / n, 1)
        for tier, ok in (("keep_only", lambda d: d == "keep"), ("keep_or_revise", lambda d: d in ("keep", "revise"))):
            s1 = {p for p in common if ok(r1[p]["verifier_decision"].strip().lower())}; s2 = {p for p in common if ok(r2[p]["verifier_decision"].strip().lower())}
            res[f"jaccard_{tier}"] = round(jacc(s1, s2), 3)
            s1a = {p for p in s1 if A_of(r1[p])}; s2a = {p for p in s2 if A_of(r2[p])}
            res[f"jaccard_{tier}_trackA_pass"] = round(jacc(s1a, s2a), 3)
    return res

results = []
for m in MODELS:
    arch_B_llama = X0 / f"out/archived_{m}_B__verifier_llama.csv"; arch_C_llama = X0 / f"out/archived_{m}_C__verifier_llama.csv"
    clean_B = CLEAN / m / "merged_baseline_b_structured_no_gate_verifier.csv"; clean_C = CLEAN / m / "merged_baseline_c_single_stage_external_verifier.csv"
    ref = CLEAN / m / "merged_full_neuroxpert_subset_verifier.csv"
    if arch_B_llama.exists():
        results.append(compare(load(arch_B_llama), load(clean_B), "two-stage (B): archived rows vs clean rows", "extraction_repro", m, "both Llama-verified"))
        results.append(compare(load(arch_C_llama), load(clean_C), "single-stage (C): archived rows vs clean rows", "extraction_repro", m, "both Llama-verified"))
        results.append(compare(load(ref), load(clean_B), "full-pipeline reference (700-run subset) vs clean two-stage replicate", "reference_vs_replicate", m, "both Llama-verified"))
    # verifier determinism across stacks on identical rows
    vname = {"llama31_8b": "llama", "qwen25_7b": "qwen", "mistral7b": "mistral"}[m]
    for c, fn in (("B", "baseline_b_structured_no_gate_verifier.csv"), ("C", "baseline_c_single_stage_external_verifier.csv")):
        fresh = X0 / f"out/archived_{m}_{c}__verifier_{vname}.csv"
        if fresh.exists():
            results.append(compare(load(ARCH / m / fn), load(fresh), f"{c}: identical archived rows, archived verdict vs fresh vLLM verdict", "verifier_repro", m, f"verifier = {vname} (self) in both"))
(OUT / "row_level_reproducibility_results.json").write_text(json.dumps(results, indent=2))
cols = ["n_matched", "all_fields_exact_pct", "sentence_exact_pct", "sentence_token_jaccard_mean", "consensus_key_same_pct", "trackA_agreement_pct", "trackA_kappa",
        "trackB_agreement_pct", "trackB_kappa", "overclaim_agreement_pct", "overclaim_kappa", "joint_state_agreement_pct", "jaccard_keep_only", "jaccard_keep_or_revise", "jaccard_keep_or_revise_trackA_pass"]
lines = ["# Row-level reproducibility (matched by PMID)", "", "| extractor | pair | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 2)]
for r in results: lines.append(f"| {r['extractor']} | {r['pair']} ({r['note']}) | " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
lines += ["", "## Per-field exact agreement (%)", "", "| extractor | pair | " + " | ".join(f.replace("extracted_", "") for f in FIELDS) + " |", "|" + "---|" * (len(FIELDS) + 2)]
for r in results:
    if r["type"] != "verifier_repro": lines.append(f"| {r['extractor']} | {r['pair']} | " + " | ".join(str(r[f"field_exact::{f}"]) for f in FIELDS) + " |")
lines += ["", "## Track-B transition matrices (run1 -> run2)", ""]
for r in results: lines.append(f"- {r['extractor']} | {r['pair']}: {r['trackB_transition_run1_to_run2']}  (overclaim yes: {r['overclaim_yes_run1']} -> {r['overclaim_yes_run2']})")
(OUT / "row_level_reproducibility_results.md").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
