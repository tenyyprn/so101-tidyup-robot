#!/usr/bin/env bash
# Live camera preview for adjusting framing. Close the window (or press q) before running record.sh.
# Usage: ./preview.sh [top|wrist]   (default: top)
case "${1:-top}" in
  top)   DEV=/dev/v4l/by-id/usb-046d_HD_Pro_Webcam_C920-video-index0; SIZE=640x480; FPS=30 ;;
  wrist) DEV=/dev/v4l/by-id/usb-Innomaker_Innomaker-U20CAM-1080p-S1_SN0001-video-index0; SIZE=640x480; FPS=30
         v4l2-ctl -d "$DEV" -c exposure_dynamic_framerate=0 2>/dev/null ;;
  *) echo "Usage: ./preview.sh [top|wrist]"; exit 1 ;;
esac
[ -e "$DEV" ] || { echo "Camera not found: $DEV (check the USB cable)"; exit 1; }
exec ffplay -hide_banner -loglevel error -window_title "$1 camera (q to quit)" \
  -f v4l2 -input_format mjpeg -video_size "$SIZE" -framerate "$FPS" "$DEV"
