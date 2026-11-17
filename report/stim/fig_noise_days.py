"""fig_noise_days.py — 날짜·시간대마다 다른 잡음 수준(물 상태 구분을 못 한 근거) (2026-11-17).
2분 단위 값: report/stim/newplant_stats.json(정상_6, 수분부족). 시간대 나누기: 수분부족 0~14.45시간 = 11-09 17:44~11-10 08:18(밤),
14.45~19.5시간 = 11-10 08:18~13:14(아침~낮, 식물 옮기기 전). 120초 시험 값: report/stim/faraday_compare120_20261104.txt, 11-05 재세팅 120초.
쓰는 법: python3 report/stim/fig_noise_days.py → report/FIG_NOISE_DAYS.png
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
H = os.path.dirname(__file__)
d = json.load(open(os.path.join(H, "newplant_stats.json"), encoding="utf-8"))
def get(n, k, t0, t1):
    r = d[n]["rows"]; t = np.array([x["t"] for x in r]) / 3600; v = np.array([x[k] for x in r])
    return v[(t >= t0) & (t < t1)]
groups = [("11-05 밤\n정상 기록", "정상_6", 0, 99, "#1f6fb4"),
          ("11-09 밤\n물 공급 중단", "수분부족", 0, 14.45, "#c0504d"),
          ("11-10 아침~낮\n물 공급 중단", "수분부족", 14.45, 19.5, "#e08a4b")]
tests = [("11-04\n상자 밖\n콘센트", 0.501, 0.080), ("11-04\n상자 안\n콘센트", 0.061, 0.003),
         ("11-04\n상자 안\n배터리", 0.083, 0.002), ("11-05\n재세팅\n배터리", 0.022, 0.001)]
fig, axs = plt.subplots(1, 2, figsize=(10, 3.9), dpi=300)
for ax, key, title, thr in ((axs[0], "rms", "(가) 0.01–1 Hz 잡음 (2분마다)", 0.1), (axs[1], "a60", "(나) 60 Hz 상용전원 성분 (2분마다)", 0.003)):
    data = [get(n, key, a, b) for _, n, a, b, _ in groups]
    bp = ax.boxplot(data, positions=range(len(groups)), widths=0.55, patch_artist=True, showfliers=True,
                    flierprops=dict(marker=".", ms=2, alpha=0.4), medianprops=dict(color="black", lw=1.2))
    for patch, g in zip(bp["boxes"], groups):
        patch.set_facecolor(g[4]); patch.set_alpha(0.55)
    for i, v in enumerate(data):
        ax.text(i + 0.33, np.median(v), f"{np.median(v):.3g}", ha="left", va="center", fontsize=7.5, fontweight="bold")
    x0 = len(groups) + 0.3
    for j, (lab, rms, a60) in enumerate(tests):
        val = rms if key == "rms" else a60
        ax.plot(x0 + j * 1.0, val, "D", ms=5.5, color="#555555")
        ax.text(x0 + j * 1.0, val * 1.6, f"{val:g}", ha="center", fontsize=7, color="#555555")
    ax.axhline(thr, color="#888888", ls="--", lw=0.8)
    ax.text(-0.45, thr * 1.12, f"분석 기준 {thr} mV", ha="left", fontsize=7, color="#666666")
    m = [np.median(v) for v in data]
    ax.annotate("", (0.75, m[1]), (0.75, m[0]), arrowprops=dict(arrowstyle="<->", lw=0.9, color="#333333"))
    ax.text(0.68, (m[0] * m[1]) ** 0.5, f"약 {m[0] / m[1]:.0f}배", ha="right", va="center", fontsize=8, color="#333333")
    ax.set_yscale("log"); ax.set_ylabel("mV")
    ax.set_xticks(list(range(len(groups))) + [x0 + j * 1.0 for j in range(len(tests))])
    ax.set_xticklabels([g[0] for g in groups] + [t[0] for t in tests], fontsize=6.6)
    ax.axvline(len(groups) - 0.35, color="#cccccc", lw=0.8)
    ax.text(1, ax.get_ylim()[1] * 0.6 if key == "rms" else 0.15, "긴 기록", ha="center", fontsize=7.5, color="#444444")
    ax.text(x0 + 1.5, ax.get_ylim()[1] * 0.6 if key == "rms" else 0.15, "120초 시험", ha="center", fontsize=7.5, color="#444444")
    ax.set_title(title, loc="left", fontsize=9.5)
    ax.grid(axis="y", lw=0.3, color="#e3e3e3")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axs[0].set_ylim(0.008, 80); axs[1].set_ylim(0.0005, 0.4)
fig.tight_layout(w_pad=2)
out = os.path.join(H, "..", "FIG_NOISE_DAYS.png")
fig.savefig(out, facecolor="white", bbox_inches="tight", pad_inches=0.04); print(out)
