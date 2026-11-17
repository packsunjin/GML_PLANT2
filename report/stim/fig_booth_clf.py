"""fig_booth_clf.py — 부스 포스터용: 손 접촉 감지 분류기 평가(보고서 표5)를 막대로 (2026-11-17).
숫자는 보고서 표5 그대로. 쓰는 법: python3 report/stim/fig_booth_clf.py → report/FIG_BOOTH_CLF.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

fm.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False

rows = [("SVM · 특징 17개", 23), ("SVM · 스펙트로그램", 22), ("랜덤 포레스트 · 특징 17개", 17),
        ("랜덤 포레스트 · 스펙트로그램", 12), ("문턱 하나 · 특징 1개", 23)]
fig, ax = plt.subplots(figsize=(8, 3.6), dpi=300)
y = range(len(rows))[::-1]
cols = ["#2E7D4F", "#2E7D4F", "#7FB394", "#7FB394", "#9E9E9E"]
ax.barh(list(y), [r[1] for r in rows], color=cols, height=0.62)
for yi, (name, n) in zip(y, rows):
    ax.text(n + 0.3, yi, f"{n} / 23", va="center", fontsize=12)
ax.set_yticks(list(y)); ax.set_yticklabels([r[0] for r in rows], fontsize=12)
ax.set_xlim(0, 27); ax.set_xlabel("평가 창의 접촉 23개 중 찾은 수", fontsize=12)
ax.axvline(23, color="#999", lw=0.8, ls="--")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", color="#e5e5e5", lw=0.6); ax.set_axisbelow(True)
fig.tight_layout()
out = os.path.join(os.path.dirname(__file__), "..", "FIG_BOOTH_CLF.png")
fig.savefig(out); print(out)
