"""Build the demo movie from video/storyboard.json.

Each scene is one of
  {"type": "card",  "duration": 5, "title": "...", "text": "..."}            text on a dark background
  {"type": "image", "duration": 8, "file": "assets/x.png", "caption": "..."}  still image, letterboxed
  {"type": "clip",  "file": "<path or dataset:NAME>", "start": 0, "end": 12,
   "speed": 1.0, "episode": 0, "caption": "..."}                             top-camera video
  {"type": "compare", "speed": 2.0, "caption": "...",
   "left": {"label": "ACT", "file": ..., "episode": 0, "start": 0, "end": 30},
   "right": {"label": "Diffusion Policy", ...}}                             two clips side by side
A clip whose file is "dataset:NAME" uses the top camera of ~/.cache/huggingface/lerobot/tenyyprn/NAME;
with "episode" given, start/end are seconds inside that episode. A missing clip becomes a placeholder card,
so the movie can be drafted before every shot is filmed. Captions are burned in as Japanese subtitles.

"speed" is relative to REAL time. Policy rollouts record fewer frames per second than they claim (Diffusion
Policy pauses ~0.18 s to re-plan, so a 45 s run is stored as ~34 s of 30 fps video). Give such a clip
"real_s": the episode's real duration (film_policy.sh seconds); the stored/real ratio is then measured and the
playback is slowed so that the labelled speed is true. start/end stay in stored-video seconds.

Usage: .venv/bin/python video/make_video.py [storyboard.json] [output.mp4]
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = Path.home() / ".cache/huggingface/lerobot/tenyyprn"
W, H, FPS = 1280, 720, 30
FONT = "Noto Sans CJK JP"
CROP_LEFT = 125  # px removed from the left of every clip (per-scene "crop_left" overrides)


def run(cmd):
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)


def ass_time(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def ass_text(s):
    return s.replace("\n", "\\N")


def resolve_clip(scene):
    """Return (video path, start s, end s, stored/real time ratio) or None when the footage does not exist yet."""
    f = scene["file"]
    start, end = scene.get("start", 0), scene.get("end")
    if f.startswith("dataset:"):
        name = f.split(":", 1)[1]
        root = DATA / name
        video = root / "videos/observation.images.top/chunk-000/file-000.mp4"
        if not video.exists():
            return None
        if "episode" in scene:
            df = pd.read_parquet(root / "data/chunk-000/file-000.parquet")
            ep = df[df.episode_index == scene["episode"]]["index"]
            offset = (ep.min() - df["index"].min()) / FPS
            length = len(ep) / FPS
            start, end = offset + start, offset + min(end if end is not None else length, length)
            if "real_s" in scene:
                return video, start, end, length / scene["real_s"]
        return video, start, end, 1.0
    path = (HERE / f) if not Path(f).is_absolute() else Path(f)
    return (path, start, end, 1.0) if path.exists() else None


def render_scene(scene, out, tmp):
    common = ["-r", str(FPS), "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "20", "-an"]
    fit = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x101418,setsar=1"
    kind = scene["type"]
    if kind == "clip":
        src = resolve_clip(scene)
        if src is None:  # not filmed yet
            scene = {"type": "card", "duration": scene.get("placeholder_duration", scene.get("end", 8) - scene.get("start", 0)),
                     "title": "(撮影予定)", "text": scene.get("todo", scene["file"])}
            kind = "card"
        else:
            video, start, end, ratio = src
            speed = scene.get("speed", 1.0) * ratio  # playback factor that gives the labelled real-time speed
            # cut the left edge of the 640x480 top camera (a book sat there in early recordings)
            left = scene.get("crop_left", CROP_LEFT)
            crop = f"crop=iw-{left}:ih:{left}:0," if left else ""
            run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
                 "-i", str(video), "-vf", f"{crop}setpts=PTS/{speed},{fit}", *common, str(out)])
            return (end - start) / speed, scene
    if kind == "compare":
        # each side: crop the left edge, fit into half the frame; the shorter side holds its last frame
        # both sides play at the same REAL-time speed, so neither policy looks faster than it is
        sides = []
        for side in (scene["left"], scene["right"]):
            video, start, end, ratio = resolve_clip(side)
            sides.append((video, start, end, side.get("crop_left", CROP_LEFT), scene.get("speed", 1.0) * ratio))
        dur = max((end - start) / speed for _, start, end, _, speed in sides)
        inputs, chains = [], []
        for i, (video, start, end, left, speed) in enumerate(sides):
            inputs += ["-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(video)]
            chains.append(f"[{i}:v]crop=iw-{left}:ih:{left}:0,setpts=PTS/{speed},"
                          f"scale={W // 2 - 10}:-2,pad={W // 2}:{H}:5:(oh-ih)/2+20:color=0x101418,"
                          f"tpad=stop_mode=clone:stop_duration={dur:.3f},trim=duration={dur:.3f},setsar=1[v{i}]")
        run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *inputs, "-filter_complex",
             ";".join(chains) + ";[v0][v1]hstack=inputs=2[v]", "-map", "[v]", *common, str(out)])
        return dur, scene
    if kind == "image":
        run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-t", str(scene["duration"]),
             "-i", str(HERE / scene["file"]), "-vf", f"{fit},format=yuv420p", *common, str(out)])
        return scene["duration"], scene
    if kind == "card":
        run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-t", str(scene["duration"]),
             "-i", f"color=c=0x101418:s={W}x{H}:r={FPS}", *common, str(out)])
        return scene["duration"], scene
    raise ValueError(f"unknown scene type: {kind}")


def main(board_path, out_path):
    board = json.loads(Path(board_path).read_text())
    events = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts, t = [], 0.0
        for i, scene in enumerate(board["scenes"]):
            part = tmp / f"s{i:02d}.mp4"
            dur, scene = render_scene(scene, part, tmp)
            parts.append(part)
            if scene["type"] == "card":
                events.append(("Title", t, t + dur, scene.get("title", "")))
                if scene.get("text"):
                    events.append(("Body", t, t + dur, scene["text"]))
            cap = scene.get("caption", "")
            if scene["type"] == "compare":  # a label above each side
                for x, side in ((W // 4, scene["left"]), (3 * W // 4, scene["right"])):
                    events.append(("Label", t, t + dur, "{\\an8\\pos(%d,%d)}" % (x, 40) + side["label"]))
            speed = scene.get("speed", 1.0) if scene["type"] in ("clip", "compare") else 1.0
            if speed != 1.0:  # the assignment requires playback speed to be stated on sped-up footage
                label = f"{speed:g}倍速"
                cap = cap.replace("(2倍速)", "").strip()
                cap = f"{cap}({label})" if cap else f"({label})"
            if cap:
                events.append(("Caption", t, t + dur, cap))
            print(f"{i:02d} {scene['type']:5} {t:6.1f}-{t + dur:6.1f}s  {(scene.get('title') or scene.get('caption') or '')[:40]}")
            t += dur
        (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
        joined = tmp / "joined.mp4"
        run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
             "-i", str(tmp / "list.txt"), "-c", "copy", str(joined)])

        ass = tmp / "subs.ass"
        lines = [
            "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Alignment, MarginL, MarginR, MarginV, BorderStyle, Outline, Shadow",
            f"Style: Title,{FONT},54,&H00FFFFFF,&H00000000,&H00000000,1,5,60,60,0,1,0,0",
            f"Style: Body,{FONT},40,&H00D8DEE4,&H00000000,&H00000000,0,8,90,90,330,1,0,0",
            f"Style: Label,{FONT},40,&H00FFFFFF,&H00000000,&H00000000,1,8,0,0,0,1,0,0",
            f"Style: Caption,{FONT},34,&H00FFFFFF,&H00000000,&H90000000,1,2,60,60,36,3,8,0",
            "", "[Events]", "Format: Layer, Start, End, Style, Text",
        ]
        for style, a, b, text in events:
            if style == "Title":  # title sits a bit above the centre when there is body text
                text = "{\\an5\\pos(%d,%d)}" % (W // 2, 230) + ass_text(text)
            elif style == "Body" and "\n" in text:  # several lines (lists): left-aligned block
                text = "{\\an7\\pos(%d,%d)}" % (170, 330) + ass_text(text)
            lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},{style},{ass_text(text)}")
        ass.write_text("\n".join(lines) + "\n", encoding="utf-8")
        run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(joined),
             "-vf", f"ass={ass}", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
             str(out_path)])
    print(f"\n{out_path}  total {t:.1f} s ({t / 60:.1f} min)")


if __name__ == "__main__":
    board = sys.argv[1] if len(sys.argv) > 1 else HERE / "storyboard.json"
    out = sys.argv[2] if len(sys.argv) > 2 else HERE / "draft.mp4"
    main(board, out)
