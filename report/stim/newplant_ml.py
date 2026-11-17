"""newplant_ml.py — 새 식물 정상(정상_6, 5.9시간) 대 물 공급 중단(수분부족 앞 52,450초 = 11-09 17:43~11-10 08:18) 분류 비교 (2026-11-17).
preprocess.py 로 30초 창·5초 이동·특징을 만든 뒤(features.csv), 각 기록의 앞/뒤 절반으로 학습·평가하고 창 표준편차 문턱 하나와 비교한다.
1) python3 -c "...정상_6·수분부족 앞 52450초를 raw 폴더에 CSV 로..." 2) cd src && python3 preprocess.py --raw_dir <raw> --out_dir <spec> --features_csv <features.csv>
3) python3 report/stim/newplant_ml.py <features.csv>
결과(2026-11-17): 창 정상 4,210·물 공급 중단 10,467. 앞→뒤 RF 99.0·SVM 99.4·문턱 99.1 %, 뒤→앞 RF 96.8·SVM 96.8·문턱 98.4 %(균형 정확도),
창 표준편차 중앙값 정상 1.10 mV·물 공급 중단 0.027 mV.
"""
import sys
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score as bac

d = pd.read_csv(sys.argv[1])
d["k"] = d.img_name.str.extract(r"_(\d+)\.png").astype(int)
F = [c for c in d.columns[3:-1] if c not in ("dc_level", "dc_slope", "dc_drift")]   # 특징 14개
d = d.sort_values(["label", "k"])
d["half"] = d.groupby("label").cumcount() / d.groupby("label").k.transform("count") < 0.5
print(d.groupby("label").size().to_dict(), len(F))
for name, tr in [("앞→뒤", True), ("뒤→앞", False)]:
    A, B = d[d.half == tr], d[d.half != tr]
    for mn, m in [("RF", RandomForestClassifier(200, random_state=0, class_weight="balanced")),
                  ("SVM", make_pipeline(StandardScaler(), SVC(class_weight="balanced")))]:
        m.fit(A[F], A.label); print(name, mn, round(bac(B.label, m.predict(B[F])) * 100, 1))
    th = np.linspace(A["std"].min(), A["std"].max(), 2000)
    best = max(th, key=lambda t: bac(A.label, np.where(A["std"] > t, "정상", "수분부족")))
    print(name, "문턱(std)", round(bac(B.label, np.where(B["std"] > best, "정상", "수분부족")) * 100, 1), f"{best*1000:.3f} mV")
print((d.groupby("label")["std"].median() * 1000).round(3).to_dict())
