"""fig_noise_time.py — 잡음이 기록마다·시간대마다 달랐다는 근거를 시각축으로 (2026-11-23, 그림4·포스터 그림5).
2분 단위 값: report/stim/newplant_stats.json. 시작 시각: 정상_6 11-05 22:42:12, 수분부족 11-09 17:44(13:14 식물 옮기기 전까지만).
가로축은 그날 18시부터의 시각(두 기록을 같은 시각에 겹쳐 그림).
쓰는 법: python3 report/stim/fig_noise_time.py
"""
import os, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
H = os.path.dirname(__file__)
d = json.load(open(os.path.join(H, "newplant_stats.json"), encoding="utf-8"))
runs = [("정상 (11-05 밤 ~ 11-06 새벽)", "정상_6", 22 + 42.2 / 60, 99, "#1f77b4"),
        ("물 공급 중단 (11-09 저녁 ~ 11-10 낮)", "수분부족", 17 + 44 / 60, 19.5, "#c0504d")]
fig, axs = plt.subplots(2, 1, figsize=(7.2, 4.8), dpi=300, sharex=True)
for ax, key, title, thr in ((axs[0], "rms", "(가) 0.01–1 Hz 잡음 (2분마다)", 0.1),
                            (axs[1], "a60", "(나) 60 Hz 상용전원 성분 (2분마다)", 0.003)):
    for name, n, t0, tmax, col in runs:
        r = d[n]["rows"]; t = np.array([x["t"] for x in r]) / 3600; v = np.array([x[key] for x in r])
        k = t < tmax
        ax.plot(t0 + t[k] - 18, v[k], color=col, lw=0.9, marker=".", ms=2, label=name)
    ax.axhline(thr, color="#888888", ls="--", lw=0.8)
    ax.text(0.1, thr * 1.25, f"분석 기준 {thr} mV", fontsize=7.5, color="#666666")
    ax.set_yscale("log"); ax.set_ylabel("mV"); ax.grid(lw=0.3, color="#e3e3e3")
    ax.set_title(title, loc="left", fontsize=9.5)
axs[0].set_ylim(0.01, 10); axs[1].set_ylim(0.0005, 0.2)
axs[1].legend(*axs[0].get_legend_handles_labels(), loc="upper left", fontsize=8, frameon=False)
# 같은 물 공급 중단 기록 안에서 바뀐 시각
for ax in axs:
    ax.axvline(8 + 18 / 60 + 6, color="#999999", lw=0.8, ls=":")
axs[0].text(8 + 18 / 60 + 6 + 0.15, 0.045, "11-10 08:18부터\n잡음 커짐", fontsize=7.5, color="#c0504d", va="center")
axs[0].text(4.0, 0.0145, "밤 14.5시간: 짧게 튄 곳 말고는 약 0.03 mV", fontsize=7.5, color="#c0504d")
ticks = list(range(0, 21, 2))
axs[1].set_xticks(ticks); axs[1].set_xticklabels([f"{(18 + h) % 24:02d}:00" for h in ticks])
axs[1].set_xlim(-0.2, 19.6); axs[1].set_xlabel("시각")
fig.tight_layout(h_pad=1.2)
out = os.path.join(H, "..", "보고서_그림_순서대로", "09_그림4_날짜별_잡음_수준.jpg")
fig.savefig(out, bbox_inches="tight", pad_inches=0.03, facecolor="white", pil_kwargs={"quality": 95}); print(out)
