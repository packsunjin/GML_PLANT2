"""본 실험 그림: 새 식물(은선 전극, 상자 안·망 GND·보조배터리)의 정상·수분부족 기록 — 2분 단위.
(가) 기준선(2분 평균)  (나) 0.01–1 Hz 잡음  (다) 60 Hz 진폭
숫자는 report/stim/newplant_stats.py 가 만든 newplant_stats.json 을 그대로 쓴다.
쓰는 법(저장소 루트): python3 report/stim/fig_newplant.py report/FIG_NEWPLANT.png
그림 글자에 U+2212 를 쓰지 않는다(글꼴에 없음)."""
import sys, os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

for f in fm.findSystemFonts():
    if "NotoSansCJK" in f or "NotoSansKR" in f:
        fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False
C_OK, C_DRY = "#1f6fb4", "#c0504d"
d = json.load(open(os.path.join(os.path.dirname(__file__), "newplant_stats.json"), encoding="utf-8"))
col = lambda n, k: np.array([r[k] for r in d[n]["rows"]])
fig, ax = plt.subplots(3, 1, figsize=(7.2, 5.7), sharex=True, gridspec_kw=dict(height_ratios=[1.25, 1, 1]))
TEND = 5.9   # 두 기록을 같은 길이(정상 기록 길이 5.9시간)로 비교(2026-11-17 사용자 지시)
for n, c, lab in (("수분부족", C_DRY, "물 공급 중단: 물 끊은 지 4.0~4.2일(11월 9일 밤)"), ("정상_6", C_OK, "정상: 물 준 뒤 4~10시간(11월 5~6일)")):
    t = col(n, "t") / 3600 + 1 / 60
    k = t <= TEND
    ax[0].plot(t[k], col(n, "mean")[k], color=c, lw=1.2, label=lab)
    ax[1].semilogy(t[k], col(n, "rms")[k], color=c, lw=0.9)
    ax[2].semilogy(t[k], col(n, "a60")[k], color=c, lw=0.9)
ax[0].set_ylabel("전압 차(mV)"); ax[0].set_ylim(195, 262); ax[0].legend(loc="center right", bbox_to_anchor=(1.0, 0.5), fontsize=8)
ax[0].set_title("(가) 기준선 (2분 평균)", loc="left", fontsize=10)
ax[1].axhline(0.1, color="#888888", lw=0.7, ls="--"); ax[1].text(5.85, 0.115, "분석 기준 0.1 mV", ha="right", va="bottom", fontsize=7.5, color="#555555")
ax[1].set_ylabel("잡음(mV)"); ax[1].set_ylim(0.01, 60)
ax[1].set_title("(나) 0.01–1 Hz 잡음 (2분 단위)", loc="left", fontsize=10)
ax[2].set_ylabel("진폭(mV)"); ax[2].set_ylim(0.0005, 0.2)
ax[2].set_title("(다) 60 Hz 상용전원 성분 (2분 단위)", loc="left", fontsize=10)
ax[2].set_xlabel("기록 시작 뒤 시간(시간) — 물 공급 중단은 17시 44분, 정상은 22시 42분에 시작")
ax[2].set_xlim(0, TEND); ax[2].set_xticks(range(0, 7, 1))
for a in ax:
    a.grid(True, which="major", color="#dddddd", lw=0.5)
fig.tight_layout()
fig.savefig(sys.argv[1], dpi=400, facecolor="white", bbox_inches="tight", pad_inches=0.04)
print("saved", sys.argv[1])
