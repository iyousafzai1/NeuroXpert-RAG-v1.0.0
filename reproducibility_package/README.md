# NeuroXpert-RAG: Reproducibility Package (15 September 2026)

This package enables exact reproduction of every table, figure, and
statistical result reported in:

> **NeuroXpert-RAG: An Auditable Two-Track Expert-System Architecture for
> LLM-Extracted Biomedical Literature Evidence**
>
> Journal of King Saud University -- Computer and Information Sciences (submitted)

---

## Important: What "Reproduction" Means

The specific numerical values reported in the paper (e.g., Llama 3.1 8B
strict groundedness = 0.904, Qwen 2.5 7B keep-or-revise = 0.879) were
obtained using a **frozen 700-abstract PubMed corpus**, **specific model
checkpoint identifiers**, **fixed random seeds**, and **exact decoding
parameters**.

**Running the NeuroXpert-RAG Python package on a different corpus, with
different model versions, or with different seeds WILL produce different
numbers.** This is expected behavior for any LLM-based pipeline. Model
behavior varies across checkpoint versions, serving configurations, and
input data — this is why we provide the frozen corpus and exact
environment specification.

| What this package provides | What it does NOT provide |
|---|---|
| Exact corpus used in the paper | Model checkpoint files (download from HuggingFace) |
| Complete extraction/verification outputs | A running GPU server |
| Step-by-step regeneration commands | Guaranteed bit-identical outputs on different hardware |
| Environment snapshots (conda + pip) | |

---

## Package Contents

```
neuroxpert_rag_reproducibility_package/
├── README.md                         # This file
├── config/
│   ├── model_identifiers.yaml        # Exact checkpoint identifiers
│   ├── decoding_params.yaml          # Temperature, top_p, token budgets
│   └── seeds.yaml                    # Bootstrap seed and configuration
├── corpus/
│   └── pubmed_corpus_700_abstracts.jsonl   # Frozen 700-abstract corpus
├── environment/
│   ├── conda_env.yaml                # Conda environment specification
│   └── pip_freeze.txt                # Exact pip freeze
├── outputs/
│   ├── extraction/                   # Per-model extracted KB rows (CSV)
│   ├── verification/                 # Per-model Track-B verification (CSV)
│   └── knowledge_base/               # Tiered knowledge base outputs
├── scripts/
│   └── regenerate_all.sh             # One-command regeneration (requires GPU)
└── paper_tables/                     # Source CSV data for every paper table
```

---

## Quick Start

### Option A: Verify the Existing Outputs (No GPU Required)

All extraction and verification CSVs are included in `outputs/`. You can
regenerate every paper table and figure from these frozen outputs:

```bash
cd paper_tables/
python regenerate_tables.py  # Regenerates all paper tables from existing CSVs
```

### Option B: Run the Full Pipeline (Requires GPU)

1. Set up the environment:
   ```bash
   conda env create -f environment/conda_env.yaml
   conda activate neuroxpert-rag
   ```

2. Download model checkpoints (see `config/model_identifiers.yaml`)

3. Start vLLM server:
   ```bash
   bash scripts/regenerate_all.sh
   ```

---

## Mapping: Paper Tables to Source Files

| Paper Table/Figure | Source Data File |
|---|---|
| Table 1 (trackA_summary) | `paper_tables/a8_phase4_ci_summary.csv` |
| Table 2 (ablation) | `paper_tables/a3_baseline_tradeoff.csv` |
| Table 3 (nonllm_baselines) | `paper_tables/nonllm_baseline_comparison.csv` |
| Table 4 (efficiency) | `paper_tables/efficiency_projection.csv` |
| Table 5 (crossdomain) | `paper_tables/crossdomain_tracka_pass.csv` |
| Table 6 (self_preference) | `paper_tables/self_preference_contingency.csv` |
| Table 7 (phi4_summary) | `paper_tables/phi4_independent_verifier.csv` |
| Fig F1 (waterfall) | `paper_tables/a2_gating_flow_waterfall.csv` |
| Fig F2 (performance CI) | `paper_tables/a8_phase4_ci_summary.csv` |
| Fig F3 (baseline tradeoff) | `paper_tables/a3_baseline_tradeoff.csv` |
| Fig F4 (overclaim envelope) | `paper_tables/a3_counterfactual_scores.csv` |
| Fig F5 (inter-model agreement) | `paper_tables/a1_inter_model_agreement.csv` |
| Fig F8 (KB diversity) | `paper_tables/n1_consensus_tier_quality.csv` |
| Fig F9 (consensus stability) | `paper_tables/n1_consensus_tier_quality.csv` |
| Pairwise significance | `paper_tables/a8_phase4_pvalue_significance.csv` |
| Supplementary Tables S1--S30 | `paper_tables/supplementary/` |

---

## Environment

Experiments ran on Ubuntu 24.04.3 LTS, Intel i9-14900K, 125 GiB RAM,
NVIDIA RTX 5880 Ada (47.35 GiB), driver 580.159.03, CUDA 13.0.

Deep learning stack: Python 3.7.8, PyTorch 1.13.1 (CUDA 11.7, cuDNN 8.5),
vLLM 0.21.0 (bfloat16, single-sequence inference).

Full environment specification: `environment/conda_env.yaml` and
`environment/pip_freeze.txt`.

---

## License & Citation

This reproducibility package accompanies the NeuroXpert-RAG paper. The
NeuroXpert-RAG Python package is available at:
`https://github.com/[username]/neuroxpert-rag`

If you use this package in your research, please cite the accompanying paper.


---

## Analysis code and per-row outputs

- `tools/ablation_clean/` — fixed-verifier architecture ablation on the 100-PMID subset (verifier = Llama-3.1-8B in every
  condition), sharded harness, merged per-row outputs, `ablation_conditions.json`, manuscript Table 8 rows, Fig. 3/4 generator.
- `tools/comparators/` — external claim-grounding verifiers (Bespoke-MiniCheck-7B, MiniCheck-Flan-T5-Large, AlignScore-large,
  DeBERTa-v3-large NLI) on the identical claim–evidence pairs: frozen protocol, validation record, raw scores, per-row results.
- `tools/audit_state_experiments/` — paired verifier crossover on byte-identical records (SHA-256 list), human-referenced
  joint Track A × Track B utility (IPW + stratified bootstrap), row-level reproducibility across repeated runs, matched-input
  Track B, Track-A fault injection (21,204 variants), paired AUROC-difference intervals, per-document McNemar tests, and the
  generator of every manuscript table/number (`06_manuscript_tables/`).
- `tools/joint_audit_state_matrix.py`, `tools/derived/` — joint audit-state matrix over the 2,100 rows (Table 6).
- `archived_inputs/baseline_ablation_100/` — the archived May-2026 ablation per-row outputs consumed by the crossover and
  reproducibility analyses; `archived_inputs/human_validation/` — answer key and the two evaluators' ratings for the
  120-row human sample (evaluators are identified only as Evaluator 1 / Evaluator 2).

Scripts under `tools/` contain the absolute paths of the authors' workstation for the archived inputs; point them at
`outputs/verification/` and `archived_inputs/` of this package to re-run.
