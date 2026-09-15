# Clean architecture ablation — fixed-verifier re-run (14 Sep 2026)

## Why
The archived ablation (`pilot/run_baseline_ablation.py`, May 2026) took the "Full pipeline" row from the primary
700-abstract run (verifier = Llama-3.1-8B for all extractors) but ran Baselines B and C inside the harness, whose
`--verifier-model` defaulted to the **extractor** model. The Track A predicates were computed identically in every
condition, so the reported 0 → 79/100 overclaim change for Qwen was not "removal of the mechanical safeguard"
(no such removal happened) but a verifier swap: Qwen verifying its own rows vs Llama verifying Qwen's rows.

## What was run
`run_baseline_ablation_fixed_verifier.py` = the archived harness with one addition (`--verifier-base-url`) so the
fixed verifier is served from a second vLLM endpoint. Same 100 PMIDs, same corpus, same prompts, same decoding
(extraction T = 0.1, top-p 0.9, 700 tokens; verifier T = 0, 350 tokens; single-stage 900 tokens). Baseline A, B, C
re-run for Llama-3.1-8B-Instruct, Qwen2.5-7B-Instruct, Mistral-7B-Instruct-v0.3 (bf16, vLLM 0.21, RTX 5880 Ada),
each as 8 parallel PMID shards against the same servers (`run_cond_sharded.sh`, merged by `merge_shards.py`).
Verifier for every condition: Llama-3.1-8B-Instruct on :8000; extractor on :8001.
Model revisions: Qwen a09a35458c702b33eeacc393d103063234e8bc28; Mistral (hf-mirror snapshot, see server dl.log);
Llama from ~/my_datasets/tracekg_project/models/llama-3.1-8b-instruct.

## Result (overclaim flags / 100)
| Extractor | Full (ref.) | Two-stage, fixed verifier (re-extracted) | Two-stage, self-verification (archived) | Single-stage, fixed | Single-stage, self (archived) |
|---|---|---|---|---|---|
| Llama | 2 | 2 | 2 | 2 | 4 |
| Qwen | 0 | 1 | 79 | 0 | 64 |
| Mistral | 0 | 0 | 1 | 1 | 0 |
Reproduction check (Llama, verifier unchanged between runs): B 2/100 vs 2/100; anchoring 0.91 vs 0.92; keep 0.51 vs 0.50.

## Files
- `out/<model>/merged_*.csv` — per-row outputs of every clean condition; `merged_metrics.json` — recomputed metrics
- `ablation_conditions.json`, `ablation_table_rows.tex` — consolidated archived + clean conditions (source of Table 7)
- `build_ablation_table_and_figures.py` — regenerates the table rows and Figs F3/F4 (originals kept in `_backup/`)
- `logs/` — chain/condition logs from the server


## Update 15 Sep 2026 — self-verification rows on byte-identical records
`b_self` / `c_self` in `ablation_conditions.json` and Table 8 now come from the paired crossover (`tools/audit_state_experiments/00_paired_crossover/`): the clean rows re-verified by the extractor itself (Qwen 79/66, Llama 2/2, Mistral 0/0). The archived May-2026 self-verification values are kept as `b_self_archived` / `c_self_archived` (Supplementary Table S22 lists both).
