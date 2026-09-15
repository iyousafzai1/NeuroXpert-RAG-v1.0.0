#!/bin/bash
cd ~/nxo_review_experiments
source ~/anaconda3/etc/profile.d/conda.sh; conda activate nxo_verif
export PYTHONPATH=$HOME/nxo_ablation_clean
for p in 8000 8001; do curl -s http://127.0.0.1:$p/v1/models | python3 -c "import sys,json; print($p, [m['id'] for m in json.load(sys.stdin)['data']])"; done
L=http://127.0.0.1:8000/v1; Q=http://127.0.0.1:8001/v1
S=scripts/rescore_rows.py
# --- Step 0: paired crossover. Llama verifier on every row set (archived + clean, B + C, all extractors) ---
(
for m in llama31_8b qwen25_7b mistral7b; do for src in archived clean; do for c in B C; do
  python $S --in-csv inputs/${src}_${m}_${c}_audit_sheet.csv --out-csv out/00_crossover/${src}_${m}_${c}__verifier_llama.csv --verifier-model llama-3.1-8b-instruct --base-url $L --workers 12 > logs/x_${src}_${m}_${c}_llama.log 2>&1
done; done; done; echo XOVER_LLAMA_DONE
) > logs/phase_xover_llama.log 2>&1 &
# --- Step 0: Qwen self-verification on Qwen rows (archived + clean, B + C) ---
(
for src in archived clean; do for c in B C; do
  python $S --in-csv inputs/${src}_qwen25_7b_${c}_audit_sheet.csv --out-csv out/00_crossover/${src}_qwen25_7b_${c}__verifier_qwen.csv --verifier-model qwen2.5-7b-instruct --base-url $Q --workers 12 > logs/x_${src}_qwen_${c}_qwen.log 2>&1
done; done; echo XOVER_QWEN_DONE
) > logs/phase_xover_qwen.log 2>&1 &
# --- Step 3: matched-input Track B (Llama) ---
nohup python scripts/run_matched_input_trackb.py --rows inputs/rows_120.jsonl inputs/rows_300.jsonl --out-dir out/03_matched --base-url $L --workers 12 > logs/matched.log 2>&1 &
sleep 2; echo "launched: $(pgrep -fc 'rescore_rows.py|run_matched_input')"
