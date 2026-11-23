"""fig_poster_spec.py — 포스터용: 11-17 손 접촉 기록의 전압과 스펙트로그램(콘센트 · 보조배터리, 같은 60초 구간).
스펙트로그램은 부스와 같은 256표본 창(0–62.5 Hz, 0.98 Hz 칸), 보기용 이동 32표본, jet 색. 노란 띠 = 잎을 잡은 시각.
쓰는 법: TOUCH_DIR=data/faraday python3 report/stim/fig_poster_spec.py → report/poster_fig/P_스펙트로그램.jpg"""
import os
import numpy as np, pandas as pd
from scipy.signal import stft
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 8.5})
D = os.environ.get("TOUCH_DIR", "data/faraday"); FS = 250.0
rows = [("콘센트 전원", "자극_콘센트_20261117.csv", 189.28, "#c0504d"), ("보조배터리 전원", "자극_배터리_20261117.csv", 189.75, "#1f77b4")]
fig, axs = plt.subplots(2, 2, figsize=(7.4, 3.6), dpi=300, gridspec_kw={"height_ratios": [1, 1.6], "hspace": 0.12, "wspace": 0.08})
specs = []
for c, (name, fn, s_first, col) in enumerate(rows):
    d = pd.read_csv(os.path.join(D, fn)); t = d.timestamp_sec.values; v = d.voltage.values * 1000
    t0 = s_first - 10; k = (t >= t0) & (t < t0 + 70); tt = t[k] - t0; vv = v[k] - np.median(v[k])  # 스펙트로그램은 원신호 250 S/s
    sig = [s_first + 30 * j - t0 for j in range(3)]
    a = axs[0, c]
    for s in sig: a.axvspan(s, s + 2, color="#f2c94c", alpha=0.6, lw=0)
    b_ = np.floor(tt / 0.1).astype(int); n_ = b_.max() + 1
    mm = np.bincount(b_, vv, n_) / np.maximum(np.bincount(b_, None, n_), 1)   # 전압은 0.1초 평균(원신호는 60 Hz 가 커서 칠해짐)
    a.plot(np.arange(n_) * 0.1 + 0.05, mm - np.median(mm), color=col, lw=0.6); a.set_xlim(0, 70); a.set_ylim(-30, 170); a.set_xticklabels([])
    a.set_title(name, fontsize=9.5, fontweight="bold", loc="left")
    if c == 0: a.set_ylabel("전압 (mV)")
    else: a.set_yticklabels([])
    f, ts, Z = stft(vv, fs=FS, nperseg=256, noverlap=224, boundary=None, padded=False)
    specs.append((ts, f, 20 * np.log10(np.abs(Z) + 1e-6), sig))
vals = np.concatenate([s[2][1:66].ravel() for s in specs]); lo, hi = np.percentile(vals, [5, 99.5])
for c, (ts, f, S, sig) in enumerate(specs):
    a = axs[1, c]
    im = a.imshow(S, origin="lower", aspect="auto", extent=[ts[0], ts[-1], f[0], f[-1]], cmap="jet", vmin=lo, vmax=hi, interpolation="bilinear")
    for s in sig: a.axvline(s, color="white", lw=0.6, ls="--")
    a.set_xlim(0, 70); a.set_ylim(0, 62.5); a.set_xlabel("시간 (초)")
    if c == 0: a.set_ylabel("주파수 (Hz)")
    else: a.set_yticklabels([])
fig.savefig("report/poster_fig/P_스펙트로그램.jpg", facecolor="white", bbox_inches="tight", pad_inches=0.03, pil_kwargs={"quality": 95})
print("ok")
