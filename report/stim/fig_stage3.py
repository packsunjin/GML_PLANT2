"""fig_stage3.py — 그림3 새 판: (가) 1단계 회로 영점 (나) 2단계 점퍼선 핀 수돗물 60분 (다) 은선 수돗물 60분 (2026-11-17).
(가)(나)는 report/figs.py fig_stage 와 같은 자료·계산, (다)는 data/faraday/은선표류_20261103.csv.gz(1분 평균).
(나)(다)는 시작값 기준 같은 세로 폭으로 그려 표류 크기를 바로 비교하게 했다.
쓰는 법(저장소 루트): python3 report/stim/fig_stage3.py → report/FIG_STAGE3.png
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import figs
plt = figs.plt

s1 = figs.minute_means(figs.load_bench("dc_shorted_30min_v2.csv"))
v2 = figs.load_bench("stage2_repeat_1012.csv"); s2 = figs.minute_means(v2)
v3 = pd.read_csv(os.path.join(figs.ROOT, "data", "faraday", "은선표류_20261103.csv.gz")).iloc[:, 1].to_numpy() * 1000.0
s3 = figs.minute_means(v3)
fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.2, 2.4), gridspec_kw={"width_ratios": [1, 1.25, 1.25]})
a.plot(np.arange(len(s1)) + 0.5, s1, color=figs.BLUE, lw=1.1)
a.set_title("(가) 1단계: 회로만, 30분", loc="left")
a.set_ylabel("전압 (mV, 1분 평균)")
a.ticklabel_format(axis="y", useOffset=False)
d2, d3 = s2 - s2[0], s3 - s3[0]
n30 = int(figs.FS * 30)
dr2 = v2[-n30:].mean() - v2[:n30].mean(); dr3 = v3[-n30:].mean() - v3[:n30].mean()   # 보고서 표류 정의(마지막 30초 - 처음 30초)
for ax, d, col, title, note in ((b, d2, figs.GREEN, "(나) 2단계: 점퍼선 핀, 수돗물 60분", f"60분 표류 {dr2:+.2f} mV"),
                                (c, d3, figs.RED, "(다) 은선, 수돗물 60분", f"60분 표류 {dr3:+.2f} mV")):
    ax.plot(np.arange(len(d)) + 0.5, d, color=col, lw=1.2)
    ax.axhspan(-5, 5, color="#999999", alpha=0.10, lw=0)
    ax.set_ylim(-65, 10)
    ax.set_title(title, loc="left")
    ax.text(0.97, 0.72, note, transform=ax.transAxes, ha="right", va="top", fontsize=7, color=col)
b.set_ylabel("시작값에서 변한 양 (mV)")
c.text(1, -9.5, "회색: 시작값 ±5 mV", fontsize=6.3, color=figs.GRAY)
for x in (a, b, c):
    x.set_xlabel("시간 (분)"); x.grid(lw=0.3, color="#e3e3e3")
fig.tight_layout(w_pad=1.6)
figs.save(fig, "FIG_STAGE3.png")
print("saved report/FIG_STAGE3.png", round(dr2, 2), round(dr3, 3))
