"""fig_band2.py — 그림1 새 판: 식물 전기신호의 주파수 위치와 측정계·필터 통과대역 (2026-11-17).
신호 범위는 지속시간 T → 주파수 약 1/T 로 환산(보고서 Ⅱ장 2절): 수분 스트레스 수 시간~수 일 → 1e-5~1e-4 Hz,
변동전위 수 분~수십 분[3] → 3e-4~3e-3 Hz, 활동전위 수십 초[3] → 0.01~0.1 Hz, 붓 접촉 활동전위 약 10.7초[6] → 0.05~0.2 Hz, 상용전원 60 Hz.
통과대역: AD8232 0.5–40 Hz[8], 본 연구 DC 결합 측정계 0 Hz ~ 125 Hz(250 S/s 의 절반), 분석 필터 0.01–1 Hz.
그림 글꼴에 U+2212 가 없어 빼기는 '-'. 쓰는 법: python3 report/stim/fig_band2.py → report/FIG_BAND2.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
INK, GRAY, BROWN, GREEN, RED, BLUE = "#1d1d1d", "#707070", "#a0522d", "#2e7d4f", "#c0392b", "#1f5f8b"

fig, ax = plt.subplots(figsize=(10, 4.3), dpi=300)
fig.subplots_adjust(left=0.03, right=0.985, top=0.83, bottom=0.14)
ax.set_xscale("log"); ax.set_xlim(1e-5, 3e2); ax.set_ylim(0, 10)
ax.set_yticks([]); ax.set_xlabel("주파수 (Hz, 로그 눈금)")
for s in ("left", "right", "top"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", which="major", lw=0.4, color="#e3e3e3", zorder=0)

# 위쪽 축: 같은 주파수의 지속시간
top = ax.secondary_xaxis("top", functions=(lambda f: f, lambda f: f))
tt = [(1 / 86400, "1일"), (1 / 3600, "1시간"), (1 / 600, "10분"), (1 / 60, "1분"), (1 / 10, "10초"), (1, "1초"), (10, "0.1초"), (100, "0.01초")]
top.set_xticks([f for f, _ in tt]); top.set_xticklabels([s for _, s in tt], fontsize=8, color=GRAY)
top.minorticks_off(); top.set_xlabel("지속시간 T (주파수 약 1/T)", color=GRAY, fontsize=8.5)

# 세로 띠: 통과대역
ax.axvspan(0.5, 40, color=BLUE, alpha=0.08, lw=0)
ax.axvline(0.5, color=BLUE, lw=1, ls="--"); ax.axvline(40, color=BLUE, lw=1, ls="--")
ax.text(6.5, 9.55, "AD8232 통과대역 0.5–40 Hz [8]", ha="center", va="center", fontsize=8.6, color=BLUE, fontweight="bold")
ax.axvspan(1e-5, 1, color=GREEN, alpha=0.08, lw=0)
ax.axvline(1, color=GREEN, lw=1, ls="--")
ax.text(1e-3, 9.55, "분석 범위 0–1 Hz  (기준선 특징 + 0.01–1 Hz 필터)", ha="center", va="center", fontsize=8.6, color=GREEN, fontweight="bold")


def pill(f0, f1, y, label, col, side="right", h=0.85):
    ax.add_patch(FancyBboxPatch((f0, y - h / 2), f1 - f0, h, boxstyle="round,pad=0,rounding_size=0.0", fc=col, ec=col, alpha=0.9, lw=0, zorder=3))
    if side == "right":
        ax.text(f1 * 1.35, y, label, ha="left", va="center", fontsize=8.3, color=INK, zorder=4,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
    else:
        ax.text(f0 / 1.35, y, label, ha="right", va="center", fontsize=8.3, color=INK, zorder=4,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


ax.text(1.2e-5, 8.45, "식물 전기신호", fontsize=8.6, color=GRAY, fontweight="bold")
pill(1e-5, 1e-4, 7.5, "수분 스트레스 (수 시간~수 일)", BROWN)
pill(3e-4, 3e-3, 6.4, "변동전위 · 손상 (수 분~수십 분) [3]", BROWN)
pill(1e-2, 1e-1, 5.3, "활동전위 (수십 초) [3]", GREEN, side="left")
pill(5e-2, 2e-1, 4.2, "붓 접촉 활동전위 (약 10.7초, 33.9 mV) [6]", GREEN, side="left")
pill(57, 63, 6.4, "60 Hz\n잡음", RED)

ax.text(1.2e-5, 3.05, "측정계", fontsize=8.6, color=GRAY, fontweight="bold")
# AD8232: 0.5–40 Hz
ax.add_patch(FancyBboxPatch((0.5, 1.75), 40 - 0.5, 0.85, boxstyle="square,pad=0", fc="white", ec=BLUE, lw=1.4))
ax.text(0.5 / 1.35, 2.17, "AD8232 (처음 쓴 심전도 증폭기)", ha="right", va="center", fontsize=8.3)
# DC 결합: 0 Hz ~ 125 Hz
ax.add_patch(FancyBboxPatch((1e-5, 0.55), 125 - 1e-5, 0.85, boxstyle="square,pad=0", fc="white", ec=GREEN, lw=1.4))
ax.text(1.4e-5, 0.97, "본 연구 DC 결합 측정계 (0 Hz부터, 250 S/s)", ha="left", va="center", fontsize=8.3)
ax.text(4.5, 2.17, "0.5 Hz 아래(활동전위 대역)를 거름", ha="center", va="center", fontsize=7.6, color=BLUE)


out = os.path.join(os.path.dirname(__file__), "..", "FIG_BAND2.png")
fig.savefig(out, facecolor="white", bbox_inches="tight", pad_inches=0.04); print(out)
