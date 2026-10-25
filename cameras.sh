# Camera definitions shared by record.sh / run_policy.sh (source this file).
# top:   Logicool C920 overhead, 640x480 MJPG 30 fps
# wrist: Inno-Maker U20CAM-1080P on the gripper (wide angle ~120°), 640x480 MJPG
TOP_DEV=/dev/v4l/by-id/usb-046d_HD_Pro_Webcam_C920-video-index0
WRIST_DEV=/dev/v4l/by-id/usb-Innomaker_Innomaker-U20CAM-1080p-S1_SN0001-video-index0
TOP_CAM="top: {type: opencv, index_or_path: $TOP_DEV, width: 640, height: 480, fps: 30, fourcc: MJPG}"
WRIST_CAM="wrist: {type: opencv, index_or_path: $WRIST_DEV, width: 640, height: 480, fps: 30, fourcc: MJPG}"

# Fail early with a clear message instead of a LeRobot traceback.
check_cameras() {
  local ok=0
  for dev in "$@"; do
    [ -e "$dev" ] || { echo "Camera not found: $dev (check the dock / USB hub)"; ok=1; }
  done
  return $ok
}

# The U20CAM lowers its frame rate in dim light (exposure_dynamic_framerate=1, ~16 fps).
# Turning it off keeps ~27-30 fps. The setting resets when the camera is re-plugged.
setup_wrist_camera() {
  v4l2-ctl -d "$WRIST_DEV" -c exposure_dynamic_framerate=0 2>/dev/null || true
}

# Run a lerobot command, retrying (up to 3 times) only when it failed while connecting to the
# follower ("no status packet" / "Incorrect status packet" inside robot.connect()). That error
# happens occasionally when all motors enable torque at once; a second attempt succeeds.
run_with_connect_retry() {
  local log status attempt opts="$-"
  log="$(mktemp)"
  set +e  # callers use `set -e`; handle the failure here instead of exiting
  for attempt in 1 2 3; do
    PYTHONUNBUFFERED=1 "$@" 2>&1 | tee "$log"
    status=${PIPESTATUS[0]}
    [ "$status" -eq 0 ] && break
    if grep -q "robot.connect()" "$log" && grep -qE "no status packet|Incorrect status packet" "$log"; then
      echo; echo ">>> Follower connection glitch (attempt $attempt/3). Retrying in 3 s..."; sleep 3
    else
      break
    fi
  done
  rm -f "$log"
  [[ "$opts" == *e* ]] && set -e
  return "$status"
}
