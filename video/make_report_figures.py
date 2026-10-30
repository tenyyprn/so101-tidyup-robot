"""Draw two photo figures for the report from top-camera demo clips (no wrist camera):
  video/assets/compare_348.png  ACT-112 vs Diffusion Policy on the same 3-4-8 layout, four moments each
  video/assets/pick9.png        Diffusion Policy clearing 9 sponges (trained on 3-sponge demos only)

Times under the photos are real seconds: Diffusion Policy recordings run at ~0.77x real time
(see make_video.py), so their clip times are scaled by real_s / clip length as in storyboard.json.

Usage: .venv/bin/python video/make_report_figures.py
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent / "demo"
BG, FG, RED, BLUE, GRAY = "#101418", "#FFFFFF", "#E5534B", "#4C9AFF", "#9AA4AE"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def frame(clip, t, crop, width):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "f.png"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", str(t), "-i", str(clip),
                        "-frames:v", "1", "-vf", crop, str(out)], check=True)
        shot = Image.open(out).convert("RGB")
    return shot.resize((width, round(shot.height * width / shot.width)))


def strip(img, draw, clip, shots, crop, top, scale, color, font, pw=300, gap=12, left=150):
    """Paste one row of frames; shots = [(clip_s, caption)], label = real seconds + caption."""
    for i, (t, text) in enumerate(shots):
        shot = frame(clip, t, crop, pw)
        x = left + i * (pw + gap)
        img.paste(shot, (x, top))
        draw.text((x + pw // 2, top + shot.height + 22), f"{round(t * scale)} 秒:{text}", font=font,
                  fill=color, anchor="mm")
    return shot.height


def compare_348():
    W, H = 1400, 790
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    title, row, label = (ImageFont.truetype(BOLD, s) for s in (40, 30, 21))
    draw.text((W // 2, 44), "同じ並べ方(マス ③④⑧)で比べる", font=title, fill=FG, anchor="mm")
    crop = "crop=400:360:125:40"
    act = DEMO / "rollout_act348_20261025_082954_ep0.mp4"   # 35 s real / 34.6 s clip
    dp = DEMO / "rollout_dp_rand348_20261025_072845_ep0.mp4"  # 45 s real / 33 s clip
    h = strip(img, draw, act, [(0, "始める前"), (10, "1個目を箱へ"), (20, "つかみ損ねを繰り返す"),
                               (32.5, "1個残る")], crop, 95, 35 / 34.6, FG, label)
    draw.text((75, 95 + h // 2), "ACT", font=row, fill=RED, anchor="mm")
    top = 95 + h + 60
    strip(img, draw, dp, [(0, "始める前"), (12.5, "1個目を箱へ"), (22.5, "2個目を箱へ"),
                          (32.5, "3個とも片付いた")], crop, top, 45 / 33, FG, label)
    draw.text((75, top + h // 2), "Diffusion\nPolicy", font=row, fill=BLUE, anchor="mm", align="center")
    draw.text((W // 2, H - 30), "同じ 112 回分のお手本で学習、上のカメラ、時間は実時間", font=label, fill=GRAY,
              anchor="mm")
    img.save(HERE / "assets/compare_348.png")


def pick9():
    W, H = 1400, 470
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    title, label = ImageFont.truetype(BOLD, 40), ImageFont.truetype(BOLD, 21)
    draw.text((W // 2, 44), "3個のお手本だけで学習したモデルが、9個を片付ける", font=title, fill=FG, anchor="mm")
    clip = DEMO / "rollout_pick8to9_20261025_222934_ep1.mp4"  # ~0.77x real time
    strip(img, draw, clip, [(0, "9マスすべてに置く"), (32, "近い順に箱へ"), (72, "残りわずか"),
                            (112, "机の上が空になった")], "crop=480:400:70:20", 95, 1 / 0.77, FG, label,
          pw=300, gap=12, left=(W - 4 * 300 - 3 * 12) // 2)
    draw.text((W // 2, H - 26), "Diffusion Policy、上のカメラ、時間は実時間(およそ)。箱があふれた分は人が空にした", font=label,
              fill=GRAY, anchor="mm")
    img.save(HERE / "assets/pick9.png")


compare_348()
pick9()
