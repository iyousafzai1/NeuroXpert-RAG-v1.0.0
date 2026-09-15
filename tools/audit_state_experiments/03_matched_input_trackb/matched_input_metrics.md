# Matched-input Track B vs native Track B vs comparators (frozen protocol)

## reference: evaluator_2 on s120

| method | view | n | AUROC [CI] | AUPRC | Acc | Prec | Rec | F1 [CI] | kappa [CI] |
|---|---|---|---|---|---|---|---|---|---|
| track-b | strict | 120 | 0.760 [0.671,0.841] | 0.334 | 0.733 | 0.400 | 0.667 | 0.500 [0.345,0.639] | 0.333 [0.158,0.507] |
| track-b | retention | 120 | 0.748 [0.667,0.830] | 0.756 | 0.775 | 0.750 | 0.896 | 0.816 [0.745,0.878] | 0.532 [0.386,0.675] |
| trackb-matched-native-instr | strict | 120 | 0.779 [0.686,0.862] | 0.378 | 0.767 | 0.400 | 0.333 | 0.364 [0.176,0.533] | 0.222 [0.016,0.426] |
| trackb-matched-native-instr | retention | 120 | 0.718 [0.637,0.798] | 0.781 | 0.717 | 0.824 | 0.627 | 0.712 [0.614,0.797] | 0.443 [0.292,0.589] |
| trackb-matched-minimal | strict | 120 | 0.635 [0.511,0.750] | 0.290 | 0.667 | 0.318 | 0.583 | 0.412 [0.258,0.551] | 0.206 [0.031,0.378] |
| trackb-matched-minimal | retention | 120 | 0.627 [0.535,0.714] | 0.700 | 0.617 | 0.600 | 0.940 | 0.733 [0.663,0.796] | 0.160 [0.030,0.300] |
| minicheck-bespoke-7b | strict | 120 | 0.790 | 0.547 | 0.825 | 0.800 | 0.167 | 0.276 | 0.222 |
| minicheck-bespoke-7b | retention | 120 | 0.736 | 0.774 | 0.483 | 1.000 | 0.075 | 0.139 | 0.066 |
| minicheck-flan-t5 | strict | 120 | 0.667 | 0.281 | 0.775 | 0.200 | 0.042 | 0.069 | 0.000 |
| minicheck-flan-t5 | retention | 120 | 0.589 | 0.651 | 0.467 | 0.800 | 0.060 | 0.111 | 0.036 |
| alignscore-large-official | strict | 120 | 0.686 | 0.345 | — | — | — | — | — |
| alignscore-large-official | retention | 120 | 0.583 | 0.626 | — | — | — | — | — |
| deberta-nli | strict | 120 | 0.741 | 0.455 | 0.800 | 0.500 | 0.208 | 0.294 | 0.200 |
| deberta-nli | retention | 120 | 0.733 | 0.743 | 0.600 | 0.587 | 0.955 | 0.727 | 0.116 |

## reference: evaluator_1 on s120

| method | view | n | AUROC [CI] | AUPRC | Acc | Prec | Rec | F1 [CI] | kappa [CI] |
|---|---|---|---|---|---|---|---|---|---|
| track-b | strict | 120 | 0.748 [0.667,0.826] | 0.357 | 0.717 | 0.425 | 0.607 | 0.500 [0.353,0.636] | 0.311 [0.134,0.486] |
| track-b | retention | 120 | 0.699 [0.593,0.801] | 0.809 | 0.733 | 0.850 | 0.773 | 0.810 [0.753,0.860] | 0.368 [0.189,0.538] |
| trackb-matched-native-instr | strict | 120 | 0.778 [0.689,0.860] | 0.423 | 0.750 | 0.450 | 0.321 | 0.375 [0.195,0.536] | 0.224 [0.023,0.418] |
| trackb-matched-native-instr | retention | 120 | 0.692 [0.601,0.774] | 0.822 | 0.625 | 0.922 | 0.534 | 0.676 [0.590,0.755] | 0.299 [0.168,0.437] |
| trackb-matched-minimal | strict | 120 | 0.639 [0.525,0.745] | 0.337 | 0.667 | 0.364 | 0.571 | 0.444 [0.293,0.580] | 0.223 [0.043,0.398] |
| trackb-matched-minimal | retention | 120 | 0.618 [0.505,0.724] | 0.772 | 0.758 | 0.781 | 0.932 | 0.850 [0.796,0.898] | 0.256 [0.064,0.440] |
| minicheck-bespoke-7b | strict | 120 | 0.807 | 0.579 | 0.792 | 0.800 | 0.143 | 0.242 | 0.185 |
| minicheck-bespoke-7b | retention | 120 | 0.672 | 0.847 | 0.308 | 1.000 | 0.057 | 0.108 | 0.031 |
| minicheck-flan-t5 | strict | 120 | 0.667 | 0.318 | 0.742 | 0.200 | 0.036 | 0.061 | -0.011 |
| minicheck-flan-t5 | retention | 120 | 0.578 | 0.803 | 0.308 | 1.000 | 0.057 | 0.108 | 0.031 |
| alignscore-large-official | strict | 120 | 0.642 | 0.377 | — | — | — | — | — |
| alignscore-large-official | retention | 120 | 0.581 | 0.780 | — | — | — | — | — |
| deberta-nli | strict | 120 | 0.765 | 0.505 | 0.783 | 0.600 | 0.214 | 0.316 | 0.220 |
| deberta-nli | retention | 120 | 0.675 | 0.840 | 0.742 | 0.761 | 0.943 | 0.843 | 0.165 |

## reference: track_b on s300

| method | view | n | AUROC [CI] | AUPRC | Acc | Prec | Rec | F1 [CI] | kappa [CI] |
|---|---|---|---|---|---|---|---|---|---|
| trackb-matched-native-instr | strict | 300 | 0.785 [0.731,0.838] | 0.720 | 0.783 | 0.878 | 0.422 | 0.570 [0.470,0.659] | 0.448 [0.343,0.550] |
| trackb-matched-native-instr | retention | 300 | 0.787 [0.748,0.825] | 0.911 | 0.723 | 0.961 | 0.612 | 0.748 [0.693,0.799] | 0.473 [0.387,0.561] |
| trackb-matched-minimal | strict | 300 | 0.619 [0.558,0.679] | 0.426 | 0.627 | 0.450 | 0.441 | 0.446 [0.357,0.529] | 0.164 [0.050,0.280] |
| trackb-matched-minimal | retention | 300 | 0.625 [0.563,0.687] | 0.747 | 0.670 | 0.709 | 0.861 | 0.778 [0.734,0.819] | 0.161 [0.050,0.277] |
| minicheck-bespoke-7b | strict | 300 | 0.628 | 0.459 | 0.653 | 0.455 | 0.098 | 0.161 | 0.046 |
| minicheck-bespoke-7b | retention | 300 | 0.675 | 0.836 | 0.403 | 1.000 | 0.109 | 0.197 | 0.075 |
| minicheck-flan-t5 | strict | 300 | 0.581 | 0.452 | 0.673 | 0.667 | 0.078 | 0.140 | 0.074 |
| minicheck-flan-t5 | retention | 300 | 0.584 | 0.781 | 0.370 | 1.000 | 0.060 | 0.113 | 0.040 |
| alignscore-large-official | strict | 300 | 0.600 | 0.397 | — | — | — | — | — |
| alignscore-large-official | retention | 300 | 0.590 | 0.745 | — | — | — | — | — |
| deberta-nli | strict | 300 | 0.616 | 0.467 | 0.677 | 0.571 | 0.196 | 0.292 | 0.143 |
| deberta-nli | retention | 300 | 0.642 | 0.808 | 0.623 | 0.671 | 0.861 | 0.754 | 0.002 |

## 3-class agreement of matched variants with native Track B

- trackb-matched-native-instr|s120: n=120 agreement=0.642 kappa=0.463 native={'drop': 40, 'keep': 40, 'revise': 40} matched={'drop': 69, 'keep': 20, 'revise': 31} transitions={'drop->drop': 39, 'drop->revise': 1, 'keep->drop': 10, 'keep->keep': 19, 'keep->revise': 11, 'revise->drop': 20, 'revise->keep': 1, 'revise->revise': 19}
- trackb-matched-native-instr|s300: n=300 agreement=0.593 kappa=0.392 native={'revise': 99, 'drop': 99, 'keep': 102} matched={'drop': 172, 'revise': 79, 'keep': 49} transitions={'drop->drop': 94, 'drop->revise': 5, 'keep->drop': 26, 'keep->keep': 43, 'keep->revise': 33, 'revise->drop': 52, 'revise->keep': 6, 'revise->revise': 41}
- trackb-matched-minimal|s120: n=120 agreement=0.392 kappa=0.088 native={'drop': 40, 'keep': 40, 'revise': 40} matched={'revise': 61, 'keep': 44, 'drop': 15} transitions={'drop->drop': 7, 'drop->keep': 9, 'drop->revise': 24, 'keep->drop': 3, 'keep->keep': 20, 'keep->revise': 17, 'revise->drop': 5, 'revise->keep': 15, 'revise->revise': 20}
- trackb-matched-minimal|s300: n=300 agreement=0.400 kappa=0.100 native={'revise': 99, 'drop': 99, 'keep': 102} matched={'revise': 144, 'drop': 56, 'keep': 100} transitions={'drop->drop': 28, 'drop->keep': 21, 'drop->revise': 50, 'keep->drop': 10, 'keep->keep': 45, 'keep->revise': 47, 'revise->drop': 18, 'revise->keep': 34, 'revise->revise': 47}

## parse status

{"native_instr|ok": 398, "minimal|ok": 398, "native_instr|rule": 22, "minimal|rule": 22}
