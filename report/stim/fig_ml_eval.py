"""fig_ml_eval.py — 손 접촉 감지 모델 학습·평가 방식과 결과 (2026-11-19).
숫자: report/stim/touch1117_ml.py 결과(touch1117_ml.json, 11-17 콘센트·보조배터리 기록, 특징 17개).
쓰는 법: python3 report/stim/fig_ml_eval.py → report/FIG_ML_EVAL.png
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch
for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
INK, GRAY, OK, DRY, M1, M2, TH = "#1d1d1d", "#707070", "#1f6fb4", "#c0504d", "#3d5a80", "#98c1d9", "#b0b0b0"

fig = plt.figure(figsize=(10, 5.0), dpi=300)
# (가) 학습·평가 방식 — 회로 구성도(그림2)와 같은 단계 띠 + 그림 위주
a = fig.add_axes([0.01, 0.60, 0.98, 0.39]); a.set_xlim(0, 100); a.set_ylim(0, 24); a.axis("off")
a.text(0, 23.9, "(가) 학습·평가 방식", fontsize=10, fontweight="bold", va="top")
PAPER = "#f4f6f8"
def band(x0, x1, t):
    a.add_patch(FancyBboxPatch((x0, 18.6), x1 - x0, 2.4, boxstyle="square,pad=0", fc=PAPER, ec="none"))
    a.text((x0 + x1) / 2, 19.8, t, ha="center", va="center", fontsize=8.3, fontweight="bold")
def arrow(x0, x1, y=9.5):
    a.annotate("", (x1, y), (x0, y), arrowprops=dict(arrowstyle="-|>", lw=1.1, color=INK, mutation_scale=9))
band(0, 31, "① 콘센트 기록을 시간으로 반씩"); band(32.5, 52, "② 2초 창 · 0.5초 이동"); band(53.5, 70, "③ 특징 추출 (17개)")
band(71.5, 84, "④ 학습"); band(85.5, 100, "⑤ 평가")
# ① 콘센트 기록 600초: 만진 시각 9번, 앞 4번/뒤 5번
L = 28.0
a.add_patch(FancyBboxPatch((0.5, 10.8), L * 0.5 - 0.15, 2.6, boxstyle="round,pad=0,rounding_size=0.35", fc=M1, ec="none"))
a.add_patch(FancyBboxPatch((0.5 + L * 0.5 + 0.15, 10.8), L * 0.5 - 0.15, 2.6, boxstyle="round,pad=0,rounding_size=0.35", fc=M1, alpha=0.28, ec="none"))
a.text(0.5 + L * 0.25, 12.1, "학습", ha="center", va="center", fontsize=7.3, color="white", fontweight="bold")
a.text(0.5 + L * 0.75, 12.1, "평가", ha="center", va="center", fontsize=7.3, color=INK, fontweight="bold")
a.text(0.5, 15.2, "콘센트 전원 600초 · 잎 만짐 9번", fontsize=7.4, color=M1, va="center")
for k in range(9):
    x = 0.5 + L * (189.28 + 30 * k) / 600
    a.plot([x, x], [7.6, 9.9], color="#d4a017", lw=1.6)
a.text(0.5, 6.2, "노란 선 = 잎을 잡은 시각", fontsize=6.8, color=GRAY, va="center")
a.annotate("", (8.6, 3.3), (22.6, 3.3), arrowprops=dict(arrowstyle="<|-|>", lw=0.9, color=GRAY, mutation_scale=8))
a.text(15.6, 1.6, "학습 · 평가 바꿔 한 번 더", ha="center", fontsize=7, color=GRAY)
arrow(29.0, 32.3)
# ② 신호 + 겹치는 창
xx = np.linspace(0, 1, 400)
a.plot(33 + 18.5 * xx, 6.0 + 1.1 * np.sin(xx * 34) * (0.6 + 0.4 * np.sin(xx * 5)), color="#4a4a4a", lw=0.9)
for k in range(4):
    x = 33.5 + k * 2.6
    a.add_patch(FancyBboxPatch((x, 9.2 + k * 1.55), 8.4, 1.05, boxstyle="round,pad=0,rounding_size=0.3", fc=M1, alpha=0.75 - k * 0.12, ec="none"))
a.text(45.6, 15.3, "2초", fontsize=7, color=M1, ha="left")
a.annotate("", (36.1, 8.6), (33.5, 8.6), arrowprops=dict(arrowstyle="<|-|>", lw=0.7, color=GRAY, mutation_scale=6))
a.text(36.6, 8.6, "0.5초", ha="left", va="center", fontsize=6.6, color=GRAY)
arrow(52.2, 53.3)
# ③ 특징 칩 3개
for k, (t1, n, col) in enumerate((("시간", "7", "#3d5a80"), ("주파수", "7", "#5c8db8"), ("기준선", "3", "#a0522d"))):
    y = 14.2 - k * 4.6
    a.add_patch(FancyBboxPatch((54.3, y - 1.6), 14.8, 3.2, boxstyle="round,pad=0,rounding_size=0.6", fc=col, ec="none", alpha=0.9))
    a.text(57.2, y, t1, va="center", fontsize=7.8, color="white", fontweight="bold")
    a.text(67.6, y, n, va="center", ha="right", fontsize=11, color="white", fontweight="bold")
arrow(69.8, 71.3)
# ④ 모델 두 개
for k, t1 in enumerate(("SVM", "랜덤\n포레스트")):
    y = 13.0 - k * 6.4
    a.add_patch(FancyBboxPatch((72.2, y - 2.3), 11.0, 4.6, boxstyle="round,pad=0,rounding_size=0.8", fc="white", ec=M1, lw=1.2))
    a.text(77.7, y, t1, ha="center", va="center", fontsize=8.2, fontweight="bold", color=M1, linespacing=1.1)
arrow(83.8, 85.3)
# ⑤ 균형 정확도
a.add_patch(FancyBboxPatch((86.2, 6.0), 13.2, 8.0, boxstyle="round,pad=0,rounding_size=0.8", fc="white", ec="#9aa7b4", lw=0.9))
a.text(92.8, 12.3, "균형 정확도", ha="center", va="center", fontsize=7.8, fontweight="bold")
for k, (h, c) in enumerate(((0.9, M1), (0.7, "#d4a017"))):
    a.add_patch(FancyBboxPatch((88.0 + k * 3.0, 7.2), 2.0, 3.6 * h, boxstyle="square,pad=0", fc=c, ec="none"))
a.text(95.0, 8.8, "두 부류\n평균", fontsize=6.8, color=GRAY, va="center")

# (나) 콘센트 기록 평가
b = fig.add_axes([0.07, 0.16, 0.38, 0.38])
labs = ["랜덤 포레스트\n(특징 추출)", "SVM\n(특징 추출)"]
fwd = [98.7, 99.8]; bwd = [95.5, 95.5]
xs = np.arange(2); w = 0.32
r1 = b.bar(xs - w / 2, fwd, w, color=M1)
r2 = b.bar(xs + w / 2, bwd, w, color=M1, alpha=0.5, hatch="///", edgecolor="white")
for r in list(r1) + list(r2):
    b.text(r.get_x() + r.get_width() / 2, r.get_height() + 1.2, f"{r.get_height():g}", ha="center", fontsize=7)
b.axhline(50, color=GRAY, ls="--", lw=0.8); b.text(-0.58, 51.5, "우연 50 %", ha="left", fontsize=7, color=GRAY, bbox=dict(fc="white", ec="none", pad=0.5))
b.set_xticks(xs); b.set_xticklabels(labs, fontsize=7.8); b.set_ylim(0, 112); b.set_xlim(-0.55, 1.55); b.set_ylabel("균형 정확도 (%)")
b.set_title("(나) 콘센트 전원 기록 — 손 접촉 감지 균형 정확도", loc="left", fontsize=9.2)
from matplotlib.patches import Patch
b.legend(handles=[Patch(fc="#888888", label="앞 절반 학습 → 뒤 절반 평가"), Patch(fc="#888888", alpha=0.5, hatch="///", ec="white", label="뒤 절반 학습 → 앞 절반 평가")],
         fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False)
# (다) 전원별: 잎 만진 창을 접촉으로 판정한 비율(콘센트 = 평가 두 방향 합, 배터리 = 콘센트 전체로 학습한 모델 적용)
c = fig.add_axes([0.60, 0.16, 0.38, 0.38])
grp = ["콘센트 전원\n(평가 창)", "보조배터리 전원\n(같은 모델 적용)"]
rfv = [68 / 72, 0 / 80]; svv = [69 / 72, 0 / 80]; lab_rf = ["68/72", "0/80"]; lab_sv = ["69/72", "0/80"]
xs2 = np.arange(2); w2 = 0.32
q1 = c.bar(xs2 - w2 / 2, [100 * v for v in rfv], w2, color=M2, label="랜덤 포레스트")
q2 = c.bar(xs2 + w2 / 2, [100 * v for v in svv], w2, color=M1, label="SVM")
for r, t in zip(list(q1) + list(q2), lab_rf + lab_sv):
    c.text(r.get_x() + r.get_width() / 2, r.get_height() + 1.5, t, ha="center", fontsize=7)
c.set_xticks(xs2); c.set_xticklabels(grp, fontsize=7.8); c.set_ylim(0, 112); c.set_xlim(-0.55, 1.55)
c.set_ylabel("접촉으로 판정한 비율 (%)")
c.set_title("(다) 잎을 만진 시각의 창 — 전원별", loc="left", fontsize=9.2)
c.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False)
for x_ in (b, c):
    x_.grid(axis="y", lw=0.3, color="#e3e3e3"); x_.set_axisbelow(True)
    for s in ("top", "right"):
        x_.spines[s].set_visible(False)
out = os.path.join(os.path.dirname(__file__), "..", "FIG_ML_EVAL.png")
fig.savefig(out, facecolor="white", bbox_inches="tight", pad_inches=0.04); print(out)
