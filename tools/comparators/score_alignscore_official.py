#!/usr/bin/env python3
"""Official AlignScore (yuh-zha/AlignScore, commit a0936d5, 2024-03-10) in nli_sp mode — reference implementation
for the parity gate and, if parity holds, the source of the manuscript's AlignScore numbers.
Same rows / same empty-evidence rule as score_on_server.py."""
import argparse, csv, json, os, hashlib
ap=argparse.ArgumentParser(); ap.add_argument("--rows", nargs="+", required=True); ap.add_argument("--ckpt", required=True); ap.add_argument("--out", required=True); a=ap.parse_args()
os.environ.setdefault("HF_ENDPOINT","https://hf-mirror.com")
from alignscore import AlignScore
allrows=[json.loads(l) for f in a.rows for l in open(f) if l.strip()]
rows=[r for r in allrows if r["premise"].strip()]; empties=[r for r in allrows if not r["premise"].strip()]
print(len(allrows),"rows,",len(empties),"empty-evidence rows scored 0 by rule", flush=True)
print("ckpt sha256:", hashlib.sha256(open(a.ckpt,"rb").read()).hexdigest(), flush=True)
scorer=AlignScore(model="roberta-large", batch_size=32, device="cuda:0", ckpt_path=a.ckpt, evaluation_mode="nli_sp", verbose=False)
scores=scorer.score(contexts=[r["premise"] for r in rows], claims=[r["hypothesis"] for r in rows])
with open(a.out,"w",newline="") as f:
    w=csv.writer(f); w.writerow(["id","set","method","score","native_pred"])
    for r,s in zip(rows,scores): w.writerow([r["id"],r["set"],"alignscore-large-official",f"{s:.6f}",""])
    for r in empties: w.writerow([r["id"],r["set"],"alignscore-large-official","0.000000",""])
print("wrote", a.out, flush=True)
