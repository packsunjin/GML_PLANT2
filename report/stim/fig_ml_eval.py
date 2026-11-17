"""fig_ml_eval.py — 모델 학습·평가 방식과 결과 (2026-11-17).
숫자: 정상·물 공급 중단 = report/stim/newplant_ml.py 결과(특징 17개), 손 접촉 = 보고서 표5(Ⅳ-2).
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
band(0, 31, "① 기록을 시간으로 반씩"); band(32.5, 52, "② 30초 창 · 5초 이동"); band(53.5, 70, "③ 특징 17개")
band(71.5, 84, "④ 학습"); band(85.5, 100, "⑤ 평가")
# ① 두 기록(같은 축척) + 학습/평가 반
U = 1.85
for y, lab, col, hrs in ((14.2, "정상 5.9시간", OK, 5.9), (8.6, "물 공급 중단 14.5시간", DRY, 14.5)):
    L = hrs * U
    a.add_patch(FancyBboxPatch((0.5, y - 1.2), L / 2 - 0.15, 2.4, boxstyle="round,pad=0,rounding_size=0.35", fc=col, ec="none"))
    a.add_patch(FancyBboxPatch((0.5 + L / 2 + 0.15, y - 1.2), L / 2 - 0.15, 2.4, boxstyle="round,pad=0,rounding_size=0.35", fc=col, alpha=0.28, ec="none"))
    a.text(0.5 + L / 4, y, "학습", ha="center", va="center", fontsize=7.3, color="white", fontweight="bold")
    a.text(0.5 + 3 * L / 4, y, "평가", ha="center", va="center", fontsize=7.3, color=INK, fontweight="bold")
    a.text(0.5, y + 1.9, lab, fontsize=7.4, color=col, va="center")
a.annotate("", (8.6, 3.3), (22.6, 3.3), arrowprops=dict(arrowstyle="<|-|>", lw=0.9, color=GRAY, mutation_scale=8))
a.text(15.6, 1.6, "학습 · 평가 바꿔 한 번 더", ha="center", fontsize=7, color=GRAY)
arrow(29.0, 32.3)
# ② 신호 + 겹치는 창
xx = np.linspace(0, 1, 400)
a.plot(33 + 18.5 * xx, 6.0 + 1.1 * np.sin(xx * 34) * (0.6 + 0.4 * np.sin(xx * 5)), color="#4a4a4a", lw=0.9)
for k in range(4):
    x = 33.5 + k * 2.6
    a.add_patch(FancyBboxPatch((x, 9.2 + k * 1.55), 8.4, 1.05, boxstyle="round,pad=0,rounding_size=0.3", fc=M1, alpha=0.75 - k * 0.12, ec="none"))
a.text(45.6, 15.3, "30초", fontsize=7, color=M1, ha="left")
a.annotate("", (36.1, 8.6), (33.5, 8.6), arrowprops=dict(arrowstyle="<|-|>", lw=0.7, color=GRAY, mutation_scale=6))
a.text(36.6, 8.6, "5초", ha="left", va="center", fontsize=6.6, color=GRAY)
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
# ⑤ 균형 정확도 막대 + 문턱 하나
a.add_patch(FancyBboxPatch((86.2, 11.0), 13.2, 5.0, boxstyle="round,pad=0,rounding_size=0.8", fc="white", ec="#9aa7b4", lw=0.9))
a.text(92.8, 14.7, "균형 정확도", ha="center", va="center", fontsize=7.8, fontweight="bold")
for k, (h, c) in enumerate(((0.9, OK), (0.7, DRY))):
    a.add_patch(FancyBboxPatch((88.0 + k * 3.0, 11.8), 2.0, 2.0 * h, boxstyle="square,pad=0", fc=c, ec="none"))
a.text(95.2, 12.6, "평균", fontsize=6.8, color=GRAY, va="center")
a.add_patch(FancyBboxPatch((86.2, 3.4), 13.2, 5.6, boxstyle="round,pad=0,rounding_size=0.8", fc="#fbf4ea", ec="#d4b48a", lw=0.9))
a.text(92.8, 7.6, "비교: 문턱 하나", ha="center", va="center", fontsize=7.8, fontweight="bold")
a.plot([87.4, 98.2], [5.0, 5.0], color=GRAY, lw=0.8)
a.plot([92.0, 92.0], [4.1, 6.3], color=TH, lw=2)
for x_, c in ((88.4, OK), (89.6, OK), (90.7, OK), (93.6, DRY), (95.0, DRY), (96.6, DRY)):
    a.plot(x_, 5.0, "o", ms=3.2, color=c)

# (나) 정상·물 공급 중단 결과
b = fig.add_axes([0.07, 0.16, 0.50, 0.38])
labs = ["랜덤 포레스트\n(특징 17개)", "SVM\n(특징 17개)", "문턱 하나\n(기준선)", "문턱 하나\n(잡음 크기)"]
fwd = [100.0, 99.9, 99.1, 99.1]; bwd = [66.3, 65.2, 100.0, 98.4]
xs = np.arange(4); w = 0.36
cols = [M1, M1, TH, TH]
r1 = b.bar(xs - w / 2, fwd, w, color=cols, label="앞 → 뒤")
r2 = b.bar(xs + w / 2, bwd, w, color=cols, alpha=0.5, hatch="///", edgecolor="white", label="뒤 → 앞")
for r in list(r1) + list(r2):
    b.text(r.get_x() + r.get_width() / 2, r.get_height() + 1.2, f"{r.get_height():g}", ha="center", fontsize=7)
b.axhline(50, color=GRAY, ls="--", lw=0.8); b.text(-0.55, 51.5, "우연 50 %", ha="left", fontsize=7, color=GRAY, bbox=dict(fc="white", ec="none", pad=0.5))
b.set_xticks(xs); b.set_xticklabels(labs, fontsize=7.6); b.set_ylim(0, 112); b.set_ylabel("균형 정확도 (%)")
b.set_title("(나) 정상 대 물 공급 중단 — 모델은 방향에 따라 흔들리고, 문턱 하나로도 갈림", loc="left", fontsize=9.2)
from matplotlib.patches import Patch
b.legend(handles=[Patch(fc="#888888", label="앞 절반 학습 → 뒤 절반 평가"), Patch(fc="#888888", alpha=0.5, hatch="///", ec="white", label="뒤 절반 학습 → 앞 절반 평가")],
         fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False)
# (다) 손 접촉
c = fig.add_axes([0.68, 0.16, 0.30, 0.38])
tl = ["SVM · 특징 17개", "SVM · 스펙트로그램", "랜덤 포레스트 · 특징", "랜덤 포레스트 · 스펙트로그램", "문턱 하나 · 특징 1개"]
tv = [23, 22, 17, 12, 23]
yy = np.arange(5)[::-1]
c.barh(yy, tv, color=[M1, M1, M2, M2, TH], height=0.6)
for y, v in zip(yy, tv):
    c.text(v + 0.3, y, f"{v}/23", va="center", fontsize=7)
c.set_yticks(yy); c.set_yticklabels(tl, fontsize=7.2); c.set_xlim(0, 27)
c.set_xlabel("평가 창의 접촉 23개 중 찾은 수")
c.set_title("(다) 손 접촉 감지 (평가 창 251개)", loc="left", fontsize=9.2)
for x_ in (b, c):
    x_.grid(axis="y" if x_ is b else "x", lw=0.3, color="#e3e3e3"); x_.set_axisbelow(True)
    for s in ("top", "right"):
        x_.spines[s].set_visible(False)
out = os.path.join(os.path.dirname(__file__), "..", "FIG_ML_EVAL.png")
fig.savefig(out, facecolor="white", bbox_inches="tight", pad_inches=0.04); print(out)
