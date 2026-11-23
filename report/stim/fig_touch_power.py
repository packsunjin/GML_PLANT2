"""fig_touch_power.py — 11-17 손 접촉, 전원별 비교(원본 CSV).
자료: main 의 data/faraday/자극_배터리_20261117.csv, 자극_콘센트_20261117.csv
만진 시각(파일 초): 배터리 129.75+30k(10번), 콘센트 189.28+30k(9번; 129.28 은 반응 없어 표시만)
(다) 예비 실험 10-16 비전도성 물체 살짝 댐: data/ds/stim/_extra/옛식물/자극_2.csv, 댄 시각 = 스톱워치 lap − 5초(몇 초 어긋날 수 있음)
쓰는 법: python3 report/stim/fig_touch_power.py <csv 폴더>
"""
import sys, os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
D = sys.argv[1] if len(sys.argv) > 1 else "data/faraday"
BLUE, RED, GRAY, INK = "#1f77b4", "#c0504d", "#9a9a9a", "#1d1d1d"

def load(n):
    d = pd.read_csv(n if os.path.exists(n) else os.path.join(D, n)); t = d.timestamp_sec.values; v = d.voltage.values * 1000
    b = np.floor(t / 0.1).astype(int); k = b.max() + 1
    m = np.bincount(b, v, k) / np.maximum(np.bincount(b, None, k), 1)
    return np.arange(k) * 0.1 + 0.05, m

runs = [("보조배터리 전원", "자극_배터리_20261117.csv", [129.75 + 30 * k for k in range(10)], BLUE),
        ("콘센트 전원", "자극_콘센트_20261117.csv", [189.28 + 30 * k for k in range(9)], RED),
        ("콘센트 전원, 비전도성 물체", "data/ds/stim/_extra/옛식물/자극_2.csv",
         [x - 5 for x in (124.78, 304.18, 483.93, 664.92, 844.12, 1024.69, 1205.09, 1384.77, 1565, 1745)], "#7a4a17")]
fig = plt.figure(figsize=(7.2, 6.9), dpi=300)
gs = fig.add_gridspec(3, 2, width_ratios=[2.3, 1], hspace=0.55, wspace=0.28)
for r, (name, fn, touches, col) in enumerate(runs):
    t, m = load(fn)
    base = np.median(m)
    a = fig.add_subplot(gs[r, 0])
    for x in touches:
        a.axvspan(x, x + 2, color="#f2c94c", alpha=0.55, lw=0 if r < 2 else 1.2)
    a.plot(t, m - base, color=col, lw=0.5)
    a.set_xlim(0, 1800 if r == 2 else 600); a.set_ylim(-80, 170)
    a.set_ylabel("전압 (mV)"); a.grid(lw=0.3, color="#e3e3e3")
    a.set_title(f"({'가나다'[r]}) {name}, " + ("예비 실험 1800초, 노란 띠 = 살짝 댄 2초" if r == 2 else "600초 기록, 노란 띠 = 잎을 잡으라고 신호한 2초"), loc="left", fontsize=9)
    if r == 2: a.set_xlabel("시간 (초)")
    b = fig.add_subplot(gs[r, 1])
    seg = []
    for x in touches:
        k = (t >= x - 5) & (t < x + 15)
        y = m[k] - np.median(m[(t >= x - 10) & (t < x - 1)])
        seg.append(y[:200]); b.plot(np.arange(len(y))[:200] * 0.1 - 5, y[:200], color=col, lw=0.5, alpha=0.45)
    b.plot(np.arange(200) * 0.1 - 5, np.median(np.array(seg), 0), color=INK, lw=1.2)
    b.axvspan(0, 2, color="#f2c94c", alpha=0.55, lw=0)
    b.set_xlim(-5, 15); b.set_ylim(-80, 170); b.grid(lw=0.3, color="#e3e3e3")
    b.set_title(f"{'댄' if r == 2 else '신호'} 시각 기준 겹쳐 보기 ({len(touches)}번)", loc="left", fontsize=9)
    if r == 2: b.set_xlabel("신호·댄 뒤 시간 (초)")
out = "report/보고서_그림_순서대로/10_그림5_전원별_손접촉.jpg"
fig.savefig(out, bbox_inches="tight", pad_inches=0.03, facecolor="white", pil_kwargs={"quality": 95})
print(out)

# 포스터용: 겹쳐 보기 세 칸만 가로로
fig = plt.figure(figsize=(7.2, 2.3), dpi=300)
for r, (name, fn, touches, col) in enumerate(runs):
    t, m = load(fn); b = fig.add_subplot(1, 3, r + 1); seg = []
    for x in touches:
        k = (t >= x - 5) & (t < x + 15)
        y = m[k] - np.median(m[(t >= x - 10) & (t < x - 1)])
        seg.append(y[:200]); b.plot(np.arange(len(y))[:200] * 0.1 - 5, y[:200], color=col, lw=0.5, alpha=0.45)
    b.plot(np.arange(200) * 0.1 - 5, np.median(np.array(seg), 0), color=INK, lw=1.2)
    b.axvspan(0, 2, color="#f2c94c", alpha=0.55, lw=0)
    b.set_xlim(-5, 15); b.set_ylim(-40, 170); b.grid(lw=0.3, color="#e3e3e3")
    b.set_title(["(가) 보조배터리, 잎을 잡음", "(나) 콘센트, 잎을 잡음", "(다) 콘센트, 비전도성 물체"][r] + f" {len(touches)}번", loc="left", fontsize=9)
    b.set_xlabel("잡은·댄 뒤 시간 (초)")
    if r == 0: b.set_ylabel("전압 (mV)")
fig.tight_layout(w_pad=1.0)
out = "report/poster_fig/P_전원별_겹쳐보기.jpg"
fig.savefig(out, bbox_inches="tight", pad_inches=0.03, facecolor="white", pil_kwargs={"quality": 95})
print(out)
