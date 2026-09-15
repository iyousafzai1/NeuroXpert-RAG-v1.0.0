#!/usr/bin/env python3
"""Merge sharded ablation outputs and recompute the harness metrics with the harness's own definitions."""
import csv, json, sys, glob, pathlib
from collections import Counter
root=pathlib.Path(sys.argv[1]); model=sys.argv[2]
def cat(name):
    rows=[]; fields=None
    for sh in sorted(root.glob("shard*")):
        f=sh/name
        if f.exists():
            r=list(csv.DictReader(open(f))); rows+=r
            if r and fields is None: fields=list(r[0].keys())
    return rows, fields
def rate(n,d): return round(n/d,4) if d else None
out={}
files={"full":"full_neuroxpert_subset_verifier.csv","naive":"baseline_a_naive_free_form.csv","B_verifier":"baseline_b_structured_no_gate_verifier.csv","B_audit":"baseline_b_structured_no_gate_audit_sheet.csv","C_verifier":"baseline_c_single_stage_external_verifier.csv","C_audit":"baseline_c_single_stage_audit_sheet.csv","C_raw":"baseline_c_single_stage_raw.csv"}
merged={}
for k,name in files.items():
    rows,fields=cat(name); merged[k]=rows
    if rows:
        with open(root/("merged_"+name),"w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def summarize(system, rows):
    n=len(rows); dec=Counter(r.get("verifier_decision") for r in rows); over=Counter(r.get("verifier_overclaiming") for r in rows)
    return {"system":system,"model":model,"n":n,
            "schema_valid_rate":rate(sum(r.get("schema_valid")=="yes" for r in rows),n),
            "citation_valid_rate":rate(sum(r.get("citation_valid")=="yes" for r in rows),n),
            "quote_anchor_rate":rate(sum(r.get("sentence_anchored")=="yes" for r in rows),n),
            "semantic_keep_rate":rate(dec.get("keep",0),n),"semantic_revise_rate":rate(dec.get("revise",0),n),"semantic_drop_rate":rate(dec.get("drop",0),n),
            "overclaim_rate":rate(over.get("yes",0),n),"overclaim_count":over.get("yes",0),
            "useful_evidence_retained_rate":rate(dec.get("keep",0)+dec.get("revise",0),n),
            "verifier_models":dict(Counter(r.get("verifier_model") for r in rows)),
            "extraction_models":dict(Counter(r.get("extraction_model") for r in rows)),
            "errors":sum(bool(r.get("verifier_error")) for r in rows)}
metrics=[summarize("full_neuroxpert_rag", merged["full"]), summarize("baseline_b_structured_no_mechanical_gate", merged["B_verifier"]), summarize("baseline_c_single_stage_extract_verify", merged["C_verifier"])]
naive=merged["naive"]; metrics.append({"system":"baseline_a_naive_free_form_rag","model":model,"n":len(naive),"schema_valid_rate":0.0,
   "quote_anchor_rate":rate(sum(str(r.get("sentence_anchored","")).lower() in ("yes","true","1") for r in naive),len(naive)) if naive else None})
json.dump(metrics, open(root/"merged_metrics.json","w"), indent=2)
for m in metrics: print({k:v for k,v in m.items() if k in ("system","n","schema_valid_rate","quote_anchor_rate","semantic_keep_rate","overclaim_count","overclaim_rate","useful_evidence_retained_rate","verifier_models","errors")})
