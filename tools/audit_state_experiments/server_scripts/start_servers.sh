#!/bin/bash
mkdir -p ~/nxo_review_experiments/logs; cd ~/nxo_review_experiments
source ~/anaconda3/etc/profile.d/conda.sh; conda activate vllm311
export HF_ENDPOINT=https://hf-mirror.com VLLM_ENABLE_V1_MULTIPROCESSING=0
LLAMA=~/my_datasets/tracekg_project/models/llama-3.1-8b-instruct
QWEN=$(ls -d /mnt/data/qwe123/nxo_models/hf/models--Qwen--Qwen2.5-7B-Instruct/snapshots/* | head -1)
nohup python -m vllm.entrypoints.openai.api_server --model "$LLAMA" --served-model-name llama-3.1-8b-instruct --dtype bfloat16 --max-model-len 4096 --gpu-memory-utilization 0.42 --port 8000 > logs/vllm_llama.log 2>&1 &
echo $! > logs/vllm_llama.pid
sleep 25
nohup python -m vllm.entrypoints.openai.api_server --model "$QWEN" --served-model-name qwen2.5-7b-instruct --dtype bfloat16 --max-model-len 4096 --gpu-memory-utilization 0.42 --port 8001 > logs/vllm_qwen.log 2>&1 &
echo $! > logs/vllm_qwen.pid
echo "started llama pid $(cat logs/vllm_llama.pid) qwen pid $(cat logs/vllm_qwen.pid)"
