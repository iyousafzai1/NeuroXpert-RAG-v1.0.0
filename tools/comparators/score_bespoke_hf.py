#!/usr/bin/env python3
"""Bespoke-MiniCheck-7B scored with plain transformers (4.46) using the checkpoint's own modeling code,
because vLLM 0.21 mis-executes this InternLM2 checkpoint (all-zero outputs) and the remote code needs transformers < 5.
Faithful to MiniCheck/minicheck/inference.py (bespoke mode): identical SYSTEM_PROMPT / USER_PROMPT, the tokenizer's
chat template with add_generation_prompt, first-token distribution; support prob = summed probability of the
top-5 first tokens whose decoded text lower()=="yes" (get_support_prob); claim split into sentences (nltk), doc kept as
one chunk (all our evidence sentences are far below the chunk size); final = min over claim sentences of max over
chunks; native label = final > 0.5. Empty-evidence rows scored 0 by rule (see PROTOCOL.md)."""
import argparse, csv, json, os, glob, sys, torch, nltk
sys.path.insert(0, os.path.expanduser("~/nxo_verifier_comparators/MiniCheck"))
from minicheck.utils import SYSTEM_PROMPT, USER_PROMPT
from transformers import AutoTokenizer, AutoModelForCausalLM
ap=argparse.ArgumentParser(); ap.add_argument("--rows", nargs="+", required=True); ap.add_argument("--out", required=True); ap.add_argument("--limit", type=int, default=0); a=ap.parse_args()
snap=glob.glob(os.path.expanduser("~/nxo_verifier_comparators/ckpts/models--bespokelabs--Bespoke-MiniCheck-7B/snapshots/*"))[0]
tok=AutoTokenizer.from_pretrained(snap, trust_remote_code=True)
model=AutoModelForCausalLM.from_pretrained(snap, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map="cuda").eval()
allrows=[json.loads(l) for f in a.rows for l in open(f) if l.strip()]
if a.limit: allrows=allrows[:a.limit]
rows=[r for r in allrows if r["premise"].strip()]; empties=[r for r in allrows if not r["premise"].strip()]
print(len(allrows),"rows,",len(empties),"empty-evidence rows scored 0 by rule", flush=True)
def support_prob(doc, sent):
    msgs=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":USER_PROMPT.replace("[DOCUMENT]",doc).replace("[CLAIM]",sent)}]
    text=tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
    ids=tok(text, return_tensors="pt", add_special_tokens=False).to("cuda")
    with torch.no_grad(): logits=model(**ids).logits[0,-1].float()
    pr=torch.softmax(logits,-1); top=torch.topk(pr,5)
    top5=[(tok.decode([int(i)]), v.item()) for v,i in zip(top.values, top.indices)]
    return sum(v for t,v in top5 if t.lower()=="yes"), [(t,round(v,3)) for t,v in top5]
out=[]
for k,r in enumerate(rows):
    sents=nltk.sent_tokenize(r["hypothesis"]) or [r["hypothesis"]]
    res=[support_prob(r["premise"], s) for s in sents]
    final=min(p for p,_ in res); out.append((r, final, 1 if final>0.5 else 0))
    if k<4: print("debug top5:", res[0][1], "| P(yes)=", round(final,3), "| trackB:", r["track_b"], flush=True)
    if k%50==0: print(k, flush=True)
with open(a.out,"w",newline="") as f:
    w=csv.writer(f); w.writerow(["id","set","method","score","native_pred"])
    for r,s,p in out: w.writerow([r["id"],r["set"],"minicheck-bespoke-7b",f"{s:.6f}",p])
    for r in empties: w.writerow([r["id"],r["set"],"minicheck-bespoke-7b","0.000000",0])
print("wrote", a.out, flush=True)
