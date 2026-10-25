#!/usr/bin/env bash
# Run a trained policy autonomously AND save the top/wrist camera videos (for demo movies).
# Usage: ./film_policy.sh <model> <clip_name> [episodes] [seconds] ["<task>"]
#   e.g. ./film_policy.sh so101_all104_ft patternD 3 45
# Saved to ~/.cache/huggingface/lerobot/tenyyprn/rollout_<clip_name>_<timestamp>/ ; then run
#   ./make_demo.sh rollout_<clip_name>_<timestamp> [--delete-wrist]   -> top-camera-only clips in demo/
# (the wrist camera must run because the policy uses it, but it also shows the room, so demo clips use the top camera only)
# Between episodes the arm returns to its start pose and waits (reset time 20 s): re-place the sponges.
# Keys: -> end episode early, <- discard and redo, Esc stop.
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate

MODEL="$1"
CLIP="$2"
EPISODES="${3:-3}"
SECONDS_TO_RUN="${4:-45}"
TASK="${5:-Put all the black sponges in the white box}"
[[ "$CLIP" =~ ^[A-Za-z0-9_-]+$ ]] || { echo "clip_name: letters, digits, _ and - only"; exit 1; }
if [ -d "outputs/$MODEL" ]; then RUN_DIR="outputs/$MODEL"; else RUN_DIR="outputs/act_$MODEL"; fi
POLICY="$RUN_DIR/checkpoints/last/pretrained_model"
[ -f "$POLICY/config.json" ] || { echo "Model not found: $POLICY"; exit 1; }
source ./cameras.sh
check_cameras "$TOP_DEV" "$WRIST_DEV" || exit 1
setup_wrist_camera

EXTRA=()
# ACT: temporal ensembling (predict every step and blend overlapping chunks) removes the jerk at
# chunk boundaries (~14 ms/step) but makes motion slow and soft. Off by default; SMOOTH=1 enables it.
if grep -q '"type": "act"' "$POLICY/config.json" && [ "${SMOOTH:-0}" = "1" ]; then
  EXTRA+=(--policy.n_action_steps=1 --policy.temporal_ensemble_coeff=0.01)
fi
# SmolVLA: STEPS=<n> re-plans every n frames instead of 50 (one plan takes ~96 ms on GB10,
# so each re-plan briefly pauses the loop; 15-25 is a reasonable range).
if grep -q '"type": "smolvla"' "$POLICY/config.json" && [ -n "${STEPS:-}" ]; then
  EXTRA+=(--policy.n_action_steps="$STEPS")
fi
if grep -q '"type": "smolvla"' "$POLICY/config.json"; then
  EXTRA+=(--rename_map='{"observation.images.top": "observation.images.camera1", "observation.images.wrist": "observation.images.camera2"}')
fi

run_with_connect_retry lerobot-rollout \
  --strategy.type=episodic \
  --policy.path="$POLICY" \
  --robot.type=so101_follower --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B014901-if00 --robot.id=my_follower \
  --robot.max_relative_target=10 \
  --robot.cameras="{ $TOP_CAM, $WRIST_CAM }" \
  --dataset.repo_id="tenyyprn/rollout_$CLIP" \
  --dataset.single_task="$TASK" \
  --dataset.num_episodes="$EPISODES" \
  --dataset.episode_time_s="$SECONDS_TO_RUN" \
  --dataset.reset_time_s=20 \
  --dataset.push_to_hub=false \
  "${EXTRA[@]}"

LATEST="$(ls -td ~/.cache/huggingface/lerobot/tenyyprn/rollout_"$CLIP"_* 2>/dev/null | head -1)"
echo
echo "Saved: $LATEST"
echo "Make the demo clips (top camera only): ./make_demo.sh $(basename "$LATEST") --delete-wrist"
