#!/usr/bin/env bash
# Train Diffusion Policy on a recorded dataset (multimodal: picks ONE of several valid actions
# instead of averaging them, unlike ACT).
# Usage: ./train_diffusion.sh <dataset_dir_name> [steps] [batch_size]
#   e.g. ./train_diffusion.sh so101_all112 40000 32
# Images are resized to 240x320 with a 95% random crop; DDIM with 10 denoising steps at inference.
# Output: outputs/diffusion_<dataset>/ , log: logs/train_diffusion_<dataset>.log
set -euo pipefail
cd "$(dirname "$0")"

DATASET="$1"
STEPS="${2:-40000}"
BATCH="${3:-32}"
ROOT=~/.cache/huggingface/lerobot/tenyyprn/"$DATASET"
OUT="outputs/diffusion_$DATASET"
LOG="logs/train_diffusion_$DATASET.log"
mkdir -p outputs logs

nohup .venv/bin/lerobot-train \
  --policy.type=diffusion --policy.device=cuda --policy.push_to_hub=false \
  --policy.resize_shape='[240, 320]' --policy.crop_ratio=0.95 \
  --policy.noise_scheduler_type=DDIM --policy.num_inference_steps=10 --policy.n_action_steps=16 \
  --dataset.repo_id="tenyyprn/$DATASET" --dataset.root="$ROOT" \
  --output_dir="$OUT" --job_name="diffusion_$DATASET" \
  --steps="$STEPS" --batch_size="$BATCH" --num_workers=8 --log_freq=200 --save_freq=5000 \
  --wandb.enable=false > "$LOG" 2>&1 &

echo "Diffusion Policy training started (PID $!). Progress: tail -f $LOG"
