#!/usr/bin/env bash
# Run a trained policy (ACT or SmolVLA) on the follower (autonomous, no leader, no recording).
# Usage: ./run_policy.sh <model> [seconds] ["<task>"]
#   ACT:     ./run_policy.sh so101_all104_ft 45          (-> outputs/act_so101_all104_ft)
#   SmolVLA: ./run_policy.sh smolvla_so101_all112 45     (-> outputs/smolvla_so101_all112)
# The task text matters only for SmolVLA (ACT ignores it).
# Ctrl+C to stop — support the follower, torque turns off.
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate

MODEL="$1"
SECONDS_TO_RUN="${2:-30}"
TASK="${3:-Put all the black sponges in the white box}"
if [ -d "outputs/$MODEL" ]; then RUN_DIR="outputs/$MODEL"; else RUN_DIR="outputs/act_$MODEL"; fi
POLICY="$RUN_DIR/checkpoints/last/pretrained_model"
[ -f "$POLICY/config.json" ] || { echo "Model not found: $POLICY"; exit 1; }
source ./cameras.sh

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
  # SmolVLA was trained with top -> camera1, wrist -> camera2
  CAMERAS="{ $TOP_CAM, $WRIST_CAM }"
  check_cameras "$TOP_DEV" "$WRIST_DEV" || exit 1
  setup_wrist_camera
  EXTRA+=(--rename_map='{"observation.images.top": "observation.images.camera1", "observation.images.wrist": "observation.images.camera2"}')
elif grep -q '"observation.images.wrist"' "$POLICY/config.json"; then
  # use the wrist camera only if the policy was trained with it
  CAMERAS="{ $TOP_CAM, $WRIST_CAM }"
  check_cameras "$TOP_DEV" "$WRIST_DEV" || exit 1
  setup_wrist_camera
else
  check_cameras "$TOP_DEV" || exit 1
  CAMERAS="{ $TOP_CAM }"
fi

run_with_connect_retry lerobot-rollout \
  --strategy.type=base \
  --policy.path="$POLICY" \
  --robot.type=so101_follower --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B014901-if00 --robot.id=my_follower \
  --robot.max_relative_target=10 \
  --robot.cameras="$CAMERAS" \
  --task="$TASK" \
  --duration="$SECONDS_TO_RUN" \
  "${EXTRA[@]}"
