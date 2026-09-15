"""Paired bootstrap 95% CIs for AUROC DIFFERENCES between verifiers on the same S120 rows (both evaluators, both views).
Same resampling scheme as the frozen protocol (stratified within Track-B strata, B = 10,000, seed 20260914); each
replicate computes both AUROCs on the same resampled rows and stores the difference. Reported: point difference,
percentile CI, and the fraction of replicates in which the first method is higher."""
import csv, json, math, pathlib, random
HERE = pathlib.Path(__file__).resolve().parent; C = HERE.parents[0].parent / "comparators"
rows = {}
for l in open(C / "data/rows_120.jsonl"):
    if l.strip(): r = json.loads(l); rows[r["id"]] = r
def view(label, v): return (1 if label == "keep" else 0) if v == "strict" else (1 if label in ("keep", "revise") else 0)
def auroc(scores, y):
    pos = [s for s, t in zip(scores, y) if t == 1]; neg = [s for s, t in zip(scores, y) if t == 0]
    if not pos or not neg: return float("nan")
    return sum((1.0 if p > n else 0.5 if p == n else 0.0) for p in pos for n in neg) / (len(pos) * len(neg))
S = {}
for f in sorted((C / "scores").glob("scores_*.csv")):
    if f.name == "scores_alignscore_large.csv": continue
    for r in csv.DictReader(open(f)):
        if r["set"] == "s120": S.setdefault(r["method"], {})[r["id"]] = float(r["score"])
S["track-b"] = {k: float(r["track_b_score"]) for k, r in rows.items()}
for r in csv.DictReader(open(HERE.parent / "03_matched_input_trackb/out/matched_input_trackb_rows.csv", encoding="utf-8")):
    if r["set"] == "s120": S.setdefault(f"trackb-matched-{r['variant'].replace('_','-')}", {})[r["id"]] = float(r["support_score"])
PAIRS = [("track-b", "minicheck-bespoke-7b"), ("track-b", "deberta-nli"), ("track-b", "alignscore-large-official"),
         ("trackb-matched-native-instr", "minicheck-bespoke-7b"), ("trackb-matched-native-instr", "deberta-nli"), ("track-b", "trackb-matched-native-instr")]
ids = sorted(rows); strata = {}
for k in ids: strata.setdefault(rows[k]["track_b"], []).append(k)
rng = random.Random(20260914); B = 10000
boots = [[st[rng.randrange(len(st))] for st in strata.values() for _ in st] for _ in range(B)]
res = {}; lines = ["# Paired bootstrap CIs for AUROC differences (S120; stratified within Track-B strata; B = 10,000; seed 20260914)", "",
                   "| reference | view | method A | method B | AUROC A | AUROC B | A − B | 95% CI | P(A > B) |", "|---|---|---|---|---|---|---|---|---|"]
for ref in ("evaluator_2", "evaluator_1"):
    for v in ("strict", "retention"):
        y = {k: view(rows[k][ref], v) for k in ids}
        for a, b in PAIRS:
            pa = auroc([S[a][k] for k in ids], [y[k] for k in ids]); pb = auroc([S[b][k] for k in ids], [y[k] for k in ids])
            d = []
            for bs in boots:
                yy = [y[k] for k in bs]; da = auroc([S[a][k] for k in bs], yy); db = auroc([S[b][k] for k in bs], yy)
                if not (math.isnan(da) or math.isnan(db)): d.append(da - db)
            d.sort(); lo, hi = d[int(0.025 * len(d))], d[min(len(d) - 1, int(0.975 * len(d)))]; pgt = sum(x > 0 for x in d) / len(d)
            res[f"{ref}|{v}|{a}|{b}"] = {"auroc_a": pa, "auroc_b": pb, "diff": pa - pb, "ci95": [lo, hi], "p_a_greater": pgt, "n_reps": len(d)}
            lines.append(f"| {ref} | {v} | {a} | {b} | {pa:.3f} | {pb:.3f} | {pa-pb:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {pgt:.3f} |")
json.dump(res, open(HERE / "paired_auroc_differences.json", "w"), indent=2); (HERE / "paired_auroc_differences.md").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
