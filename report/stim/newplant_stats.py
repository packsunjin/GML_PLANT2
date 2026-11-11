"""새 식물(은선 전극, 상자 안·망 GND·보조배터리) 정상_6·수분부족 기록의 2분 단위 통계.
평균, 0.01–1 Hz 실효값(25개 평균 → 10 S/s, 4차 버터워스 앞뒤로), 60 Hz 진폭(Hann 창 FFT 59.5–60.5 Hz 최대).
쓰는 법(저장소 루트): python3 report/stim/newplant_stats.py  → report/stim/newplant_stats.json"""
import os, json
import numpy as np, pandas as pd
from scipy import signal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "data", "ds", "stim", "raw")
FS, WIN = 250, 120


def stats(name):
    d = pd.read_csv(os.path.join(RAW, name), usecols=["timestamp_sec", "voltage"])
    t = d.timestamp_sec.to_numpy(); v = d.voltage.to_numpy() * 1000
    m = len(v) // 25 * 25
    v10 = v[:m].reshape(-1, 25).mean(1); t10 = t[:m].reshape(-1, 25).mean(1)
    b, a = signal.butter(4, [0.01, 1], btype="band", fs=10)
    f10 = signal.filtfilt(b, a, v10)
    rows = []
    for k in range(int(t[-1] // WIN) + 1):
        i0, i1 = np.searchsorted(t, [k * WIN, (k + 1) * WIN])
        if i1 - i0 < FS * 110:
            continue
        x = v[i0:i1]; y = x - x.mean(); w = np.hanning(len(y))
        amp = 2 * np.abs(np.fft.rfft(y * w)) / w.sum(); f = np.fft.rfftfreq(len(y), 1 / FS)
        q = (f >= 59.5) & (f <= 60.5)
        j0, j1 = np.searchsorted(t10, [k * WIN, (k + 1) * WIN])
        rows.append(dict(t=k * WIN, mean=round(float(x.mean()), 3), rms=round(float(np.sqrt(np.mean(f10[j0:j1] ** 2))), 4),
                         a60=round(float(amp[q].max()), 5)))
    return dict(seconds=round(float(t[-1]), 1), n=int(len(v)), rows=rows)


if __name__ == "__main__":
    out = {n: stats(n + ".csv.gz") for n in ("정상_6", "수분부족")}
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "newplant_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    for n, r in out.items():
        print(n, r["seconds"], r["n"], len(r["rows"]))
