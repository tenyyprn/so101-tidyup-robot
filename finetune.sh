#!/usr/bin/env bash
# Continue training from an already trained ACT model on a (larger) dataset.
# Usage: ./finetune.sh <base_dataset_name> <new_dataset_dir_name> [steps]
#   e.g. ./finetune.sh so101_all94 so101_all104 20000
# Starts from outputs/act_<base>/checkpoints/last/pretrained_model; normalization stats are
# recomputed from the new dataset. Output: outputs/act_<new>_ft/ , log: logs/train_<new>_ft.log
set -euo pipefail
cd "$(dirname "$0")"

BASE="$1"
DATASET="$2"
STEPS="${3:-20000}"
BASE_MODEL="outputs/act_$BASE/checkpoints/last/pretrained_model"
ROOT=~/.cache/huggingface/lerobot/tenyyprn/"$DATASET"
OUT="outputs/act_${DATASET}_ft"
LOG="logs/train_${DATASET}_ft.log"
[ -d "$BASE_MODEL" ] || { echo "Base model not found: $BASE_MODEL"; exit 1; }
mkdir -p outputs logs

nohup .venv/bin/lerobot-train \
  --policy.path="$BASE_MODEL" --policy.device=cuda --policy.push_to_hub=false \
  --dataset.repo_id="tenyyprn/$DATASET" --dataset.root="$ROOT" \
  --output_dir="$OUT" --job_name="act_${DATASET}_ft" \
  --steps="$STEPS" --batch_size=8 --log_freq=200 --save_freq=5000 \
  --wandb.enable=false > "$LOG" 2>&1 &

echo "Fine-tuning started (PID $!). Progress: tail -f $LOG"
