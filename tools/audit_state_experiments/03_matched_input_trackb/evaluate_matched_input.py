"""Evaluate matched-input Track B against the frozen comparator protocol (Step 3 / Experiment 1).

Metric code (view mapping, AUROC with ties=0.5, average precision, Cohen's kappa, P/R/F1, stratified bootstrap within
Track-B strata on S120 with B=10,000 and seed 20260914) is copied verbatim from tools/comparators/evaluate_comparators.py
so that every number is computed exactly as in Table 13 / Tables S18-S19. Comparator scores are read from the frozen
score files; nothing is re-tuned.
Methods added: trackb-matched-native-instr, trackb-matched-minimal (Llama-3.1-8B, hypothesis + premise only).
Also reported: 3-class agreement / kappa / transition matrices between each matched variant and native Track B (S120, S300).
"""
import csv, json, math, pathlib, random
from collections import defaultdict, Counter
HERE = pathlib.Path(__file__).resolve().parent; C = HERE.parents[0].parent / "comparators"; D = C / "data"; S = C / "scores"
rows = {}
for f in ("rows_300.jsonl", "rows_120.jsonl"):
    for l in open(D / f):
        if l.strip(): r = json.loads(l); rows[(r["set"], r["id"])] = r
def view(label, v): return (1 if label == "keep" else 0) if v == "strict" else (1 if label in ("keep", "revise") else 0)
def auroc(scores, y):
    pos = [s for s, t in zip(scores, y) if t == 1]; neg = [s for s, t in zip(scores, y) if t == 0]
    if not pos or not neg: return float("nan")
    return sum((1.0 if p > n else 0.5 if p == n else 0.0) for p in pos for n in neg) / (len(pos) * len(neg))
def auprc(scores, y):
    order = sorted(range(len(y)), key=lambda i: -scores[i]); tp = 0; fp = 0; ap = 0.0; P = sum(y)
    if P == 0: return float("nan")
    for i in order:
        if y[i] == 1: tp += 1; ap += tp / (tp + fp)
        else: fp += 1
    return ap / P
def kappa(a, b):
    n = len(a); labs = set(a) | set(b); po = sum(x == y for x, y in zip(a, b)) / n; pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labs)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")
def prf(pred, y):
    tp = sum(p == 1 and t == 1 for p, t in zip(pred, y)); fp = sum(p == 1 and t == 0 for p, t in zip(pred, y)); fn = sum(p == 0 and t == 1 for p, t in zip(pred, y))
    P = tp / (tp + fp) if tp + fp else 0.0; R = tp / (tp + fn) if tp + fn else 0.0; F = 2 * P * R / (P + R) if P + R else 0.0
    return sum(p == t for p, t in zip(pred, y)) / len(y), P, R, F
M = defaultdict(dict)
for f in sorted(S.glob("scores_*.csv")):
    if f.name == "scores_alignscore_large.csv": continue
    for r in csv.DictReader(open(f)):
        np_ = r["native_pred"]; np_ = None if np_ == "" else (int(np_) if np_ in ("0", "1") else np_)
        M[r["method"]][(r["set"], r["id"])] = (float(r["score"]), np_)
for k, r in rows.items(): M["track-b"][k] = (float(r["track_b_score"]), r["track_b"])
matched = list(csv.DictReader(open(HERE / "out/matched_input_trackb_rows.csv", encoding="utf-8")))
for r in matched: M[f"trackb-matched-{r['variant'].replace('_','-')}"][(r["set"], r["id"])] = (float(r["support_score"]), r["decision"])
def native(method, val, v):
    if val is None: return None
    return val if isinstance(val, int) else view(val, v)
res = {}
for method, d in M.items():
    for setname, refs in (("s300", ["track_b"]), ("s120", ["track_b", "evaluator_1", "evaluator_2"])):
        keys = [k for k in rows if k[0] == setname and k in d]
        if not keys: continue
        for ref in refs:
            if method == "track-b" and ref == "track_b": continue
            for v in ("strict", "retention"):
                y = [view(rows[k][ref], v) for k in keys]; sc = [d[k][0] for k in keys]
                e = {"n": len(keys), "auroc": auroc(sc, y), "auprc": auprc(sc, y), "positives": sum(y)}
                np_ = [native(method, d[k][1], v) for k in keys]
                if all(p is not None for p in np_):
                    acc, P, Rr, F = prf(np_, y); e.update({"acc": acc, "precision": P, "recall": Rr, "f1": F, "kappa": kappa(np_, y)})
                res[f"{method}|{setname}|{ref}|{v}"] = e
def boot_ci(method, setname, ref, v, B=10000, seed=20260914):
    d = M[method]; keys = [k for k in rows if k[0] == setname and k in d]; rng = random.Random(seed); strata = {}
    for k in keys: strata.setdefault(rows[k]["track_b"] if setname == "s120" else "all", []).append(k)
    y_all = {k: view(rows[k][ref], v) for k in keys}; sc_all = {k: d[k][0] for k in keys}; np_all = {k: native(method, d[k][1], v) for k in keys}
    has_native = all(p is not None for p in np_all.values()); acc = {"auroc": [], "auprc": [], "f1": [], "kappa": []}
    for _ in range(B):
        ks = []
        for st in strata.values(): ks += [st[rng.randrange(len(st))] for _ in st]
        y = [y_all[k] for k in ks]; sc = [sc_all[k] for k in ks]; acc["auroc"].append(auroc(sc, y)); acc["auprc"].append(auprc(sc, y))
        if has_native: npv = [np_all[k] for k in ks]; acc["f1"].append(prf(npv, y)[3]); acc["kappa"].append(kappa(npv, y))
    def ci(a):
        a = sorted(x for x in a if not (isinstance(x, float) and math.isnan(x)))
        return [a[int(0.025 * len(a))], a[min(len(a) - 1, int(0.975 * len(a)))]] if a else None
    return {m: ci(a) for m, a in acc.items() if a}
for key in list(res):
    method, setname, ref, v = key.split("|")
    if method.startswith("trackb-matched") or method == "track-b":
        res[key]["ci95"] = boot_ci(method, setname, ref, v)
# 3-class agreement with native Track B
agree = {}
for m in ("trackb-matched-native-instr", "trackb-matched-minimal"):
    for setname in ("s120", "s300"):
        keys = [k for k in rows if k[0] == setname and k in M[m]]
        a = [rows[k]["track_b"] for k in keys]; b = [M[m][k][1] for k in keys]
        agree[f"{m}|{setname}"] = {"n": len(keys), "agreement": sum(x == y for x, y in zip(a, b)) / len(keys), "kappa": kappa(a, b),
                                   "transition_native_to_matched": {f"{x}->{y}": c for (x, y), c in sorted(Counter(zip(a, b)).items())},
                                   "matched_decision_counts": dict(Counter(b)), "native_decision_counts": dict(Counter(a))}
parse = Counter((r["variant"], r["parse_status"]) for r in matched)
out = {"metrics": res, "agreement_with_native_trackb": agree, "parse_status": {f"{k[0]}|{k[1]}": v for k, v in parse.items()}}
json.dump(out, open(HERE / "matched_input_metrics.json", "w"), indent=2)
fmt = lambda x: "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"
lines = ["# Matched-input Track B vs native Track B vs comparators (frozen protocol)", ""]
ORDER = ["track-b", "trackb-matched-native-instr", "trackb-matched-minimal", "minicheck-bespoke-7b", "minicheck-flan-t5", "alignscore-large-official", "deberta-nli"]
for setname, refs in (("s120", ["evaluator_2", "evaluator_1"]), ("s300", ["track_b"])):
    for ref in refs:
        lines += [f"## reference: {ref} on {setname}", "", "| method | view | n | AUROC [CI] | AUPRC | Acc | Prec | Rec | F1 [CI] | kappa [CI] |", "|---|---|---|---|---|---|---|---|---|---|"]
        for m in ORDER:
            for v in ("strict", "retention"):
                e = res.get(f"{m}|{setname}|{ref}|{v}")
                if not e: continue
                ci = e.get("ci95", {}); cia = f" [{ci['auroc'][0]:.3f},{ci['auroc'][1]:.3f}]" if ci.get("auroc") else ""
                cif = f" [{ci['f1'][0]:.3f},{ci['f1'][1]:.3f}]" if ci.get("f1") else ""; cik = f" [{ci['kappa'][0]:.3f},{ci['kappa'][1]:.3f}]" if ci.get("kappa") else ""
                lines.append(f"| {m} | {v} | {e['n']} | {fmt(e['auroc'])}{cia} | {fmt(e['auprc'])} | {fmt(e.get('acc'))} | {fmt(e.get('precision'))} | {fmt(e.get('recall'))} | {fmt(e.get('f1'))}{cif} | {fmt(e.get('kappa'))}{cik} |")
        lines.append("")
lines += ["## 3-class agreement of matched variants with native Track B", ""]
for k, a in agree.items(): lines.append(f"- {k}: n={a['n']} agreement={a['agreement']:.3f} kappa={a['kappa']:.3f} native={a['native_decision_counts']} matched={a['matched_decision_counts']} transitions={a['transition_native_to_matched']}")
lines += ["", "## parse status", "", json.dumps(out["parse_status"])]
(HERE / "matched_input_metrics.md").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
