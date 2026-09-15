#!/usr/bin/env bash
# NeuroXpert-RAG: Full Pipeline Regeneration Script
# =================================================
# This script regenerates the complete experimental pipeline described in:
# "NeuroXpert-RAG: An Auditable Two-Track Expert-System Architecture for
#  LLM-Extracted Biomedical Literature Evidence"
#
# Requirements:
#   - NVIDIA GPU with >= 48 GiB memory (RTX 5880 Ada or equivalent)
#   - vLLM server running at http://127.0.0.1:8000/v1
#   - Conda environment: neuroxpert-rag (see environment/conda_env.yaml)
#   - Model checkpoints downloaded (see config/model_identifiers.yaml)
#
# ⚠️ WARNING: Running this script on different hardware, with different model
#    checkpoint versions, or on a different corpus WILL produce different numbers
#    from those reported in the paper. For exact paper-number reproduction, use
#    the frozen outputs in outputs/ rather than regenerating.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
CORPUS="${PKG_DIR}/corpus/pubmed_corpus_700_abstracts.jsonl"
OUTPUT_DIR="${PKG_DIR}/outputs"
CONFIG_DIR="${PKG_DIR}/config"
VLLM_URL="${VLLM_URL:-http://127.0.0.1:8000/v1}"

# Model list (must match config/model_identifiers.yaml)
EXTRACTORS=("llama-3.1-8b-instruct" "qwen2.5-7b-instruct" "mistral-7b-instruct-v0.3")
VERIFIER="llama-3.1-8b-instruct"

echo "============================================================"
echo "NeuroXpert-RAG: Full Pipeline Regeneration"
echo "============================================================"
echo "Corpus: ${CORPUS}"
echo "Output: ${OUTPUT_DIR}"
echo "vLLM URL: ${VLLM_URL}"
echo ""

# Stage 1: Structured Extraction (one run per extractor model)
echo "[Stage 1/4] Structured Extraction"
for MODEL in "${EXTRACTORS[@]}"; do
    MODEL_OUT="${OUTPUT_DIR}/extraction/${MODEL}"
    mkdir -p "${MODEL_OUT}"

    echo "  Extracting with ${MODEL}..."
    python -m neuroxpert_rag.pilot.extract_triples \
        --corpus "${CORPUS}" \
        --out "${MODEL_OUT}/extracted_kb.csv" \
        --backend vllm \
        --vllm-model "${MODEL}" \
        --vllm-base-url "${VLLM_URL}" \
        --max-papers 700

    echo "  ${MODEL} extraction complete."
done

# Stage 2: Mechanical Grounding (Track A) + Semantic Verification (Track B)
echo "[Stage 2/4] Two-Track Audit (Track A + Track B)"
for MODEL in "${EXTRACTORS[@]}"; do
    MODEL_IN="${OUTPUT_DIR}/extraction/${MODEL}/extracted_kb.csv"
    MODEL_OUT="${OUTPUT_DIR}/verification/${MODEL}"
    mkdir -p "${MODEL_OUT}"

    echo "  Auditing ${MODEL}..."
    python -m neuroxpert_rag.pilot.semantic_llm_verifier \
        --input "${MODEL_IN}" \
        --corpus "${CORPUS}" \
        --out "${MODEL_OUT}/verified_kb.csv" \
        --backend vllm \
        --vllm-model "${VERIFIER}" \
        --vllm-base-url "${VLLM_URL}"
done

# Stage 3: Tiered Knowledge-Base Construction
echo "[Stage 3/4] Tiered Knowledge-Base Construction"
KB_OUT="${OUTPUT_DIR}/knowledge_base"
mkdir -p "${KB_OUT}"

VERIFIED_FILES=""
for MODEL in "${EXTRACTORS[@]}"; do
    VERIFIED_FILES="${VERIFIED_FILES} ${OUTPUT_DIR}/verification/${MODEL}/verified_kb.csv"
done

python -m neuroxpert_rag.pilot.build_verified_kb \
    --inputs ${VERIFIED_FILES} \
    --out "${KB_OUT}" \
    --consensus-min-models 2

# Stage 4: Regenerate Paper Tables
echo "[Stage 4/4] Regenerating Paper Tables"
python "${PKG_DIR}/paper_tables/regenerate_tables.py" \
    --kb-dir "${KB_OUT}" \
    --verification-dir "${OUTPUT_DIR}/verification" \
    --out-dir "${PKG_DIR}/paper_tables/regenerated"

echo ""
echo "============================================================"
echo "Pipeline complete. Outputs in: ${OUTPUT_DIR}"
echo "Regenerated tables in: ${PKG_DIR}/paper_tables/regenerated"
echo "============================================================"
