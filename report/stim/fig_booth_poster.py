"""부스 설명 포스터 그림(2026-11-17).
  FIG_BOOTH_SCREEN.png  화면 보는 법 — 실시간 전압·스펙트로그램(최근 30초)·오른쪽 끝 '모델 입력' 2초
  FIG_BOOTH_FLOW.png    원리 — 2초 신호 → 스펙트로그램 → SVM → 정상/자극
  FIG_BOOTH_STEP1~6.png 체험 단계 그림
신호는 실측 손 접촉 기록 data/plant/live_20260915_070020.csv(250 S/s, DC 결합)의 한 구간.
스펙트로그램은 src/booth.py 와 같은 계산(앞 20초 중앙값을 빼고 256표본 창, 0–62.5 Hz, dB).
쓰는 법(저장소 루트): python3 report/stim/fig_booth_poster.py
그림 글자에 U+2212 를 쓰지 않는다(한글 글꼴에 없음)."""
import os
import numpy as np
import pandas as pd
from scipy import signal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse, Polygon, Circle, FancyArrowPatch

for f in fm.findSystemFonts():
    if "NotoSansCJK" in f:
        fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["axes.unicode_minus"] = False

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "report")
FS, NPERSEG, FMAX = 250, 256, 62.5
BROWN, GREEN, RED, BLUE = "#905720", "#047857", "#b91c1c", "#1f77b4"
NORMAL_BG, STIM_BG = "#d1fae5", "#fee2e2"

v = pd.read_csv(os.path.join(ROOT, "data/plant/live_20260915_070020.csv"))["voltage_mV"].to_numpy()


def spec(x, base, hop):
    f, t, s = signal.spectrogram(x - np.median(base), fs=FS, nperseg=NPERSEG, noverlap=NPERSEG - hop,
                                 detrend=False, scaling="spectrum")
    keep = f <= FMAX + 1e-9
    return f[keep], t, np.maximum(10 * np.log10(s[keep] + 1e-30), -120)


def find_touch():
    """1초 중앙값이 100 mV 넘게 뛰는 첫 곳(손이 닿은 순간)."""
    m = np.array([np.median(v[i:i + FS]) for i in range(0, len(v) - FS, FS)])
    k = int(np.where(np.abs(np.diff(m)) > 100)[0][0])     # 첫 큰 계단(약 1263초, 115 mV)
    seg = v[k * FS:(k + 3) * FS]
    j = int(np.argmax(np.abs(np.diff(seg)) > 15))
    return k * FS + j


T0 = find_touch()
END = T0 + int(1.2 * FS)               # 손이 닿고 1.2초 뒤 — 오른쪽 끝 2초 안에 닿는 순간이 들어온다
X30 = v[END - 30 * FS:END]
BASE = v[END - 2 * FS - 20 * FS:END - 2 * FS]


def jet_ax(ax, f, t, db, x0=0):
    lo, hi = np.percentile(db[1:], [5, 99.5])
    ax.imshow(db, aspect="auto", origin="lower", cmap="jet", vmin=lo, vmax=hi, interpolation="bilinear",
              extent=[x0 + t[0], x0 + t[-1], f[0], f[-1]])


def badge(ax, x, y, n, size=20):
    ax.annotate(str(n), (x, y), xycoords="axes fraction", ha="center", va="center", fontsize=size, color="white",
                fontweight="bold", bbox=dict(boxstyle="circle,pad=0.3", fc=RED, ec="none"), zorder=10)


def fig_screen():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 11), gridspec_kw=dict(hspace=0.36))
    t = np.arange(len(X30)) / FS
    a1.plot(t, X30 - np.median(BASE), color=BLUE, lw=1.0)
    a1.set_xlim(0, 30); a1.grid(alpha=0.3)
    a1.set_ylabel("전압 (mV)", fontsize=20); a1.set_xlabel("시간 (초)", fontsize=20)
    a1.set_title("실시간 전압 (최근 30초)", fontsize=24, loc="left", fontweight="bold")
    a1.tick_params(labelsize=17)
    a1.axvspan(28, 30, color=RED, alpha=0.12)
    f, ts, db = spec(X30, X30, 32)
    jet_ax(a2, f, ts, db)
    a2.set_xlim(0, 30)
    a2.set_ylabel("주파수 (Hz)", fontsize=20); a2.set_xlabel("시간 (초)", fontsize=20)
    a2.set_title("실시간 스펙트로그램 (최근 30초)", fontsize=24, loc="left", fontweight="bold")
    a2.tick_params(labelsize=17)
    a2.add_patch(Rectangle((28, 0.5), 1.95, 61.5, fill=False, ec="white", lw=3, ls=(0, (4, 3))))
    a2.text(29, 63.5, "모델 입력 (2초)", color=RED, fontsize=22, fontweight="bold", ha="right", va="bottom")
    badge(a1, -0.07, 1.09, 1, 26); badge(a2, -0.07, 1.09, 2, 26); badge(a2, 0.66, 1.09, 3, 26)
    fig.savefig(os.path.join(OUT, "FIG_BOOTH_SCREEN.png"), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_flow():
    fig = plt.figure(figsize=(13, 4.2))
    x2 = X30[-2 * FS:]
    # ① 2초 신호
    a = fig.add_axes([0.02, 0.22, 0.22, 0.58])
    a.plot(np.arange(len(x2)) / FS, x2 - np.median(BASE), color=BLUE, lw=1.2)
    a.set_xticks([0, 1, 2]); a.set_yticks([]); a.tick_params(labelsize=15)
    a.set_xlabel("시간 (초)", fontsize=16)
    a.set_title("2초 신호", fontsize=22, fontweight="bold")
    # ② 스펙트로그램
    b = fig.add_axes([0.32, 0.22, 0.22, 0.58])
    f, t, db = spec(x2, BASE, 8)
    jet_ax(b, f, t, db)
    b.set_xticks([]); b.set_yticks([]); b.tick_params(labelsize=15)
    b.set_title("스펙트로그램", fontsize=22, fontweight="bold")
    # ③ SVM
    c = fig.add_axes([0.60, 0.1, 0.16, 0.8]); c.axis("off"); c.set_xlim(0, 1); c.set_ylim(0, 1)
    c.add_patch(FancyBboxPatch((0.08, 0.28), 0.84, 0.44, boxstyle="round,pad=0.04", fc=BROWN, ec="none"))
    c.text(0.5, 0.5, "SVM", color="white", fontsize=30, fontweight="bold", ha="center", va="center")
    c.text(0.5, 0.92, "학습·판정", fontsize=20, ha="center", va="center", color="#333")
    # ④ 정상/자극
    d = fig.add_axes([0.81, 0.1, 0.17, 0.8]); d.axis("off"); d.set_xlim(0, 1); d.set_ylim(0, 1)
    d.add_patch(FancyBboxPatch((0.08, 0.56), 0.84, 0.28, boxstyle="round,pad=0.03", fc=NORMAL_BG, ec=GREEN, lw=2))
    d.text(0.5, 0.70, "정상", color=GREEN, fontsize=24, fontweight="bold", ha="center", va="center")
    d.add_patch(FancyBboxPatch((0.08, 0.14), 0.84, 0.28, boxstyle="round,pad=0.03", fc=STIM_BG, ec=RED, lw=2))
    d.text(0.5, 0.28, "자극", color=RED, fontsize=24, fontweight="bold", ha="center", va="center")
    for x0, x1 in ((0.255, 0.305), (0.555, 0.61), (0.765, 0.815)):
        fig.add_artist(FancyArrowPatch((x0, 0.5), (x1, 0.5), transform=fig.transFigure, arrowstyle="-|>",
                                       mutation_scale=30, lw=3, color="#555"))
    fig.savefig(os.path.join(OUT, "FIG_BOOTH_FLOW.png"), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ── 단계 그림(정사각형) ──
def canvas():
    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.add_patch(FancyBboxPatch((0.3, 0.3), 9.4, 9.4, boxstyle="round,pad=0,rounding_size=1.0", fc="#f6ebdd", ec="none"))
    return fig, ax


def plant(ax, cx=5, base=1.2, scale=1.0):
    s = scale
    ax.add_patch(Polygon([[cx - 1.6 * s, base + 1.6 * s], [cx + 1.6 * s, base + 1.6 * s], [cx + 1.2 * s, base],
                          [cx - 1.2 * s, base]], fc="#2b7bb9", ec="none"))
    top = base + 6.3 * s
    ax.plot([cx, cx], [base + 1.6 * s, top], color="#2e7d32", lw=5 * s, solid_capstyle="round")
    for y, side in ((base + 3.4 * s, -1), (base + 4.6 * s, 1), (base + 5.6 * s, -1)):
        ax.add_patch(Ellipse((cx + side * 1.15 * s, y + 0.25 * s), 2.2 * s, 0.95 * s, angle=side * 25, fc="#43a047", ec="none"))
    ax.add_patch(Ellipse((cx, top + 0.3 * s), 1.2 * s, 0.9 * s, fc="#43a047", ec="none"))
    ax.add_patch(Circle((cx + 0.55 * s, base + 5.0 * s), 0.38 * s, fc="#e53935", ec="none"))   # 방울토마토
    # 은선 전극 두 가닥
    for yy in (base + 2.3 * s, base + 2.9 * s):
        ax.plot([cx, cx + 2.6 * s], [yy, yy - 0.4 * s], color="#9e9e9e", lw=2.2)
    return top


def hand(ax, x, y, s=1.0):
    ax.add_patch(FancyBboxPatch((x, y), 1.9 * s, 1.5 * s, boxstyle="round,pad=0.1,rounding_size=0.5", fc="#f2c29b", ec="#c98d63", lw=1.5))
    for i in range(4):
        ax.add_patch(FancyBboxPatch((x - 1.5 * s, y + 0.1 * s + i * 0.36 * s), 1.6 * s, 0.3 * s,
                                    boxstyle="round,pad=0,rounding_size=0.15", fc="#f2c29b", ec="#c98d63", lw=1.2))


def timer(ax, x, y, txt="8초", col=BROWN):
    ax.add_patch(Circle((x, y), 1.05, fc="white", ec=col, lw=3))
    ax.text(x, y, txt, fontsize=21, fontweight="bold", ha="center", va="center", color=col)


def save(fig, n):
    fig.savefig(os.path.join(OUT, f"FIG_BOOTH_STEP{n}.png"), dpi=110, facecolor="white")
    plt.close(fig)


def steps():
    # 1 학교 이름 입력
    fig, ax = canvas()
    ax.add_patch(FancyBboxPatch((1.2, 6.6), 7.6, 1.6, boxstyle="round,pad=0.1,rounding_size=0.3", fc="white", ec=BROWN, lw=2.5))
    ax.text(5, 7.4, "○○고등학교", fontsize=21, ha="center", va="center", color="#222")
    keys = ["ㅂㅈㄷㄱㅅ", "ㅁㄴㅇㄹㅎ", "ㅋㅌㅊㅍㅠ"]
    for r, row in enumerate(keys):
        for c, k in enumerate(row):
            x, y = 1.4 + c * 1.48, 4.6 - r * 1.4
            ax.add_patch(FancyBboxPatch((x, y), 1.2, 1.1, boxstyle="round,pad=0,rounding_size=0.2", fc="white", ec="#bbb"))
            ax.text(x + 0.6, y + 0.55, k, fontsize=15, ha="center", va="center")
    save(fig, 1)
    # 2 정상 — 손대지 않고 8초
    fig, ax = canvas()
    plant(ax, cx=4.0, base=1.0)
    timer(ax, 7.8, 7.9)
    ax.add_patch(Circle((7.6, 3.8), 1.2, fc="none", ec=RED, lw=4))
    hand(ax, 7.3, 3.1, 0.55)
    ax.plot([6.75, 8.45], [2.95, 4.65], color=RED, lw=4)
    save(fig, 2)
    # 3 자극 — 잎에 손 올리고 8초
    fig, ax = canvas()
    plant(ax, cx=4.0, base=1.0)
    timer(ax, 7.8, 7.9, col=RED)
    hand(ax, 6.0, 4.4, 0.9)
    save(fig, 3)
    # 4 모델 생성
    fig, ax = canvas()
    for i, (x, y) in enumerate([(2.0, 6.8), (2.0, 5.0), (2.0, 3.2), (5.0, 6.0), (5.0, 4.0)]):
        ax.add_patch(Circle((x, y), 0.5, fc=BROWN if i < 3 else "#c7a27c", ec="none"))
    for (x0, y0) in [(2.0, 6.8), (2.0, 5.0), (2.0, 3.2)]:
        for (x1, y1) in [(5.0, 6.0), (5.0, 4.0)]:
            ax.plot([x0, x1], [y0, y1], color="#c7a27c", lw=1.5, zorder=0)
    ax.add_patch(Circle((7.8, 5.0), 1.3, fc=GREEN, ec="none"))
    ax.plot([7.2, 7.7, 8.5], [5.0, 4.4, 5.7], color="white", lw=5, solid_capstyle="round")
    for y in (6.0, 4.0):
        ax.plot([5.0, 6.5], [y, 5.0], color="#c7a27c", lw=1.5, zorder=0)
    save(fig, 4)
    # 5 모델 선택하기
    fig, ax = canvas()
    for i, (name, sel) in enumerate([("○○고", True), ("△△중", False), ("□□고", False)]):
        y = 7.0 - i * 2.2
        ax.add_patch(FancyBboxPatch((1.0, y), 8.0, 1.6, boxstyle="round,pad=0,rounding_size=0.3",
                                    fc="white", ec=BROWN if sel else "#ccc", lw=3 if sel else 1.5))
        ax.text(1.6, y + 0.8, name, fontsize=19, va="center")
        ax.add_patch(FancyBboxPatch((6.2, y + 0.3), 2.4, 1.0, boxstyle="round,pad=0,rounding_size=0.25",
                                    fc=BROWN if sel else "#eee", ec="none"))
        ax.text(7.4, y + 0.8, "선택", fontsize=15, ha="center", va="center", color="white" if sel else "#666")
    save(fig, 5)
    # 6 실시간 판정
    fig, ax = canvas()
    ax.add_patch(FancyBboxPatch((1.0, 2.6), 8.0, 5.8, boxstyle="round,pad=0,rounding_size=0.4", fc="#1f2937", ec="none"))
    ax.add_patch(Rectangle((4.2, 1.4), 1.6, 1.2, fc="#555"))
    ax.add_patch(FancyBboxPatch((1.8, 5.5), 6.4, 2.0, boxstyle="round,pad=0,rounding_size=0.3", fc=STIM_BG, ec=RED, lw=2))
    ax.text(5, 6.5, "자극", fontsize=30, fontweight="bold", ha="center", va="center", color=RED)
    tt = np.linspace(1.8, 8.2, 80)
    ax.plot(tt, 4.0 + 0.25 * np.sin(tt * 5) + np.where(tt > 6.5, 0.9, 0), color="#4fc3f7", lw=2.5)
    save(fig, 6)


if __name__ == "__main__":
    print("손 닿은 표본", T0, f"({T0 / FS:.1f} 초)")
    fig_screen(); fig_flow(); steps()
    print("→ report/FIG_BOOTH_*.png")
