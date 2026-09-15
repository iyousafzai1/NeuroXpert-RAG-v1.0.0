# audit_state_experiments — paired crossover, joint-state utility, reproducibility, matched-input Track B, Track-A fault injection, paired statistics

Analyses reported in the manuscript's Sections 4.4–4.8, 5.1, 5.2, 5.4, 5.5 and Supplementary Tables S20–S26.
All model calls were made on one workstation with vLLM 0.21.0 (bfloat16, 4,096-token context) using the production
Track-B prompt builder, decoding (temperature 0.0, top-p 0.9, 350 tokens) and parser of the `neuroxpert_rag` package.
Bootstrap: B = 10,000, seed 20260914 (stratified within the three Track-B strata on the 120-row human sample).

```
00_paired_crossover/        inputs/ (12 audit sheets + SHA256SUMS.txt)  out/ (verifier CSVs with raw responses)  summarize_crossover.py  crossover_summary.{md,json}
01_joint_state_utility/     joint_state_utility.py  s120_joint_state_rows.csv  joint_state_utility_results.{md,json}
02_row_level_reproducibility/  row_level_reproducibility.py  row_level_reproducibility_results.{md,json}
03_matched_input_trackb/    out/ (per-row decisions + raw responses)  evaluate_matched_input.py  matched_input_metrics.{md,json}
04_fault_injection/         track_a_fault_injection.py  track_a_fault_rows.csv  track_a_fault_injection_results.{md,json}
05_paired_statistics/       paired_auroc_differences.py  mcnemar_paired_model_tests.py  *.{md,json}
06_manuscript_tables/       make_tables.py -> LaTeX row snippets + numbers.json (single source for every number in the text)
server_scripts/             rescore_rows.py  run_matched_input_trackb.py  start_servers.sh  launch_phase1.sh  swap_mistral.sh
server_logs/                per-job logs and trimmed vLLM logs
```

Reproduce on a GPU host: `start_servers.sh` → `launch_phase1.sh` → `swap_mistral.sh`; then run the local analysis
scripts in numerical order (Step 2 needs Step 0 outputs; Step 3 needs `03_matched_input_trackb/out/`).
Paths inside the scripts point at the frozen results package (`results_package_mature_2026_05_29`) and the
comparator data in `../comparators/data/`.
