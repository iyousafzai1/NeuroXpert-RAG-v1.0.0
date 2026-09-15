#!/usr/bin/env python3
"""Consolidated architecture ablation (100-PMID subset, 3 extractors) combining
  - the clean 2026-09-14 re-run (run_baseline_ablation_fixed_verifier.py; verifier = Llama-3.1-8B-Instruct in every condition),
  - the 2026-09-15 paired crossover (tools/audit_state_experiments/00_paired_crossover): the SAME clean rows re-verified by the
    extractor itself (self-verification) -> b_self / c_self are now byte-identical-row conditions, and
  - the archived 2026-05 run (pilot/run_baseline_ablation.py; verifier = extractor model) kept as b_self_archived / c_self_archived / naive.
Emits ablation_conditions.json, table rows (LaTeX) and regenerates Fig. F3 / F4 PDFs.  Single source of truth for the manuscript."""
import csv, json, pathlib, statistics
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE=pathlib.Path(__file__).resolve().parent; PKG=HERE.parent.parent
ARCH=pathlib.Path("/Users/irfankhan/Documents/project 4/Egyptial_Informatics_Journal/neuroxpert_rag/results_package_mature_2026_05_29/03_figure_source_data/baseline_ablation_100/baseline_ablation_metrics_all_models.csv")
MODELS=[("llama31_8b","llama-3.1-8b-instruct","Llama 3.1 8B"),("qwen25_7b","qwen2.5-7b-instruct","Qwen 2.5 7B"),("mistral7b","mistral-7b-instruct-v0.3","Mistral 7B")]
def f(x): return None if x in ("",None) else float(x)
arch={}
for r in csv.DictReader(open(ARCH)):
    arch[(r["model"],r["system"])]={k:f(r[k]) for k in ("schema_valid_rate","quote_anchor_rate","semantic_keep_rate","overclaim_rate","useful_evidence_retained_rate")}
clean={}
for d,m,_ in MODELS:
    for r in json.load(open(HERE/"out"/d/"merged_metrics.json")):
        clean[(m,r["system"])]={k:r.get(k) for k in ("schema_valid_rate","quote_anchor_rate","semantic_keep_rate","overclaim_rate","useful_evidence_retained_rate","overclaim_count")}
# paired crossover: clean rows x self-verifier (fresh vLLM verdicts) -> same metric dictionary shape
XO=HERE.parent/"audit_state_experiments"/"00_paired_crossover"/"out"; SELF={"llama31_8b":"llama","qwen25_7b":"qwen","mistral7b":"mistral"}
xover={}
for d,m,_ in MODELS:
    for cond,sysname in (("B","baseline_b_structured_no_mechanical_gate"),("C","baseline_c_single_stage_extract_verify")):
        rows=list(csv.DictReader(open(XO/f"clean_{d}_{cond}__verifier_{SELF[d]}.csv",encoding="utf-8"))); n=len(rows)
        dec=[r["verifier_decision"].strip().lower() for r in rows]; oc=sum(r["verifier_overclaiming"].strip().lower()=="yes" for r in rows)
        xover[(m,sysname)]={"schema_valid_rate":sum(r["schema_valid"]=="yes" for r in rows)/n,"quote_anchor_rate":sum(r["sentence_anchored"]=="yes" for r in rows)/n,
                            "semantic_keep_rate":dec.count("keep")/n,"overclaim_rate":oc/n,"overclaim_count":oc,
                            "useful_evidence_retained_rate":(dec.count("keep")+dec.count("revise"))/n}
# condition -> (source, system)
COND=[("full","Full pipeline: two-stage, fixed independent verifier (reference run)", "clean","full_neuroxpert_rag"),
      ("b_fixed","Two-stage, fixed independent verifier, fresh re-extraction", "clean","baseline_b_structured_no_mechanical_gate"),
      ("b_self","Two-stage, self-verification on the same rows (extractor verifies its own rows)", "xover","baseline_b_structured_no_mechanical_gate"),
      ("c_fixed","Single-stage extraction+verification, fixed independent verifier", "clean","baseline_c_single_stage_extract_verify"),
      ("c_self","Single-stage extraction+verification, self-verification on the same rows", "xover","baseline_c_single_stage_extract_verify"),
      ("naive","Naive free-form RAG (no schema, no verification)", "arch","baseline_a_naive_free_form_rag"),
      ("b_self_archived","Two-stage, self-verification, archived May-2026 rows (Supplementary only)", "arch","baseline_b_structured_no_mechanical_gate"),
      ("c_self_archived","Single-stage, self-verification, archived May-2026 rows (Supplementary only)", "arch","baseline_c_single_stage_extract_verify")]
out={}
for key,label,src,sysname in COND:
    per={}
    for d,m,disp in MODELS:
        e={"clean":clean,"arch":arch,"xover":xover}[src][(m,sysname)]
        per[disp]=dict(e); 
        if e.get("overclaim_rate") is not None and "overclaim_count" not in e: per[disp]["overclaim_count"]=round(e["overclaim_rate"]*100)
    mean=lambda k: (statistics.mean(v[k] for v in per.values() if v.get(k) is not None) if any(v.get(k) is not None for v in per.values()) else None)
    out[key]={"label":label,"source":src,"per_model":per,"mean":{k:mean(k) for k in ("schema_valid_rate","quote_anchor_rate","semantic_keep_rate","overclaim_rate","useful_evidence_retained_rate")}}
json.dump(out, open(HERE/"ablation_conditions.json","w"), indent=2)
# ---- LaTeX rows
def pct(x): return "---" if x is None else f"{round(x*100):d}\\%"
def oc(per,disp): v=per[disp].get("overclaim_count"); return "---" if v is None else f"{int(v)}"
rows=[]
for key,label,src,_ in COND:
    if key.endswith("_archived"): continue
    e=out[key]; m=e["mean"]; per=e["per_model"]
    rows.append(f"{label} & {pct(m['schema_valid_rate'])} & {pct(m['quote_anchor_rate'])} & {pct(m['semantic_keep_rate'])} & {pct(m['overclaim_rate'])} & {pct(m['useful_evidence_retained_rate'])} & {oc(per,'Llama 3.1 8B')} / {oc(per,'Qwen 2.5 7B')} / {oc(per,'Mistral 7B')} \\\\")
(HERE/"ablation_table_rows.tex").write_text("\n".join(rows)+"\n"); print("\n".join(rows))
# ---- Fig F4: overclaim by model x condition (5 verified conditions)
labels=["Full\n(two-stage,\nfixed verifier)","Two-stage\nfixed verifier\n(re-extracted)","Two-stage\nself-verification\n(same rows)","Single-stage\nfixed verifier","Single-stage\nself-verification\n(same rows)"]
keys=["full","b_fixed","b_self","c_fixed","c_self"]; colors={"Llama 3.1 8B":"#2b8cbe","Qwen 2.5 7B":"#b5478a","Mistral 7B":"#f28e2b"}
fig,ax=plt.subplots(figsize=(7.2,3.3)); x=range(len(keys)); w=0.26
for i,(d,m,disp) in enumerate(MODELS):
    vals=[out[k]["per_model"][disp]["overclaim_count"] for k in keys]
    bars=ax.bar([xx+(i-1)*w for xx in x], vals, w, label=disp, color=colors[disp])
    for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2, v+1.2, f"{v}", ha="center", va="bottom", fontsize=7)
ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=7.5); ax.set_ylabel("Automatic overclaim flags (per 100 rows)", fontsize=8); ax.set_ylim(0,92)
ax.axvspan(1.5,2.5,color="#f3e6ee",zorder=0); ax.axvspan(3.5,4.5,color="#f3e6ee",zorder=0)
ax.text(2.0,86,"verifier = extractor",ha="center",fontsize=7.5,color="#7a2f5e"); ax.text(4.0,86,"verifier = extractor",ha="center",fontsize=7.5,color="#7a2f5e")
ax.set_title("Overclaim flags by extractor and pipeline condition (100-PMID subset)", fontsize=9); ax.legend(fontsize=7.5, frameon=False, loc="upper left")
ax.spines[["top","right"]].set_visible(False); fig.tight_layout(); fig.savefig(PKG/"figures"/"F4_overclaim_failure_envelope.pdf"); plt.close(fig)
# ---- Fig F3: trade-off scatter, grounding strength vs safety-adjusted utility
mk={"full":("*",180,"Full (fixed verifier)"),"b_fixed":("o",70,"Two-stage, fixed verifier"),"b_self":("s",70,"Two-stage, self-verification"),"c_fixed":("^",80,"Single-stage, fixed verifier"),"c_self":("D",60,"Single-stage, self-verification")}
fig,ax=plt.subplots(figsize=(6.6,4.2))
for k,(marker,size,lab) in mk.items():
    for d,m,disp in MODELS:
        e=out[k]["per_model"][disp]; gs=(e["schema_valid_rate"]+e["quote_anchor_rate"])/2; su=e["useful_evidence_retained_rate"]*(1-e["overclaim_rate"])
        ax.scatter(gs,su,marker=marker,s=size,color=colors[disp],edgecolor="black",linewidth=0.5,zorder=3)
for k,(marker,size,lab) in mk.items(): ax.scatter([],[],marker=marker,s=size*0.8,color="grey",edgecolor="black",linewidth=0.5,label=lab)
for d,m,disp in MODELS: ax.scatter([],[],marker="o",s=50,color=colors[disp],label=disp)
ax.set_xlabel("Grounding strength (mean of schema validity and quote anchoring)", fontsize=8); ax.set_ylabel("Safety-adjusted utility\n(useful retained × (1 − overclaim rate))", fontsize=8)
ax.set_xlim(0.25,1.02); ax.set_ylim(0.1,1.02); ax.grid(alpha=0.25); ax.legend(fontsize=7, frameon=False, ncol=2, loc="lower left")
ax.set_title("Baseline trade-off on the fixed 100-PMID subset", fontsize=9); ax.spines[["top","right"]].set_visible(False)
fig.tight_layout(); fig.savefig(PKG/"figures"/"F3_baseline_tradeoff.pdf"); plt.close(fig)
print("figures written")
