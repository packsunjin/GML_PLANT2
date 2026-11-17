"""newplant_ml.py — 새 식물 정상(정상_6, 5.9시간) 대 물 공급 중단(수분부족 앞 52,450초 = 11-09 17:43~11-10 08:18) 분류 비교 (2026-11-17).
preprocess.py 로 30초 창·5초 이동·특징 17개(기준선 3 + 0.01–1 Hz 14)를 만든 뒤(features.csv), 각 기록의 앞/뒤 절반으로 학습·평가하고
기준선(dc_level)·창 표준편차 문턱 하나와 비교한다(보고서 Ⅳ-6, 분석 범위 0–1 Hz).
1) python3 -c "...정상_6·수분부족 앞 52450초를 raw 폴더에 CSV 로..." 2) cd src && python3 preprocess.py --raw_dir <raw> --out_dir <spec> --features_csv <features.csv>
3) python3 report/stim/newplant_ml.py <features.csv>
결과(2026-11-17, 특징 17개): 창 정상 4,210·물 공급 중단 10,467. 앞→뒤 RF 100·SVM 99.9 %, 뒤→앞 RF 66.3·SVM 65.2 %.
문턱 하나: 기준선 99.1·100 %(약 221 mV), 표준편차 99.1·98.4 %(약 0.5 mV). (특징 14개였을 때 RF 99.0/96.8·SVM 99.4/96.8)
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
F = list(d.columns[3:-1])   # 특징 17개(기준선 3 + 대역 14)
d = d.sort_values(["label", "k"])
d["half"] = d.groupby("label").cumcount() / d.groupby("label").k.transform("count") < 0.5
print(d.groupby("label").size().to_dict(), len(F))
for name, tr in [("앞→뒤", True), ("뒤→앞", False)]:
    A, B = d[d.half == tr], d[d.half != tr]
    for mn, m in [("RF", RandomForestClassifier(200, random_state=0, class_weight="balanced")),
                  ("SVM", make_pipeline(StandardScaler(), SVC(class_weight="balanced")))]:
        m.fit(A[F], A.label); print(name, mn, round(bac(B.label, m.predict(B[F])) * 100, 1))
    for f in ("dc_level", "std"):
        th = np.linspace(A[f].min(), A[f].max(), 3000)
        sc = lambda t, hi: bac(A.label, np.where((A[f] > t) if hi else (A[f] <= t), "정상", "수분부족"))
        best, hi = max(((t, h) for t in th for h in (True, False)), key=lambda x: sc(*x))
        pr = np.where((B[f] > best) if hi else (B[f] <= best), "정상", "수분부족")
        print(name, "문턱", f, round(bac(B.label, pr) * 100, 1), f"{best*1000:.1f} mV")
print((d.groupby("label")["std"].median() * 1000).round(3).to_dict())
