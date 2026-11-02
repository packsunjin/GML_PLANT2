"""정상 / 수분부족 분류 — 패러데이 상자 안 기록(2026-11-02).

회차(기록 파일)를 통째로 나눠 학습·평가한다(창이 80% 겹쳐 무작위 분할은 정확도를 부풀린다).
  정상은 물을 준 직후의 밤샘 12시간(10-28) 하나뿐이라 앞 6시간·뒤 6시간으로 나눈다.
  (10-30 5분은 물을 끊은 지 약 2일째라 정상 라벨로 쓰지 않는다 — 2026-11-02 검토 지적)
  A: 학습 = 정상 앞 6시간 + 수분부족 14시간(10-30~31) → 평가 = 정상 뒤 6시간 + 수분부족 30분(11-02, 물 주기 직전)
  B: A 를 뒤집음
물 준 뒤 1시간·화상 45분·10-30 5분은 라벨을 붙이지 않고, A 모델이 수분부족이라고 답한 창 비율만 본다.
비교 기준선: 창 안 "2초 사이 최대 변화" 하나에 문턱 하나.

쓰는 법(저장소 루트에서):  python3 report/stim/ml_water.py <작업폴더>
결과: <작업폴더>/ml_water.json 과 report/stim/ml_water.json
"""
import sys, os, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import ml_touch as mt                           # windows·scores·best_threshold 를 같이 쓴다
from feature_extraction import FEATURE_NAMES     # noqa: E402
import preprocess as pp                          # noqa: E402
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FAR = os.path.join(mt.ROOT, "data", "faraday")
pp.make_spectrogram_image = lambda *a, **k: None   # 특징만 쓰므로 그림은 안 만든다(시간 절약)

FILES = {   # 이름: (원본, 임시 이름, 라벨) — 임시 이름은 전부 '정상_' 으로 둬 창 선별이 안 걸리게 한다
    "정상밤샘": ("상자후GND_정상_20261028.csv.gz", "정상_21.csv", 0),
    "정상5분": ("상자후GND_5분_20261030.csv", "정상_22.csv", None),
    "수분부족14시간": ("상자후GND_수분부족_20261030.csv.gz", "정상_23.csv", 1),
    "수분부족30분": ("상자후GND_수분부족_물주기전30분_20261102.csv.gz", "정상_24.csv", 1),
    "물준뒤1시간": ("상자후GND_물준뒤1시간_20261102.csv.gz", "정상_25.csv", None),
    "화상45분": ("상자후GND_화상_20261102.csv.gz", "정상_26.csv", None),
}

def main(work):
    os.makedirs(work, exist_ok=True)
    D = {k: mt.windows(os.path.join(FAR, f), tmp, work) for k, (f, tmp, _) in FILES.items()}
    for k, (_, _, y) in FILES.items():
        if y is not None:
            D[k]["y"] = y
    n = D.pop("정상밤샘"); half = n["start_s"] < 6 * 3600
    D["정상앞6시간"] = n[half].copy(); D["정상뒤6시간"] = n[~half].copy()
    feats = [c for c in FEATURE_NAMES if c not in mt.SLOW]
    folds = {"A": (["정상앞6시간", "수분부족14시간"], ["정상뒤6시간", "수분부족30분"]),
             "B": (["정상뒤6시간", "수분부족30분"], ["정상앞6시간", "수분부족14시간"])}
    out = {"창 수": {k: int(len(d)) for k, d in D.items()},
           "특징": feats, "양성": "수분부족"}
    for name, (tr, te) in folds.items():
        Tr = pd.concat([D[k] for k in tr]); Te = pd.concat([D[k] for k in te])
        r = {}
        models = {
            "랜덤 포레스트": RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                              min_samples_leaf=2, random_state=0, n_jobs=-1),
            "SVM": make_pipeline(StandardScaler(), SVC(kernel="rbf", C=1.0, class_weight="balanced",
                                                       random_state=0)),
        }
        for mname, m in models.items():
            m.fit(Tr[feats].to_numpy(), Tr["y"].to_numpy())
            s = mt.scores(Te["y"].to_numpy(), m.predict(Te[feats].to_numpy()))
            s["균형 정확도"] = round((s["재현율"] + 1 - s["오경보율"]) / 2, 4)
            r[mname] = s
            if name == "A" and mname == "랜덤 포레스트":
                out["A 모델이 수분부족이라고 답한 비율"] = {
                    k: round(float(m.predict(D[k][feats].to_numpy()).mean()), 4)
                    for k in ("물준뒤1시간", "화상45분", "정상5분")}
        th = mt.best_threshold(Tr["max_jump_mV"].to_numpy(), Tr["y"].to_numpy())
        s = mt.scores(Te["y"].to_numpy(), (Te["max_jump_mV"].to_numpy() > th).astype(int))
        s["균형 정확도"] = round((s["재현율"] + 1 - s["오경보율"]) / 2, 4)
        r["문턱 하나(2초 최대 변화 > %.2f mV)" % th] = s
        out["평가 " + name + " (" + "+".join(te) + ")"] = r
    txt = json.dumps(out, ensure_ascii=False, indent=1)
    for p in (os.path.join(work, "ml_water.json"), os.path.join(mt.ROOT, "report", "stim", "ml_water.json")):
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
    print(txt)

if __name__ == "__main__":
    main(sys.argv[1])
