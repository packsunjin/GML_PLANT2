import sys, numpy as np, pandas as pd
from scipy import signal
fs = 250
print("기록 | 60 Hz 진폭(mV) | 0.01–1 Hz 실효값(mV) | 표본 간 |Δv| 중앙값(mV) | 표본 수")
for p in sys.argv[1:]:
    d = pd.read_csv(p)
    t = d.timestamp_sec.values; v = d.voltage.values * 1000
    s = t - t[0] < 120
    t, v = t[s], v[s]
    x = v - v.mean()
    w = np.hanning(len(x))
    X = np.fft.rfft(x * w)
    amp = 2 * np.abs(X) / w.sum()
    f = np.fft.rfftfreq(len(x), 1 / fs)
    a60 = amp[(f >= 59.5) & (f <= 60.5)].max()
    n = 25
    m = len(v) // n * n
    v10 = v[:m].reshape(-1, n).mean(1)
    b, a = signal.butter(4, [0.01, 1], btype="band", fs=10)
    rms = np.sqrt(np.mean(signal.filtfilt(b, a, v10) ** 2))
    dv = np.median(np.abs(np.diff(v)))
    print("%s | %.3f | %.3f | %.4f | %d" % (p.split("/")[-1], a60, rms, dv, len(v)))
