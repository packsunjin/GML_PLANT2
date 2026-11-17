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
# (가) 학습·평가 방식
a = fig.add_axes([0.02, 0.63, 0.96, 0.36]); a.set_xlim(0, 100); a.set_ylim(2.5, 20); a.axis("off")
a.text(0, 19.6, "(가) 학습·평가 방식", fontsize=10, fontweight="bold", va="top")
for y, lab, col, n in ((13.3, "정상 기록 (5.9시간)", OK, "창 4,210개"), (8.3, "물 공급 중단 밤 기록 (14.5시간)", DRY, "창 10,467개")):
    a.text(0.5, y + 1.4, lab, fontsize=8.5, color=col, va="center")
    a.add_patch(FancyBboxPatch((0.5, y - 1.3), 19, 2, boxstyle="round,pad=0,rounding_size=0.4", fc=col, alpha=0.85, ec="none"))
    a.add_patch(FancyBboxPatch((19.7, y - 1.3), 19, 2, boxstyle="round,pad=0,rounding_size=0.4", fc=col, alpha=0.35, ec="none"))
    a.text(10, y - 0.3, "앞 절반 → 학습", ha="center", va="center", fontsize=7.8, color="white")
    a.text(29.2, y - 0.3, "뒤 절반 → 평가", ha="center", va="center", fontsize=7.8, color=INK)
    a.text(39.3, y - 0.3, n, va="center", fontsize=7.4, color=GRAY)
a.text(0.5, 3.6, "그리고 반대로(뒤 절반 학습 → 앞 절반 평가)도 한 번 더", fontsize=7.8, color=GRAY)
steps = [("30초 창", "5초씩 옮기며 자름"), ("특징 17개", "시간 7 · 주파수 7\n기준선 3 (0–1 Hz)"), ("SVM ·\n랜덤 포레스트", "학습"),
         ("균형 정확도", "두 부류 정확도의\n평균"), ("문턱 하나와 비교", "특징 1개로도 갈리면\n모델이 그것을 가른 것")]
x = 51
for k, (t1, t2) in enumerate(steps):
    a.add_patch(FancyBboxPatch((x, 5.5), 8.6, 9.5, boxstyle="round,pad=0.25,rounding_size=0.8", fc="#f4f6f8", ec="#9aa7b4", lw=0.8))
    a.text(x + 4.3, 12.6, t1, ha="center", va="center", fontsize=7.8, fontweight="bold")
    a.text(x + 4.3, 8.4, t2, ha="center", va="center", fontsize=6.6, color=GRAY)
    if k:
        a.annotate("", (x - 0.15, 10.2), (x - 0.95, 10.2), arrowprops=dict(arrowstyle="-|>", lw=0.9, color=GRAY))
    x += 9.8

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
