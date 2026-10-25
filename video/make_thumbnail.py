"""Draw video/thumbnail.png (1280x720) for YouTube, top camera only.
Left: ACT-112 on the 2-5-9 layout after putting one sponge in the box, closing the gripper between the two that are
left (rollout_act259, 3rd run, 22.6 s). Right: Diffusion Policy with every sponge in the box (3-4-8 layout).

Usage: .venv/bin/python video/make_thumbnail.py
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
DATA = Path.home() / ".cache/huggingface/lerobot/tenyyprn"
W, H = 1280, 720
BG, FG, MUTED, RED, GREEN = "#101418", "#FFFFFF", "#9AA4AE", "#E5534B", "#3FB950"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
CROP_LEFT = 125  # same left crop as the movie

SHOTS = [  # (dataset, second in the stored video, badge, colour, sponge centres to ring in source pixels)
    ("rollout_act259_20261025_230214", 89.367 + 22.6, "ACT:2個の「間」をつかむ", RED, [(120, 140), (195, 368)]),
    ("rollout_dp_rand348_20261025_072845", 33.5, "Diffusion Policy:全部片付け", GREEN, []),
]


def frame(name, t, out):
    video = DATA / name / "videos/observation.images.top/chunk-000/file-000.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", str(t), "-i", str(video), "-frames:v", "1",
                    "-vf", f"crop=iw-{CROP_LEFT}:ih:{CROP_LEFT}:0", str(out)], check=True)
    return Image.open(out).convert("RGB")


def font(size):
    return ImageFont.truetype(BOLD, size)


img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)
draw.text((W // 2, 62), "同じデータで、モデルを変えただけ", font=font(64), fill=FG, anchor="mm")

panel_w, panel_h, top = 600, 480, 125
with tempfile.TemporaryDirectory() as tmp:
    for i, (name, t, badge, color, rings) in enumerate(SHOTS):
        shot = frame(name, t, Path(tmp) / f"{i}.png")
        k = panel_w / shot.width
        shot = shot.resize((panel_w, round(shot.height * k)))
        ring = ImageDraw.Draw(shot)
        for cx, cy in rings:
            ring.ellipse((cx * k - 58, cy * k - 52, cx * k + 58, cy * k + 52), outline="#FFD33D", width=7)
        shot = shot.crop((0, 0, panel_w, panel_h))
        x = 26 + i * (panel_w + 28)
        img.paste(shot, (x, top))
        draw.rectangle((x, top, x + panel_w - 1, top + panel_h - 1), outline=color, width=8)
        f = font(40)
        tw = draw.textlength(badge, font=f)
        # badge at the top: the remaining sponges sit low in the left frame
        draw.rounded_rectangle((x + 16, top + 18, x + 16 + tw + 36, top + 78), radius=12, fill=color)
        draw.text((x + 34, top + 48), badge, font=f, fill=FG, anchor="lm")

draw.text((W // 2, 664), "「間」をつかむ失敗 75% → 0%  ・  SO101 × 模倣学習", font=font(40), fill=FG, anchor="mm")
out = HERE / "thumbnail.png"
img.save(out)
print(out)
