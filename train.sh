#!/usr/bin/env bash
# Train an ACT policy on a recorded dataset.
# Usage: ./train.sh <dataset_dir_name> [steps]
#   e.g. ./train.sh so101_pick_20261018_195353 20000
# Output: outputs/act_<dataset_dir_name>/ , log: logs/train_<dataset_dir_name>.log
set -euo pipefail
cd "$(dirname "$0")"

DATASET="$1"
STEPS="${2:-20000}"
ROOT=~/.cache/huggingface/lerobot/tenyyprn/"$DATASET"
OUT="outputs/act_$DATASET"
LOG="logs/train_$DATASET.log"
mkdir -p outputs logs

nohup .venv/bin/lerobot-train \
  --dataset.repo_id="tenyyprn/$DATASET" --dataset.root="$ROOT" \
  --policy.type=act --policy.device=cuda --policy.push_to_hub=false \
  --output_dir="$OUT" --job_name="act_$DATASET" \
  --steps="$STEPS" --batch_size=8 --log_freq=200 --save_freq=5000 \
  --wandb.enable=false > "$LOG" 2>&1 &

echo "Training started (PID $!). Progress: tail -f $LOG"
