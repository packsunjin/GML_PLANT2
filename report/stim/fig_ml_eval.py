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

fig = plt.figure(figsize=(10, 5.6), dpi=300)
# (가) 학습·평가 방식
a = fig.add_axes([0.02, 0.60, 0.96, 0.39]); a.set_xlim(0, 100); a.set_ylim(0, 22); a.axis("off")
a.text(0, 21.8, "(가) 학습·평가 방식", fontsize=10, fontweight="bold", va="top")
# ① 기록을 시간으로 반 나눔(같은 축척: 1시간 = 2.35칸)
a.text(0, 18.6, "① 기록을 시간 순서로 반으로 나눔", fontsize=8.6, fontweight="bold", va="center")
U = 2.35
for y, lab, col, hrs, n in ((15.6, "정상", OK, 5.9, "4,210창"), (12.2, "물 공급 중단", DRY, 14.5, "10,467창")):
    a.text(0, y, lab, fontsize=8, color=col, va="center")
    x0, L = 9.5, hrs * U
    a.add_patch(FancyBboxPatch((x0, y - 1.05), L / 2 - 0.15, 2.1, boxstyle="round,pad=0,rounding_size=0.35", fc=col, ec="none"))
    a.add_patch(FancyBboxPatch((x0 + L / 2 + 0.15, y - 1.05), L / 2 - 0.15, 2.1, boxstyle="round,pad=0,rounding_size=0.35", fc=col, alpha=0.3, ec="none"))
    a.text(x0 + L / 4, y, "학습", ha="center", va="center", fontsize=7.6, color="white", fontweight="bold")
    a.text(x0 + 3 * L / 4, y, "평가", ha="center", va="center", fontsize=7.6, color=INK, fontweight="bold")
    a.text(x0 + L + 0.8, y, f"{hrs}시간 · {n}", fontsize=7.2, color=GRAY, va="center")
a.text(9.5, 9.6, "→ 학습·평가를 바꿔 한 번 더 (뒤 절반 학습 → 앞 절반 평가)", fontsize=7.3, color=GRAY, va="center")
# 왜 시간으로 나누나: 창이 겹침
a.text(0, 6.9, "왜 섞지 않고 시간으로 나누나", fontsize=8, fontweight="bold", va="center")
xs_ = np.linspace(0, 1, 300)
a.plot(1 + 28 * xs_, 2.6 + 0.9 * np.sin(xs_ * 40) * np.exp(-((xs_ - 0.5) ** 2) * 3), color="#555555", lw=0.8)
for k in range(4):
    x = 3 + k * 3.2
    a.add_patch(FancyBboxPatch((x, 3.9 + k * 0.55), 12, 0.42, boxstyle="square,pad=0", fc=M1, alpha=0.55, ec="none"))
a.text(29.5, 4.9, "30초 창을 5초씩 옮겨 자르면\n이웃 창이 25초 겹친다 → 무작위로 섞으면\n거의 같은 창이 학습·평가 양쪽에 들어가\n정확도가 부풀어 오른다", fontsize=6.8, color=GRAY, va="center", linespacing=1.45)
# ② 처리 흐름
a.text(56, 18.6, "② 창마다 특징을 뽑아 학습", fontsize=8.6, fontweight="bold", va="center")
steps = [("30초 창", "5초 이동"), ("특징 17개", "시간 7 · 주파수 7\n기준선 3"), ("SVM\n랜덤 포레스트", ""), ("균형 정확도", "두 부류 정확도\n의 평균")]
x = 56
for k, (t1, t2) in enumerate(steps):
    a.add_patch(FancyBboxPatch((x, 10.3), 9.0, 6.5, boxstyle="round,pad=0.2,rounding_size=0.7", fc="#f4f6f8", ec="#9aa7b4", lw=0.8))
    a.text(x + 4.5, 14.9 if t2 else 13.55, t1, ha="center", va="center", fontsize=7.8, fontweight="bold")
    if t2:
        a.text(x + 4.5, 12.0, t2, ha="center", va="center", fontsize=6.5, color=GRAY)
    if k:
        a.annotate("", (x - 0.25, 13.55), (x - 1.25, 13.55), arrowprops=dict(arrowstyle="-|>", lw=0.9, color=GRAY))
    x += 10.6
# ③ 문턱 하나와 비교
a.text(56, 7.6, "③ 가장 단순한 기준과 비교", fontsize=8.6, fontweight="bold", va="center")
a.add_patch(FancyBboxPatch((56, 0.6), 41.6, 5.6, boxstyle="round,pad=0.2,rounding_size=0.7", fc="#fbf4ea", ec="#d4b48a", lw=0.8))
a.text(76.8, 3.4, "특징 하나에 문턱 하나만 대도 똑같이 갈리면,\n모델은 식물 상태가 아니라 그 특징(손 접촉 · 기준선 · 잡음 크기)을 가른 것이다",
       ha="center", va="center", fontsize=7.2, color=INK)

# (나) 정상·물 공급 중단 결과
b = fig.add_axes([0.07, 0.15, 0.50, 0.34])
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
c = fig.add_axes([0.68, 0.15, 0.30, 0.34])
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
