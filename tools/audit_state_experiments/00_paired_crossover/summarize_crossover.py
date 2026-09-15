"""Paired verifier crossover on byte-identical extracted records (Step 0).
For each extractor x condition (B two-stage / C single-stage) x row set (archived May-2026 rows / clean Sep-2026 rows), the
SAME audit-sheet rows were verified by (i) the fixed Llama-3.1-8B verifier and (ii) the extractor itself (self-verification).
Archived verdicts (from the original run) are shown alongside the fresh vLLM verdicts. Input SHA-256 digests are recorded."""
import csv, json, pathlib, collections
H = pathlib.Path(__file__).parent; OUT = H / "out"; INP = H / "inputs"
ARCH = pathlib.Path("/Users/irfankhan/Documents/project 4/Egyptial_Informatics_Journal/neuroxpert_rag/results_package_mature_2026_05_29/03_figure_source_data/baseline_ablation_100")
CLEAN = H.parent.parent / "ablation_clean/out"
sha = dict(l.split()[::-1] for l in open(INP / "SHA256SUMS.txt"))
def summ(p):
    rows = list(csv.DictReader(open(p, encoding="utf-8"))); d = collections.Counter(r["verifier_decision"].strip().lower() for r in rows)
    return {"n": len(rows), "keep": d["keep"], "revise": d["revise"], "drop": d["drop"], "overclaim_yes": sum(r["verifier_overclaiming"].strip().lower() == "yes" for r in rows),
            "errors": sum(bool(r.get("verifier_error")) for r in rows), "verifier": rows[0]["verifier_model"]}
def rowwise(p1, p2):
    a = {r["pmid"]: r for r in csv.DictReader(open(p1, encoding="utf-8"))}; b = {r["pmid"]: r for r in csv.DictReader(open(p2, encoding="utf-8"))}
    ks = [k for k in a if k in b]; return {"n": len(ks), "decision_agree": sum(a[k]["verifier_decision"] == b[k]["verifier_decision"] for k in ks),
                                          "overclaim_agree": sum(a[k]["verifier_overclaiming"] == b[k]["verifier_overclaiming"] for k in ks)}
SELF = {"llama31_8b": "llama", "qwen25_7b": "qwen", "mistral7b": "mistral"}
ARCHF = {"B": "baseline_b_structured_no_gate_verifier.csv", "C": "baseline_c_single_stage_external_verifier.csv"}
CLEANF = {"B": "merged_baseline_b_structured_no_gate_verifier.csv", "C": "merged_baseline_c_single_stage_external_verifier.csv"}
table = []; lines = ["# Paired verifier crossover on byte-identical extracted records", "",
                     "| extractor | condition | row set (sha256[:12]) | verifier | source of verdict | keep/revise/drop | overclaim /100 |", "|---|---|---|---|---|---|---|"]
for m in ["llama31_8b", "qwen25_7b", "mistral7b"]:
    for c in ("B", "C"):
        for src in ("archived", "clean"):
            f = f"{src}_{m}_{c}_audit_sheet.csv"; s12 = sha[f][:12]
            cells = []
            # original verdict as recorded in the archived run / clean run
            orig = summ(ARCH / m / ARCHF[c]) if src == "archived" else summ(CLEAN / m / CLEANF[c])
            cells.append(("original run", orig))
            fl = OUT / f"{src}_{m}_{c}__verifier_llama.csv"; cells.append(("fresh (vLLM) Llama", summ(fl)))
            fs = OUT / f"{src}_{m}_{c}__verifier_{SELF[m]}.csv"
            if m != "llama31_8b": cells.append((f"fresh (vLLM) self = {SELF[m]}", summ(fs)))
            for lab, s in cells:
                table.append({"extractor": m, "condition": c, "row_set": src, "sha256": sha[f], "verdict_source": lab, **s})
                lines.append(f"| {m} | {c} | {src} ({s12}) | {s['verifier']} | {lab} | {s['keep']}/{s['revise']}/{s['drop']} | {s['overclaim_yes']} |")
            # row-wise reproducibility of the same verifier on identical rows (archived verdict vs fresh)
            if src == "archived":
                orig_path = ARCH / m / ARCHF[c]; fresh_same = fl if m == "llama31_8b" else fs
                rw = rowwise(orig_path, fresh_same); table[-1]["rowwise_same_verifier_archived_vs_fresh"] = rw
                lines.append(f"|  |  |  |  | row-wise, same verifier, archived vs fresh | decisions identical {rw['decision_agree']}/{rw['n']} | overclaim flags identical {rw['overclaim_agree']}/{rw['n']} |")
            if src == "clean":
                rw = rowwise(CLEAN / m / CLEANF[c], fl); lines.append(f"|  |  |  |  | row-wise, Llama clean-run verdict vs fresh Llama | decisions identical {rw['decision_agree']}/{rw['n']} | overclaim flags identical {rw['overclaim_agree']}/{rw['n']} |")
json.dump(table, open(H / "crossover_summary.json", "w"), indent=2); (H / "crossover_summary.md").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
