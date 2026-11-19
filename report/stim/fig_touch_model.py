"""fig_touch_model.py — 손 접촉 감지 모델이 파형 어디를 '접촉'으로 판정했는지 보여 주는 그림(보고서 그림6, 2026-11-19).
콘센트 기록: 앞 절반으로 학습한 모델이 뒤 절반을, 뒤 절반으로 학습한 모델이 앞 절반을 판정(자기가 배운 구간은 판정하지 않음).
보조배터리 기록: 콘센트 기록 전체로 학습한 모델이 판정. 창·특징·라벨은 touch1117_ml.py 와 같다.
쓰는 법: python3 report/stim/fig_touch_model.py <csv 폴더>
"""
import sys, os, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch
sys.path.insert(0, os.path.dirname(__file__))
import touch1117_ml as T   # series, windows, models
for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
INK, GRAY, BLUE, RED, YEL, HIT = "#1d1d1d", "#707070", "#1f77b4", "#c0504d", "#f2c94c", "#2e7d32"

def feats(t, m, starts):
    from scipy.signal import spectrogram
    from feature_extraction import extract_features
    X = []
    for s0 in starts:
        i0, i1 = int(round(s0 * T.FS)), int(round((s0 + 2) * T.FS))
        w = m[i0:i1] - np.median(m[int((s0 - 20) * T.FS):i0])
        f, tt, S = spectrogram(w, fs=T.FS, nperseg=16, noverlap=12)
        X.append(extract_features(w, 10 * np.log10(S + 1e-12), f, tt, fs=T.FS, raw_window=w, raw_fs=T.FS))
    return np.array(X)

ta, ma = T.series("자극_콘센트_20261117.csv"); sa = [189.28 + 30 * k for k in range(9)]
Xa, ya, ca = T.windows(ta, ma, sa, skip=(129.28, 159.28))
tb, mb = T.series("자극_배터리_20261117.csv"); sb = [129.75 + 30 * k for k in range(10)]
sta = np.arange(20.0, ta[-1] - 2.0, 0.5); stb = np.arange(20.0, tb[-1] - 2.0, 0.5)
Fa, Fb = feats(ta, ma, sta), feats(tb, mb, stb)
front = ca < 310
res = {}
for name in ("SVM", "랜덤 포레스트"):
    mf = T.models[name]().fit(Xa[front], ya[front]); mbk = T.models[name]().fit(Xa[~front], ya[~front])
    pa = np.where(sta < 310, mbk.predict(Fa), mf.predict(Fa))        # 배운 적 없는 쪽 모델이 판정
    pb = T.models[name]().fit(Xa, ya).predict(Fb)
    res[name] = (pa, pb)

def count(starts, pred, sigs):
    found = sum(any(pred[(starts >= s - 0.5) & (starts <= s + 6)]) for s in sigs)
    far = pred.copy()
    for s in list(sigs) + [129.28, 159.28]:
        far[(starts >= s - 2) & (starts <= s + 8)] = 0
    ev = int(np.sum(np.diff(np.r_[0, far]) == 1))
    return found, ev

fig = plt.figure(figsize=(7.4, 5.6), dpi=300)
# 맨 위: 모델이 하는 일 한 줄
a = fig.add_axes([0.0, 0.88, 1.0, 0.11]); a.set_xlim(0, 100); a.set_ylim(0, 10); a.axis("off")
steps = ["전압 기록", "2초씩 자르기", "특징 17개 계산", "모델(SVM · 랜덤 포레스트)", "접촉 / 비접촉"]
xs = [1, 21, 41, 61, 85]; ws = [15, 15, 15, 20, 14]
for x, w_, s in zip(xs, ws, steps):
    a.add_patch(FancyBboxPatch((x, 2.5), w_, 5, boxstyle="round,pad=0,rounding_size=1.2", fc="#eef2f6", ec="#9aa7b4", lw=0.8))
    a.text(x + w_ / 2, 5, s, ha="center", va="center", fontsize=8.2, fontweight="bold" if s == steps[-1] else None)
for x0, x1 in ((16, 21), (36, 41), (56, 61), (81, 85)):
    a.annotate("", (x1, 5), (x0 + 0.3, 5), arrowprops=dict(arrowstyle="-|>", lw=1, color=INK, mutation_scale=8))

def panel(y0, title, t, m, sigs, starts, key, col, note):
    ax = fig.add_axes([0.08, y0 + 0.13, 0.9, 0.2])
    for s in sigs: ax.axvspan(s, s + 2, color=YEL, alpha=0.6, lw=0)
    ax.plot(t, m - np.median(m), color=col, lw=0.5)
    ax.set_xlim(0, 600); ax.set_ylim(-40, 170); ax.set_ylabel("전압 (mV)"); ax.set_xticklabels([])
    ax.grid(lw=0.3, color="#e3e3e3"); ax.set_title(title, loc="left", fontsize=9.2, fontweight="bold")
    for k, name in enumerate(("SVM", "랜덤 포레스트")):
        pr = res[name][key]
        b = fig.add_axes([0.08, y0 + 0.075 - k * 0.04, 0.9, 0.032])
        b.set_xlim(0, 600); b.set_ylim(0, 1); b.set_yticks([])
        for s0, p in zip(starts, pr):
            if p: b.axvspan(s0, s0 + 2, color=HIT, lw=0)
        b.set_facecolor("#f4f4f4")
        for sp in b.spines.values(): sp.set_visible(False)
        found, fa = count(starts, pr, sigs)
        b.text(-8, 0.5, name, ha="right", va="center", fontsize=7.6)
        b.text(606, 0.5, f"찾음 {found}/{len(sigs)}  · 헛판정 {fa}번", ha="left", va="center", fontsize=7.6,
               color=HIT if found else GRAY, fontweight="bold")
        if k == 0: b.set_xticks([])
        else: b.set_xlabel("시간 (초)")
    ax.text(598, 160, note, ha="right", va="top", fontsize=7.6, color=GRAY)

panel(0.47, "(가) 콘센트 전원 — 모델이 처음 보는 구간을 판정", ta, ma, sa, sta, 0, RED, "")
panel(0.02, "(나) 보조배터리 전원 — 같은 모델로 판정", tb, mb, sb, stb, 1, BLUE, "")
fig.text(0.08, 0.865, "노란 띠 = 잎을 잡은 시각     초록 칸 = 모델이 '접촉'이라고 판정한 2초", fontsize=7.8, color=INK)
out = "report/보고서_그림_순서대로/11_그림6_모델_학습_평가.jpg"
fig.savefig(out, bbox_inches="tight", pad_inches=0.04, facecolor="white", pil_kwargs={"quality": 95})
print(out, {k: (count(sta, v[0], sa), count(stb, v[1], sb)) for k, v in res.items()})
