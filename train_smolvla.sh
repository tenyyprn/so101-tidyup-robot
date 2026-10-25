#!/usr/bin/env bash
# Fine-tune SmolVLA (lerobot/smolvla_base) on a recorded dataset.
# Usage: ./train_smolvla.sh <dataset_dir_name> [steps] [batch_size]
#   e.g. ./train_smolvla.sh so101_all112 30000 8
# smolvla_base expects camera1..camera3: top -> camera1, wrist -> camera2 (camera3 unused).
# Output: outputs/smolvla_<dataset>/ , log: logs/train_smolvla_<dataset>.log
set -euo pipefail
cd "$(dirname "$0")"

DATASET="$1"
STEPS="${2:-30000}"
BATCH="${3:-8}"
ROOT=~/.cache/huggingface/lerobot/tenyyprn/"$DATASET"
OUT="outputs/smolvla_$DATASET"
LOG="logs/train_smolvla_$DATASET.log"
mkdir -p outputs logs

nohup .venv/bin/lerobot-train \
  --policy.path=lerobot/smolvla_base --policy.device=cuda --policy.push_to_hub=false \
  --dataset.repo_id="tenyyprn/$DATASET" --dataset.root="$ROOT" \
  --rename_map='{"observation.images.top": "observation.images.camera1", "observation.images.wrist": "observation.images.camera2"}' \
  --output_dir="$OUT" --job_name="smolvla_$DATASET" \
  --steps="$STEPS" --batch_size="$BATCH" --log_freq=200 --save_freq=5000 \
  --wandb.enable=false > "$LOG" 2>&1 &

echo "SmolVLA training started (PID $!). Progress: tail -f $LOG"
