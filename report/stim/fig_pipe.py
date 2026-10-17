# 그림: CSV 에서 분류기 입력을 만드는 과정 — 어느 구간을 잘라 무엇으로 바꿔 학습에 썼는지
#   (가) 자극 1회차 30분 기록에서 창 하나(30초)와 그 앞 문맥(90초), 창마다 붙인 라벨
#   (나) 그 창을 0.01–1 Hz 로 거른 신호  (다) 스펙트로그램(시간 6칸 × 주파수 13칸)  (라) 특징 14개 중 일부 → 모델
# 사용(저장소 루트): python3 report/stim/fig_pipe.py <ml_touch 작업폴더> report/FIG_PIPE.png
import sys, os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import ml_touch as M
from band_filter import analysis_filter, CONTEXT_SEC, HIGHCUT_HZ
from spectro_render import compute_spectrogram
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
fm.fontManager.addfont("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
plt.rcParams["font.family"] = "WenQuanYi Zen Hei"; plt.rcParams["axes.unicode_minus"] = False
work, out = sys.argv[1], sys.argv[2]
FS, WIN, A = 250.0, 30.0, 655.0          # 보기로 든 창: 655~685초(누를 때 계단이 생긴 창)
v = pd.read_csv(os.path.join(M.RAW, "자극.csv")).iloc[:, 1].values
s01 = v[: len(v) // 25 * 25].reshape(-1, 25).mean(1) * 1000          # 0.1초 평균(mV)
t1, _ = M.touch_times()
F = pd.read_csv(os.path.join(work, "정상_11.csv.feat.csv")); F["y"] = M.label(F, t1)
raw = v[int((A - CONTEXT_SEC) * FS): int((A + WIN) * FS)]
seg, fs_a = analysis_filter(raw, FS, WIN)
S, f, _ = compute_spectrogram(seg, fs_a, high=HIGHCUT_HZ)
row = F[F["start_s"] == A].iloc[0]

fig = plt.figure(figsize=(9.4, 5.6), dpi=300)
gs = fig.add_gridspec(2, 3, height_ratios=[1.15, 1], hspace=0.55, wspace=0.32)
ax = fig.add_subplot(gs[0, :])
tt = np.arange(len(s01)) / 600
ax.plot(tt, s01, color="#2b6cb0", lw=0.5)
ax.axvspan((A - CONTEXT_SEC) / 60, A / 60, color="#cbd5e0", alpha=0.7, lw=0)
ax.axvspan(A / 60, (A + WIN) / 60, color="#f6ad55", alpha=0.8, lw=0)
for x in t1: ax.axvline(x / 60, color="#c05621", ls="--", lw=0.6)
lo, hi = ax.get_ylim(); band = (hi - lo) * 0.06
for st, y in zip(F["start_s"], F["y"]):      # 창마다 붙인 라벨(창 시작 위치에 한 칸)
    ax.add_patch(plt.Rectangle((st / 60, lo - band * 1.4), 5 / 60, band, color="#e53e3e" if y else "#a0aec0", lw=0))
ax.set_ylim(lo - band * 1.6, hi); ax.set_xlim(0, 30)
ax.set_title("(가) 자극 1회차 30분 기록에서 30초 창을 5초씩 옮기며 자름 — 아래 띠는 창 시작 위치마다 붙인 라벨", loc="left", fontsize=10)
ax.set_xlabel("수집 시간 (분)"); ax.set_ylabel("전위 (mV)")
ax.legend(handles=[Patch(color="#f6ad55", label="보기로 든 창 (655~685초)"),
                   Patch(color="#cbd5e0", label="필터 문맥 (창 앞 90초)"),
                   Line2D([], [], color="#c05621", ls="--", label="누른 시각"),
                   Patch(color="#e53e3e", label="라벨 자극 (누른 시각이 든 창)"),
                   Patch(color="#a0aec0", label="라벨 정상")],
          loc="upper left", ncol=3, fontsize=7.5, frameon=True)
ax = fig.add_subplot(gs[1, 0])
ax.plot(np.arange(len(seg)) / fs_a, seg * 1000, color="#2f855a", lw=0.9)
ax.set_title("(나) 0.01–1 Hz 로 거른 창", loc="left", fontsize=10)
ax.set_xlabel("창 안의 시간 (초)"); ax.set_ylabel("mV"); ax.set_xlim(0, WIN)
ax = fig.add_subplot(gs[1, 1])
ax.imshow(S, origin="lower", aspect="auto", extent=[0, WIN, f[0], f[-1]], cmap="viridis", interpolation="nearest")
ax.set_title("(다) 스펙트로그램 6×13칸", loc="left", fontsize=10)
ax.set_xlabel("창 안의 시간 (초)"); ax.set_ylabel("주파수 (Hz)")
ax = fig.add_subplot(gs[1, 2]); ax.axis("off")
ax.set_title("(라) 특징 14개 중 일부 → 모델", loc="left", fontsize=10)
lines = [("최대–최소 폭", row["peak_to_peak"] * 1000, "mV"), ("실효값", row["rms"] * 1000, "mV"),
         ("표준편차", row["std"] * 1000, "mV"), ("영점 교차율", row["zero_crossing_rate"], ""),
         ("스펙트럼 중심", row["spectral_centroid"], "Hz"), ("첨도", row["kurtosis"], "")]
txt = "\n".join(f"{n:<8s} {val:8.2f} {u}" for n, val, u in lines)
ax.text(0.0, 0.95, txt + "\n  …(나머지 8개)", va="top", ha="left", fontsize=8.5, family="WenQuanYi Zen Hei",
        transform=ax.transAxes, bbox=dict(boxstyle="round", fc="#f7fafc", ec="#a0aec0"))
ax.text(0.0, 0.08, "→ 랜덤 포레스트·SVM\n→ 이 창의 자극 확률", va="bottom", ha="left", fontsize=9,
        color="#2b6cb0", transform=ax.transAxes)
fig.savefig(out, bbox_inches="tight")
print("창", int(len(F)), "자극 라벨", int(F["y"].sum()), "보기 창 라벨", int(row["y"]))
