"""포스터 그림1 — 식물 전기신호의 주파수 위치와 필터 통과대역(2026-11-12).
보고서 그림1(report/figs.py fig_band)과 같은 값을 포스터에서 읽히게 크게 다시 그린다.
'기존 전처리 0.5–20 Hz' 줄은 포스터에서 뺐다(본문에 안 나옴).
쓰는 법(저장소 루트): python3 report/stim/fig_poster_band.py report/FIG_POSTER_BAND.png
그림 글자에 U+2212 를 쓰지 않는다."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.patches import Rectangle
from matplotlib import font_manager as fm

for f in fm.findSystemFonts():
    if "NotoSansCJK" in f:
        fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False
BROWN, GREEN, RED, BLUE, GREY = "#905720", "#2e7d4f", "#c0392b", "#2c6fb0", "#666666"

ROWS = [  # (이름, 시작 Hz, 끝 Hz, 색, 채움)
    ("수분 스트레스 (수 시간~수 일)", 1e-5, 1e-4, BROWN, True),
    ("변동전위 (손상, 최대 수십 분)", 3e-4, 3e-3, BROWN, True),
    ("활동전위 (수십 초)", 1e-2, 1e-1, GREEN, True),
    ("활동전위, 접촉 자극 (약 10초)", 5e-2, 2e-1, GREEN, True),
    ("상용전원 잡음 60 Hz", 57, 63, RED, True),
    (None,),
    ("본 연구 분석 대역 (0.01–1 Hz)", 1e-2, 1, GREEN, False),
    ("AD8232 통과대역 (0.5–40 Hz)", 0.5, 40, BLUE, False),
]

fig, ax = plt.subplots(figsize=(12, 5.2))
ax.set_xscale("log"); ax.set_xlim(1e-5, 2e3)
n = len(ROWS)
ax.set_ylim(-0.6, n - 0.4); ax.invert_yaxis()
labels = []
for i, r in enumerate(ROWS):
    if r[0] is None:
        ax.axhline(i, color="#cccccc", lw=1.2, ls="--")
        labels.append("")
        continue
    name, f0, f1, c, fill = r
    ax.add_patch(Rectangle((f0, i - 0.32), f1 - f0, 0.64, fc=c if fill else "none", ec=c,
                           lw=2.6 if not fill else 1.2, alpha=0.85 if fill else 1))
    labels.append(name)
ax.set_yticks(range(n)); ax.set_yticklabels(labels, fontsize=15)
ax.tick_params(axis="y", length=0)
ax.xaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10, numticks=12))
ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: (f"{v:.6f}".rstrip("0").rstrip(".") if v < 1 else f"{v:g}")))
ax.tick_params(axis="x", labelsize=13)
ax.set_xlabel("주파수 (Hz, 로그 눈금) — T초 동안 이어지는 신호는 약 1/T Hz", fontsize=14)
for s in ("left", "right", "top"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", color="#e4e4e4", lw=0.8); ax.set_axisbelow(True)
ax.annotate("AD8232는 0.5 Hz 아래를 지워\n활동전위·수분 신호를 볼 수 없다", xy=(0.5, 7), xytext=(1.3e-5, 6.75),
            fontsize=14, color=BLUE, fontweight="bold", va="center", ha="left",
            arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.8))
fig.tight_layout()
fig.savefig(sys.argv[1], dpi=300)
print("saved", sys.argv[1])
