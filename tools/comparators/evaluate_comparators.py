#!/usr/bin/env python3
"""Evaluate every verifier on the SAME rows against the SAME reference labels, under two predefined binary views:
  strict support      : keep -> 1 ; revise, drop -> 0
  review retention    : keep, revise -> 1 ; drop -> 0
Continuous scores -> AUROC / AUPRC (no thresholds tuned).  Native discrete predictions (where a method has one)
-> accuracy, precision, recall, F1 on the positive class, plus Cohen's kappa.
Methods: DeBERTa-NLI (archived jsonl, 300 rows), AlignScore-large, MiniCheck-Flan-T5-Large, Bespoke-MiniCheck-7B,
and NeuroXpert Track B (support score s in {0,1,2} as the continuous score; decision as native prediction).
References: Track B (300- and 120-row sets), Evaluator 1 and Evaluator 2 (120-row set)."""
import csv, json, math, pathlib, sys
from collections import defaultdict
HERE=pathlib.Path(__file__).resolve().parent; D=HERE/"data"; S=HERE/"scores"; OUT=HERE/"results"; OUT.mkdir(exist_ok=True)
rows={}
for f in ("rows_300.jsonl","rows_120.jsonl"):
    for l in open(D/f):
        if l.strip(): r=json.loads(l); rows[(r["set"],r["id"])]=r
def view(label, v): return (1 if label=="keep" else 0) if v=="strict" else (1 if label in ("keep","revise") else 0)
def auroc(scores, y):
    pos=[s for s,t in zip(scores,y) if t==1]; neg=[s for s,t in zip(scores,y) if t==0]
    if not pos or not neg: return float("nan")
    return sum((1.0 if p>n else 0.5 if p==n else 0.0) for p in pos for n in neg)/(len(pos)*len(neg))
def auprc(scores, y):  # average precision
    order=sorted(range(len(y)), key=lambda i:-scores[i]); tp=0; fp=0; ap=0.0; P=sum(y)
    if P==0: return float("nan")
    for i in order:
        if y[i]==1: tp+=1; ap+=tp/(tp+fp)
        else: fp+=1
    return ap/P
def kappa(a,b):
    n=len(a); labs=set(a)|set(b); po=sum(x==y for x,y in zip(a,b))/n; pe=sum((a.count(l)/n)*(b.count(l)/n) for l in labs); return (po-pe)/(1-pe) if pe<1 else float("nan")
def prf(pred, y):
    tp=sum(p==1 and t==1 for p,t in zip(pred,y)); fp=sum(p==1 and t==0 for p,t in zip(pred,y)); fn=sum(p==0 and t==1 for p,t in zip(pred,y))
    P=tp/(tp+fp) if tp+fp else 0.0; R=tp/(tp+fn) if tp+fn else 0.0; F=2*P*R/(P+R) if P+R else 0.0; acc=sum(p==t for p,t in zip(pred,y))/len(y); return acc,P,R,F
# ---- collect method outputs: {method: {(set,id): (score, native_label or None)}}
M=defaultdict(dict)
for f in sorted(S.glob("scores_*.csv")):
    if f.name=="scores_alignscore_large.csv": continue   # lightweight loader = cross-check only; official file is the record
    for r in csv.DictReader(open(f)):
        np_=r["native_pred"]; np_=None if np_=="" else (int(np_) if np_ in ("0","1") else np_)
        M[r["method"]][(r["set"],r["id"])]=(float(r["score"]), np_)
deb=pathlib.Path("/Users/irfankhan/Documents/ESWA Paper Finalization/additional analysis/06_reference_outputs_and_tables/deberta_nli_verifier_results.jsonl")
if deb.exists() and "deberta-nli" not in M:   # archived 300-row run, used only if no fresh scores exist
    for l in open(deb):
        if l.strip():
            r=json.loads(l); k=("s300",r["custom_id"])
            if k in rows: M["deberta-nli"][k]=(r["nli_scores"]["entailment"], r["deberta_decision"])  # native 3-class decision
for k,r in rows.items():
    M["track-b"][k]=(float(r["track_b_score"]) if r["track_b_score"] not in ("",None) else float("nan"), r["track_b"])
# native prediction per view: minicheck label (1=supported) applies to both views; 3-class decisions map through view()
def native(method, val, v):
    if val is None: return None
    if isinstance(val,int): return val
    return view(val, v)
res={}
for method, d in M.items():
    for setname, refs in (("s300",["track_b"]),("s120",["track_b","evaluator_1","evaluator_2"])):
        keys=[k for k in rows if k[0]==setname and k in d]
        if not keys: continue
        for ref in refs:
            if method=="track-b" and ref=="track_b": continue
            for v in ("strict","retention"):
                y=[view(rows[k][ref], v) for k in keys]; sc=[d[k][0] for k in keys]
                entry={"n":len(keys),"auroc":auroc(sc,y),"auprc":auprc(sc,y),"positives":sum(y)}
                np_=[native(method,d[k][1],v) for k in keys]
                if all(p is not None for p in np_):
                    acc,P,R,F=prf(np_,y); entry.update({"acc":acc,"precision":P,"recall":R,"f1":F,"kappa":kappa(np_,y)})
                res[f"{method}|{setname}|{ref}|{v}"]=entry
# ---- 95% CIs: stratified bootstrap within Track-B strata on S120 (B=10,000, seed 20260914); plain bootstrap on S300
import random
def boot_ci(method, setname, ref, v, B=10000, seed=20260914):
    d=M[method]; keys=[k for k in rows if k[0]==setname and k in d]
    if not keys: return None
    rng=random.Random(seed)
    strata={}
    for k in keys: strata.setdefault(rows[k]["track_b"] if setname=="s120" else "all", []).append(k)
    y_all={k:view(rows[k][ref], v) for k in keys}; sc_all={k:d[k][0] for k in keys}; np_all={k:native(method,d[k][1],v) for k in keys}
    has_native=all(p is not None for p in np_all.values())
    acc={"auroc":[],"auprc":[],"f1":[],"kappa":[]}
    for _ in range(B):
        ks=[]; 
        for st in strata.values(): ks += [st[rng.randrange(len(st))] for _ in st]
        y=[y_all[k] for k in ks]; sc=[sc_all[k] for k in ks]
        acc["auroc"].append(auroc(sc,y)); acc["auprc"].append(auprc(sc,y))
        if has_native:
            npv=[np_all[k] for k in ks]; acc["f1"].append(prf(npv,y)[3]); acc["kappa"].append(kappa(npv,y))
    def ci(a):
        a=[x for x in a if not (isinstance(x,float) and math.isnan(x))]
        if not a: return None
        a=sorted(a); return [a[int(0.025*len(a))], a[min(len(a)-1,int(0.975*len(a)))]]
    return {m:ci(a) for m,a in acc.items() if a}
for key in list(res):
    method,setname,ref,v=key.split("|")
    if method=="track-b" and ref=="track_b": continue
    c=boot_ci(method,setname,ref,v)
    if c: res[key]["ci95"]=c
# ---- overlap between S120 and S300 (pmid is not stored in rows; use extractor + premise + hypothesis)
sig=lambda r:(r["extractor_model"],r["premise"],r["hypothesis"])
s120={sig(r) for k,r in rows.items() if k[0]=="s120"}; s300={sig(r) for k,r in rows.items() if k[0]=="s300"}
res["_overlap_S120_S300"]={"shared_rows":len(s120&s300),"n_S120":len(s120),"n_S300":len(s300)}
# ---- DeBERTa reproduction gate (fresh S300 scores vs archived per-row labels)
if deb.exists() and "deberta-nli" in M:
    arch={json.loads(l)["custom_id"]:json.loads(l)["deberta_decision"] for l in open(deb) if l.strip()}
    fresh={k[1]:M["deberta-nli"][k][1] for k in M["deberta-nli"] if k[0]=="s300"}
    common=[i for i in fresh if i in arch]; agree=sum(fresh[i]==arch[i] for i in common)
    res["_deberta_reproduction"]={"rows_compared":len(common),"identical_labels":agree,"fraction":agree/len(common) if common else None}
# ---- per-row reproducibility file
cols=["set","row_id","extractor","supporting_sentence","canonical_claim_text","trackb_original_decision","trackb_support_score","human_eval1","human_eval2"]
meths=[m for m in ["minicheck-bespoke-7b","minicheck-flan-t5","alignscore-large-official","deberta-nli"] if m in M]
with open(OUT/"per_row_all_methods.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(cols+[f"{m}_{x}" for m in meths for x in ("score","native_pred")])
    for k in sorted(rows):
        r=rows[k]; base=[k[0],k[1],r["extractor_model"],r["premise"],r["hypothesis"],r["track_b"],r["track_b_score"],r.get("evaluator_1",""),r.get("evaluator_2","")]
        ext=[]
        for m in meths:
            sc,np_=M[m].get(k,(None,None)); ext += ["" if sc is None else f"{sc:.6f}", "" if np_ is None else np_]
        w.writerow(base+ext)
json.dump(res, open(OUT/"comparator_metrics.json","w"), indent=2)
# ---- compact tables
def fmt(x): return "—" if x is None or (isinstance(x,float) and math.isnan(x)) else f"{x:.3f}"
lines=[]
for setname, ref in (("s120","evaluator_2"),("s120","evaluator_1"),("s300","track_b"),("s120","track_b")):
    lines.append(f"\n=== reference: {ref} on {setname} ===")
    lines.append(f"{'method':<24}{'view':<11}{'n':>4}{'AUROC':>8}{'AUPRC':>8}{'Acc':>7}{'Prec':>7}{'Rec':>7}{'F1':>7}{'kappa':>8}")
    for method in ["deberta-nli","alignscore-large-official","minicheck-flan-t5","minicheck-bespoke-7b","track-b"]:
        for v in ("strict","retention"):
            e=res.get(f"{method}|{setname}|{ref}|{v}")
            if not e: continue
            ci=e.get("ci95",{}); cia=ci.get("auroc"); cif=ci.get("f1")
            lines.append(f"{method:<24}{v:<11}{e['n']:>4}{fmt(e['auroc']):>8}{fmt(e['auprc']):>8}{fmt(e.get('acc')):>7}{fmt(e.get('precision')):>7}{fmt(e.get('recall')):>7}{fmt(e.get('f1')):>7}{fmt(e.get('kappa')):>8}"
                         + (f"   AUROC CI [{cia[0]:.3f},{cia[1]:.3f}]" if cia else "") + (f"  F1 CI [{cif[0]:.3f},{cif[1]:.3f}]" if cif else ""))
lines.append(f"\noverlap S120/S300: {res['_overlap_S120_S300']}"); 
if "_deberta_reproduction" in res: lines.append(f"DeBERTa reproduction: {res['_deberta_reproduction']}")
txt="\n".join(lines); print(txt); (OUT/"comparator_metrics.txt").write_text(txt)
