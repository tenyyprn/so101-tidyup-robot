#!/usr/bin/env bash
# Make shareable demo clips from a filmed rollout, using ONLY the top camera
# (the wrist camera also shows the room, so it is never included).
# Usage: ./make_demo.sh <rollout_dir_name> [--delete-wrist]
#   e.g. ./make_demo.sh rollout_patternD_20261024_174500
# Output: demo/<name>_ep<N>.mp4 (one clip per episode) and demo/<name>_all.mp4
# --delete-wrist removes the recorded wrist-camera video of this rollout from disk afterwards.
set -euo pipefail
cd "$(dirname "$0")"
NAME="$1"
ROOT=~/.cache/huggingface/lerobot/tenyyprn/"$NAME"
TOP="$ROOT/videos/observation.images.top/chunk-000/file-000.mp4"
[ -f "$TOP" ] || { echo "Top camera video not found: $TOP"; exit 1; }
mkdir -p demo

ffmpeg -hide_banner -loglevel error -y -i "$TOP" -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart "demo/${NAME}_all.mp4"

# one clip per episode, cut at the exact episode boundaries (30 fps)
.venv/bin/python - "$ROOT" <<'EOF' | while read -r EP START END; do
import sys, pandas as pd
df = pd.read_parquet(f"{sys.argv[1]}/data/chunk-000/file-000.parquet")
first = df["index"].min()
for e, g in df.groupby("episode_index")["index"]:
    print(e, (g.min() - first) / 30, (g.max() - first + 1) / 30)
EOF
  ffmpeg -nostdin -hide_banner -loglevel error -y -ss "$START" -to "$END" -i "$TOP" \
    -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart "demo/${NAME}_ep${EP}.mp4"
done
ls -1 demo/"${NAME}"_*.mp4

if [ "${2:-}" = "--delete-wrist" ]; then
  rm -rf "$ROOT/videos/observation.images.wrist"
  echo "Deleted the wrist-camera video of $NAME."
fi
# open in VS Code
[ -t 1 ] && code -r demo/"${NAME}"_all.mp4
