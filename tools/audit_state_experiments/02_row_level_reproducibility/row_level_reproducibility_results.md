# Row-level reproducibility (matched by PMID)

| extractor | pair | n_matched | all_fields_exact_pct | sentence_exact_pct | sentence_token_jaccard_mean | consensus_key_same_pct | trackA_agreement_pct | trackA_kappa | trackB_agreement_pct | trackB_kappa | overclaim_agreement_pct | overclaim_kappa | joint_state_agreement_pct | jaccard_keep_only | jaccard_keep_or_revise | jaccard_keep_or_revise_trackA_pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| llama31_8b | two-stage (B): archived rows vs clean rows (both Llama-verified) | 100 | 67.0 | 90.0 | 0.947 | 83.0 | 97.0 | 0.807 | 85.0 | 0.749 | 98.0 | 0.743 | 83.0 | 0.804 | 0.944 | 0.917 |
| llama31_8b | single-stage (C): archived rows vs clean rows (both Llama-verified) | 100 | 61.0 | 87.0 | 0.901 | 86.0 | 100.0 | nan | 90.0 | 0.807 | 96.0 | 0.541 | 90.0 | 0.896 | 0.957 | 1.0 |
| llama31_8b | full-pipeline reference (700-run subset) vs clean two-stage replicate (both Llama-verified) | 100 | 61.0 | 91.0 | 0.951 | 85.0 | 97.0 | 0.807 | 92.0 | 0.867 | 99.0 | 0.853 | 90.0 | 0.925 | 0.943 | 0.916 |
| llama31_8b | B: identical archived rows, archived verdict vs fresh vLLM verdict (verifier = llama (self) in both) | 100 |  |  |  |  |  |  | 98.0 | 0.967 | 100.0 | 1.0 |  |  |  |  |
| llama31_8b | C: identical archived rows, archived verdict vs fresh vLLM verdict (verifier = llama (self) in both) | 100 |  |  |  |  |  |  | 96.0 | 0.924 | 100.0 | 1.0 |  |  |  |  |
| qwen25_7b | two-stage (B): archived rows vs clean rows (both Llama-verified) | 100 | 79.0 | 89.0 | 0.942 | 83.0 | 98.0 | 0.938 | 94.0 | 0.893 | 99.0 | 0.853 | 92.0 | 0.912 | 0.978 | 0.96 |
| qwen25_7b | single-stage (C): archived rows vs clean rows (both Llama-verified) | 100 | 54.0 | 95.0 | 0.985 | 93.0 | 100.0 | nan | 92.0 | 0.83 | 99.0 | 0.0 | 92.0 | 0.901 | 0.989 | 1.0 |
| qwen25_7b | full-pipeline reference (700-run subset) vs clean two-stage replicate (both Llama-verified) | 100 | 85.0 | 86.0 | 0.924 | 84.0 | 97.0 | 0.904 | 94.0 | 0.893 | 99.0 | 0.853 | 91.0 | 0.931 | 0.967 | 0.934 |
| qwen25_7b | B: identical archived rows, archived verdict vs fresh vLLM verdict (verifier = qwen (self) in both) | 100 |  |  |  |  |  |  | 98.0 | 0.967 | 98.0 | 0.938 |  |  |  |  |
| qwen25_7b | C: identical archived rows, archived verdict vs fresh vLLM verdict (verifier = qwen (self) in both) | 100 |  |  |  |  |  |  | 97.0 | 0.944 | 92.0 | 0.828 |  |  |  |  |
| mistral7b | two-stage (B): archived rows vs clean rows (both Llama-verified) | 100 | 80.0 | 86.0 | 0.93 | 84.0 | 93.0 | 0.859 | 89.0 | 0.816 | 98.0 | 0.823 | 84.0 | 0.842 | 0.943 | 0.863 |
| mistral7b | single-stage (C): archived rows vs clean rows (both Llama-verified) | 100 | 67.0 | 82.0 | 0.935 | 81.0 | 100.0 | nan | 92.0 | 0.804 | 99.0 | 0.796 | 92.0 | 0.922 | 0.979 | 1.0 |
| mistral7b | full-pipeline reference (700-run subset) vs clean two-stage replicate (both Llama-verified) | 100 | 83.0 | 89.0 | 0.956 | 87.0 | 94.0 | 0.879 | 94.0 | 0.899 | 100.0 | 1.0 | 89.0 | 0.895 | 1.0 | 0.898 |
| mistral7b | B: identical archived rows, archived verdict vs fresh vLLM verdict (verifier = mistral (self) in both) | 100 |  |  |  |  |  |  | 100.0 | 1.0 | 100.0 | 1.0 |  |  |  |  |
| mistral7b | C: identical archived rows, archived verdict vs fresh vLLM verdict (verifier = mistral (self) in both) | 100 |  |  |  |  |  |  | 99.0 | 0.963 | 100.0 | nan |  |  |  |  |

## Per-field exact agreement (%)

| extractor | pair | phenotype | feature_type | relationship | direction | directness | diagnostic_context | brain_system | mechanism |
|---|---|---|---|---|---|---|---|---|---|
| llama31_8b | two-stage (B): archived rows vs clean rows | 96.0 | 95.0 | 97.0 | 95.0 | 91.0 | 91.0 | 99.0 | 87.0 |
| llama31_8b | single-stage (C): archived rows vs clean rows | 95.0 | 95.0 | 86.0 | 93.0 | 90.0 | 89.0 | 88.0 | 77.0 |
| llama31_8b | full-pipeline reference (700-run subset) vs clean two-stage replicate | 97.0 | 95.0 | 95.0 | 95.0 | 87.0 | 90.0 | 98.0 | 86.0 |
| qwen25_7b | two-stage (B): archived rows vs clean rows | 97.0 | 95.0 | 98.0 | 97.0 | 97.0 | 95.0 | 99.0 | 97.0 |
| qwen25_7b | single-stage (C): archived rows vs clean rows | 99.0 | 98.0 | 83.0 | 95.0 | 94.0 | 82.0 | 91.0 | 77.0 |
| qwen25_7b | full-pipeline reference (700-run subset) vs clean two-stage replicate | 97.0 | 96.0 | 98.0 | 96.0 | 98.0 | 98.0 | 99.0 | 97.0 |
| mistral7b | two-stage (B): archived rows vs clean rows | 97.0 | 100.0 | 100.0 | 100.0 | 94.0 | 98.0 | 100.0 | 91.0 |
| mistral7b | single-stage (C): archived rows vs clean rows | 97.0 | 99.0 | 83.0 | 94.0 | 95.0 | 94.0 | 94.0 | 93.0 |
| mistral7b | full-pipeline reference (700-run subset) vs clean two-stage replicate | 99.0 | 99.0 | 99.0 | 100.0 | 93.0 | 100.0 | 100.0 | 93.0 |

## Track-B transition matrices (run1 -> run2)

- llama31_8b | two-stage (B): archived rows vs clean rows: {'drop->drop': 11, 'drop->keep': 1, 'drop->revise': 2, 'keep->keep': 45, 'keep->revise': 5, 'revise->drop': 2, 'revise->keep': 5, 'revise->revise': 29}  (overclaim yes: 2 -> 2)
- llama31_8b | single-stage (C): archived rows vs clean rows: {'drop->drop': 8, 'drop->keep': 1, 'drop->revise': 1, 'keep->keep': 60, 'keep->revise': 1, 'revise->drop': 2, 'revise->keep': 5, 'revise->revise': 22}  (overclaim yes: 4 -> 2)
- llama31_8b | full-pipeline reference (700-run subset) vs clean two-stage replicate: {'drop->drop': 12, 'drop->keep': 1, 'drop->revise': 3, 'keep->keep': 49, 'keep->revise': 2, 'revise->drop': 1, 'revise->keep': 1, 'revise->revise': 31}  (overclaim yes: 2 -> 2)
- llama31_8b | B: identical archived rows, archived verdict vs fresh vLLM verdict: {'drop->drop': 14, 'keep->keep': 49, 'keep->revise': 1, 'revise->keep': 1, 'revise->revise': 35}  (overclaim yes: 2 -> 2)
- llama31_8b | C: identical archived rows, archived verdict vs fresh vLLM verdict: {'drop->drop': 10, 'keep->keep': 60, 'keep->revise': 3, 'revise->keep': 1, 'revise->revise': 26}  (overclaim yes: 4 -> 4)
- qwen25_7b | two-stage (B): archived rows vs clean rows: {'drop->drop': 8, 'keep->drop': 1, 'keep->keep': 52, 'keep->revise': 1, 'revise->drop': 1, 'revise->keep': 3, 'revise->revise': 34}  (overclaim yes: 0 -> 1)
- qwen25_7b | single-stage (C): archived rows vs clean rows: {'drop->drop': 5, 'drop->revise': 1, 'keep->keep': 64, 'revise->keep': 7, 'revise->revise': 23}  (overclaim yes: 1 -> 0)
- qwen25_7b | full-pipeline reference (700-run subset) vs clean two-stage replicate: {'drop->drop': 8, 'drop->revise': 1, 'keep->drop': 1, 'keep->keep': 54, 'keep->revise': 2, 'revise->drop': 1, 'revise->keep': 1, 'revise->revise': 32}  (overclaim yes: 0 -> 1)
- qwen25_7b | B: identical archived rows, archived verdict vs fresh vLLM verdict: {'drop->drop': 28, 'drop->revise': 1, 'keep->keep': 18, 'revise->drop': 1, 'revise->revise': 52}  (overclaim yes: 79 -> 81)
- qwen25_7b | C: identical archived rows, archived verdict vs fresh vLLM verdict: {'drop->drop': 5, 'keep->keep': 39, 'keep->revise': 1, 'revise->keep': 2, 'revise->revise': 53}  (overclaim yes: 64 -> 62)
- mistral7b | two-stage (B): archived rows vs clean rows: {'drop->drop': 13, 'drop->keep': 2, 'keep->drop': 1, 'keep->keep': 48, 'keep->revise': 4, 'revise->drop': 2, 'revise->keep': 2, 'revise->revise': 28}  (overclaim yes: 0 -> 0)
- mistral7b | single-stage (C): archived rows vs clean rows: {'drop->drop': 5, 'drop->revise': 1, 'keep->keep': 71, 'keep->revise': 4, 'revise->drop': 1, 'revise->keep': 2, 'revise->revise': 16}  (overclaim yes: 1 -> 1)
- mistral7b | full-pipeline reference (700-run subset) vs clean two-stage replicate: {'drop->drop': 16, 'keep->keep': 51, 'keep->revise': 5, 'revise->keep': 1, 'revise->revise': 27}  (overclaim yes: 0 -> 0)
- mistral7b | B: identical archived rows, archived verdict vs fresh vLLM verdict: {'drop->drop': 5, 'keep->keep': 49, 'revise->revise': 46}  (overclaim yes: 1 -> 1)
- mistral7b | C: identical archived rows, archived verdict vs fresh vLLM verdict: {'drop->drop': 4, 'keep->keep': 84, 'revise->keep': 1, 'revise->revise': 11}  (overclaim yes: 0 -> 0)
