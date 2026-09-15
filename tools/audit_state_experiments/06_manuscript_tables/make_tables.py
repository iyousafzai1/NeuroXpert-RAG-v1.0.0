"""Generate every LaTeX table row / number snippet that the round-2 integration inserts into the manuscript and the
Supplementary, reading only the result JSON files of Steps 0-5 and tools/ablation_clean/ablation_conditions.json.
Outputs *.tex snippet files consumed by tools/confidence_rewrite.py (section I) and numbers.json for the text."""
import json, pathlib, csv
H = pathlib.Path(__file__).resolve().parent; R = H.parent; T = R.parent
J = lambda p: json.load(open(p))
abl = J(T / "ablation_clean/ablation_conditions.json"); xo = J(R / "00_paired_crossover/crossover_summary.json")
ju = J(R / "01_joint_state_utility/joint_state_utility_results.json"); rr = J(R / "02_row_level_reproducibility/row_level_reproducibility_results.json")
mi = J(R / "03_matched_input_trackb/matched_input_metrics.json"); ta = J(R / "04_fault_injection/track_a_fault_injection_results.json")
pd_ = J(R / "05_paired_statistics/paired_auroc_differences.json"); mc = J(R / "05_paired_statistics/mcnemar_paired_model_tests.json")
sha = dict(l.split()[::-1] for l in open(R / "00_paired_crossover/inputs/SHA256SUMS.txt"))
N = {}
pct = lambda x: f"{round(x*100):d}\\%"; f3 = lambda x: f"{x:.3f}"
# ---------------- Table 7 rows (main) ----------------
SHORT = {"full": "Full pipeline (two-stage, fixed verifier; reference run)", "b_fixed": "Two-stage, fixed verifier, re-extracted",
         "b_self": "Two-stage, self-verification (same rows)", "c_fixed": "Single-stage, fixed verifier", "c_self": "Single-stage, self-verification (same rows)", "naive": "Naive free-form RAG"}
rows = []
for k in ("full", "b_fixed", "b_self", "c_fixed", "c_self", "naive"):
    e = abl[k]; m = e["mean"]; per = e["per_model"]
    oc = lambda d: "---" if per[d].get("overclaim_count") is None else str(int(per[d]["overclaim_count"]))
    v = lambda key, bold=False: ("---" if m[key] is None else (("\\textbf{" + pct(m[key]) + "}") if bold else pct(m[key])))
    rows.append(f"{SHORT[k]} & {v('schema_valid_rate', k=='full')} & {v('quote_anchor_rate')} & {v('semantic_keep_rate')} & {v('overclaim_rate', k=='full')} & {v('useful_evidence_retained_rate')} & {oc('Llama 3.1 8B')} / {oc('Qwen 2.5 7B')} / {oc('Mistral 7B')} \\\\")
(H / "table7_rows.tex").write_text("\n".join(rows) + "\n")
for k in ("b_self", "c_self"):
    for d in ("Llama 3.1 8B", "Qwen 2.5 7B", "Mistral 7B"): N[f"oc_{k}_{d.split()[0]}"] = int(abl[k]["per_model"][d]["overclaim_count"])
    N[f"mean_over_{k}"] = round(abl[k]["mean"]["overclaim_rate"] * 100)
# ---------------- Crossover (Supplementary S20) ----------------
q = {(r["extractor"], r["condition"], r["row_set"], r["verdict_source"]): r for r in xo}
mpx = {"llama31_8b": "Llama~3.1~8B", "qwen25_7b": "Qwen~2.5~7B", "mistral7b": "Mistral~7B"}; SELFX = {"llama31_8b": "llama", "qwen25_7b": "qwen", "mistral7b": "mistral"}
fmtx = lambda r: f"{r['keep']}/{r['revise']}/{r['drop']} ({r['overclaim_yes']})"
xrows = []
for m in ("llama31_8b", "qwen25_7b", "mistral7b"):
    for c in ("B", "C"):
        for src in ("archived", "clean"):
            o = q[(m, c, src, "original run")]; fl = q[(m, c, src, "fresh (vLLM) Llama")]; fs = q.get((m, c, src, f"fresh (vLLM) self = {SELFX[m]}"))
            xrows.append(f"{mpx[m]} & {c} & {src} \\texttt{{{o['sha256'][:12]}}} & {fmtx(o)} & {fmtx(fl)} & {fmtx(fs) if fs else '= Llama'} \\\\")
(H / "tableS_crossover_rows.tex").write_text("\n".join(xrows) + "\n")
q = {(r["extractor"], r["condition"], r["row_set"], r["verdict_source"]): r for r in xo}
N["xo_qwenB_arch_llama"] = q[("qwen25_7b", "B", "archived", "fresh (vLLM) Llama")]["overclaim_yes"]; N["xo_qwenB_arch_self"] = q[("qwen25_7b", "B", "archived", "fresh (vLLM) self = qwen")]["overclaim_yes"]
N["xo_qwenC_arch_llama"] = q[("qwen25_7b", "C", "archived", "fresh (vLLM) Llama")]["overclaim_yes"]; N["xo_qwenC_arch_self"] = q[("qwen25_7b", "C", "archived", "fresh (vLLM) self = qwen")]["overclaim_yes"]
N["xo_qwenB_clean_self"] = q[("qwen25_7b", "B", "clean", "fresh (vLLM) self = qwen")]["overclaim_yes"]; N["xo_qwenC_clean_self"] = q[("qwen25_7b", "C", "clean", "fresh (vLLM) self = qwen")]["overclaim_yes"]
rw = [r["rowwise_same_verifier_archived_vs_fresh"] for r in xo if "rowwise_same_verifier_archived_vs_fresh" in r]
N["stack_dec_min"] = min(x["decision_agree"] for x in rw); N["stack_dec_max"] = max(x["decision_agree"] for x in rw)
N["stack_oc_min"] = min(x["overclaim_agree"] for x in rw); N["stack_oc_max"] = max(x["overclaim_agree"] for x in rw)
# ---------------- Joint-state utility (main Table 8 + Supplementary S21) ----------------
Q = ju["questions"]; cells = ju["s120_cell_label_distributions"]
def est(qn, crit): e = Q[qn]["estimates"][crit]; return e
A = Q["A_gate_would_discard_human_acceptable"]; Bq = Q["B_trackA_only_would_admit_human_rejected"]
N.update(jA_n=A["n_s120"], jA_pop=A["n_population_2100"], jA_e1=est("A_gate_would_discard_human_acceptable", "E1_acceptable")["count"], jA_e2=est("A_gate_would_discard_human_acceptable", "E2_acceptable")["count"],
         jA_both=est("A_gate_would_discard_human_acceptable", "both_acceptable")["count"], jA_ipw=est("A_gate_would_discard_human_acceptable", "both_acceptable")["ipw_pct"],
         jA_ci=est("A_gate_would_discard_human_acceptable", "both_acceptable")["ipw_ci95"], jA_proj=est("A_gate_would_discard_human_acceptable", "both_acceptable")["projected_rows_in_2100"],
         jA_proj_ci=est("A_gate_would_discard_human_acceptable", "both_acceptable")["projected_ci95"],
         jB_n=Bq["n_s120"], jB_pop=Bq["n_population_2100"], jB_e1=est("B_trackA_only_would_admit_human_rejected", "E1_drop")["count"], jB_e2=est("B_trackA_only_would_admit_human_rejected", "E2_drop")["count"],
         jB_e1_pct=est("B_trackA_only_would_admit_human_rejected", "E1_drop")["raw_pct"], jB_e2_pct=est("B_trackA_only_would_admit_human_rejected", "E2_drop")["raw_pct"],
         jB_e2_ci=est("B_trackA_only_would_admit_human_rejected", "E2_drop")["ipw_ci95"], jB_e1_ci=est("B_trackA_only_would_admit_human_rejected", "E1_drop")["ipw_ci95"],
         jB_e1_revise=cells["pass/drop"]["E1"].get("revise", 0), jB_e1_keep=cells["pass/drop"]["E1"].get("keep", 0), jB_e2_keep=cells["pass/drop"]["E2"].get("keep", 0),
         jC_both=est("C_agreement_pass_keeprevise_human_acceptable", "both_acceptable")["raw_pct"], jC_n=Q["C_agreement_pass_keeprevise_human_acceptable"]["n_s120"],
         jD_e1=est("D_agreement_fail_drop_human_drop", "E1_drop")["raw_pct"], jD_e2=est("D_agreement_fail_drop_human_drop", "E2_drop")["raw_pct"], jD_n=Q["D_agreement_fail_drop_human_drop"]["n_s120"],
         ipw=ju["ipw_weights"])
def cirng(c): return f"{c[0]:.1f}--{c[1]:.1f}"
t8 = [f"Track~A fail, Track~B keep/revise & {A['n_s120']} / {A['n_population_2100']} & keep or revise & {N['jA_e1']} & {N['jA_e2']} & {N['jA_both']} & {N['jA_ipw']:.0f} [{cirng(N['jA_ci'])}] & $\\approx${N['jA_proj']:.0f} [{N['jA_proj_ci'][0]:.0f}--{N['jA_proj_ci'][1]:.0f}] \\\\",
      f"Track~A pass, Track~B drop & {Bq['n_s120']} / {Bq['n_population_2100']} & drop & {N['jB_e1']} & {N['jB_e2']} & {est('B_trackA_only_would_admit_human_rejected','both_drop')['count']} & E1 {N['jB_e1_pct']:.0f} [{cirng(N['jB_e1_ci'])}]; E2 {N['jB_e2_pct']:.0f} [{cirng(N['jB_e2_ci'])}] & E2 $\\approx${est('B_trackA_only_would_admit_human_rejected','E2_drop')['projected_rows_in_2100']:.0f} [{est('B_trackA_only_would_admit_human_rejected','E2_drop')['projected_ci95'][0]:.0f}--{est('B_trackA_only_would_admit_human_rejected','E2_drop')['projected_ci95'][1]:.0f}] \\\\",
      f"Track~A pass, Track~B keep/revise & {Q['C_agreement_pass_keeprevise_human_acceptable']['n_s120']} / {Q['C_agreement_pass_keeprevise_human_acceptable']['n_population_2100']} & keep or revise & {est('C_agreement_pass_keeprevise_human_acceptable','E1_acceptable')['count']} & {est('C_agreement_pass_keeprevise_human_acceptable','E2_acceptable')['count']} & {est('C_agreement_pass_keeprevise_human_acceptable','both_acceptable')['count']} & {est('C_agreement_pass_keeprevise_human_acceptable','both_acceptable')['ipw_pct']:.0f} [{cirng(est('C_agreement_pass_keeprevise_human_acceptable','both_acceptable')['ipw_ci95'])}] & --- \\\\",
      f"Track~A fail, Track~B drop & {Q['D_agreement_fail_drop_human_drop']['n_s120']} / {Q['D_agreement_fail_drop_human_drop']['n_population_2100']} & drop & {est('D_agreement_fail_drop_human_drop','E1_drop')['count']} & {est('D_agreement_fail_drop_human_drop','E2_drop')['count']} & {est('D_agreement_fail_drop_human_drop','both_drop')['count']} & {est('D_agreement_fail_drop_human_drop','both_drop')['ipw_pct']:.0f} [{cirng(est('D_agreement_fail_drop_human_drop','both_drop')['ipw_ci95'])}] & --- \\\\"]
(H / "table8_rows.tex").write_text("\n".join(t8) + "\n")
s21 = []
for c, d in cells.items():
    g = lambda D: "/".join(str(D.get(x, 0)) for x in ("keep", "revise", "drop"))
    a, b = c.split("/"); s21.append(f"{a} & {b} & {d['n']} & {ju['population_joint_matrix_2100'][c]} & {g(d['E1'])} & {g(d['E2'])} & {g(d['both_agree'])} \\\\")
(H / "tableS_jointstate_rows.tex").write_text("\n".join(s21) + "\n")
# ---------------- Row-level reproducibility (Supplementary S22) ----------------
s22 = []; mp = {"llama31_8b": "Llama~3.1~8B", "qwen25_7b": "Qwen~2.5~7B", "mistral7b": "Mistral~7B"}
for r in rr:
    if r["type"] == "verifier_repro": continue
    lab = {"extraction_repro": ("B" if "two-stage" in r["pair"] else "C") + ": archived vs clean", "reference_vs_replicate": "reference vs clean B"}[r["type"]]
    k3 = lambda x: "---" if x != x else f"{x:.3f}"
    s22.append(f"{mp[r['extractor']]} & {lab} & {r['all_fields_exact_pct']:.0f} & {r['sentence_exact_pct']:.0f} & {r['consensus_key_same_pct']:.0f} & {r['trackA_agreement_pct']:.0f} ({k3(r['trackA_kappa'])}) & {r['trackB_agreement_pct']:.0f} ({k3(r['trackB_kappa'])}) & {r['overclaim_agreement_pct']:.0f} ({k3(r['overclaim_kappa'])}) & {r['jaccard_keep_only']:.3f} & {r['jaccard_keep_or_revise']:.3f} \\\\")
(H / "tableS_repro_rows.tex").write_text("\n".join(s22) + "\n")
ref = [r for r in rr if r["type"] == "reference_vs_replicate"]; two = [r for r in rr if r["type"] == "extraction_repro" and "two-stage" in r["pair"]]
allp = ref + two
N.update(rr_trackA_k=(min(r["trackA_kappa"] for r in allp), max(r["trackA_kappa"] for r in allp)), rr_trackB_k=(min(r["trackB_kappa"] for r in allp), max(r["trackB_kappa"] for r in allp)),
         rr_oc_k=(min(r["overclaim_kappa"] for r in allp), max(r["overclaim_kappa"] for r in allp)), rr_jacc=(min(r["jaccard_keep_or_revise"] for r in allp), max(r["jaccard_keep_or_revise"] for r in allp)),
         rr_ref_trackB_k=(min(r["trackB_kappa"] for r in ref), max(r["trackB_kappa"] for r in ref)), rr_ref_jacc=(min(r["jaccard_keep_or_revise"] for r in ref), max(r["jaccard_keep_or_revise"] for r in ref)),
         rr_ref_trackA_k=(min(r["trackA_kappa"] for r in ref), max(r["trackA_kappa"] for r in ref)), rr_ref_oc_k=(min(r["overclaim_kappa"] for r in ref), max(r["overclaim_kappa"] for r in ref)),
         rr_allfields=(min(r["all_fields_exact_pct"] for r in ref), max(r["all_fields_exact_pct"] for r in ref)))
cv = ["extracted_phenotype", "extracted_feature_type", "extracted_relationship", "extracted_direction", "extracted_directness"]; ft = ["extracted_mechanism", "extracted_diagnostic_context"]
N["rr_cv_fields"] = (min(r[f"field_exact::{f}"] for r in ref for f in cv), max(r[f"field_exact::{f}"] for r in ref for f in cv)); N["rr_ft_fields"] = (min(r[f"field_exact::{f}"] for r in ref for f in ft), max(r[f"field_exact::{f}"] for r in ref for f in ft))
# ---------------- Matched input (Table 13 rows + Supplementary) ----------------
M = mi["metrics"]; fmt = lambda x: "---" if x is None else f3(x)
def row13(method, label, setname, ref, bold_none=True):
    out = []
    for v, vname in (("strict", "strict support"), ("retention", "review retention")):
        e = M[f"{method}|{setname}|{ref}|{v}"]; ci = e.get("ci95", {}).get("auroc")
        cis = f" [{ci[0]:.3f}--{ci[1]:.3f}]" if ci else ""
        out.append(f"{label if v=='strict' else ''} & {vname} & {f3(e['auroc'])}{cis} & {f3(e['auprc'])} & {fmt(e.get('precision'))} & {fmt(e.get('recall'))} & {fmt(e.get('f1'))} & {fmt(e.get('kappa'))} \\\\")
    return out
(H / "table13_matched_rows.tex").write_text("\n".join(row13("trackb-matched-native-instr", "Track~B, matched input", "s120", "evaluator_2")) + "\n")
supp = row13("trackb-matched-native-instr", "Own instruction block", "s120", "evaluator_1") + row13("trackb-matched-minimal", "Bare claim/evidence prompt", "s120", "evaluator_1")
supp2 = row13("trackb-matched-native-instr", "Own instruction block", "s120", "evaluator_2") + row13("trackb-matched-minimal", "Bare claim/evidence prompt", "s120", "evaluator_2")
supp3 = row13("trackb-matched-native-instr", "Own instruction block", "s300", "track_b") + row13("trackb-matched-minimal", "Bare claim/evidence prompt", "s300", "track_b")
(H / "tableS_matched_e1_rows.tex").write_text("\n".join(supp) + "\n"); (H / "tableS_matched_e2_rows.tex").write_text("\n".join(supp2) + "\n"); (H / "tableS_matched_s300_rows.tex").write_text("\n".join(supp3) + "\n")
e = lambda v, ref="evaluator_2": M[f"trackb-matched-native-instr|s120|{ref}|{v}"]
N.update(mi_strict_auroc=e("strict")["auroc"], mi_strict_ci=e("strict")["ci95"]["auroc"], mi_ret_auroc=e("retention")["auroc"], mi_strict_f1=e("strict")["f1"], mi_strict_k=e("strict")["kappa"],
         mi_ret_f1=e("retention")["f1"], mi_ret_k=e("retention")["kappa"], mi_min_strict_auroc=M["trackb-matched-minimal|s120|evaluator_2|strict"]["auroc"], mi_min_ret_auroc=M["trackb-matched-minimal|s120|evaluator_2|retention"]["auroc"],
         mi_e1_strict_auroc=e("strict", "evaluator_1")["auroc"], mi_e1_ret_k=e("retention", "evaluator_1")["kappa"], mi_e1_strict_k=e("strict", "evaluator_1")["kappa"],
         mi_s300_k=mi["agreement_with_native_trackb"]["trackb-matched-native-instr|s300"]["kappa"], mi_s120_k=mi["agreement_with_native_trackb"]["trackb-matched-native-instr|s120"]["kappa"],
         mi_min_s300_k=mi["agreement_with_native_trackb"]["trackb-matched-minimal|s300"]["kappa"])
# paired AUROC differences
pdrows = []
for key, r in pd_.items():
    ref, v, a, b = key.split("|"); pdrows.append(f"{ref.replace('_',' ').replace('evaluator','Evaluator')} & {v} & {a} & {b} & {r['auroc_a']:.3f} & {r['auroc_b']:.3f} & {r['diff']:+.3f} & [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] & {r['p_a_greater']:.2f} \\\\")
(H / "tableS_paired_auroc_rows.tex").write_text("\n".join(pdrows).replace("trackb-matched-native-instr", "Track~B matched").replace("track-b", "Track~B").replace("minicheck-bespoke-7b", "Bespoke-MiniCheck-7B").replace("deberta-nli", "DeBERTa-NLI").replace("alignscore-large-official", "AlignScore-large") + "\n")
g = lambda k: pd_[k]
N.update(pd_tb_mc=g("evaluator_2|strict|track-b|minicheck-bespoke-7b"), pd_tb_mc_ret=g("evaluator_2|retention|track-b|minicheck-bespoke-7b"), pd_tb_as_ret=g("evaluator_2|retention|track-b|alignscore-large-official"),
         pd_tb_mi=g("evaluator_2|strict|track-b|trackb-matched-native-instr"), pd_tb_mi_ret=g("evaluator_2|retention|track-b|trackb-matched-native-instr"), pd_mi_mc=g("evaluator_2|strict|trackb-matched-native-instr|minicheck-bespoke-7b"))
# ---------------- McNemar ----------------
mcr = []
for key, r in mc.items():
    met, pair = key.split("|"); mcr.append(f"{ {'trackA':'Track~A strict groundedness','trackB_kr':'Track~B keep-or-revise','overclaim':'Automatic overclaim flag'}[met] } & {pair.replace('-','--')} & {r['rate_a']:.3f} & {r['rate_b']:.3f} & {r['diff_pp']:+.1f} & {r['discordant_a_only']} / {r['discordant_b_only']} & {('$<10^{-6}$' if r['p_holm'] < 1e-6 else f'{r['p_holm']:.3f}')} \\\\")
(H / "tableS_mcnemar_rows.tex").write_text("\n".join(mcr) + "\n")
N.update(mc_trackB={k.split('|')[1]: v["p_holm"] for k, v in mc.items() if k.startswith("trackB_kr")}, mc_over_min=min(v["p_holm"] for k, v in mc.items() if k.startswith("overclaim")),
         mc_trackA_max=max(v["p_holm"] for k, v in mc.items() if k.startswith("trackA")))
# ---------------- Track A fault injection (main Table 12 + Supplementary S24) ----------------
BF = ta["by_fault_type"]; PRETTY = {"wrong_pmid_in_corpus": "Wrong PMID (another corpus document)", "wrong_pmid_not_in_corpus": "Wrong PMID (absent from corpus)", "sentence_from_other_pmid": "Sentence taken from another abstract",
    "number_changed": "One numeral altered", "direction_word_changed": "One direction word altered", "sentence_composed_two_abstracts": "Span spliced from two abstracts", "word_dropped": "One word dropped",
    "schema_missing_field": "Required schema field missing", "schema_strength_out_of_range": "Evidence strength outside $[0,1]$", "whitespace_variant": "Whitespace re-flowed", "nbsp_variant": "Non-breaking spaces",
    "trailing_period_removed": "Trailing period removed", "case_variant": "Initial letter case changed", "unicode_dash_quote_variant": "ASCII dash/quote $\\rightarrow$ Unicode", "truncated_quote": "Truncated verbatim span"}
CLASS = {"reject": "Corruption", "retain": "Normalization variant", "surface": "Outside the normalization contract"}
t12 = []; s24 = []
for ft, d in BF.items():
    t12.append(f"{CLASS[d['expected']]} & {PRETTY[ft]} & {d['n']} & {d['rejected']} & {d['retained']} \\\\")
    s24.append(f"{CLASS[d['expected']]} & {PRETTY[ft]} & {d['n']} & {d['rejected']} & {d['retained']} & {d['rejection_rate']:.1f} & {d['failing_checks'].replace('_','\\_') or '---'} \\\\")
(H / "table12_rows.tex").write_text("\n".join(t12) + "\n"); (H / "tableS_trackA_rows.tex").write_text("\n".join(s24) + "\n")
N.update(ta_base=ta["n_base_rows"], ta_corrupt_n=sum(d["n"] for d in BF.values() if d["expected"] == "reject"), ta_corrupt_rej=sum(d["rejected"] for d in BF.values() if d["expected"] == "reject"),
         ta_norm_n=sum(d["n"] for d in BF.values() if d["expected"] == "retain"), ta_norm_ret=sum(d["retained"] for d in BF.values() if d["expected"] == "retain"),
         ta_total=sum(d["n"] for d in BF.values()), ta_case_rej=BF["case_variant"]["rejected"], ta_case_n=BF["case_variant"]["n"], ta_uni_n=BF["unicode_dash_quote_variant"]["n"], ta_trunc_n=BF["truncated_quote"]["n"], ta_trunc_ret=BF["truncated_quote"]["retained"])
assert N["ta_corrupt_rej"] == N["ta_corrupt_n"] and N["ta_norm_ret"] == N["ta_norm_n"]
json.dump(N, open(H / "numbers.json", "w"), indent=2, default=list); print(json.dumps(N, indent=1, default=list)[:3000])
