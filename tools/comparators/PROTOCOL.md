# Verifier-comparison protocol — FROZEN 14 Sep 2026, before any comparator score was inspected

## Samples (kept separate; never merged)
- **S120** — the prespecified stratified human-audit sample: 40 Track-B keep + 40 revise + 40 drop, rated independently
  by Evaluator 1 and Evaluator 2. *Primary* comparison set. Selected by Track-B decision strata, so results are
  reported as a "matched evaluation on the prespecified stratified human-audit sample", not as full-corpus accuracy.
- **S300** — the stratified 300-row independent-verifier sample (100 rows per extractor). Reference = Track B decision.
  Used for agreement with Track B and for reproducing the archived DeBERTa result; it carries no human labels.
- Overlap between S120 and S300 is computed (pmid + extractor + supporting sentence) and reported.

## Inputs (identical for every method)
- context/premise = the extractor-provided supporting sentence, verbatim.
- claim/hypothesis = deterministic rule-based textualisation `verbalize_claim()` copied verbatim from the archived
  `run_deberta_nli_verifier.py`; verified byte-identical to the archived DeBERTa hypotheses on 300/300 S300 rows.
- Both strings are stored in the per-row reproducibility file. No LLM is involved in textualisation.
- Track B originally received richer structured context; the comparison is therefore described as a
  *matched claim–evidence comparison*, not identical prompts.

## Empty-evidence rows
Rows whose supporting sentence is empty (extraction-failure rows: 17 in S300, 5 in S120) receive a deterministic
*unsupported* output from every comparator (score 0; native prediction unsupported/drop), exactly as the archived DeBERTa
run did (contradiction = 1). No model is called on an empty document.

## Reference labels and binary views (fixed)
- strict support:     keep -> 1 ; revise, drop -> 0
- review retention:   keep, revise -> 1 ; drop -> 0
Applied identically to Evaluator 1, Evaluator 2 and Track B.

## Method outputs
| Method | Continuous score | Native discrete prediction |
|---|---|---|
| NeuroXpert Track B | support score s in {0,1,2} | keep/revise/drop decision -> view mapping |
| Bespoke-MiniCheck-7B (main) / MiniCheck-Flan-T5-Large (supplement) | P(supported) | native supported/unsupported (model's own 0.5 rule) |
| AlignScore-large, mode nli_sp | P(aligned) | none — **no threshold is tuned on S120 or S300**; AUROC/AUPRC only |
| DeBERTa-v3-large NLI (MoritzLaurer/...-mnli-fever-anli-ling-wanli) | P(entailment) | predetermined mapping entail->keep, neutral->revise, contradiction->drop (archived experiment) |

## Metrics
- Continuous: AUROC (rank-based, ties = 0.5) and AUPRC (average precision) per view.
- Discrete (where native): accuracy, precision, recall, F1 of the positive class, Cohen's kappa.
- 95% CIs on S120: stratified bootstrap, resampling with replacement *within* the three Track-B strata
  (40/40/40), B = 10,000, seed 20260914. On S300: PMID-level bootstrap not applicable (rows are claim-level);
  plain bootstrap, B = 10,000.
- No post-stratification to corpus prevalence in the main paper.

## Validation gates (all must pass before any number enters the manuscript)
1. Checkpoint identity: HF repo id + revision/sha256 recorded for every model file.
2. AlignScore parity: the lightweight nli_sp loader must agree with the official AlignScore implementation
   (repo commit recorded) on a fixed batch to |diff| <= 1e-4; otherwise the official implementation is used.
3. DeBERTa reproduction: fresh S300 predictions must reproduce the archived kappa = 0.008 / drop F1 = 0.21 and
   the archived per-row labels.
4. Environment record: python, torch, transformers, vllm, CUDA, MiniCheck commit, AlignScore commit.

## Reporting
- Main table: Track B, Bespoke-MiniCheck-7B, AlignScore-large, DeBERTa-NLI on S120 vs Evaluator 2 (and Evaluator 1),
  both views. Supplement: MiniCheck-Flan-T5-Large; S300 agreement with Track B.
- The MiniCheck variants are one method family, not two independent baselines.
