"""fig_ap_diff.py — 그림1(Ⅱ-1): 줄기를 따라 전파하는 활동전위가 두 전극의 전위 차이로 잡히는 원리 (2026-11-17, 모식도).
문헌 값 [6] Degli Agosti 2014: 붓 접촉 활동전위 33.9 mV, 약 10.7초, 전파 1.32 mm/s, 접촉 지점에 가까운 전극에 먼저 도착.
본 연구 전극 간격 약 1 cm → 도착 시간 차 10 / 1.32 ≈ 7.6초. 파형 모양(가우스형)은 설명용 가정이다.
그림 글꼴에 U+2212 가 없어 빼기는 '-'. 쓰는 법: python3 report/stim/fig_ap_diff.py → report/FIG_AP_DIFF.png
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

fm.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
INK, GRAY, C1, C2, CD = "#222222", "#6b6b6b", "#c0392b", "#1f5f8b", "#222222"

AMP, WID, V, GAP = 33.9, 10.7, 1.32, 10.0          # mV, 초, mm/s, mm
DT = GAP / V                                        # 7.6초
t = np.linspace(0, 60, 2000)
t1 = 20.0
ap = lambda tc: -AMP * np.exp(-0.5 * ((t - tc) / (WID / 4)) ** 2)   # 문헌 표기처럼 음의 방향
v1, v2 = ap(t1), ap(t1 + DT)

fig = plt.figure(figsize=(10, 3.6), dpi=300)
# (가) 모식도
a = fig.add_axes([0.02, 0.08, 0.40, 0.84]); a.set_xlim(0, 40); a.set_ylim(0, 30); a.axis("off")
a.text(0, 28.5, "(가) 줄기를 따라 전파하는 활동전위", fontsize=9.5, va="top")
a.add_patch(FancyBboxPatch((3, 13), 34, 3.2, boxstyle="round,pad=0,rounding_size=1.5", fc="#d8ead2", ec="#3b7d3b", lw=1.1))
a.text(3, 17.2, "줄기", fontsize=8, color="#3b7d3b")
a.annotate("자극", (3.5, 14.6), (0.2, 21), fontsize=8, color=INK, arrowprops=dict(arrowstyle="-|>", lw=1, color=INK))
for x, c, lab in ((15, C1, "전극 1 (가까움)"), (25, C2, "전극 2 (멂)")):
    a.plot([x, x], [16.4, 22.5], color=c, lw=1.6); a.plot(x, 16.2, "o", ms=5, color=c)
    a.text(x, 23.2, lab, ha="center", fontsize=8, color=c)
xs = np.linspace(3, 37, 300)
for xc, al in ((15, 1.0), (25, 0.35)):
    a.plot(xs, 10.5 - 3.2 * np.exp(-0.5 * ((xs - xc) / 1.8) ** 2), color=INK, lw=1.2, alpha=al)
a.text(15, 5.8, "시각 t", ha="center", fontsize=7.5, color=GRAY)
a.text(25, 5.8, "t + 7.6초", ha="center", fontsize=7.5, color=GRAY)
a.annotate("", (24, 4.4), (16, 4.4), arrowprops=dict(arrowstyle="-|>", lw=1, color=GRAY))
a.text(20, 2.0, "전파 1.32 mm/s [6]", ha="center", fontsize=7.8, color=GRAY)
a.annotate("", (25, 19.8), (15, 19.8), arrowprops=dict(arrowstyle="<->", lw=0.8, color=GRAY))
a.text(20, 20.3, "약 1 cm", ha="center", fontsize=7.5, color=GRAY)

# (나) 각 전극 전위
b = fig.add_axes([0.50, 0.58, 0.47, 0.32])
b.plot(t, v1, color=C1, lw=1.4, label="전극 1")
b.plot(t, v2, color=C2, lw=1.4, label="전극 2")
b.set_ylabel("전위 (mV)"); b.set_xlim(0, 60); b.set_ylim(-40, 8); b.set_xticklabels([])
b.legend(loc="lower right", fontsize=7.5, frameon=False, ncol=2)
b.set_title("(나) 각 전극의 세포 밖 전위 (문헌 크기 33.9 mV, 약 10.7초 [6])", fontsize=9.5, loc="left")
b.annotate("", (t1 + DT, 3), (t1, 3), arrowprops=dict(arrowstyle="<->", lw=0.8, color=GRAY))
b.text(t1 + DT / 2, 4, "7.6초", ha="center", fontsize=7.5, color=GRAY)
# (다) 차이
c = fig.add_axes([0.50, 0.12, 0.47, 0.32])
c.plot(t, v1 - v2, color=CD, lw=1.4)
c.axhline(0, color=GRAY, lw=0.6, ls="--")
c.set_ylabel("전위 차 (mV)"); c.set_xlabel("시간 (초)"); c.set_xlim(0, 60)
c.set_title("(다) 측정값 = 전극 1 - 전극 2", fontsize=9.5, loc="left")
for x in (b, c):
    x.grid(lw=0.3, color="#e3e3e3")
    for s in ("top", "right"):
        x.spines[s].set_visible(False)
out = os.path.join(os.path.dirname(__file__), "..", "FIG_AP_DIFF.png")
fig.savefig(out, facecolor="white"); print(out)
