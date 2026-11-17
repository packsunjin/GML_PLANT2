"""fig_sys_block.py — 측정 시스템 구성도(회로도식): 두 줄기 전극의 전위 차이를 재는 DC 결합 측정계 (2026-11-17).
배선은 CLAUDE.md 3절·보고서 배선표와 같다: 위 은선→MCP6002 3번(폴로어 A, 출력 1번=2번)→A0, 아래 은선→5번(폴로어 B, 출력 7번=6번)→A1,
3.3 V-10 kΩ-중점-10 kΩ-GND, 중점 1.65 V → 흙 기준 전극·A2(점검), 차동 A0-A1, PGA ±2.048 V, 칩 860 SPS·4 ms마다 읽기(250 S/s), 상자 망 → GND.
그림 글꼴에 U+2212 가 없어 빼기는 '-' 로 쓴다. 쓰는 법: python3 report/stim/fig_sys_block.py → report/FIG_SYS_BLOCK.png
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon, Ellipse

for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False})
INK, GRAY, ACC, PLANT, PAPER = "#1d1d1d", "#707070", "#1f5f8b", "#3b7d3b", "#f4f6f8"

fig = plt.figure(figsize=(10, 3.9), dpi=300)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 39); ax.axis("off")
L = dict(color=INK, lw=1.1, solid_capstyle="round")


def wire(xs, ys, c=INK, lw=1.1, ls="-"):
    ax.plot(xs, ys, color=c, lw=lw, ls=ls, solid_capstyle="round")


def dot(x, y, c=INK):
    ax.plot(x, y, "o", ms=3.2, color=c)


def txt(x, y, s, size=7.6, c=INK, **kw):
    ax.text(x, y, s, fontsize=size, color=c, **kw)


def stage(x0, x1, label):
    ax.add_patch(Rectangle((x0, 33.6), x1 - x0, 2.6, fc=PAPER, ec="none"))
    txt((x0 + x1) / 2, 34.9, label, 8.2, INK, ha="center", va="center", fontweight="bold")


stage(0.5, 25.5, "① 식물·전극 (차폐 상자 안)")
stage(26.5, 49.5, "② 전압 폴로어·기준 전압")
stage(50.5, 70.5, "③ 16비트 차동 측정")
stage(71.5, 99.5, "④ 수집·분석·판정")

# ① 상자·식물
ax.add_patch(Rectangle((1, 1), 24, 31.5, fill=False, ls=(0, (4, 3)), ec=GRAY, lw=1))
txt(24.3, 31.2, "방충망 → GND", 7, GRAY, ha="right", va="top")
ax.add_patch(Rectangle((3.5, 2.5), 14, 6.5, fc="#efe7db", ec=INK, lw=0.9))
txt(4.3, 3.2, "흙", 7.4, GRAY)
wire([9, 9], [9, 30], PLANT, 3)
for (y, d) in ((28.6, -1), (27, 1)):
    ax.add_patch(Ellipse((9 + 2.5 * d, y + 0.7), 4.6, 1.6, angle=25 * d, fc="#86b886", ec=PLANT, lw=0.7))
YA, YB, YR = 24, 15, 5.5
for y, lab in ((YA, "위 은선"), (YB, "아래 은선")):
    wire([9, 25], [y, y], ACC, 1.3); dot(9, y, ACC)
    txt(17, y + 0.5, lab, 7.6, ACC, ha="center", va="bottom")
wire([5.6, 5.6], [YB, YA], GRAY, 0.7)
for y in (YA, YB):
    wire([5.1, 6.1], [y, y], GRAY, 0.7)
txt(5.2, (YA + YB) / 2, "약\n1 cm", 6.8, GRAY, ha="right", va="center")
ax.plot(13.5, YR, "s", ms=4.5, color=INK)
txt(13.5, YR + 1.0, "기준 전극", 7.2, INK, ha="center", va="bottom")


# ② 폴로어(연산증폭기 삼각형) — + 입력 위, - 입력 아래, 출력을 - 입력에 묶음
def follower(xl, yc, name, pins):
    w, h = 8, 6.4
    ax.add_patch(Polygon([[xl, yc - h / 2], [xl, yc + h / 2], [xl + w, yc]], closed=True, fc="white", ec=INK, lw=1.1))
    yp, ym = yc + 1.6, yc - 1.6
    txt(xl + 0.6, yp, "+", 8, INK, va="center"); txt(xl + 0.6, ym, "-", 8, INK, va="center")
    txt(xl + 3.0, yc, name, 7, INK, va="center")
    xo = xl + w
    wire([xo, xo + 2.2], [yc, yc]); dot(xo + 1.2, yc)
    wire([xo + 1.2, xo + 1.2, xl - 1.2, xl - 1.2, xl], [yc, yc - 4.3, yc - 4.3, ym, ym])
    txt(xl + w / 2, yc + h / 2 + 0.5, pins, 6.6, GRAY, ha="center", va="bottom")
    return xl, yp, xo + 2.2


for y, n, pins in ((YA, "A", "MCP6002 3번 → 1번"), (YB, "B", "MCP6002 5번 → 7번")):
    xl, yp, xout = follower(30.5, y, n, pins)
    wire([25, 28.5, 28.5, xl], [y, y, yp, yp], ACC, 1.3)
ax.add_patch(FancyBboxPatch((28.2, 9.0), 14.2, 22.0, boxstyle="round,pad=0.2,rounding_size=0.8", fc="none", ec=ACC, lw=0.8, ls=(0, (3, 2))))
txt(35.3, 8.1, "MCP6002 한 칩 · 이득 1 · 입력 ±1 pA", 6.6, ACC, ha="center", va="center")


# 기준 전압: 3.3 V - R - 중점 - R - GND (저항 지그재그, 가로)
def resistor(x0, x1, y):
    xs = np.linspace(x0, x1, 13); ys = y + np.array([0, 0.6, -0.6] * 4 + [0])[:13] * 1.0
    ys[0] = ys[-1] = y
    ax.plot(xs, ys, color=INK, lw=1)


yv = 3.2
txt(27, yv, "3.3 V", 7, INK, va="center", ha="left")
wire([30.6, 31.5], [yv, yv]); resistor(31.5, 36, yv); wire([36, 39], [yv, yv]); dot(37.5, yv)
resistor(39, 43.5, yv); wire([43.5, 45], [yv, yv])
def gnd(x, y):
    for k, w in enumerate((1.4, 0.9, 0.4)):
        wire([x - w / 2, x + w / 2], [y - k * 0.45, y - k * 0.45], INK, 1)
wire([45, 45.8], [yv, yv]); wire([45.8, 45.8], [yv, yv - 0.6]); gnd(45.8, yv - 0.6)
txt(33.7, yv + 1.2, "10 kΩ", 6.5, GRAY, ha="center"); txt(41.2, yv + 1.2, "10 kΩ", 6.5, GRAY, ha="center")
wire([37.5, 37.5], [yv, YR]); wire([37.5, 14.1], [YR, YR])     # 중점 → 기준 전극
txt(31, YR + 0.5, "1.65 V", 7, INK, ha="center", va="bottom")

# ③ ADS1115
ax.add_patch(FancyBboxPatch((53, 3), 15.5, 28.5, boxstyle="round,pad=0.2,rounding_size=0.8", fc="white", ec=INK, lw=1.1))
txt(60.75, 29.3, "ADS1115", 9, INK, ha="center", fontweight="bold")
txt(60.75, 27.0, "16비트 ADC", 7.4, GRAY, ha="center")
for y, pin in ((YA, "A0"), (YB, "A1"), (YR, "A2")):
    txt(53.7, y, pin, 7.4, INK, va="center")
wire([40.7, 53], [YA, YA]); wire([40.7, 53], [YB, YB])
wire([37.5, 37.5], [YR, YR]); wire([37.5, 50, 50, 53], [YR, YR, YR, YR], GRAY, 0.9, (0, (2, 2)))
txt(50.5, YR + 0.5, "점검", 6.5, GRAY, ha="center", va="bottom")
for k, s in enumerate(["차동 A0 - A1", "PGA ±2.048 V", "1 LSB 62.5 µV", "860 SPS 연속 변환"]):
    txt(61.5, 23.5 - k * 2.9, s, 7.2, INK, ha="center", va="center")

# ④ 라즈베리파이 처리 흐름
ax.annotate("", (73.6, 17.25), (68.7, 17.25), arrowprops=dict(arrowstyle="-|>", lw=1.1, color=INK, mutation_scale=9))
txt(71.15, 17.8, "I²C", 7, GRAY, ha="center", va="bottom")
ax.add_patch(FancyBboxPatch((74, 3), 25, 28.5, boxstyle="round,pad=0.2,rounding_size=0.8", fc="white", ec=INK, lw=1.1))
txt(86.5, 29.3, "라즈베리파이 5", 9, INK, ha="center", fontweight="bold")
txt(86.5, 27.0, "전원: 보조배터리", 7, GRAY, ha="center")
steps = ["4 ms마다 읽기 → 250 S/s 기록", "0.01–1 Hz 대역 필터", "30초 창 · 특징 14개", "SVM · 랜덤 포레스트", "웹 대시보드 실시간 판정"]
for k, s in enumerate(steps):
    y = 23.2 - k * 4.4
    ax.add_patch(FancyBboxPatch((76, y - 1.45), 21, 2.9, boxstyle="round,pad=0.05,rounding_size=0.6", fc=PAPER, ec="#c9d3dc", lw=0.7))
    txt(86.5, y, s, 7.2, INK, ha="center", va="center")
    if k:
        ax.annotate("", (86.5, y + 1.5), (86.5, y + 2.95), arrowprops=dict(arrowstyle="-|>", lw=0.8, color=GRAY, mutation_scale=6))

txt(50, 37.6, "측정값  V = V(A0) - V(A1)  =  위 은선 전위 - 아래 은선 전위   (두 전극 모두 흙 기준 1.65 V 위에서 움직임)",
    8.6, INK, ha="center", va="center")

out = os.path.join(os.path.dirname(__file__), "..", "FIG_SYS_BLOCK.png")
fig.savefig(out, facecolor="white"); print(out)
