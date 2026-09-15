#!/usr/bin/env python3
"""Cross-tabulate Track A strict grounding x Track B decision for every row of the primary
700-abstract evaluation (3 extractors, 2,100 rows). Source: results_package_mature_2026_05_29/
03_figure_source_data/final_<model>_700/semantic_llm_verifier_all.csv (one row per abstract).
Strict grounding = schema_valid & citation_valid & sentence_present & sentence_anchored.
Writes tools/derived/joint_audit_state_matrix.csv"""
import csv, collections, pathlib, sys
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
    "/Users/irfankhan/Documents/project 4/Egyptial_Informatics_Journal/neuroxpert_rag/results_package_mature_2026_05_29/03_figure_source_data")
MODELS = [("Llama 3.1 8B","final_llama31_8b_700"),("Qwen 2.5 7B","final_qwen25_7b_700"),("Mistral 7B","final_mistral7b_700")]
tb = lambda v: str(v).strip().lower() in ("true","1","yes","t")
cells = {}
for name, d in MODELS:
    c = collections.Counter()
    for r in csv.DictReader(open(ROOT / d / "semantic_llm_verifier_all.csv")):
        A = all(tb(r[k]) for k in ("schema_valid","citation_valid","sentence_present","sentence_anchored"))
        c[("pass" if A else "fail", r["verifier_decision"].strip().lower())] += 1
    cells[name] = c
out = pathlib.Path(__file__).parent / "derived" / "joint_audit_state_matrix.csv"
with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["track_a","track_b"] + [m for m,_ in MODELS] + ["pooled"])
    for a in ("pass","fail"):
        for b in ("keep","revise","drop"):
            vals = [cells[m][(a,b)] for m,_ in MODELS]; w.writerow([a,b]+vals+[sum(vals)])
    hid_seq = [cells[m][("fail","keep")]+cells[m][("fail","revise")] for m,_ in MODELS]
    hid_col = [cells[m][("pass","drop")] for m,_ in MODELS]
    w.writerow(["hidden_by_sequential_gating","fail&keep|revise"]+hid_seq+[sum(hid_seq)])
    w.writerow(["hidden_by_grounded_accept_collapse","pass&drop"]+hid_col+[sum(hid_col)])
    w.writerow(["disagreement_total",""]+[x+y for x,y in zip(hid_seq,hid_col)]+[sum(hid_seq)+sum(hid_col)])
print(open(out).read())
