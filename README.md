# NeuroXpert-RAG

An auditable two-track expert-system architecture for LLM-extracted biomedical
literature evidence. Separates deterministic mechanical grounding (Track A)
from model-based semantic verification (Track B).

**Key innovation**: Track-A (model-free) and Track-B (model-based) produce
DISTINCT audit signals. Models that appear interchangeable under Track-B
acceptance rates differ fundamentally in mechanical traceability under Track-A.

## Installation

```bash
pip install neuroxpert-rag
```

## Demo: See the Core Dissociation (No GPU Required)

The demo runs on 3 real PubMed abstracts processed by all three extractors
(Llama 3.1 8B, Qwen 2.5 7B, Mistral 7B) with pre-computed outputs from the paper.

```bash
python demo.py
```

**What the demo shows — the paper's central finding at miniature scale:**

```
Model              Track-A Strict Grounded     Track-B KoR
────────────────── ──────────────────────  ──────────────
Llama 3.1 8B       3/3 = 1.000             3/3 = 1.000
Qwen 2.5 7B        3/3 = 1.000             3/3 = 1.000
Mistral 7B         1/3 = 0.333             3/3 = 1.000

TRACK-A RANGE: 0.333 → 1.000  (diverges by 66.7%)
TRACK-B RANGE: 1.000 → 1.000  (converges)
```

**Error signatures detected by the demo:**

| Model | Signature |
|---|---|
| Mistral 7B | MECHANICAL UNTRACEABILITY: 2/3 rows fail quote anchoring but are semantically accepted — paraphrastic sentences |
| Llama 3.1 8B | PARTIAL SUPPORT: 1/3 rows are grounded but need field-level correction |
| Qwen 2.5 7B | PARTIAL SUPPORT: 1/3 rows are grounded but need field-level correction |

The demo also verifies verifier blinding (zero extractor identity in prompts),
maps the architecture to classical expert-system components, and shows the
full 700-abstract paper results for comparison.

## Quick Start (Requires GPU + LLM Server)

```python
from neuroxpert_rag.pilot.extract_triples import ollama_extract
from neuroxpert_rag.llm.openai_compat_client import OpenAICompatClient

# Connect to your LLM backend
client = OpenAICompatClient(base_url="http://127.0.0.1:8000/v1")

# Extract structured claims from a PubMed abstract
paper = {
    "pmid": "39315326",
    "title": "Functional connectivity and impulsivity...",
    "abstract": "We examined resting-state fMRI..."
}
record = ollama_extract(paper, client=client, model="llama-3.1-8b-instruct")
```

Or from the command line:
```bash
python -m neuroxpert_rag.pilot.extract_triples \
    --corpus your_corpus.jsonl --out output.csv \
    --backend vllm --vllm-model llama-3.1-8b-instruct

python -m neuroxpert_rag.pilot.semantic_llm_verifier \
    --input output.csv --corpus your_corpus.jsonl \
    --out verified.csv --backend vllm --vllm-model llama-3.1-8b-instruct
```

## ⚠️ Reproducing Paper Results

The specific numbers reported in the NeuroXpert-RAG paper were obtained using a
frozen 700-abstract PubMed corpus, specific model checkpoint identifiers, fixed
seeds, and exact decoding parameters. Running this package on different data or
with different model versions WILL produce different numbers.

To exactly reproduce the paper results, use the frozen reproducibility package:
`https://doi.org/10.5281/zenodo.20740642`

## Architecture

```
Corpus → Extraction → Track A (Deterministic Grounding) → Track B (Semantic Verification) → Tiered KB
                  ↘                                    ↓
                   Per-row audit trail (PMID + sentence + both verdicts)
```

- **Track A**: Deterministic, model-free (schema, citation, sentence anchoring)
- **Track B**: LLM-based, blinded to extractor identity
- **Tiered KB**: Keep-only, keep-or-revise, and consensus tiers for expert review

## Modules

| Module | Purpose |
|---|---|
| `pilot/extract_triples.py` | Schema-constrained extraction from PubMed |
| `pilot/semantic_llm_verifier.py` | Blinded semantic verification (Track B) |
| `pilot/build_verified_kb.py` | Tiered knowledge-base construction |
| `pilot/pubmed_retrieve.py` | NCBI E-utilities corpus retrieval |
| `pilot/schemas.py` | Controlled vocabularies and record validation |
| `llm/openai_compat_client.py` | vLLM / OpenAI-compatible API client |
| `llm/prompts.py` | Prompt template builder |

## Sample Data

The `samples/` directory contains:
- `sample_corpus.jsonl` — 3 real PubMed abstracts from the paper's corpus
- `sample_llama31_8b_output.csv` — Llama 3.1 8B extraction + Track-A/B outputs
- `sample_qwen25_7b_output.csv` — Qwen 2.5 7B extraction + Track-A/B outputs
- `sample_mistral7b_output.csv` — Mistral 7B extraction + Track-A/B outputs

## License

MIT. See accompanying paper for citation.
