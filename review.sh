#!/usr/bin/env bash
# Convert the latest (or given) recording to H.264 + thumbnail sheet and open them in VS Code.
# Usage: ./review.sh [dataset_dir_name]
set -euo pipefail
cd "$(dirname "$0")"
ROOT=~/.cache/huggingface/lerobot/tenyyprn
if [ $# -ge 1 ]; then
  NAME="$1"
else
  LATEST="$(ls -td "$ROOT"/*/ | head -1)"
  NAME="$(basename "$LATEST")"
fi
SRC="$ROOT/$NAME/videos/observation.images.top/chunk-000/file-000.mp4"
WRIST="$ROOT/$NAME/videos/observation.images.wrist/chunk-000/file-000.mp4"
mkdir -p review
if [ -e "$WRIST" ]; then
  # top | wrist side by side, labeled
  ffmpeg -hide_banner -loglevel error -y -i "$SRC" -i "$WRIST" -filter_complex \
    "[0]scale=640:480,drawtext=text='top':x=10:y=10:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5[a];[1]scale=640:480,drawtext=text='wrist':x=10:y=10:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5[b];[a][b]hstack" \
    -c:v libx264 -pix_fmt yuv420p -crf 26 -movflags +faststart "review/$NAME.mp4"
else
  ffmpeg -hide_banner -loglevel error -y -i "$SRC" -c:v libx264 -pix_fmt yuv420p -crf 26 -movflags +faststart "review/$NAME.mp4"
fi
# one thumbnail per episode (middle frame), up to 20, tiled 5 per row
EPISODES=$(python3 -c "import json;print(json.load(open('$ROOT/$NAME/meta/info.json'))['total_episodes'])")
N=$(( EPISODES < 20 ? EPISODES : 20 )); ROWS=$(( (N + 4) / 5 ))
# frames per episode (episodes are recorded with a fixed length)
LEN=$(python3 -c "import json;d=json.load(open('$ROOT/$NAME/meta/info.json'));print(round(d['total_frames']/d['total_episodes']))")
ffmpeg -hide_banner -loglevel error -y -i "$SRC" -vf "select='eq(mod(n\,$LEN)\,trunc($LEN/2))',scale=320:-1,tile=5x$ROWS" -fps_mode vfr -frames:v 1 "review/${NAME}_sheet.png"
# first 4 s of each episode (0,1,2,3,4 s per row): hands placing the sponge show up here
ffmpeg -hide_banner -loglevel error -y -i "$SRC" -vf "select='lt(mod(n\,$LEN)\,121)*not(mod(mod(n\,$LEN)\,30))',scale=160:-1,tile=5x$N" -fps_mode vfr -frames:v 1 "review/${NAME}_starts.png"

# first and last frame of each episode, using the exact episode boundaries
# (row of pairs: start, end, start, end ...): leftover sponges show up in the "end" frames
SEL=$(.venv/bin/python - "$ROOT/$NAME" <<'EOF'
import sys, pandas as pd
df = pd.read_parquet(f"{sys.argv[1]}/data/chunk-000/file-000.parquet")
g = df.groupby("episode_index")["index"]
first = df["index"].min()
print("+".join(f"eq(n\\,{s - first + 3})+eq(n\\,{e - first - 3})" for s, e in zip(g.min(), g.max())))
EOF
)
ffmpeg -hide_banner -loglevel error -y -i "$SRC" -vf "select='$SEL',scale=200:-1,tile=10x$(( (EPISODES + 4) / 5 ))" -fps_mode vfr -frames:v 1 "review/${NAME}_startend.png"

# per-episode movement check: a joint range near 0 means the arm did not move
.venv/bin/python - "$ROOT/$NAME" <<'EOF'
import sys, numpy as np, pandas as pd
df = pd.read_parquet(f"{sys.argv[1]}/data/chunk-000/file-000.parquet")
for e, g in df.groupby("episode_index"):
    a = np.stack(g["action"].values)
    move = (a.max(0) - a.min(0))
    status = "OK" if move[:5].max() > 10 else "NOT MOVING"
    print(f"episode {e}: {len(g)/30:.0f}s  gripper {a[:,5].min():.0f}-{a[:,5].max():.0f}  {status}")
EOF
echo "Check review/${NAME}_starts.png for hands in the first seconds (one row per episode)."
code -r "review/${NAME}_startend.png" "review/${NAME}_starts.png" "review/${NAME}_sheet.png" "review/$NAME.mp4"
