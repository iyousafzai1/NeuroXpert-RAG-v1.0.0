# Paired McNemar tests (exact, two-sided; Holm-Bonferroni over the three model pairs within each metric); n = 700 shared abstracts

| metric | pair | rate A | rate B | Δ (pp) | discordant b / c | p (raw) | p (Holm) |
|---|---|---|---|---|---|---|---|
| trackA | Llama–Qwen | 0.904 | 0.814 | +9.0 | 104 / 41 | 1.70e-07 | 1.7e-07 |
| trackA | Llama–Mistral | 0.904 | 0.594 | +31.0 | 251 / 34 | 4.72e-42 | 1.42e-41 |
| trackA | Qwen–Mistral | 0.814 | 0.594 | +22.0 | 231 / 77 | 4.97e-19 | 9.94e-19 |
| trackB_kr | Llama–Qwen | 0.847 | 0.879 | -3.1 | 49 / 71 | 5.48e-02 | 0.11 |
| trackB_kr | Llama–Mistral | 0.847 | 0.840 | +0.7 | 55 / 50 | 6.96e-01 | 0.696 |
| trackB_kr | Qwen–Mistral | 0.879 | 0.840 | +3.9 | 76 / 49 | 1.97e-02 | 0.059 |
| overclaim | Llama–Qwen | 0.011 | 0.009 | +0.3 | 6 / 4 | 7.54e-01 | 1 |
| overclaim | Llama–Mistral | 0.011 | 0.007 | +0.4 | 7 / 4 | 5.49e-01 | 1 |
| overclaim | Qwen–Mistral | 0.009 | 0.007 | +0.1 | 6 / 5 | 1.00e+00 | 1 |
