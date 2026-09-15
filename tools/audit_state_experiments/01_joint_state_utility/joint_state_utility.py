"""Joint Track-A x Track-B utility analysis on the 120-row human-rated sample (Step 1 / Experiment 2). No model calls.

Rows: S120 (40 Track-B keep / 40 revise / 40 drop, drawn from all 2,100 archived records; Evaluator 1 and Evaluator 2).
Track A status is joined from the archived 700-abstract runs (answer key: model_label + pmid + record_id);
pass = schema_valid & citation_valid & sentence_present & sentence_anchored (the manuscript's Track-A definition).
Reported: raw six-cell counts; within-cell human-label percentages; inverse-probability-weighted (IPW) estimates
(weight = population stratum size / 40, strata = Track-B decision); population projections onto the 2,100 rows;
stratified bootstrap 95% CIs (resampling within the three Track-B strata; B = 10,000; seed 20260914).
Question A: A=fail & B in {keep,revise}  -> share the humans consider keep/revise (what a terminal Track-A gate would discard).
Question B: A=pass & B=drop              -> share the humans also drop (what Track-A-only acceptance would admit).
"""
import csv, json, random, collections, pathlib, statistics
SRC = pathlib.Path("/Users/irfankhan/Documents/project 4/Egyptial_Informatics_Journal/neuroxpert_rag/results_package_mature_2026_05_29")
FIG = SRC / "03_figure_source_data"; OUT = pathlib.Path(__file__).parent
MODELS = {"Llama 3.1 8B": "final_llama31_8b_700", "Qwen 2.5 7B": "final_qwen25_7b_700", "Mistral 7B": "final_mistral7b_700"}
tb = lambda v: str(v).strip().lower() in ("true", "1", "yes", "t")
A_of = lambda r: "pass" if all(tb(r[k]) for k in ("schema_valid", "citation_valid", "sentence_present", "sentence_anchored")) else "fail"

full = {}
for m, d in MODELS.items():
    for r in csv.DictReader(open(FIG / d / "semantic_llm_verifier_all.csv", encoding="utf-8")):
        full[(m, r["pmid"], r["record_id"])] = r
key = {r["annotation_id"]: r for r in csv.DictReader(open(SRC / "08_human_validation_package/human_annotation_answer_key_120.csv", encoding="utf-8"))}
s120 = [json.loads(l) for l in open("/Users/irfankhan/Documents/papers/NeuroXpert-RAG_JKSUCIS_Springer_Submission/tools/comparators/data/rows_120.jsonl", encoding="utf-8")]
rows = []
for hv in s120:
    k = key[hv["id"]]; r = full[(k["model_label"], k["pmid"], k["record_id"])]
    assert r["verifier_decision"].strip().lower() == hv["track_b"]
    rows.append({"id": hv["id"], "extractor": k["model_label"], "pmid": k["pmid"], "record_id": k["record_id"], "A": A_of(r), "B": hv["track_b"],
                 "E1": hv["evaluator_1"], "E2": hv["evaluator_2"], "track_a_failures": ";".join(x for x in ("schema_valid","citation_valid","sentence_present","sentence_anchored") if not tb(r[x]))})
# population (2,100 rows) joint matrix and strata sizes
popcell = collections.Counter((A_of(r), r["verifier_decision"].strip().lower()) for r in full.values())
popB = collections.Counter(b for (_, b) in popcell.elements())
n_s = collections.Counter(r["B"] for r in rows); W = {b: popB[b] / n_s[b] for b in n_s}
for r in rows: r["ipw"] = W[r["B"]]
with open(OUT / "s120_joint_state_rows.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

acc = lambda lab: lab in ("keep", "revise")
def est(sub, pred, weighted):
    """proportion of rows in sub satisfying pred (IPW-weighted if weighted)."""
    if not sub: return float("nan")
    num = sum((r["ipw"] if weighted else 1) for r in sub if pred(r)); den = sum((r["ipw"] if weighted else 1) for r in sub)
    return num / den
QUESTIONS = {
  "A_gate_would_discard_human_acceptable": (lambda r: r["A"] == "fail" and r["B"] in ("keep", "revise"), {
      "E1_acceptable": lambda r: acc(r["E1"]), "E2_acceptable": lambda r: acc(r["E2"]),
      "both_acceptable": lambda r: acc(r["E1"]) and acc(r["E2"]), "either_acceptable": lambda r: acc(r["E1"]) or acc(r["E2"])}),
  "B_trackA_only_would_admit_human_rejected": (lambda r: r["A"] == "pass" and r["B"] == "drop", {
      "E1_drop": lambda r: r["E1"] == "drop", "E2_drop": lambda r: r["E2"] == "drop",
      "both_drop": lambda r: r["E1"] == "drop" and r["E2"] == "drop", "either_drop": lambda r: r["E1"] == "drop" or r["E2"] == "drop"}),
  "C_agreement_pass_keeprevise_human_acceptable": (lambda r: r["A"] == "pass" and r["B"] in ("keep", "revise"), {
      "E1_acceptable": lambda r: acc(r["E1"]), "E2_acceptable": lambda r: acc(r["E2"]), "both_acceptable": lambda r: acc(r["E1"]) and acc(r["E2"])}),
  "D_agreement_fail_drop_human_drop": (lambda r: r["A"] == "fail" and r["B"] == "drop", {
      "E1_drop": lambda r: r["E1"] == "drop", "E2_drop": lambda r: r["E2"] == "drop", "both_drop": lambda r: r["E1"] == "drop" and r["E2"] == "drop"}),
}
rng = random.Random(20260914); B = 10000
strata = {b: [r for r in rows if r["B"] == b] for b in ("keep", "revise", "drop")}
boot = [[rng.choice(strata[b]) for b in strata for _ in range(len(strata[b]))] for _ in range(B)]
def ci(cellpred, pred, weighted):
    vals = [est([r for r in bs if cellpred(r)], pred, weighted) for bs in boot]
    vals = sorted(v for v in vals if v == v)
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1], len(vals)) if vals else (float("nan"),) * 3

out = {"population_joint_matrix_2100": {f"{a}/{b}": n for (a, b), n in sorted(popcell.items())},
       "population_trackB_strata": dict(popB), "sample_strata": dict(n_s), "ipw_weights": W,
       "s120_cells": {f"{a}/{b}": n for (a, b), n in sorted(collections.Counter((r["A"], r["B"]) for r in rows).items())},
       "s120_cell_label_distributions": {}, "questions": {}}
for (a, b), _ in sorted(collections.Counter((r["A"], r["B"]) for r in rows).items()):
    sub = [r for r in rows if r["A"] == a and r["B"] == b]
    out["s120_cell_label_distributions"][f"{a}/{b}"] = {"n": len(sub), "E1": dict(collections.Counter(r["E1"] for r in sub)),
        "E2": dict(collections.Counter(r["E2"] for r in sub)), "both_agree": dict(collections.Counter(r["E1"] for r in sub if r["E1"] == r["E2"]))}
for qname, (cellpred, preds) in QUESTIONS.items():
    sub = [r for r in rows if cellpred(r)]
    popN = sum(n for (a, b), n in popcell.items() if cellpred({"A": a, "B": b}))
    q = {"n_s120": len(sub), "n_population_2100": popN, "by_extractor": dict(collections.Counter(r["extractor"] for r in sub)), "estimates": {}}
    for pname, pred in preds.items():
        raw = est(sub, pred, False); ipw = est(sub, pred, True)
        lo, hi, nb = ci(cellpred, pred, True); lo_r, hi_r, _ = ci(cellpred, pred, False)
        q["estimates"][pname] = {"count": sum(1 for r in sub if pred(r)), "raw_pct": round(100 * raw, 1), "raw_ci95": [round(100 * lo_r, 1), round(100 * hi_r, 1)],
                                 "ipw_pct": round(100 * ipw, 1), "ipw_ci95": [round(100 * lo, 1), round(100 * hi, 1)], "bootstrap_reps_nonempty": nb,
                                 "projected_rows_in_2100": round(popN * ipw, 0), "projected_ci95": [round(popN * lo, 0), round(popN * hi, 0)]}
    out["questions"][qname] = q
(OUT / "joint_state_utility_results.json").write_text(json.dumps(out, indent=2))
# human-readable table
lines = ["# Joint Track-A x Track-B utility on the 120-row human sample", "",
         "Population joint matrix (2,100 rows): " + ", ".join(f"{k}={v}" for k, v in out["population_joint_matrix_2100"].items()), "",
         "| Cell (A/B) | n S120 | E1 keep/revise/drop | E2 keep/revise/drop | both agree keep/revise/drop |", "|---|---|---|---|---|"]
for c, d in out["s120_cell_label_distributions"].items():
    g = lambda D: "/".join(str(D.get(x, 0)) for x in ("keep", "revise", "drop"))
    lines.append(f"| {c} | {d['n']} | {g(d['E1'])} | {g(d['E2'])} | {g(d['both_agree'])} |")
lines += ["", "| Question | cell n (S120 / 2,100) | criterion | count | raw % [CI] | IPW % [CI] | projected rows in 2,100 [CI] |", "|---|---|---|---|---|---|---|"]
for qn, q in out["questions"].items():
    for pn, e in q["estimates"].items():
        lines.append(f"| {qn} | {q['n_s120']} / {q['n_population_2100']} | {pn} | {e['count']} | {e['raw_pct']} [{e['raw_ci95'][0]}, {e['raw_ci95'][1]}] | {e['ipw_pct']} [{e['ipw_ci95'][0]}, {e['ipw_ci95'][1]}] | {e['projected_rows_in_2100']:.0f} [{e['projected_ci95'][0]:.0f}, {e['projected_ci95'][1]:.0f}] |")
(OUT / "joint_state_utility_results.md").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
