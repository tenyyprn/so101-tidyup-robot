"""Draw video/assets/between_grasp.png: three frames of ACT-112 on the 2-5-9 layout (rollout_act259, 2nd run)
showing the "between" grasp: the gripper comes down between two sponges, closes on nothing and lifts empty.

Usage: .venv/bin/python video/make_between_figure.py
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
CLIP = HERE.parent / "demo/rollout_act259_20261025_230214_ep1.mp4"  # top camera only (make_demo.sh)
W, H = 1280, 720
BG, FG, RED = "#101418", "#FFFFFF", "#E5534B"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
CROP = "crop=400:360:125:40"  # the cells and the box, without the left edge of the room
SHOTS = [(0.0, "① 始める前"), (3.4, "② 2個の「間」に下ろして閉じる"), (6.6, "③ 何も持たずに戻る")]

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)
title = ImageFont.truetype(BOLD, 44)
label = ImageFont.truetype(BOLD, 28)
draw.text((W // 2, 50), "ACT:2つのスポンジの「間」をつかむ", font=title, fill=FG, anchor="mm")

pw, gap, top = 404, 18, 110
with tempfile.TemporaryDirectory() as tmp:
    for i, (t, text) in enumerate(SHOTS):
        out = Path(tmp) / f"{i}.png"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", str(t), "-i", str(CLIP),
                        "-frames:v", "1", "-vf", CROP, str(out)], check=True)
        shot = Image.open(out).convert("RGB")
        shot = shot.resize((pw, round(shot.height * pw / shot.width)))
        x = (W - 3 * pw - 2 * gap) // 2 + i * (pw + gap)
        img.paste(shot, (x, top))
        draw.text((x + pw // 2, top + shot.height + 34), text, font=label, fill=RED if i == 1 else FG, anchor="mm")

note = ImageFont.truetype(BOLD, 26)
draw.text((W // 2, 610), "箱は空のまま、2個とも机に残る(マス ②⑤⑨、ACT-112、上のカメラ)", font=note, fill="#9AA4AE", anchor="mm")
out = HERE / "assets/between_grasp.png"
img.save(out)
print(out)
