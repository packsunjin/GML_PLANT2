"""touch1117_ml.py — 11-17 손 접촉 기록으로 손 접촉 감지 모델 학습·평가.
자료: data/faraday/자극_콘센트_20261117.csv(학습·평가), 자극_배터리_20261117.csv(같은 모델 적용)
처리: 0.1초 평균(10 S/s) → 앞 20초 중앙값을 뺀 값 → 2초 창·0.5초 이동 → 특징 17개(feature_extraction)
라벨: 신호 시각 s 기준 [s, s+6]초 안에 든 창 = 접촉, [s-1, s+8] 과 겹치지 않는 창 = 비접촉, 나머지는 뺌.
      콘센트 20:40:20(129.28초)·20:40:50(159.28초)은 만졌는지 불확실해 앞뒤 10초를 뺌.
평가: 신호 시각 310초 기준 앞·뒤로 나눠 앞→뒤, 뒤→앞. 배터리 기록에는 콘센트 전체로 학습한 모델을 적용.
쓰는 법: python3 report/stim/touch1117_ml.py <csv 폴더>
"""
import sys, os, json
import numpy as np, pandas as pd
from scipy.signal import spectrogram
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score as bac
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from feature_extraction import extract_features
D = os.environ.get("TOUCH_DIR") or (sys.argv[1] if len(sys.argv) > 1 else "data/faraday")
FS = 10.0

def series(fn):
    d = pd.read_csv(os.path.join(D, fn)); t = d.timestamp_sec.values; v = d.voltage.values * 1000
    b = np.floor(t / 0.1).astype(int); k = b.max() + 1
    m = np.bincount(b, v, k) / np.maximum(np.bincount(b, None, k), 1)
    return np.arange(k) / FS, m

def windows(t, m, sigs, skip=()):
    X, y, c = [], [], []
    for s0 in np.arange(20.0, t[-1] - 2.0, 0.5):
        e0 = s0 + 2.0
        if any(abs(s0 - u) < 10 for u in skip): continue
        pos = any(s0 >= s and e0 <= s + 6 for s in sigs)
        neg = all(e0 <= s - 1 or s0 >= s + 8 for s in sigs)
        if not (pos or neg): continue
        i0, i1 = int(round(s0 * FS)), int(round(e0 * FS))
        base = np.median(m[int((s0 - 20) * FS):i0])
        w = m[i0:i1] - base
        f, tt, S = spectrogram(w, fs=FS, nperseg=16, noverlap=12)
        X.append(extract_features(w, 10 * np.log10(S + 1e-12), f, tt, fs=FS, raw_window=w, raw_fs=FS))
        y.append(1 if pos else 0); c.append(s0)
    return np.array(X), np.array(y), np.array(c)

models = {"랜덤 포레스트": lambda: RandomForestClassifier(300, class_weight="balanced", random_state=0),
          "SVM": lambda: make_pipeline(StandardScaler(), SVC(C=10, class_weight="balanced"))}
if __name__ == "__main__":
    ta, ma = series("자극_콘센트_20261117.csv")
    sa = [189.28 + 30 * k for k in range(9)]
    Xa, ya, ca = windows(ta, ma, sa, skip=(129.28, 159.28))
    tb, mb = series("자극_배터리_20261117.csv")
    sb = [129.75 + 30 * k for k in range(10)]
    Xb, yb, cb = windows(tb, mb, sb)
    out = {"콘센트 창": [int((ya == 1).sum()), int((ya == 0).sum())], "배터리 창": [int((yb == 1).sum()), int((yb == 0).sum())]}
    front = ca < 310
    for name, mk in models.items():
        r = {}
        for tag, tr in (("앞→뒤", front), ("뒤→앞", ~front)):
            m_ = mk().fit(Xa[tr], ya[tr]); p = m_.predict(Xa[~tr]); yt = ya[~tr]
            r[tag] = {"균형정확도": round(100 * bac(yt, p), 1), "접촉 찾음": f"{int(((p == 1) & (yt == 1)).sum())}/{int((yt == 1).sum())}",
                      "비접촉 맞힘": f"{int(((p == 0) & (yt == 0)).sum())}/{int((yt == 0).sum())}"}
        m_ = mk().fit(Xa, ya); p = m_.predict(Xb)
        r["배터리 기록에 적용"] = {"만진 시각 창을 접촉으로": f"{int(((p == 1) & (yb == 1)).sum())}/{int((yb == 1).sum())}",
                            "안 만진 창을 접촉으로": f"{int(((p == 1) & (yb == 0)).sum())}/{int((yb == 0).sum())}"}
        out[name] = r
    print(json.dumps(out, ensure_ascii=False, indent=1))
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "touch1117_ml.json"), "w"), ensure_ascii=False, indent=1)
