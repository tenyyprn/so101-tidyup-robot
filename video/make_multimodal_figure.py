"""Draw video/assets/multimodal.png: why ACT grasps "between" two sponges and Diffusion Policy does not.

The demonstrations hold two answers for the same scene (take the left sponge / take the right one).
ACT (a CVAE whose latent is fixed at inference) gives one action per scene and was observed to land
between them; Diffusion Policy samples one of the two peaks.

Usage: .venv/bin/python video/make_multimodal_figure.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
BG, FG, MUTED = "#101418", "#FFFFFF", "#9AA4AE"
DEMO, ACT, DP = "#7FA7D9", "#E5534B", "#3FB950"
plt.rcParams["font.family"] = "Noto Sans CJK JP"

x = np.linspace(-3, 3, 400)
demo = np.exp(-((x + 1.5) ** 2) / 0.18) + np.exp(-((x - 1.5) ** 2) / 0.18)

fig, axes = plt.subplots(1, 2, figsize=(12.8, 7.2), dpi=100, facecolor=BG)
fig.subplots_adjust(left=0.05, right=0.95, top=0.74, bottom=0.17, wspace=0.12)
fig.text(0.5, 0.91, "お手本には「左を取る」と「右を取る」、2つの答えがある(多峰性)",
         ha="center", va="center", color=FG, fontsize=26, weight="bold")

panels = [
    (axes[0], "ACT:2つの答えの中間に寄る", ACT, 0.0, "×", "間(何もない場所)をつかむ"),
    (axes[1], "Diffusion Policy:どちらか1つを選ぶ", DP, -1.5, "○", "スポンジをつかむ"),
]
for ax, title, color, out_x, mark, result in panels:
    ax.set_facecolor(BG)
    ax.fill_between(x, demo, color=DEMO, alpha=0.35, lw=0)
    ax.plot(x, demo, color=DEMO, lw=2)
    ax.text(-1.5, 1.1, "左のスポンジ", ha="center", color=MUTED, fontsize=17)
    ax.text(1.5, 1.1, "右のスポンジ", ha="center", color=MUTED, fontsize=17)
    ax.plot([out_x, out_x], [0, 1.02], color=color, lw=4)
    ax.text(out_x, -0.17, mark, ha="center", va="center", color=color, fontsize=34, weight="bold")
    ax.text(0, -0.42, result, ha="center", va="center", color=color, fontsize=21, weight="bold")
    ax.set_title(title, color=FG, fontsize=24, pad=18, weight="bold")
    ax.set_xlim(-3, 3)
    ax.set_ylim(-0.55, 1.3)
    ax.axis("off")
    ax.plot([-3, 3], [0, 0], color=MUTED, lw=1)

out = HERE / "assets/multimodal.png"
fig.savefig(out, facecolor=BG)
print(out)
