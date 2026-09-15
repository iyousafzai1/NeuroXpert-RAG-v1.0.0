"""Paired (per-document) McNemar tests replacing the independent two-proportion z-tests for extractor-pair rate comparisons.
The three extractors processed the SAME 700 abstracts, so each headline rate comparison is a paired binary outcome per PMID.
Exact McNemar (two-sided binomial on the discordant pairs), Holm-Bonferroni within each metric over the three planned pairs.
Metrics: Track-A strict groundedness (all four predicates), Track-B keep-or-revise, automatic overclaim flag."""
import csv, json, math, pathlib, itertools
FIG = pathlib.Path("/Users/irfankhan/Documents/project 4/Egyptial_Informatics_Journal/neuroxpert_rag/results_package_mature_2026_05_29/03_figure_source_data")
MODELS = [("Llama", "final_llama31_8b_700"), ("Qwen", "final_qwen25_7b_700"), ("Mistral", "final_mistral7b_700")]
tb = lambda v: str(v).strip().lower() in ("true", "1", "yes", "t")
data = {}
for name, d in MODELS:
    for r in csv.DictReader(open(FIG / d / "semantic_llm_verifier_all.csv", encoding="utf-8")):
        data.setdefault(name, {})[r["pmid"]] = {"trackA": all(tb(r[k]) for k in ("schema_valid", "citation_valid", "sentence_present", "sentence_anchored")),
                                                 "trackB_kr": r["verifier_decision"].strip().lower() in ("keep", "revise"),
                                                 "overclaim": r["verifier_overclaiming"].strip().lower() == "yes"}
pmids = sorted(set.intersection(*(set(v) for v in data.values()))); assert len(pmids) == 700, len(pmids)
def binom_two_sided(k, n):
    if n == 0: return 1.0
    p = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n * 2
    return min(1.0, p)
def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0] * len(ps); m = len(ps); run = 0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * ps[i]); adj[i] = min(1.0, run)
    return adj
res = {}; lines = ["# Paired McNemar tests (exact, two-sided; Holm-Bonferroni over the three model pairs within each metric); n = 700 shared abstracts", "",
                   "| metric | pair | rate A | rate B | Δ (pp) | discordant b / c | p (raw) | p (Holm) |", "|---|---|---|---|---|---|---|---|"]
for metric in ("trackA", "trackB_kr", "overclaim"):
    pairs = list(itertools.combinations([m for m, _ in MODELS], 2)); ps = []; rowsm = []
    for a, b in pairs:
        ra = sum(data[a][p][metric] for p in pmids) / 700; rb = sum(data[b][p][metric] for p in pmids) / 700
        bc = sum(data[a][p][metric] and not data[b][p][metric] for p in pmids); cb = sum(data[b][p][metric] and not data[a][p][metric] for p in pmids)
        p = binom_two_sided(min(bc, cb), bc + cb); ps.append(p); rowsm.append((a, b, ra, rb, bc, cb, p))
    adj = holm(ps)
    for (a, b, ra, rb, bc, cb, p), pa in zip(rowsm, adj):
        res[f"{metric}|{a}-{b}"] = {"rate_a": ra, "rate_b": rb, "diff_pp": 100 * (ra - rb), "discordant_a_only": bc, "discordant_b_only": cb, "p_raw": p, "p_holm": pa}
        lines.append(f"| {metric} | {a}–{b} | {ra:.3f} | {rb:.3f} | {100*(ra-rb):+.1f} | {bc} / {cb} | {p:.2e} | {pa:.3g} |")
json.dump(res, open(pathlib.Path(__file__).parent / "mcnemar_paired_model_tests.json", "w"), indent=2)
(pathlib.Path(__file__).parent / "mcnemar_paired_model_tests.md").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
