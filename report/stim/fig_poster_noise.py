"""fig_poster_noise.py — 포스터용: 차폐·전원별 120초 기록의 잡음(2026-11-04, 보고서 Ⅳ-4 숫자).
60 Hz 상용전원 성분: 상자 밖·콘센트 0.080, 상자 안·콘센트 0.003, 상자 안·보조배터리 0.001~0.002 mV
0.01–1 Hz 잡음: 0.50, 0.06, 0.02~0.08 mV
쓰는 법: python3 report/stim/fig_poster_noise.py → report/poster_fig/P_차폐전원_잡음.jpg"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
labs = ["상자 밖\n콘센트", "상자 안\n콘센트", "상자 안\n보조배터리"]
hz60 = [0.080, 0.003, 0.0015]; hz60_t = ["0.080", "0.003", "0.001~0.002"]
low = [0.50, 0.06, 0.05]; low_t = ["0.50", "0.06", "0.02~0.08"]
cols = ["#b9b2a8", "#c9925a", "#905720"]
fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.6), dpi=300)
for ax, v, t, title in ((axs[0], hz60, hz60_t, "60 Hz 상용전원 성분 (mV)"), (axs[1], low, low_t, "0.01–1 Hz 잡음 (mV)")):
    bars = ax.bar(range(3), v, color=cols, width=0.6)
    ax.set_yscale("log"); ax.set_xticks(range(3)); ax.set_xticklabels(labs, fontsize=8.4)
    for b, s in zip(bars, t):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() * 1.25, s, ha="center", fontsize=8.6, fontweight="bold")
    ax.set_title(title, fontsize=9.5, loc="left"); ax.set_ylim(min(v) / 2.5, max(v) * 4)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.grid(axis="y", lw=0.3, color="#e3e3e3"); ax.set_axisbelow(True)
axs[0].annotate("약 1/27", xy=(0.72, 0.0062), xytext=(0.45, 0.025), fontsize=9, color="#905720", fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="#905720", lw=1))
fig.tight_layout()
fig.savefig("report/poster_fig/P_차폐전원_잡음.jpg", facecolor="white", bbox_inches="tight", pad_inches=0.03, pil_kwargs={"quality": 95})
print("ok")
