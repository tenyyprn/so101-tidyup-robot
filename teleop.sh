#!/usr/bin/env bash
# Teleoperation only (no recording) for practice. Ctrl+C to stop — support the follower, torque turns off.
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate

lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B014901-if00 --robot.id=my_follower \
  --teleop.type=so101_leader --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B014960-if00 --teleop.id=my_leader
