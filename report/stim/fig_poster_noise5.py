"""fig_poster_noise5.py — 포스터 그림5: 긴 기록 다섯 개 잡음(처음 5.9시간), 크게 튄 2분 구간을 뺀 비교(2026-11-23 사용자 지시).
튄 구간 = 그 기록 0.01–1 Hz 잡음 중앙값의 3배를 넘는 2분 구간(그 구간은 두 그래프 모두에서 뺌). 자료는 noise5.json(fig_noise5.py).
가로로 두 칸(가: 0.01–1 Hz, 나: 60 Hz), 범례는 아래 — 포스터 칸 폭을 다 채우도록.
쓰는 법: python3 report/stim/fig_poster_noise5.py"""
import os, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 10})
H = os.path.dirname(__file__)
out = json.load(open(os.path.join(H, "noise5.json"), encoding="utf-8"))
COL = ["#9a9a9a", "#1f77b4", "#c0504d", "#2ca02c", "#e08a4b"]
fig, axs = plt.subplots(1, 2, figsize=(11, 4.0), dpi=300)
summ = {}
for (name, r), col in zip(out.items(), COL):
    name = name.replace("물 공급 중단", "수분부족")   # 포스터는 "수분부족"(사용자 11-23)
    t = np.array([x["t"] for x in r]) / 3600; a = np.array([x["rms"] for x in r]); b = np.array([x["a60"] for x in r])
    keep = a <= 3 * np.median(a)
    summ[name] = dict(drop=int((~keep).sum()), n=len(a), rms=float(np.median(a[keep])), a60=float(np.median(b[keep])),
                      below=float((a[keep] < 0.1).mean() * 100))
    for ax, y in ((axs[0], a), (axs[1], b)):
        yy = y.astype(float).copy(); yy[~keep] = np.nan
        ax.plot(t, yy, color=col, lw=1.0, label=f"{name} (중앙값 {summ[name]['rms']:.3g} mV)" if ax is axs[0] else None)
for ax, title, thr in ((axs[0], "(가) 0.01–1 Hz 잡음 (2분마다)", 0.1), (axs[1], "(나) 60 Hz 상용전원 성분 (2분마다)", 0.003)):
    ax.axhline(thr, color="#888888", ls="--", lw=0.8)
    ax.text(5.85, thr * 1.15, f"분석 기준 {thr} mV", fontsize=8.5, color="#666666", ha="right", va="bottom")
    ax.set_yscale("log"); ax.set_ylabel("mV"); ax.grid(lw=0.3, color="#e3e3e3"); ax.set_xlim(0, 5.9)
    ax.set_xlabel("기록 시작 뒤 시간 (시간)"); ax.set_title(title, loc="left", fontsize=11)
fig.tight_layout(rect=(0, 0.13, 1, 1), w_pad=2)
fig.legend(*axs[0].get_legend_handles_labels(), loc="lower center", ncol=3, fontsize=9, frameon=False)
o = os.path.join(H, "..", "poster_fig", "P_긴기록_잡음.jpg")
fig.savefig(o, bbox_inches="tight", pad_inches=0.03, facecolor="white", pil_kwargs={"quality": 95}); print(o)
json.dump(summ, open(os.path.join(H, "noise5_nospike.json"), "w"), ensure_ascii=False, indent=1)
for k, v in summ.items(): print(k, v)
