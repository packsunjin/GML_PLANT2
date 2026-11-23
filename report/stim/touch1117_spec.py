"""touch1117_spec.py — 11-17 손 접촉 기록을 스펙트로그램 입력으로 분류해 특징 추출(touch1117_ml.py)과 비교한다(2026-11-23).
창·라벨·평가는 touch1117_ml.py 와 같다(2초 창·0.5초 이동, 신호 뒤 6초 = 접촉, 앞·뒤 절반 바꿔 2회, 보조배터리 기록 적용).
스펙트로그램은 부스(src/booth.py)와 같은 방식: 창 앞 20초 중앙값을 뺀 250 S/s 원신호 2초 → 256표본 창·8표본 이동 STFT,
0–62.5 Hz 65칸 × 31칸, dB. 그림: 콘센트 기록의 잡은 순간 앞뒤 스펙트로그램(포스터용).
쓰는 법: TOUCH_DIR=data/faraday python3 report/stim/touch1117_spec.py
"""
import os, sys, json
import numpy as np, pandas as pd
from scipy.signal import stft
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import balanced_accuracy_score as bac
D = os.environ.get("TOUCH_DIR", "data/faraday"); FS = 250.0

def raw(fn):
    d = pd.read_csv(os.path.join(D, fn)); return d.timestamp_sec.values, d.voltage.values * 1000

def spec(t, v, s0):
    i0, i1 = np.searchsorted(t, [s0, s0 + 2.0]); b0 = np.searchsorted(t, s0 - 20)
    w = v[i0:i1] - np.median(v[b0:i0]); w = w[:500]
    f, tt, Z = stft(w, fs=FS, nperseg=256, noverlap=248, boundary=None, padded=False)
    S = 20 * np.log10(np.abs(Z) + 1e-6)
    return S[:, :31] if S.shape[1] >= 31 else np.pad(S, ((0, 0), (0, 31 - S.shape[1])), mode="edge")

def windows(t, v, sigs, skip=()):
    X, y, c = [], [], []
    for s0 in np.arange(20.0, t[-1] - 2.0, 0.5):
        e0 = s0 + 2.0
        if any(abs(s0 - u) < 10 for u in skip): continue
        pos = any(s0 >= s and e0 <= s + 6 for s in sigs); neg = all(e0 <= s - 1 or s0 >= s + 8 for s in sigs)
        if not (pos or neg): continue
        X.append(spec(t, v, s0).ravel()); y.append(1 if pos else 0); c.append(s0)
    return np.array(X), np.array(y), np.array(c)

ta, va = raw("자극_콘센트_20261117.csv"); sa = [189.28 + 30 * k for k in range(9)]
tb, vb = raw("자극_배터리_20261117.csv"); sb = [129.75 + 30 * k for k in range(10)]
Xa, ya, ca = windows(ta, va, sa, skip=(129.28, 159.28)); Xb, yb, cb = windows(tb, vb, sb)
models = {"SVM": lambda: make_pipeline(StandardScaler(), PCA(30, random_state=0), SVC(C=10, class_weight="balanced")),
          "랜덤 포레스트": lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0)}
front = ca < 310; out = {"창": [int((ya == 1).sum()), int((ya == 0).sum())], "스펙트로그램 크기": "65x31"}
for name, mk in models.items():
    r = {}
    for tag, tr in (("앞→뒤", front), ("뒤→앞", ~front)):
        p = mk().fit(Xa[tr], ya[tr]).predict(Xa[~tr]); yt = ya[~tr]
        r[tag] = {"균형정확도": round(100 * bac(yt, p), 1), "접촉 찾음": f"{int(((p == 1) & (yt == 1)).sum())}/{int((yt == 1).sum())}",
                  "비접촉 맞힘": f"{int(((p == 0) & (yt == 0)).sum())}/{int((yt == 0).sum())}"}
    p = mk().fit(Xa, ya).predict(Xb)
    r["배터리 기록에 적용"] = {"만진 시각 창을 접촉으로": f"{int(((p == 1) & (yb == 1)).sum())}/{int((yb == 1).sum())}",
                        "안 만진 창을 접촉으로": f"{int(((p == 1) & (yb == 0)).sum())}/{int((yb == 0).sum())}"}
    out[name] = r
print(json.dumps(out, ensure_ascii=False, indent=1))
json.dump(out, open(os.path.join(os.path.dirname(__file__), "touch1117_spec.json"), "w"), ensure_ascii=False, indent=1)
