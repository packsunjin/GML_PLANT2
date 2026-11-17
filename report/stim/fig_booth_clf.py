"""fig_booth_clf.py — 부스 포스터용 그림 (2026-11-17).
① FIG_BOOTH_CLF: 손 접촉 감지 분류기 평가(보고서 표5) 막대
② FIG_BOOTH_TOUCH: 보고서 그림4(FIG_TOUCH)와 같은 그림을 포스터 색(남색)으로 — 보고서 그림은 그대로 둔다.
숫자는 보고서 표5 그대로. 쓰는 법: python3 report/stim/fig_booth_clf.py → report/FIG_BOOTH_CLF.png
"""
import os, sys
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
cols = ["#1F4E79", "#1F4E79", "#8FAACC", "#8FAACC", "#9E9E9E"]
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

# ② 손 접촉 그림 색만 바꿔 다시 그림
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import figs
figs.GREEN, figs.BLUE = "#1F4E79", "#B5651D"
_save = figs.save
figs.save = lambda f, name: _save(f, "FIG_BOOTH_TOUCH.png" if name == "FIG_TOUCH.png" else name)
figs.fig_touch(); print("FIG_BOOTH_TOUCH.png")
