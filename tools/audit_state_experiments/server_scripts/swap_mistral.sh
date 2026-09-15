#!/bin/bash
cd ~/nxo_review_experiments
kill $(cat logs/vllm_qwen.pid); sleep 8
nvidia-smi --query-gpu=memory.used --format=csv,noheader
source ~/anaconda3/etc/profile.d/conda.sh; conda activate vllm311
export HF_ENDPOINT=https://hf-mirror.com VLLM_ENABLE_V1_MULTIPROCESSING=0
MIS=$(ls -d /mnt/data/qwe123/nxo_models/hf/models--mistralai--Mistral-7B-Instruct-v0.3/snapshots/* | head -1)
nohup python -m vllm.entrypoints.openai.api_server --model "$MIS" --served-model-name mistral-7b-instruct-v0.3 --dtype bfloat16 --max-model-len 4096 --gpu-memory-utilization 0.42 --port 8001 > logs/vllm_mistral.log 2>&1 &
echo $! > logs/vllm_mistral.pid
until grep -qE "Application startup complete|Traceback" logs/vllm_mistral.log; do sleep 10; done
grep -q Traceback logs/vllm_mistral.log && { echo MISTRAL_FAILED; tail -5 logs/vllm_mistral.log; exit 1; }
conda activate nxo_verif; export PYTHONPATH=$HOME/nxo_ablation_clean
for src in archived clean; do for c in B C; do
  python scripts/rescore_rows.py --in-csv inputs/${src}_mistral7b_${c}_audit_sheet.csv --out-csv out/00_crossover/${src}_mistral7b_${c}__verifier_mistral.csv --verifier-model mistral-7b-instruct-v0.3 --base-url http://127.0.0.1:8001/v1 --workers 12 > logs/x_${src}_mistral_${c}_mistral.log 2>&1
done; done
echo XOVER_MISTRAL_DONE
