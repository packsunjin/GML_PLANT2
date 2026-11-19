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

fig = plt.figure(figsize=(10, 6.2), dpi=300)
# (가) 평가 방식 — 실제 콘센트 기록 위에 학습/평가 구간을 칠해 1회·2회를 보여 줌
import sys as _s; _s.path.insert(0, os.path.dirname(__file__))
import touch1117_ml as T
ta, ma = T.series("자극_콘센트_20261117.csv"); za = np.median(ma)
sa = [189.28 + 30 * k for k in range(9)]
TRC, TEC, YEL = "#cfe0f3", "#fde3cf", "#e0a800"
fig.text(0.01, 0.985, "(가) 학습·평가 방식", fontsize=10, fontweight="bold", va="top")
for r, (lab, tr, te) in enumerate((("1회", (0, 310), (310, 600)), ("2회", (310, 600), (0, 310)))):
    a = fig.add_axes([0.07, 0.80 - r * 0.13, 0.55, 0.10])
    a.axvspan(*tr, color=TRC, lw=0); a.axvspan(*te, color=TEC, lw=0)
    for s_ in sa: a.axvline(s_, color=YEL, lw=0.9)
    a.plot(ta, ma - za, color=INK, lw=0.35)
    a.set_xlim(0, 600); a.set_ylim(-40, 175); a.set_yticks([]); a.set_xticks([] if r == 0 else [0, 100, 200, 300, 400, 500, 600])
    if r == 1: a.set_xlabel("콘센트 전원 기록 (초)", fontsize=8)
    a.text(-12, 65, lab, ha="right", va="center", fontsize=9.5, fontweight="bold")
    a.text(sum(tr) / 2, 150, "학습", ha="center", va="top", fontsize=8.5, color="#2b5d8a", fontweight="bold")
    a.text(sum(te) / 2, 150, "평가", ha="center", va="top", fontsize=8.5, color="#b5651d", fontweight="bold")
p_ = fig.add_axes([0.65, 0.66, 0.34, 0.27]); p_.axis("off"); p_.set_xlim(0, 10); p_.set_ylim(0, 10)
chips = ["2초씩 자르기 (0.5초씩 밀며)", "창마다 특징 17개 계산", "SVM · 랜덤 포레스트 학습", "평가 구간 창을 접촉 / 비접촉 판정"]
for k, t_ in enumerate(chips):
    y = 9.0 - k * 2.5
    p_.add_patch(FancyBboxPatch((0.3, y - 0.8), 9.4, 1.6, boxstyle="round,pad=0,rounding_size=0.4", fc="#eef2f6", ec="#9aa7b4", lw=0.7))
    p_.text(5, y, t_, ha="center", va="center", fontsize=7.8)
    if k < 3: p_.annotate("", (5, y - 1.7), (5, y - 0.85), arrowprops=dict(arrowstyle="-|>", lw=0.9, color=INK, mutation_scale=7))
fig.text(0.07, 0.575, "노란 선 = 잎을 잡은 시각     파란 바탕 = 학습에 쓴 구간     주황 바탕 = 평가에 쓴 구간(모델이 처음 보는 구간)", fontsize=7.4, color=GRAY)

# (나) 콘센트 기록 평가
b = fig.add_axes([0.07, 0.10, 0.38, 0.40])
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
c = fig.add_axes([0.60, 0.10, 0.38, 0.40])
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
