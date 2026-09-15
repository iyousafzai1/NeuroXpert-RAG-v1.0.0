# Validation record — verifier comparators (14 Sep 2026)

## Environments (ThinkStation, NVIDIA RTX 5880 Ada 48 GB, driver 580.159.03)
| env | python | torch | CUDA | transformers | other |
|---|---|---|---|---|---|
| `nxo_verif` (MiniCheck, DeBERTa, lightweight AlignScore loader) | 3.11.15 | 2.11.0+cu130 | 13.0 | 5.9.0 | vllm 0.21.0, accelerate 1.15.0, MiniCheck 0.1.0 (GitHub main, cloned 14 Sep 2026) |
| `alignscore_official` (official AlignScore) | 3.9.23 | 1.13.1+cu117 | 11.7 | 4.31.0 | pytorch_lightning 1.9.5, spacy 3.7.5 + en_core_web_sm 3.7.1, AlignScore commit a0936d5 (2024-03-10) |

## Checkpoints (downloaded via hf-mirror.com transport; identities are the Hugging Face repo revisions)
| model | HF repo | revision | weight file sha256 |
|---|---|---|---|
| MiniCheck-Flan-T5-Large | lytang/MiniCheck-Flan-T5-Large | 96eafd01cee2d16cf81aaa2fb226b14f422a37b3 | 41291881e13c6235ed47149cec903bee9493e45d9d7325587a9fa2e266c526c0 |
| AlignScore-large | yzha/AlignScore, file AlignScore-large.ckpt | 8509e78d25bb914939fc585c626500c9b2944249 | ff4336312b377edcbcdad5694a2d09d73dc4225422c0422d810aa7e78485e32d |
| DeBERTa-v3-large NLI | MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli | b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7 | c03cd208bf920b4fbbb182a0535859a566e8acc3477d2b536bf87b769978524b |
| Bespoke-MiniCheck-7B | bespokelabs/Bespoke-MiniCheck-7B | 1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8 | (multi-shard; see server sha256 list) |

## Gates
1. **AlignScore parity** — official `nli_sp` vs lightweight loader, same checkpoint file, all 420 rows.
   First attempt: 14/420 rows differed (max |diff| 0.467) because the loader scored premise sentences separately;
   the official code joins all premise sentences into one chunk when the evidence is < 350 words.
   After replicating that rule: **max |diff| = 2.0e-6 on 420/420 rows** (gate ≤ 1e-4). The **official implementation's
   outputs** (`scores_alignscore_official.csv`) are nevertheless used as the record; the loader is a cross-check only.
2. **DeBERTa reproduction** — fresh run vs archived `deberta_nli_verifier_results.jsonl` on S300:
   **299/300 identical labels** (one near-tie flip, gptv_0111), max entailment-probability difference 0.071;
   3-class kappa 0.003 vs archived 0.008, drop F1 0.20 vs 0.21, revise share 0.74 vs 0.74. Passed.
3. **Input identity** — premise/hypothesis pairs byte-identical to the archived DeBERTa run on 300/300 S300 rows.
4. **Empty-evidence rule** — 17 (S300) + 5 (S120) rows with an empty supporting sentence scored *unsupported* by rule for
   every method, exactly as the archived DeBERTa run did.
5. **Overlap** — 18 claim rows are shared between S120 and S300 (by extractor + sentence + claim); the samples are
   evaluated separately and never merged.
6. **Bespoke-MiniCheck-7B execution** — the MiniCheck package runs this model through vLLM. Under vLLM 0.21.0 /
   transformers 5.9 the checkpoint produced degenerate outputs (first-token top-5 = " ", " clear", " conj", "公正";
   support probability 0.000 on all 420 rows). That run is **discarded** (kept as
   `INVALID_vllm_scores_minicheck_bespoke_7b.csv.bak` on the server). The tokenizer round-trip was verified correct,
   so the fault is in vLLM's execution of this InternLM2 checkpoint on the newer stack. The checkpoint's own
   `modeling_internlm2.py` requires transformers < 5, so a third env `bespoke_hf` (clone of `nxo_verif` with
   transformers 4.46.3, accelerate 1.1.1) runs the model in plain transformers via `score_bespoke_hf.py`, which
   replicates MiniCheck's bespoke path exactly: identical `SYSTEM_PROMPT`/`USER_PROMPT` (minicheck/utils.py), the
   tokenizer's chat template with `add_generation_prompt=True`, first-token distribution, support probability =
   summed probability of top-5 first tokens whose decoded text `.lower()=="yes"`, nltk sentence split of the claim,
   min over claim sentences of max over document chunks (one chunk for all our evidence), label = prob > 0.5.
   Sanity check on the first rows: clean Yes/No distributions (e.g. No 0.835 / Yes 0.164).
