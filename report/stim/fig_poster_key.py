"""포스터용 핵심 그림 — 측정을 제한한 것은 어디인가(2026-11-12).
(가) 표류: 회로만 30분 / 점퍼선 핀 전극 60분 / 은선 전극 60분 (예비 1·2단계, 본 실험 ①)
(나) 60 Hz 상용전원 성분: 상자 밖·콘센트 / 상자 안·콘센트 / 상자 안·보조배터리 (본 실험 ②, 2026-11-04)
숫자는 보고서 Ⅳ장(표4, 2·3절)과 같다. 크기 차이가 수천 배라 가로축은 로그.
쓰는 법(저장소 루트): python3 report/stim/fig_poster_key.py report/FIG_POSTER_KEY.png
그림 글자에 U+2212 를 쓰지 않는다(글꼴에 없음) — 표류 부호는 빼고 크기만 그린다."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib import font_manager as fm

for f in fm.findSystemFonts():
    if "NotoSansCJK" in f:
        fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False

BROWN, GREY, GREEN = "#905720", "#b9b2a8", "#2e7d4f"
fig, axes = plt.subplots(1, 2, figsize=(12, 4.3))

def panel(ax, title, rows, xlim, unit):
    labels = [r[0] for r in rows][::-1]
    vals = [r[1] for r in rows][::-1]
    cols = [r[3] for r in rows][::-1]
    ax.barh(range(len(rows)), vals, color=cols, height=0.62)
    ax.set_xscale("log"); ax.set_xlim(*xlim)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels(labels, fontsize=15)
    for i, r in enumerate(rows[::-1]):
        ax.text(r[1] * 1.35, i, r[2], va="center", ha="left", fontsize=16, fontweight="bold", color="#222222")
    ax.set_xlabel(unit + " (로그 눈금)", fontsize=13)
    ax.set_title(title, loc="left", fontsize=17, fontweight="bold", pad=10)
    ax.tick_params(axis="x", labelsize=12)
    ax.xaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10, numticks=12))
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="x", which="major", color="#e4e4e4", lw=0.8); ax.set_axisbelow(True)

panel(axes[0], "(가) 기준선 표류 — 한계는 전극",
      [("회로만 (30분)", 0.0003, "0.0003 mV", GREY),
       ("점퍼선 핀 전극 (60분)", 59.20, "59.20 mV", BROWN),
       ("은선 전극 (60분)", 0.02, "0.02 mV", GREEN)],
      (0.0001, 3000), "표류 크기 (mV)")
panel(axes[1], "(나) 60 Hz 잡음 — 차폐·배터리로 감소",
      [("상자 밖 · 콘센트", 0.080, "0.080 mV", BROWN),
       ("상자 안 · 콘센트", 0.003, "0.003 mV (약 1/27)", GREY),
       ("상자 안 · 보조배터리", 0.0015, "0.001~0.002 mV", GREEN)],
      (0.0005, 3), "60 Hz 성분 진폭 (mV)")
fig.tight_layout(w_pad=3)
fig.savefig(sys.argv[1], dpi=300)
print("saved", sys.argv[1])
