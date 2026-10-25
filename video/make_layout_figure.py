"""Draw video/assets/layout.png: top view of the 3x3 cells (1-9), the box, the robot and the cameras.

Positions are approximate, read off the top-camera footage: the box sits just right of cell 6,
the follower's base right of the box, and the C920 looks down from above the near-left corner.

Usage: .venv/bin/python video/make_layout_figure.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

HERE = Path(__file__).resolve().parent
BG, FG, MUTED = "#FFFFFF", "#1F2328", "#6E7781"
TAPE, TABLE, BOX, ROBOT, CAM = "#E3B341", "#F6EBD9", "#FFFFFF", "#D0D7DE", "#0969DA"
plt.rcParams["font.family"] = "Noto Sans CJK JP"
NUM = "①②③④⑤⑥⑦⑧⑨"

fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
ax.set_xlim(-2.6, 7.6)
ax.set_ylim(-1.9, 4.6)
ax.set_aspect("equal")
ax.axis("off")

ax.add_patch(Rectangle((-0.6, -0.6), 7.3, 4.2, facecolor=TABLE, edgecolor="none", zorder=0))
for i in range(9):  # row 0 = near (1-3), column 0 = left
    r, c = divmod(i, 3)
    ax.add_patch(Rectangle((c, r), 1, 1, facecolor="none", edgecolor=TAPE, lw=4, zorder=1))
    ax.text(c + 0.5, r + 0.5, NUM[i], ha="center", va="center", fontsize=34, color=FG, zorder=2)

ax.add_patch(Rectangle((3.4, 1.05), 0.9, 0.9, facecolor=BOX, edgecolor=MUTED, lw=2.5, zorder=2))
ax.text(3.85, 1.5, "箱", ha="center", va="center", fontsize=22, color=FG, zorder=3)
ax.add_patch(Rectangle((5.0, 0.9), 1.3, 1.2, facecolor=ROBOT, edgecolor=MUTED, lw=2.5, zorder=2))
ax.text(5.65, 1.5, "ロボット\nの土台", ha="center", va="center", fontsize=17, color=FG, zorder=3)
ax.text(5.65, 0.55, "フォロワー(SO101)", ha="center", va="top", fontsize=15, color=MUTED)
ax.add_patch(FancyArrowPatch((5.0, 1.85), (2.85, 3.2), connectionstyle="arc3,rad=0.25", arrowstyle="-|>",
                             mutation_scale=22, lw=2, color=MUTED, zorder=3))
ax.add_patch(Rectangle((2.55, 3.1), 0.3, 0.3, facecolor=CAM, edgecolor="none", zorder=4))
ax.text(3.15, 3.55, "手首カメラ:アームの手先に付き、\nつかむ直前を大きく映す", ha="left", va="center",
        fontsize=15, color=CAM)

# top camera above the near-left corner, looking diagonally across the cells toward the robot
ax.add_patch(Polygon([(-1.9, -1.2), (-0.2, 3.4), (4.6, 0.1)], closed=True, facecolor=CAM, alpha=0.08,
                     edgecolor="none", zorder=0))
ax.add_patch(Rectangle((-2.3, -1.55), 0.8, 0.55, facecolor=CAM, edgecolor="none", zorder=3))
ax.text(-1.35, -1.28, "上のカメラ(C920):手前・左の斜め上から全体を見下ろす", ha="left", va="center",
        fontsize=15, color=CAM)

ax.text(1.5, 3.3, "奥", ha="center", va="bottom", fontsize=18, color=MUTED)
ax.text(1.5, -0.3, "手前", ha="center", va="top", fontsize=18, color=MUTED)
ax.text(-0.25, 1.5, "左", ha="right", va="center", fontsize=18, color=MUTED)
ax.text(6.55, 1.5, "右", ha="left", va="center", fontsize=18, color=MUTED)
ax.text(2.5, 4.2, "上から見た配置(おおよそ)", ha="center", va="center", fontsize=24, color=FG, weight="bold")

out = HERE / "assets/layout.png"
fig.savefig(out, facecolor=BG, bbox_inches="tight", pad_inches=0.15)
# the video burns a caption into the bottom edge, so its copy gets a wider margin
fig.savefig(HERE / "assets/layout_video.png", facecolor=BG, bbox_inches="tight", pad_inches=0.9)
print(out)
