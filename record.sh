#!/usr/bin/env bash
# SO101 data recording.
# Usage: ./record.sh <dataset_name> <num_episodes> "<task description>" [reset_seconds] [episode_seconds]   (defaults: reset 30, episode 20)
#   e.g. ./record.sh so101_test 2 "Pick up the block and place it in the box"
# Saved to ~/.cache/huggingface/lerobot/tenyyprn/<dataset_name>_<timestamp>/
# Check camera framing beforehand with ./preview.sh, check the result with ./review.sh
# (Rerun viewer does not render on this machine).
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate

NAME="${1:-so101_test}"
EPISODES="${2:-2}"
TASK="${3:-Pick up the block and place it in the box}"
RESET="${4:-30}"
EPISODE_TIME="${5:-20}"
source ./cameras.sh

# guard against typos like: ./record.sh so101_test2"Pick up ..."
if [[ ! "$NAME" =~ ^[A-Za-z0-9_-]+$ ]] || [[ ! "$EPISODES" =~ ^[0-9]+$ ]] || [[ ! "$RESET" =~ ^[0-9]+$ ]] || [[ ! "$EPISODE_TIME" =~ ^[0-9]+$ ]]; then
  echo "Error: check spaces between arguments."
  echo "  Usage: ./record.sh <name> <episodes> \"<task>\""
  echo "  e.g.   ./record.sh so101_test 2 \"Pick up the block and place it in the box\""
  exit 1
fi

check_cameras "$TOP_DEV" "$WRIST_DEV" || exit 1
setup_wrist_camera

run_with_connect_retry lerobot-record \
  --robot.type=so101_follower --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B014901-if00 --robot.id=my_follower \
  --robot.cameras="{ $TOP_CAM, $WRIST_CAM }" \
  --teleop.type=so101_leader --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B014960-if00 --teleop.id=my_leader \
  --display_data=false \
  --dataset.repo_id="tenyyprn/$NAME" \
  --dataset.single_task="$TASK" \
  --dataset.num_episodes="$EPISODES" \
  --dataset.episode_time_s="$EPISODE_TIME" \
  --dataset.reset_time_s="$RESET" \
  --dataset.push_to_hub=false

LATEST="$(ls -td ~/.cache/huggingface/lerobot/tenyyprn/"$NAME"_* | head -1)"
echo
echo "Saved: $LATEST"
echo "Check: ./review.sh"
