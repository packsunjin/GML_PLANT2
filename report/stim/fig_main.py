"""본 실험 그림(그림4): 패러데이 상자 안 기준선 — 차폐·수분부족·화상.
(가) 상자 전 20시간 중 처음 12시간 vs 상자 안(망 GND) 물 준 뒤 12시간 — 1분 평균
(나) 물 끊은 지 약 2일째 14시간(10-30~31) — 1분 평균
(다) 5일째(11-02): 물 주기 전 30분 | 물 준 뒤 1시간 | 화상 45분(지진 시각 표시) — 10초 평균
쓰는 법(저장소 루트): python3 report/stim/fig_main.py report/FIG_MAIN.png
그림 글자에 '−'(U+2212)를 쓰지 않는다(글꼴에 없음)."""
import sys, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FAR = os.path.join(ROOT, "data", "faraday")
for f in fm.findSystemFonts():
    if "NotoSansCJK" in f or "NotoSansKR" in f:
        fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False


def avg(name, sec):
    d = pd.read_csv(os.path.join(FAR, name), usecols=["timestamp_sec", "voltage"])
    t = d.timestamp_sec.to_numpy(); v = d.voltage.to_numpy() * 1000
    k = np.floor(t / sec).astype(int)
    n = np.bincount(k); s = np.bincount(k, weights=v)
    ok = n > 0
    return (np.arange(len(n))[ok] + 0.5) * sec, s[ok] / n[ok]


fig, ax = plt.subplots(3, 1, figsize=(7.2, 7.6))
# (가)
t1, v1 = avg("상자전_정상_20261021.csv.gz", 60); m = t1 <= 12 * 3600
t2, v2 = avg("상자후GND_정상_20261028.csv.gz", 60)
ax[0].plot(t1[m] / 3600, v1[m], color="#c0504d", lw=0.9, label="상자 전(10월 21~22일)")
ax[0].plot(t2 / 3600, v2, color="#1f6fb4", lw=1.3, label="상자 안, 망 GND 연결(10월 28~29일, 물 준 뒤)")
ax[0].set_xlim(0, 12); ax[0].set_ylabel("전압 차(mV)"); ax[0].set_xlabel("기록 시간(시간)")
ax[0].set_title("(가) 차폐 전후 — 1분 평균", loc="left", fontsize=10)
ax[0].legend(loc="lower right", fontsize=7.5)
# (나)
t3, v3 = avg("상자후GND_수분부족_20261030.csv.gz", 60)
ax[1].plot(t3 / 3600, v3, color="#7a4fa0", lw=0.9)
ax[1].axhline(np.median(v2), color="#1f6fb4", lw=0.8, ls="--", label="물 준 뒤 12시간의 중앙값(약 -8.9 mV)")
ax[1].set_xlim(0, 14); ax[1].set_ylabel("전압 차(mV)"); ax[1].set_xlabel("기록 시간(시간)")
ax[1].set_title("(나) 물을 끊은 지 약 2일째, 상자 안 14시간 — 1분 평균", loc="left", fontsize=10)
ax[1].legend(loc="upper left", fontsize=7.5)
# (다)
segs = [("상자후GND_수분부족_물주기전30분_20261102.csv.gz", "물 주기 전 30분", "#7a4fa0"),
        ("상자후GND_물준뒤1시간_20261102.csv.gz", "물 준 뒤 1시간", "#2e8b57"),
        ("상자후GND_화상_20261102.csv.gz", "화상 45분", "#d07a1f")]
x0 = 0.0
for i, (f, lab, c) in enumerate(segs):
    t, v = avg(f, 10)
    ax[2].plot((x0 + t) / 60, v, color=c, lw=1.0, label=lab)
    if f.startswith("상자후GND_화상"):
        ax[2].axvline((x0 + 571.5) / 60, color="k", lw=0.9, ls="--")
        ax[2].text((x0 + 571.5) / 60 + 1, ax[2].get_ylim()[1] if False else 60, "갈래 끝을 지짐", fontsize=8)
    x0 += t[-1] + 5 * 60   # 기록 사이 빈 시간은 5분으로 줄여 그림
    if i < 2:
        ax[2].axvline(x0 / 60 - 2.5, color="0.6", lw=0.6, ls=":")
ax[2].set_ylabel("전압 차(mV)"); ax[2].set_xlabel("이어 붙인 기록 시간(분, 기록 사이 빈 시간은 줄임)")
ax[2].set_title("(다) 물을 끊은 지 5일째(11월 2일) — 10초 평균", loc="left", fontsize=10)
ax[2].legend(loc="lower left", fontsize=7.5, ncol=3)
fig.tight_layout()
fig.savefig(sys.argv[1], dpi=400)
print("ok")
