# 그림: 조용한 창 vs 누를 때 계단이 생긴 창 — 분류기가 보는 입력(0.01–1 Hz, 30초 창, 앞 90초 문맥) 그대로
# 사용: python3 -I report/stim/fig_stim_spec.py 정상_5.csv 자극.csv 출력.png
import sys, os, numpy as np, pandas as pd, matplotlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from band_filter import analysis_filter, CONTEXT_SEC, HIGHCUT_HZ
from spectro_render import compute_spectrogram
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
plt.rcParams["font.family"] = "WenQuanYi Zen Hei"; plt.rcParams["axes.unicode_minus"] = False
FS, WIN = 250.0, 30.0
def window(path, end_sec):
    v = pd.read_csv(path).iloc[:, 1].values
    a, b = int((end_sec - WIN - CONTEXT_SEC) * FS), int(end_sec * FS)
    raw = v[a:b]
    seg, fs_a = analysis_filter(raw, FS, WIN)
    S, f, t = compute_spectrogram(seg, fs_a, high=HIGHCUT_HZ)
    r = raw[-int(WIN * FS):].reshape(-1, 25).mean(1) * 1000
    return r - r[:50].mean(), seg * 1000, S, f, t
cases = [("(가) 정상 1회차 — 조용한 30초 (300~330초)", sys.argv[1], 330.0),
         ("(나) 자극 1회차 — 누를 때 계단이 생긴 30초 (655~685초)", sys.argv[2], 685.0)]
data = [window(p, e) for _, p, e in cases]
vmin = min(d[2].min() for d in data); vmax = max(d[2].max() for d in data)
fig, ax = plt.subplots(3, 2, figsize=(9.4, 6.4), dpi=300, sharex="col",
                       gridspec_kw={"height_ratios": [1, 1, 1.2], "hspace": 0.35, "wspace": 0.18})
for c, ((title, _, _), (r, seg, S, f, t)) in enumerate(zip(cases, data)):
    tt = np.arange(len(r)) * 0.1; ts = np.arange(len(seg)) / 10.0
    ax[0, c].plot(tt, r, color="#2b6cb0", lw=0.8); ax[0, c].set_title(title, loc="left", fontsize=10)
    ax[1, c].plot(ts, seg, color="#2f855a", lw=0.8)
    im = ax[2, c].imshow(S, origin="lower", aspect="auto", extent=[0, WIN, f[0], f[-1]], vmin=vmin, vmax=vmax, cmap="viridis", interpolation="nearest")  # 분류기에 들어가는 그림처럼 창 전체에 펼침
    ax[2, c].set_xlabel("창 안의 시간 (초)")
    for k in range(2): ax[k, c].grid(alpha=0.3, lw=0.5)
    for k in range(3): ax[k, c].tick_params(labelsize=8)
for c, lim in enumerate([None, None]):
    y0 = min(ax[0, 0].get_ylim()[0], ax[0, 1].get_ylim()[0]); y1 = max(ax[0, 0].get_ylim()[1], ax[0, 1].get_ylim()[1])
    ax[0, c].set_ylim(y0, y1)
    y0 = min(ax[1, 0].get_ylim()[0], ax[1, 1].get_ylim()[0]); y1 = max(ax[1, 0].get_ylim()[1], ax[1, 1].get_ylim()[1])
    ax[1, c].set_ylim(y0, y1)
ax[0, 0].set_ylabel("원신호\n변화 (mV)", fontsize=9); ax[1, 0].set_ylabel("0.01–1 Hz\n통과 (mV)", fontsize=9)
ax[2, 0].set_ylabel("스펙트로그램\n주파수 (Hz)", fontsize=9)
cb = fig.colorbar(im, ax=ax[2, :], fraction=0.03, pad=0.01); cb.set_label("세기 (dB)", fontsize=8); cb.ax.tick_params(labelsize=7)
fig.savefig(sys.argv[3], bbox_inches="tight")
print("시간 칸", data[0][4].shape, "주파수", np.round(data[0][3], 2))
