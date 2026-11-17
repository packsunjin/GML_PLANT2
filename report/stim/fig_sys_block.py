"""fig_sys_block.py — 그림2: 두 줄기 전극의 전위 차이를 재는 DC 결합 측정계 블록도 (2026-11-17, 논문 그림 모양).
배선은 CLAUDE.md 3절·보고서 표7과 같다: 위 은선→MCP6002 3번(폴로어 A)→A0, 아래 은선→5번(폴로어 B)→A1,
3.3 V-10 kΩ-중점-10 kΩ-GND 중점 1.65 V → 흙 기준 전극·A2(점검), 차동 A0-A1, PGA ±2.048 V, 250 S/s, 상자 망 → GND.
그림 글꼴에 U+2212 가 없어 빼기는 '-' 로 쓴다. 쓰는 법: python3 report/stim/fig_sys_block.py → report/FIG_SYS_BLOCK.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Rectangle

for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False})

INK, GRAY, ACC, LIGHT = "#222222", "#6b6b6b", "#1f5f8b", "#eef3f7"
fig = plt.figure(figsize=(10, 4.4), dpi=300)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 44); ax.axis("off")


def box(x, y, w, h, title, lines=(), fc="white", ec=INK, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8", fc=fc, ec=ec, lw=1.1))
    ax.text(x + w / 2, y + h - 2.2, title, ha="center", va="center", fontsize=9.5, fontweight="bold" if bold else "normal", color=INK)
    for k, s in enumerate(lines):
        ax.text(x + w / 2, y + h - 5.2 - k * 2.6, s, ha="center", va="center", fontsize=7.6, color=GRAY)


def arrow(x0, y0, x1, y1, label=None, dy=1.1, color=INK, ls="-"):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=color, lw=1.1, ls=ls, mutation_scale=9))
    if label:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, label, ha="center", va="bottom", fontsize=7.4, color=GRAY)


# ── 패러데이 상자(점선) 안의 식물 ──
from matplotlib.patches import Ellipse
YA, YB, YR = 28, 18, 6.5          # 위 은선·아래 은선·기준 전극 높이(그림 좌표, 간격은 실제 비율 아님)
ax.add_patch(Rectangle((1.5, 1.5), 25, 38.5, fill=False, ls=(0, (4, 3)), ec=GRAY, lw=1))
ax.text(14, 38, "패러데이 상자 (방충망, GND 연결)", ha="center", fontsize=8, color=GRAY)
ax.add_patch(Rectangle((5, 3), 16, 8.5, fc="#f3eee6", ec=INK, lw=1))
ax.text(6, 4, "흙", ha="left", va="bottom", fontsize=8, color=GRAY)
ax.plot([12, 12], [11.5, 35], color="#3b7d3b", lw=3, solid_capstyle="round")
for (y, d) in ((33, -1), (31, 1), (24, -1)):
    ax.add_patch(Ellipse((12 + 2.6 * d, y + 0.8), 5, 1.8, angle=25 * d, fc="#7fb27f", ec="#3b7d3b", lw=0.8))
for y, lab in ((YA, "위 은선"), (YB, "아래 은선")):
    ax.plot([12, 26.5], [y, y], color=ACC, lw=1.4); ax.plot(12, y, "o", ms=5, color=ACC)
    ax.text(19.5, y + 0.7, lab, ha="center", va="bottom", fontsize=7.6, color=ACC)
ax.plot([8.5, 8.5], [YB, YA], color=GRAY, lw=0.8)
for y in (YA, YB):
    ax.plot([8, 9], [y, y], color=GRAY, lw=0.8)
ax.text(7.7, (YA + YB) / 2, "약 1 cm", ha="right", va="center", fontsize=7, color=GRAY)
ax.plot(17, YR, "s", ms=5, color=INK)
ax.text(17, YR + 1.3, "기준 전극", ha="center", va="bottom", fontsize=7.6, color=INK)

# ── 기준 전압 ──
box(29.5, 2.5, 17, 8.5, "기준 전압 1.65 V", ["3.3 V - 10 kΩ - 10 kΩ - GND"])
ax.annotate("", (17.6, YR), (29.3, YR), arrowprops=dict(arrowstyle="-|>", lw=1, color=INK, mutation_scale=8))

# ── 전압 폴로어 ──
for y, t, pins in ((YA, "전압 폴로어 A", "MCP6002 3번 → 1번"), (YB, "전압 폴로어 B", "MCP6002 5번 → 7번")):
    box(31, y - 4, 14, 8, t, [pins], fc=LIGHT, ec=ACC)
    ax.annotate("", (30.8, y), (26.5, y), arrowprops=dict(arrowstyle="-|>", lw=1.2, color=ACC, mutation_scale=8))
ax.text(38, YB - 6.3, "이득 1 · 입력 바이어스 ±1 pA", ha="center", fontsize=7, color=GRAY)

# ── ADC ──
box(52, 9.5, 18, 26.5, "16비트 ADC", ["ADS1115", "차동 A0 - A1", "PGA ±2.048 V", "1 LSB 62.5 µV", "250 S/s"])
arrow(45.4, YA, 51.8, YA, "A0", dy=0.5)
arrow(45.4, YB, 51.8, YB, "A1", dy=0.5)
ax.plot([46.7, 49, 49, 51.2], [YR, YR, 11.5, 11.5], color=GRAY, lw=0.9, ls=(0, (2, 2)))
ax.annotate("", (51.8, 11.5), (51.0, 11.5), arrowprops=dict(arrowstyle="-|>", lw=0.9, color=GRAY, mutation_scale=7))
ax.text(49.6, 7.6, "A2 (기준 점검)", ha="left", fontsize=6.8, color=GRAY)

# ── 라즈베리파이 ──
box(75.5, 9.5, 23, 26.5, "라즈베리파이 5", ["수집 (CSV)", "0.01–1 Hz 필터", "30초 창 · 특징", "SVM · 랜덤 포레스트", "웹 대시보드 실시간 판정"])
arrow(70.3, 22.75, 75.3, 22.75, "I²C", dy=0.5)
ax.text(87, 6.8, "전원: 보조배터리", ha="center", fontsize=7.6, color=GRAY)

ax.text(62, 40.5, "측정값  V = V(A0) - V(A1)  =  위 은선 전위 - 아래 은선 전위  (기준: 흙 1.65 V)", ha="center", fontsize=9, color=INK)

out = os.path.join(os.path.dirname(__file__), "..", "FIG_SYS_BLOCK.png")
fig.savefig(out, facecolor="white"); print(out)
