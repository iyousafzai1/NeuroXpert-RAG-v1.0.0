# Joint Track-A x Track-B utility on the 120-row human sample

Population joint matrix (2,100 rows): fail/drop=77, fail/keep=233, fail/revise=171, pass/drop=227, pass/keep=805, pass/revise=587

| Cell (A/B) | n S120 | E1 keep/revise/drop | E2 keep/revise/drop | both agree keep/revise/drop |
|---|---|---|---|---|
| fail/drop | 9 | 0/2/7 | 0/1/8 | 0/1/7 |
| fail/keep | 8 | 2/3/3 | 2/3/3 | 2/2/2 |
| fail/revise | 6 | 2/3/1 | 1/4/1 | 1/3/1 |
| pass/drop | 31 | 1/17/13 | 1/5/25 | 1/5/13 |
| pass/keep | 32 | 15/14/3 | 14/10/8 | 14/9/3 |
| pass/revise | 34 | 8/21/5 | 6/20/8 | 6/17/4 |

| Question | cell n (S120 / 2,100) | criterion | count | raw % [CI] | IPW % [CI] | projected rows in 2,100 [CI] |
|---|---|---|---|---|---|---|
| A_gate_would_discard_human_acceptable | 14 / 404 | E1_acceptable | 10 | 71.4 [45.5, 92.9] | 69.9 [42.9, 93.0] | 282 [173, 376] |
| A_gate_would_discard_human_acceptable | 14 / 404 | E2_acceptable | 10 | 71.4 [45.5, 92.9] | 69.9 [43.4, 93.0] | 282 [175, 376] |
| A_gate_would_discard_human_acceptable | 14 / 404 | both_acceptable | 9 | 64.3 [37.5, 88.9] | 61.8 [34.5, 88.1] | 250 [139, 356] |
| A_gate_would_discard_human_acceptable | 14 / 404 | either_acceptable | 11 | 78.6 [54.5, 100.0] | 77.9 [53.0, 100.0] | 315 [214, 404] |
| B_trackA_only_would_admit_human_rejected | 31 / 227 | E1_drop | 13 | 41.9 [25.0, 59.4] | 41.9 [25.0, 59.4] | 95 [57, 135] |
| B_trackA_only_would_admit_human_rejected | 31 / 227 | E2_drop | 25 | 80.6 [65.6, 93.5] | 80.6 [65.6, 93.5] | 183 [149, 212] |
| B_trackA_only_would_admit_human_rejected | 31 / 227 | both_drop | 13 | 41.9 [25.0, 59.4] | 41.9 [25.0, 59.4] | 95 [57, 135] |
| B_trackA_only_would_admit_human_rejected | 31 / 227 | either_drop | 25 | 80.6 [65.6, 93.5] | 80.6 [65.6, 93.5] | 183 [149, 212] |
| C_agreement_pass_keeprevise_human_acceptable | 66 / 1392 | E1_acceptable | 58 | 87.9 [79.4, 95.4] | 88.3 [79.9, 95.5] | 1229 [1113, 1330] |
| C_agreement_pass_keeprevise_human_acceptable | 66 / 1392 | E2_acceptable | 50 | 75.8 [65.1, 85.9] | 75.6 [64.7, 85.9] | 1053 [901, 1196] |
| C_agreement_pass_keeprevise_human_acceptable | 66 / 1392 | both_acceptable | 49 | 74.2 [63.2, 84.5] | 74.4 [63.2, 84.7] | 1035 [880, 1179] |
| D_agreement_fail_drop_human_drop | 9 / 77 | E1_drop | 7 | 77.8 [50.0, 100.0] | 77.8 [50.0, 100.0] | 60 [38, 77] |
| D_agreement_fail_drop_human_drop | 9 / 77 | E2_drop | 8 | 88.9 [62.5, 100.0] | 88.9 [62.5, 100.0] | 68 [48, 77] |
| D_agreement_fail_drop_human_drop | 9 / 77 | both_drop | 7 | 77.8 [50.0, 100.0] | 77.8 [50.0, 100.0] | 60 [38, 77] |
