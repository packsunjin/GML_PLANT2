"""fig_noise5.py — 같은 화분·은선 전극 긴 기록 다섯 개의 잡음을 같은 길이(처음 5.9시간 = 정상_6 길이)로 비교 (2026-11-23, 그림4·포스터 그림5).
계산은 newplant_stats.py 와 같다: 2분마다 0.01–1 Hz 실효값(25개 평균 → 10 S/s, 4차 버터워스 앞뒤로), 60 Hz 진폭(Hann 창 FFT 59.5–60.5 Hz 최대).
자료(main): data/faraday/새식물_적응_20261104.csv.gz, data/ds/stim/raw/정상_6.csv.gz, data/ds/stim/raw/수분부족.csv.gz,
data/faraday/정상_7_20261110.csv.gz, data/faraday/수분부족_2_20261113_part1.csv.gz(처음 5.9시간은 part1 안에 있음).
쓰는 법(저장소 루트): DATA_ROOT=<main 체크아웃> python3 report/stim/fig_noise5.py → report/stim/noise5.json, 그림 09
"""
import os, json, sys
import numpy as np, pandas as pd
from scipy import signal
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
H = os.path.dirname(__file__); R = os.environ.get("DATA_ROOT", os.path.join(H, "..", ".."))
FS, WIN, L = 250, 120, 21165.0
RUNS = [("11-04 21:04 꽂은 직후", "data/faraday/새식물_적응_20261104.csv.gz", "#9a9a9a"),
        ("11-05 22:42 정상", "data/ds/stim/raw/정상_6.csv.gz", "#1f77b4"),
        ("11-09 17:44 물 공급 중단", "data/ds/stim/raw/수분부족.csv.gz", "#c0504d"),
        ("11-10 21:04 정상(다시 꽂은 뒤)", "data/faraday/정상_7_20261110.csv.gz", "#2ca02c"),
        ("11-13 20:57 물 공급 중단(다른 줄기)", "data/faraday/수분부족_2_20261113_part1.csv.gz", "#e08a4b")]

def stats(fn):
    p = fn if os.path.exists(fn) else os.path.join(R, fn)
    d = pd.read_csv(p, usecols=["timestamp_sec", "voltage"], nrows=int(L * FS) + 2000)
    t = d.timestamp_sec.to_numpy(); v = d.voltage.to_numpy() * 1000
    k = t < L; t, v = t[k], v[k]
    m = len(v) // 25 * 25
    v10 = v[:m].reshape(-1, 25).mean(1); t10 = t[:m].reshape(-1, 25).mean(1)
    b, a = signal.butter(4, [0.01, 1], btype="band", fs=10); f10 = signal.filtfilt(b, a, v10)
    rows = []
    for j in range(int(L // WIN)):
        i0, i1 = np.searchsorted(t, [j * WIN, (j + 1) * WIN])
        if i1 - i0 < FS * 110: continue
        x = v[i0:i1]; y = x - x.mean(); w = np.hanning(len(y))
        amp = 2 * np.abs(np.fft.rfft(y * w)) / w.sum(); f = np.fft.rfftfreq(len(y), 1 / FS)
        j0, j1 = np.searchsorted(t10, [j * WIN, (j + 1) * WIN])
        rows.append(dict(t=j * WIN, rms=float(np.sqrt(np.mean(f10[j0:j1] ** 2))), a60=float(amp[(f >= 59.5) & (f <= 60.5)].max())))
    return rows

if __name__ == "__main__":
    js = os.path.join(H, "noise5.json")
    if os.path.exists(js) and "--recalc" not in sys.argv:
        out = json.load(open(js, encoding="utf-8"))
    else:
        out = {name: stats(fn) for name, fn, _ in RUNS}
        json.dump(out, open(js, "w", encoding="utf-8"), ensure_ascii=False)
    fig, axs = plt.subplots(2, 1, figsize=(7.2, 5.0), dpi=300, sharex=True)
    for ax, key, title, thr in ((axs[0], "rms", "(가) 0.01–1 Hz 잡음 (2분마다)", 0.1), (axs[1], "a60", "(나) 60 Hz 상용전원 성분 (2분마다)", 0.003)):
        for name, fn, col in RUNS:
            r = out[name]; t = np.array([x["t"] for x in r]) / 3600; y = np.array([x[key] for x in r])
            med = np.median(y)
            ax.plot(t, y, color=col, lw=0.9, label=f"{name} (중앙값 {med:.3g} mV)")
        ax.axhline(thr, color="#888888", ls="--", lw=0.8)
        ax.text(5.9, thr * 1.15, f"분석 기준 {thr} mV", fontsize=7.5, color="#666666", ha="right", va="bottom")
        ax.set_yscale("log"); ax.set_ylabel("mV"); ax.grid(lw=0.3, color="#e3e3e3")
        ax.set_title(title, loc="left", fontsize=9.5)
        ax.legend(fontsize=6.8, frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    axs[1].set_xlim(0, 5.9); axs[1].set_xlabel("기록 시작 뒤 시간 (시간)")
    fig.tight_layout(h_pad=1.0)
    o = os.path.join(H, "..", "보고서_그림_순서대로", "09_그림4_날짜별_잡음_수준.jpg")
    fig.savefig(o, bbox_inches="tight", pad_inches=0.03, facecolor="white", pil_kwargs={"quality": 95}); print(o)
    for name in out:
        r = out[name]; a = np.array([x["rms"] for x in r]); b = np.array([x["a60"] for x in r])
        print(name, len(r), "rms 중앙", round(np.median(a), 4), "기준 아래", f"{(a < 0.1).mean() * 100:.1f}%", "60Hz 중앙", round(np.median(b), 4))
