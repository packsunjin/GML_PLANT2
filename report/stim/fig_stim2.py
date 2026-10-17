# 그림7: 자극 2회차(살짝 댐)와 분류기 입력·판정
#   (가) 자극 2회차 — 댄 시각에 맞춰 9번 겹침(그림6(다)와 같은 세로 범위)
#   (나)(다) 분류기 입력 스펙트로그램 — 조용한 창 vs 누를 때 계단이 생긴 창
#   (라)(마) 분류기의 창별 자극 확률 — 회차를 바꿔 학습·평가(ml_touch.py 와 같은 설정)
# 사용(저장소 루트): python3 report/stim/fig_stim2.py <ml_touch 작업폴더> report/FIG_STIM2.png
import sys, os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import ml_touch as M
from band_filter import analysis_filter, CONTEXT_SEC, HIGHCUT_HZ
from spectro_render import compute_spectrogram
from sklearn.ensemble import RandomForestClassifier
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
fm.fontManager.addfont("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
plt.rcParams["font.family"] = "WenQuanYi Zen Hei"; plt.rcParams["axes.unicode_minus"] = False
work, out = sys.argv[1], sys.argv[2]
FS, WIN = 250.0, 30.0

def load01(p):  # 0.1초 평균, mV
    v = pd.read_csv(p).iloc[:, 1].values
    return v[: len(v) // 25 * 25].reshape(-1, 25).mean(1) * 1000

def spec(path, end_sec):
    v = pd.read_csv(path).iloc[:, 1].values
    raw = v[int((end_sec - WIN - CONTEXT_SEC) * FS): int(end_sec * FS)]
    seg, fs_a = analysis_filter(raw, FS, WIN)
    return compute_spectrogram(seg, fs_a, high=HIGHCUT_HZ)

# 창별 확률(ml_touch 의 평가 A·B 와 같은 학습)
t1, t2 = M.touch_times()
F = {k: pd.read_csv(os.path.join(work, n + ".feat.csv")) for k, n in
     [("자극1", "정상_11.csv"), ("자극2", "정상_12.csv"), ("정상1", "정상_13.csv"), ("정상밤샘", "정상_14.csv")]}
F["자극1"]["y"] = M.label(F["자극1"], t1); F["자극2"]["y"] = M.label(F["자극2"], t2)
F["정상1"]["y"] = 0; F["정상밤샘"]["y"] = 0
feats = [c for c in M.FEATURE_NAMES if c not in M.SLOW]
def rf(train):
    T = pd.concat([F[k] for k in train])
    return RandomForestClassifier(n_estimators=300, class_weight="balanced", min_samples_leaf=2,
                                  random_state=0, n_jobs=-1).fit(T[feats], T["y"])
p1 = rf(["자극2", "정상밤샘"]).predict_proba(F["자극1"][feats])[:, 1]
p2 = rf(["자극1", "정상1"]).predict_proba(F["자극2"][feats])[:, 1]

raw = os.path.join(M.RAW)
a2 = load01(os.path.join(raw, "자극_2.csv"))
S0, f, _ = spec(os.path.join(raw, "정상_5.csv"), 330.0)
S1, _, _ = spec(os.path.join(raw, "자극.csv"), 685.0)

fig = plt.figure(figsize=(9.4, 9.6), dpi=300)
gs = fig.add_gridspec(4, 2, height_ratios=[1.15, 1, 0.9, 0.9], hspace=0.62, wspace=0.18)
ax = fig.add_subplot(gs[0, :]); tt = np.arange(-200, 1200) / 10
for p in t2[:9]:
    i = int(round(p * 10)); seg = a2[i - 200:i + 1200] - np.median(a2[i - 300:i - 100])
    ax.plot(tt, seg, color="#a0aec0", lw=0.7)
ax.axvline(0, color="k", lw=0.8); ax.axvspan(-2.5, 2.5, color="#fbd38d", alpha=0.5, lw=0)
ax.set_ylim(-36, 30); ax.set_xlim(-20, 120)
ax.set_title("(가) 자극 2회차(살짝 댐) — 댄 시각을 0초에 맞춰 9번을 겹쳐 그림 (세로 범위는 그림6(다)와 같음)", loc="left", fontsize=10)
ax.set_xlabel("댄 시각 뒤 시간 (초)"); ax.set_ylabel("변화 (mV)")
ax.legend(handles=[Line2D([], [], color="#a0aec0", lw=1.2, label="댄 뒤 변화 (9번)"),
                   matplotlib.patches.Patch(color="#fbd38d", alpha=0.6, label="댄 시각의 불확실 구간(±2.5초)")],
          loc="lower center", ncol=2, fontsize=8, frameon=True)
vmin, vmax = min(S0.min(), S1.min()), max(S0.max(), S1.max())
for c, (S, ttl) in enumerate([(S0, "(나) 분류기 입력 — 정상 1회차의 조용한 30초"),
                              (S1, "(다) 분류기 입력 — 자극 1회차의 계단이 든 30초")]):
    ax = fig.add_subplot(gs[1, c])
    im = ax.imshow(S, origin="lower", aspect="auto", extent=[0, WIN, f[0], f[-1]],
                   vmin=vmin, vmax=vmax, cmap="viridis", interpolation="nearest")
    ax.set_title(ttl, loc="left", fontsize=9.5); ax.set_xlabel("창 안의 시간 (초)")
    if c == 0: ax.set_ylabel("주파수 (Hz)")
cb = fig.colorbar(im, ax=fig.axes[-2:], fraction=0.03, pad=0.01); cb.set_label("세기 (dB)", fontsize=8)
for r, (k, p, tt_, ttl) in enumerate([
        ("자극1", p1, t1, "(라) 자극 1회차의 창별 자극 확률 — 자극 2회차·정상 밤샘으로 학습"),
        ("자극2", p2, t2, "(마) 자극 2회차의 창별 자극 확률 — 자극 1회차·정상 1회차로 학습")]):
    ax = fig.add_subplot(gs[2 + r, :]); c = (F[k]["start_s"].to_numpy() + WIN / 2) / 60
    ax.plot(c, p, color="#2b6cb0", lw=1.0)
    for x in tt_: ax.axvline(x / 60, color="#c05621", ls="--", lw=0.7)
    ax.axhline(0.5, color="0.4", lw=0.6, ls=":"); ax.set_ylim(-0.03, 1.03); ax.set_xlim(0, 30)
    ax.set_title(ttl, loc="left", fontsize=10); ax.set_ylabel("자극 확률")
    if r == 1: ax.set_xlabel("수집 시간 (분)")
    ax.legend(handles=[Line2D([], [], color="#2b6cb0", lw=1.2, label="30초 창의 자극 확률(창 가운데에 표시)"),
                       Line2D([], [], color="#c05621", ls="--", lw=1, label="누른(댄) 시각"),
                       Line2D([], [], color="0.4", ls=":", lw=1, label="판정 기준 0.5")],
              loc="upper right", fontsize=7.5, ncol=3, frameon=True)
for ax in fig.axes:
    ax.tick_params(labelsize=8)
fig.savefig(out, bbox_inches="tight")
# 2회차 겹침 구간의 최대 변화(본문 숫자 확인용)
mx = [np.abs(a2[int(p*10):int(p*10)+300] - np.median(a2[int(p*10)-300:int(p*10)-100])).max() for p in t2[:9]]
print("2회차 댄 뒤 30초 최대 |변화| mV:", np.round(mx, 1))
