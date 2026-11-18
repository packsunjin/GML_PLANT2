"""11-17 손 접촉: 보조배터리 vs 콘센트 전원. 잡은 시각 뒤 10초 최대 상승(앞 10초 중앙값 기준, 0.1초 평균).
숫자는 파이에서 계산한 표(자극.csv, 자극_3.csv) 그대로."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
from matplotlib import font_manager as fm
import os
for f in os.listdir("/usr/share/fonts/opentype/noto/"):
    if "CJK" in f: fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
bat_t = [5.05, 2.18, 2.92, 3.30, 2.33, 2.98, 2.73, 2.59, 3.31, 3.34]
bat_c = [2.42, 2.19, 4.09, 4.15, 3.82, 2.15, 5.74, 3.87, 6.44, 3.39]
ac_t = [138.38, 141.98, 144.74, 149.08, 149.16, 144.17, 146.89, 155.43, 147.33]
ac_c = [4.48, 7.34, 6.52, 4.71, 4.34, 4.56, 7.03, 7.51, 5.12]
BLUE, GRAY, INK = "#1f77b4", "#9a9a9a", "#222222"
fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=300)
groups = [("보조배터리\n잎 만짐", bat_t, BLUE), ("보조배터리\n안 만짐", bat_c, GRAY),
          ("콘센트\n잎 만짐", ac_t, BLUE), ("콘센트\n안 만짐", ac_c, GRAY)]
rng = np.random.default_rng(0)
for i, (lab, v, c) in enumerate(groups):
    x = i + rng.uniform(-0.12, 0.12, len(v))
    ax.scatter(x, v, s=22, color=c, edgecolor="white", linewidth=0.5, zorder=3)
    m = np.median(v)
    ax.plot([i - 0.25, i + 0.25], [m, m], color=INK, lw=1.4, zorder=4)
    ax.text(i + 0.3, m, f"{m:.0f} mV" if m > 20 else f"{m:.1f} mV", va="center", fontsize=8, color=INK)
ax.set_xticks(range(4)); ax.set_xticklabels([g[0] for g in groups])
ax.set_ylabel("만진 뒤 10초 최대 상승 (mV)")
ax.set_ylim(0, 170); ax.set_xlim(-0.6, 3.9)
ax.grid(axis="y", color="#e5e5e5", lw=0.6); ax.set_axisbelow(True)
ax.axvline(1.5, color="#cccccc", lw=0.8)
ax.text(0.5, 160, f"만짐 {len(bat_t)}번 · 안 만짐 {len(bat_c)}곳", ha="center", fontsize=8, color=GRAY)
ax.text(2.5, 160, f"만짐 {len(ac_t)}번 · 안 만짐 {len(ac_c)}곳", ha="center", fontsize=8, color=GRAY)
fig.tight_layout()
out = "report/보고서_그림_순서대로/12_그림7_전원별_손접촉.jpg"
fig.savefig(out, bbox_inches="tight", pad_inches=0.03, facecolor="white", pil_kwargs={"quality": 95})
print(out)
