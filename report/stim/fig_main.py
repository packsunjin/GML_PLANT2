"""본 실험 그림(그림4): 같은 식물, 패러데이 상자 안(망 GND) — 정상과 수분부족을 같은 축에서 비교.
(가) 물 준 뒤 12시간(정상, 10-28~29) 과 물 끊은 지 약 2일째 14시간(10-30~31) 을 겹쳐 그림 — 1분 평균
(나) 같은 10초 평균·같은 세로축으로 이어 붙임: 정상(10-28 처음 30분) | 물 끊은 지 5일째 30분 | 물 준 뒤 1시간 | 화상 45분
두 칸 모두 정상 기록의 중앙값(약 -8.9 mV)을 점선으로 그어 기준으로 삼는다.
(차폐 전후 비교는 본문 숫자로만 쓴다 — 2026-11-02 사용자 "그래프가 다 따로 있어서 뭘 말하는지 모르겠다")
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

C_OK, C_DRY, C_WET, C_BURN = "#1f6fb4", "#c0504d", "#2e8b57", "#d07a1f"


def avg(name, sec, tmax=None):
    d = pd.read_csv(os.path.join(FAR, name), usecols=["timestamp_sec", "voltage"])
    if tmax is not None:
        d = d[d.timestamp_sec < tmax]
    t = d.timestamp_sec.to_numpy(); v = d.voltage.to_numpy() * 1000
    k = np.floor(t / sec).astype(int)
    n = np.bincount(k); s = np.bincount(k, weights=v)
    ok = n > 0
    return (np.arange(len(n))[ok] + 0.5) * sec, s[ok] / n[ok]


OK = "상자후GND_정상_20261028.csv.gz"
fig, ax = plt.subplots(2, 1, figsize=(7.2, 6.4))

# (가)
t1, v1 = avg(OK, 60)
t2, v2 = avg("상자후GND_수분부족_20261030.csv.gz", 60)
base = float(np.median(v1))
ax[0].plot(t2 / 3600, v2, color=C_DRY, lw=1.0, label="물 끊은 지 약 2일째(10월 30~31일)")
ax[0].plot(t1 / 3600, v1, color=C_OK, lw=1.6, label="정상: 물 준 뒤(10월 28~29일)")
ax[0].set_xlim(0, 14); ax[0].set_ylabel("전압 차(mV)"); ax[0].set_xlabel("기록 시작 뒤 시간(시간)")
ax[0].set_title("(가) 정상은 12시간 내내 평평, 물을 끊자 수십 mV 출렁임 (1분 평균)", loc="left", fontsize=10)
ax[0].legend(loc="upper left", fontsize=8)

# (나)
segs = [(OK, "정상(10월 28일)", C_OK, 1800),
        ("상자후GND_수분부족_물주기전30분_20261102.csv.gz", "물 끊은 지 5일째", C_DRY, None),
        ("상자후GND_물준뒤1시간_20261102.csv.gz", "물 준 뒤", C_WET, None),
        ("상자후GND_화상_20261102.csv.gz", "화상", C_BURN, None)]
ax[1].axhline(base, color=C_OK, lw=0.8, ls="--")
x0 = 0.0; GAP = 4 * 60
for f, lab, c, tmax in segs:
    t, v = avg(f, 10, tmax)
    ax[1].plot((x0 + t) / 60, v, color=c, lw=1.1)
    ax[1].text((x0 + t[-1] / 2) / 60, 118, lab, color=c, ha="center", fontsize=8.5)
    if lab == "화상":
        ax[1].axvline((x0 + 571.5) / 60, color="k", lw=0.9, ls=":")
        ax[1].annotate("갈래 끝을 지짐", xy=((x0 + 571.5) / 60, -75), xytext=((x0 + 571.5) / 60 + 3, -90),
                       fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.7))
    x0 += t[-1] + GAP
    ax[1].axvline((x0 - GAP / 2) / 60, color="0.75", lw=0.6)
ax[1].set_ylim(-110, 130)
ax[1].set_ylabel("전압 차(mV)"); ax[1].set_xlabel("이어 붙인 기록 시간(분, 회색 선 = 다른 기록)")
ax[1].set_title("(나) 같은 크기로 본 네 기록 (10초 평균, 점선 = 정상 중앙값 약 -8.9 mV)", loc="left", fontsize=10)
fig.tight_layout()
fig.savefig(sys.argv[1], dpi=400)
print("ok", base)
