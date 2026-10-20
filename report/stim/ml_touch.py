"""자극 실험 분류 — 누른(댄) 시각이 든 30초 창 = 자극, 나머지 = 정상 (0절 ㉓, 2026-10-16).

회차 전체를 "자극"으로 라벨하면 자극 회차 창의 대부분(누르지 않은 시간)이 정상과 같아 학습이
성립하지 않는다. 그래서 창마다 누른 시각이 들어 있는지로 라벨을 붙인다.

평가는 회차를 통째로 나눈다(창이 80% 겹쳐 무작위 분할은 정확도를 부풀린다).
  A: 학습 = 자극 2회차(살짝 댐) + 정상 밤샘   → 평가 = 자극 1회차(꾹 누름) + 정상 1회차
  B: 학습 = 자극 1회차 + 정상 1회차            → 평가 = 자극 2회차 + 정상 밤샘
비교 기준선: 창 안 "2초 사이 최대 변화" 하나에 문턱 하나(학습 쪽에서 F1 이 가장 큰 값).

쓰는 법(저장소 루트에서):
  python3 report/stim/ml_touch.py <작업폴더>
결과: <작업폴더>/ml_touch.json, report/FIG_STIM_ML.png
"""
import sys, os, gzip, shutil, json
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import preprocess as pp                      # noqa: E402
from feature_extraction import FEATURE_NAMES  # noqa: E402
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RAW = os.path.join(ROOT, "data", "ds", "stim", "raw")
WIN = pp.WINDOW_SEC
FS = pp.SAMPLE_RATE_HZ
SLOW = {"dc_level", "dc_slope", "dc_drift"}   # 0절 ⑳ — 실시간과 맞추려고 뺀다

def touch_times():
    """회차별 누른(댄) 시각(파일 기준 초)."""
    p1 = pd.read_csv(os.path.join(RAW, "자극.presses.csv"), comment="#")
    # 1회차: 누르고 바로 기록(최대 10초 늦음), file_sec = 기록 + 6 → 누른 시각 ≈ file_sec − 5
    t1 = (p1["file_sec"] - 5).to_numpy(float)
    p2 = pd.read_csv(os.path.join(RAW, "자극_2.presses.csv"), comment="#")
    # 2회차: 대고 약 5초 뒤 기록, 스톱워치는 수집 초가 오를 때 켬(0~5초 늦음) → ≈ lap − 2.5
    t2 = (p2["lap_sec"] - 2.5).to_numpy(float)
    return t1, t2

def windows(src, tmp_name, work):
    """preprocess.process_file 로 창별 특징을 뽑는다. 상태 이름이 '정상'이어야 자극 전용 창 선별이 안 걸린다."""
    csv_dir = os.path.join(work, "csv"); os.makedirs(csv_dir, exist_ok=True)
    dst = os.path.join(csv_dir, tmp_name)
    if not os.path.exists(dst):
        if src.endswith(".gz"):
            with gzip.open(src, "rb") as fi, open(dst, "wb") as fo:
                shutil.copyfileobj(fi, fo)
        else:
            shutil.copy(src, dst)
    cache = os.path.join(work, tmp_name + ".feat.csv")
    if os.path.exists(cache):
        return pd.read_csv(cache)
    _, rows, _ = pp.process_file(dst, os.path.join(work, "img"))
    df = pd.DataFrame([r[3:] for r in rows], columns=FEATURE_NAMES)
    df["start_s"] = [int(r[0].rsplit("_", 1)[1].split(".")[0]) / FS for r in rows]
    # 기준선 특징: 창 안 1초 평균의 2초 사이 최대 변화(mV)
    v = pd.read_csv(dst)["voltage"].to_numpy(float) * 1000
    s = v[: len(v) // 250 * 250].reshape(-1, 250).mean(1)
    dj = np.abs(s[2:] - s[:-2])
    df["max_jump_mV"] = [dj[int(a): int(a + WIN) - 2].max() for a in df["start_s"]]
    df.to_csv(cache, index=False)
    return df

LATE = os.environ.get("GML_LABEL") == "late"   # 검토 반영(2026-10-20): 늦게 오는 반응용 라벨

def label(df, touches):
    st = df["start_s"].to_numpy()
    if LATE:
        # 누른 뒤 20~50초 구간과 15초 이상 겹치는 창 = 자극(누르기 1번당 창 7개)
        ov = lambda a, t: max(0.0, min(a + WIN, t + 50) - max(a, t + 20))
        return np.array([any(ov(a, t) >= 15 for t in touches) for a in st]).astype(int)
    return np.array([np.any((touches >= a) & (touches <= a + WIN)) for a in st]).astype(int)

def scores(y, p):
    tp = int(((p == 1) & (y == 1)).sum()); fp = int(((p == 1) & (y == 0)).sum())
    fn = int(((p == 0) & (y == 1)).sum()); tn = int(((p == 0) & (y == 0)).sum())
    rec = tp / max(1, tp + fn); prec = tp / max(1, tp + fp)
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "정확도": round((tp + tn) / len(y), 4),
            "재현율": round(rec, 3), "정밀도": round(prec, 3),
            "오경보율": round(fp / max(1, fp + tn), 4)}

def best_threshold(x, y):
    best = (0, None)
    for th in np.unique(np.round(x, 2)):
        p = (x > th).astype(int); s = scores(y, p)
        f1 = 2 * s["재현율"] * s["정밀도"] / max(1e-9, s["재현율"] + s["정밀도"])
        if f1 > best[0]:
            best = (f1, float(th))
    return best[1] if best[1] is not None else float(np.max(x))

def main(work):
    os.makedirs(work, exist_ok=True)
    t1, t2 = touch_times()
    D = {
        "자극1": windows(os.path.join(RAW, "자극.csv"), "정상_11.csv", work),
        "자극2": windows(os.path.join(RAW, "자극_2.csv"), "정상_12.csv", work),
        "정상1": windows(os.path.join(RAW, "정상_5.csv"), "정상_13.csv", work),
        "정상밤샘": windows(os.path.join(RAW, "정상_2.csv.gz"), "정상_14.csv", work),
    }
    D["자극1"]["y"] = label(D["자극1"], t1)
    D["자극2"]["y"] = label(D["자극2"], t2)
    D["정상1"]["y"] = 0; D["정상밤샘"]["y"] = 0
    feats = [c for c in FEATURE_NAMES if c not in SLOW]
    folds = {"A": (["자극2", "정상밤샘"], ["자극1", "정상1"]),
             "B": (["자극1", "정상1"], ["자극2", "정상밤샘"])}
    out = {"창 수": {k: [int(len(d)), int(d["y"].sum())] for k, d in D.items()}}
    probs = {}
    for name, (tr, te) in folds.items():
        Tr = pd.concat([D[k] for k in tr]); Te = pd.concat([D[k] for k in te])
        r = {}
        models = {
            "RandomForest": RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                                   min_samples_leaf=2, random_state=0, n_jobs=-1),
            "SVM": make_pipeline(StandardScaler(), SVC(kernel="rbf", C=1.0, class_weight="balanced",
                                                       probability=True, random_state=0)),
        }
        for mname, m in models.items():
            m.fit(Tr[feats].to_numpy(), Tr["y"].to_numpy())
            p = m.predict(Te[feats].to_numpy())
            r[mname] = scores(Te["y"].to_numpy(), p)
            if mname == "RandomForest":
                for k in te:
                    if k.startswith("자극"):
                        probs[k] = m.predict_proba(D[k][feats].to_numpy())[:, 1]
        th = best_threshold(Tr["max_jump_mV"].to_numpy(), Tr["y"].to_numpy())
        r["문턱 하나(2초 최대 변화 > %.2f mV)" % th] = scores(
            Te["y"].to_numpy(), (Te["max_jump_mV"].to_numpy() > th).astype(int))
        r["모두 정상이라고 답함"] = scores(Te["y"].to_numpy(), np.zeros(len(Te), int))
        out["평가 " + name + " (" + "+".join(te) + ")"] = r
    out["라벨"] = "누른 뒤 20~50초와 15초 이상 겹치는 창" if LATE else "누른 시각이 든 30초 창"
    if LATE:
        with open(os.path.join(work, "ml_touch_late.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    with open(os.path.join(work, "ml_touch.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    figure(D, t1, t2, probs)

def figure(D, t1, t2, probs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm
    fm.fontManager.addfont("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
    plt.rcParams["font.family"] = "WenQuanYi Zen Hei"; plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=True)
    for ax, k, tt, ttl in [(axes[0], "자극1", t1, "(가) 자극 1회차(꾹 누름) — 자극 2회차·정상 밤샘으로 학습한 모델"),
                           (axes[1], "자극2", t2, "(나) 자극 2회차(살짝 댐) — 자극 1회차·정상 1회차로 학습한 모델")]:
        d = D[k]; c = d["start_s"].to_numpy() + WIN / 2
        ax.plot(c / 60, probs[k], color="#2a6fbb", lw=1.2, label="자극일 확률(30초 창 가운데에 표시)")
        for i, x in enumerate(tt):
            ax.axvline(x / 60, color="#d0473a", ls="--", lw=0.8, label="누른(댄) 시각" if i == 0 else None)
        ax.axhline(0.5, color="0.4", lw=0.6, ls=":")
        ax.set_ylim(-0.03, 1.03); ax.set_ylabel("자극 확률")
        ax.set_title(ttl, loc="left", fontsize=10); ax.legend(loc="upper right", fontsize=7.5)
    axes[1].set_xlabel("수집 시간(분)")
    fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "report", "FIG_STIM_ML.png"), dpi=400)

if __name__ == "__main__":
    main(sys.argv[1])
