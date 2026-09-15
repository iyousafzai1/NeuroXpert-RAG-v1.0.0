source ~/anaconda3/etc/profile.d/conda.sh; conda activate nxo_verif
export PYTHONPATH=$HOME/nxo_ablation_clean
for i in 0 1 2 3 4 5 6 7; do
  python run_baseline_ablation_fixed_verifier.py --corpus data/pubmed_corpus_700_abstracts.jsonl --pmids data/pmids_shard$i.csv \
    --out-dir out/$3/shard$i --backend vllm --base-url http://127.0.0.1:$2/v1 --model $1 \
    --verifier-model llama-3.1-8b-instruct --verifier-base-url http://127.0.0.1:8000/v1 --full-run-dir full_runs/$4 > logs/$3_shard$i.log 2>&1 &
done
wait
echo COND_DONE_$3
