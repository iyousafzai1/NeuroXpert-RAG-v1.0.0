#!/usr/bin/env python3
"""Server-side scorer: runs claim-grounding models on (premise, hypothesis) rows and writes raw scores.
usage: python score_on_server.py --rows rows_300.jsonl rows_120.jsonl --method minicheck-flan-t5 --out scores_minicheck_flan_t5.csv
methods: minicheck-flan-t5 | minicheck-bespoke-7b | alignscore-large
Environment: HF_ENDPOINT=https://hf-mirror.com (server cannot reach huggingface.co)."""
import argparse, csv, json, os, sys, pathlib
ap=argparse.ArgumentParser(); ap.add_argument("--rows", nargs="+", required=True); ap.add_argument("--method", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--cache", default=os.path.expanduser("~/nxo_verifier_comparators/ckpts")); a=ap.parse_args()
allrows=[json.loads(l) for f in a.rows for l in open(f) if l.strip()]
# Empty supporting sentence (extraction-failure rows): deterministic 'unsupported' for every method, exactly as the
# archived DeBERTa run did (contradiction=1 -> drop); the model is not called on an empty document.
rows=[r for r in allrows if r["premise"].strip()]; empties=[r for r in allrows if not r["premise"].strip()]
docs=[r["premise"] for r in rows]; claims=[r["hypothesis"] for r in rows]
print(f"{len(allrows)} rows ({len(empties)} empty-evidence rows scored 0 by rule), method={a.method}", flush=True)

if a.method.startswith("minicheck"):
    from minicheck.minicheck import MiniCheck
    name = "flan-t5-large" if a.method=="minicheck-flan-t5" else "Bespoke-MiniCheck-7B"
    scorer = MiniCheck(model_name=name, cache_dir=a.cache, enable_prefix_caching=False)
    labels, probs, _, _ = scorer.score(docs=docs, claims=claims)
    preds=[int(x) for x in labels]; scores=[float(p) for p in probs]
elif a.method=="alignscore-large":
    # Faithful minimal re-implementation of AlignScore 'nli_sp' (Zha et al., ACL 2023) for the released
    # AlignScore-large checkpoint: RoBERTa-large encoder + 3-way alignment head; score = P(aligned).
    # Sentence handling replicates inference_per_example: max over premise sentences, mean over hypothesis sentences.
    import torch, torch.nn as nn, nltk
    from nltk.tokenize import sent_tokenize
    from transformers import AutoTokenizer, RobertaModel, AutoConfig
    from huggingface_hub import hf_hub_download
    ckpt = hf_hub_download("yzha/AlignScore", "AlignScore-large.ckpt", cache_dir=a.cache)
    tok = AutoTokenizer.from_pretrained("roberta-large", cache_dir=a.cache)
    base = RobertaModel(AutoConfig.from_pretrained("roberta-large", cache_dir=a.cache))   # pooler included
    tri = nn.Linear(base.config.hidden_size, 3)
    sd = torch.load(ckpt, map_location="cpu")["state_dict"]
    base_sd = {k[len("base_model."):]:v for k,v in sd.items() if k.startswith("base_model.")}
    missing, unexpected = base.load_state_dict(base_sd, strict=False)
    print("base_model load: missing", [m for m in missing if "pooler" in m or "encoder" in m][:5], "unexpected", unexpected[:5], flush=True)
    tri.load_state_dict({"weight": sd["tri_layer.weight"], "bias": sd["tri_layer.bias"]})
    dev = "cuda" if torch.cuda.is_available() else "cpu"; base.to(dev).eval(); tri.to(dev).eval(); sm = nn.Softmax(dim=-1)
    def pair_scores(prem_list, hypo_list):
        out=[]
        with torch.no_grad():
            for i in range(0, len(prem_list), 32):
                b = tok(prem_list[i:i+32], hypo_list[i:i+32], truncation="only_first", padding="max_length", max_length=512, return_tensors="pt").to(dev)
                o = base(input_ids=b["input_ids"], attention_mask=b["attention_mask"])
                out += sm(tri(o.pooler_output))[:,0].cpu().tolist()
        return out
    scores=[]
    def chunks(lst, n):
        for i in range(0, len(lst), n): yield " ".join(lst[i:i+n])
    for d,c in zip(docs,claims):
        # replicate inference_per_example exactly: premise sentences are grouped into chunks of
        # n_chunk = max(len(sents) // (len(words)//350 + 1), 1) sentences (one chunk for evidence < 350 words)
        ps = sent_tokenize(d) or [""]
        n_chunk = len(d.strip().split()) // 350 + 1; n_chunk = max(len(ps) // n_chunk, 1)
        ps = list(chunks(ps, n_chunk)); hs = sent_tokenize(c) or [c]
        mat = pair_scores([p for p in ps for _ in hs], [h for _ in ps for h in hs])
        m = torch.tensor(mat).view(len(ps), len(hs)).max(dim=0).values.mean().item(); scores.append(m)
    preds=[None]*len(scores)   # AlignScore has no native discrete prediction; thresholds are not tuned
elif a.method=="deberta-nli":
    # Same checkpoint and formulation as the archived run (run_deberta_nli_verifier.py):
    # premise = supporting sentence, hypothesis = verbalised claim; entail->keep, neutral->revise, contradiction->drop
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    ck="MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli"
    tok=AutoTokenizer.from_pretrained(ck, cache_dir=a.cache); mdl=AutoModelForSequenceClassification.from_pretrained(ck, cache_dir=a.cache)
    dev="cuda" if torch.cuda.is_available() else "cpu"; mdl.to(dev).eval()
    id2label={int(k):v.lower() for k,v in mdl.config.id2label.items()}
    scores=[]; preds=[]
    with torch.no_grad():
        for i in range(0,len(docs),32):
            b=tok(docs[i:i+32], claims[i:i+32], truncation=True, padding=True, max_length=512, return_tensors="pt").to(dev)
            pr=torch.softmax(mdl(**b).logits, dim=-1).cpu()
            for row in pr:
                d={id2label[j]:float(row[j]) for j in range(len(row))}
                scores.append(d["entailment"]); top=max(d,key=d.get)
                preds.append({"entailment":"keep","neutral":"revise","contradiction":"drop"}[top])
else:
    sys.exit("unknown method")

empty_pred = "drop" if a.method=="deberta-nli" else (None if a.method=="alignscore-large" else 0)
with open(a.out,"w",newline="") as f:
    w=csv.writer(f); w.writerow(["id","set","method","score","native_pred"])
    for r,s,p in zip(rows,scores,preds): w.writerow([r["id"],r["set"],a.method,f"{s:.6f}","" if p is None else p])
    for r in empties: w.writerow([r["id"],r["set"],a.method,"0.000000","" if empty_pred is None else empty_pred])
print("wrote", a.out, flush=True)
