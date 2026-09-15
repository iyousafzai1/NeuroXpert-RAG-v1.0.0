# Paired bootstrap CIs for AUROC differences (S120; stratified within Track-B strata; B = 10,000; seed 20260914)

| reference | view | method A | method B | AUROC A | AUROC B | A − B | 95% CI | P(A > B) |
|---|---|---|---|---|---|---|---|---|
| evaluator_2 | strict | track-b | minicheck-bespoke-7b | 0.760 | 0.790 | -0.030 | [-0.162, +0.104] | 0.343 |
| evaluator_2 | strict | track-b | deberta-nli | 0.760 | 0.741 | +0.020 | [-0.121, +0.164] | 0.605 |
| evaluator_2 | strict | track-b | alignscore-large-official | 0.760 | 0.686 | +0.075 | [-0.064, +0.217] | 0.854 |
| evaluator_2 | strict | trackb-matched-native-instr | minicheck-bespoke-7b | 0.779 | 0.790 | -0.012 | [-0.135, +0.116] | 0.428 |
| evaluator_2 | strict | trackb-matched-native-instr | deberta-nli | 0.779 | 0.741 | +0.038 | [-0.088, +0.167] | 0.716 |
| evaluator_2 | strict | track-b | trackb-matched-native-instr | 0.760 | 0.779 | -0.018 | [-0.098, +0.069] | 0.332 |
| evaluator_2 | retention | track-b | minicheck-bespoke-7b | 0.748 | 0.736 | +0.012 | [-0.099, +0.131] | 0.594 |
| evaluator_2 | retention | track-b | deberta-nli | 0.748 | 0.733 | +0.015 | [-0.099, +0.139] | 0.605 |
| evaluator_2 | retention | track-b | alignscore-large-official | 0.748 | 0.583 | +0.165 | [+0.044, +0.290] | 0.996 |
| evaluator_2 | retention | trackb-matched-native-instr | minicheck-bespoke-7b | 0.718 | 0.736 | -0.018 | [-0.127, +0.096] | 0.377 |
| evaluator_2 | retention | trackb-matched-native-instr | deberta-nli | 0.718 | 0.733 | -0.015 | [-0.123, +0.100] | 0.395 |
| evaluator_2 | retention | track-b | trackb-matched-native-instr | 0.748 | 0.718 | +0.030 | [-0.046, +0.108] | 0.783 |
| evaluator_1 | strict | track-b | minicheck-bespoke-7b | 0.748 | 0.807 | -0.059 | [-0.177, +0.065] | 0.176 |
| evaluator_1 | strict | track-b | deberta-nli | 0.748 | 0.765 | -0.017 | [-0.146, +0.115] | 0.399 |
| evaluator_1 | strict | track-b | alignscore-large-official | 0.748 | 0.642 | +0.106 | [-0.031, +0.246] | 0.933 |
| evaluator_1 | strict | trackb-matched-native-instr | minicheck-bespoke-7b | 0.778 | 0.807 | -0.029 | [-0.147, +0.090] | 0.313 |
| evaluator_1 | strict | trackb-matched-native-instr | deberta-nli | 0.778 | 0.765 | +0.013 | [-0.110, +0.135] | 0.581 |
| evaluator_1 | strict | track-b | trackb-matched-native-instr | 0.748 | 0.778 | -0.029 | [-0.106, +0.053] | 0.240 |
| evaluator_1 | retention | track-b | minicheck-bespoke-7b | 0.699 | 0.672 | +0.026 | [-0.121, +0.177] | 0.643 |
| evaluator_1 | retention | track-b | deberta-nli | 0.699 | 0.675 | +0.023 | [-0.122, +0.171] | 0.626 |
| evaluator_1 | retention | track-b | alignscore-large-official | 0.699 | 0.581 | +0.118 | [-0.033, +0.277] | 0.933 |
| evaluator_1 | retention | trackb-matched-native-instr | minicheck-bespoke-7b | 0.692 | 0.672 | +0.019 | [-0.123, +0.161] | 0.612 |
| evaluator_1 | retention | trackb-matched-native-instr | deberta-nli | 0.692 | 0.675 | +0.016 | [-0.110, +0.150] | 0.595 |
| evaluator_1 | retention | track-b | trackb-matched-native-instr | 0.699 | 0.692 | +0.007 | [-0.084, +0.093] | 0.573 |
