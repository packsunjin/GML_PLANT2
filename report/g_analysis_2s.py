"""g_analysis_2s.py — 표10 을 **2초 창 · 느린 특징 제외**로 다시 계산한다.

g_analysis.py 는 표10 을 10초 창·특징 17개로 계산한다. 실시간 판정은 2초 창 모델
(`models/touch2s_ns`, `train.py --no_slow`)이라 둘이 다르다(CLAUDE.md 0절 ⑳).
이 스크립트는 g_analysis.py 의 표10 부분만 떼어, 실시간 모델과 같은 조건으로 돌린다.

같은 점
  · 평가 파일 14개(TEST) — 표10 과 같다. 파일 하나가 세션 하나라서 학습/평가가 겹치지 않는다.
  · SVM·RandomForest 격자탐색, GroupKFold(3), 문턱 하나 규칙, 전부 비접촉 기준.
다른 점
  · 입력이 data/touch2s/features.csv (2초 창, 0.5초 이동)이다.
  · 느린 특징 3개(dc_level·dc_slope·dc_drift)를 **뺀다** → 특징 14개.
    train.py --no_slow 는 이 3개를 0 으로 두는데, 표준화·RandomForest 에서는 뺀 것과
    같은 결과다(상수 열은 정보가 없다). 그래서 실시간 모델과 같은 입력이다.
  · 세션 교차검증을 따로 낸다(train.cross_session_scores 와 같은 방식).

사용 (파이에서, data/touch2s 가 있는 곳):
    nice -n 19 venv/bin/python3 -I report/g_analysis_2s.py
    venv/bin/python3 report/g_analysis_2s.py --data data/touch2s --pixel   # 픽셀 입력 비교도
    venv/bin/python3 report/g_analysis_2s.py --infer                       # 2초 창 추론시간도

출력: 화면에 표10 형식 표, report/g_analysis_2s_result.json 에 같은 숫자.
⚠️ 이 스크립트는 저장소에서 실행해 본 적이 없다(CSV 가 GitHub 릴리스에만 있다).
   파이에서 처음 돌릴 때 에러가 나면 CLAUDE.md 에 적고 고쳐라.
"""
import os, sys, json, time, argparse
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.base import clone
from sklearn.metrics import confusion_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("GML_ROOT", os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "src"))

# 표10과 같은 평가 파일 (g_analysis.py 의 TEST 와 같다)
TEST = {"자극_1", "자극_11", "자극_12", "자극_3", "자극_4", "정상_11", "정상_13", "정상_21",
        "정상_24", "정상_28", "정상_30", "정상_6", "정상_7", "정상_9"}
SLOW = ("dc_level", "dc_slope", "dc_drift")        # 실시간에서 쓸 수 없는 느린 특징
META = ("img_name", "source_file", "label")
MAX_CV_SESSION_FOLDS = 5                           # train.py 와 같다


def cross_session(model, X, y, groups, max_folds=MAX_CV_SESSION_FOLDS):
    """train.cross_session_scores 와 같은 방식: 클래스마다 세션 하나씩 빼고 평가."""
    by_label = {}
    for g in np.unique(groups):
        by_label.setdefault(int(y[np.where(groups == g)[0][0]]), []).append(g)
    if len(by_label) < 2 or any(len(v) < 2 for v in by_label.values()):
        return None
    n_folds = min(max_folds, min(len(v) for v in by_label.values()))
    picks = {k: sorted(v) for k, v in by_label.items()}
    accs = []
    for i in range(n_folds):
        held = [picks[k][i % len(picks[k])] for k in sorted(picks)]
        te = np.isin(groups, held)
        if te.all() or not te.any():
            continue
        m = clone(model).fit(X[~te], y[~te])
        accs.append(float(m.score(X[te], y[te])))
    return accs or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/touch2s", help="features.csv 가 있는 폴더(저장소 루트 기준)")
    ap.add_argument("--pixel", action="store_true", help="픽셀 입력(224x224, PCA 30) 비교도 낸다")
    ap.add_argument("--infer", action="store_true", help="2초 창 하나의 추론시간도 잰다")
    args = ap.parse_args()

    data_dir = args.data if os.path.isabs(args.data) else os.path.join(ROOT, args.data)
    d = pd.read_csv(os.path.join(data_dir, "features.csv"))
    d = d[d["label"].isin(["정상", "자극"])].reset_index(drop=True)
    sess = d["source_file"].str.replace(".csv", "", regex=False)
    te = sess.isin(TEST).values
    tr = ~te
    y = (d["label"] == "자극").astype(int).values
    groups = sess.values

    FEATS = [c for c in d.columns if c not in META and c not in SLOW]
    XF = d[FEATS].values.astype(float)

    missing = TEST - set(sess.unique())
    if missing:
        print(f"⚠️ 평가 파일 {sorted(missing)} 가 features.csv 에 없다 — 표10과 같은 평가셋이 아니다.")
    n_touch, n_quiet = int(y[te].sum()), int((1 - y[te]).sum())
    out = {"n": dict(window="2초(0.5초 이동)", total=len(d), feats=len(FEATS), train=int(tr.sum()),
                     test=int(te.sum()), test_touch=n_touch, test_quiet=n_quiet,
                     all_touch=int(y.sum()), all_quiet=int((1 - y).sum()))}
    print(f"창 {len(d)}개 (학습 {int(tr.sum())}, 평가 {int(te.sum())}: 접촉 {n_touch}, 비접촉 {n_quiet}), 특징 {len(FEATS)}개")

    cv = GroupKFold(n_splits=3)

    def evaluate(X, name, pca):
        res = {}
        pre = [("sc", StandardScaler())] + ([("pca", PCA(n_components=30, random_state=42))] if pca else [])
        svm = GridSearchCV(Pipeline(pre + [("svm", SVC())]),
                           {"svm__kernel": ["linear", "rbf"], "svm__C": [0.1, 1, 10], "svm__gamma": ["scale", "auto"]},
                           cv=cv, n_jobs=2)
        rf = GridSearchCV(Pipeline(pre + [("rf", RandomForestClassifier(random_state=42))]),
                          {"rf__n_estimators": [100, 200], "rf__max_depth": [None, 10, 20]}, cv=cv, n_jobs=2)
        for mname, g in (("SVM", svm), ("RandomForest", rf)):
            g.fit(X[tr], y[tr], groups=groups[tr])
            p = g.predict(X[te])
            cm = confusion_matrix(y[te], p, labels=[0, 1])
            res[mname] = dict(params=g.best_params_, correct=int((p == y[te]).sum()),
                              touch_hit=int(cm[1, 1]), quiet_hit=int(cm[0, 0]), cm=cm.tolist())
            cvs = cross_session(g.best_estimator_, X, y, groups)
            if cvs:
                res[mname]["session_cv"] = dict(n=len(cvs), mean=round(float(np.mean(cvs)), 4),
                                                min=round(min(cvs), 4), max=round(max(cvs), 4))
        out[name] = res
        return res

    feat_res = evaluate(XF, "features14", pca=False)

    # 문턱 하나 규칙 (학습 데이터에서 찾고 평가 데이터에 적용 — g_analysis.py 와 같다)
    best = None
    for j, c in enumerate(FEATS):
        x = XF[:, j]
        for s in (1, -1):
            for t in np.unique(np.quantile(x[tr], np.linspace(0.01, 0.99, 99))):
                p = s * x > s * t
                ba = (p[tr & (y == 1)].mean() + (~p[tr & (y == 0)]).mean()) / 2
                if best is None or ba > best[0]:
                    best = (ba, c, s, float(t))
    _, c, s, t = best
    p = s * XF[:, FEATS.index(c)] > s * t
    out["threshold"] = dict(feature=c, sign=s, thr=t, correct=int((p[te] == y[te]).sum()),
                            touch_hit=int((p & te & (y == 1)).sum()), quiet_hit=int((~p & te & (y == 0)).sum()))
    out["all_quiet_baseline"] = dict(correct=n_quiet, touch_hit=0, quiet_hit=n_quiet)

    # 픽셀 입력 (선택)
    if args.pixel:
        try:
            from PIL import Image
            def img(row):
                return np.asarray(Image.open(os.path.join(data_dir, "spectrogram", row["label"], row["img_name"])).convert("L"),
                                  dtype=np.float32).ravel() / 255.0
            XP = np.stack([img(r) for _, r in d.iterrows()])
            evaluate(XP, "pixel224", pca=True)
        except Exception as e:                         # 이미지가 없거나 경로가 다르면 건너뛴다
            print(f"⚠️ 픽셀 입력 비교를 건너뜀: {e}")

    # 추론시간 (선택): 2초 창 하나의 전처리+특징+예측
    if args.infer:
        try:
            import preprocess, spectro_render, feature_extraction
            raw = pd.read_csv(os.path.join(ROOT, "data", "touch", "raw", "자극_1.csv"))["voltage"].to_numpy(float)
            fs = 250.0
            seg = raw[: int(2 * fs)]
            model = Pipeline([("sc", StandardScaler()), ("svm", SVC(kernel="linear", C=10))]).fit(XF[tr], y[tr])
            times = []
            for _ in range(100):
                t0 = time.perf_counter()
                filt = preprocess.bandpass_filter(seg, fs)
                Sxx, f, tt = spectro_render.compute_spectrogram(filt, fs, high=20.0)
                feats = feature_extraction.extract_features(filt, Sxx, f, tt, fs=fs, raw_window=seg,
                                                            baseline=float(seg.mean()))
                model.predict(np.asarray(feats, float)[: len(FEATS)].reshape(1, -1))
                times.append(time.perf_counter() - t0)
            out["infer_ms"] = dict(median=round(float(np.median(times)) * 1000, 2),
                                   p90=round(float(np.percentile(times, 90)) * 1000, 2))
        except Exception as e:
            print(f"⚠️ 추론시간 측정을 건너뜀: {e}")

    # ── 표10 형식으로 출력 ──
    def row(name, r):
        return (f"| {name} | {r['correct']} / {n_touch + n_quiet} | {r['touch_hit']} / {n_touch} "
                f"| {r['quiet_hit']} / {n_quiet} |")
    print()
    print(f"표10 (2초 창). 학습에 쓰지 않은 {n_touch + n_quiet}창: 접촉 {n_touch}, 비접촉 {n_quiet}")
    print("| 방법 | 맞힌 창 | 접촉 중 찾음 | 비접촉 중 맞음 |")
    print("|---|---|---|---|")
    print(row("전부 ‘비접촉’이라고 답함", out["all_quiet_baseline"]))
    print(row(f"SVM {feat_res['SVM']['params']}", feat_res["SVM"]))
    print(row(f"Random Forest {feat_res['RandomForest']['params']}", feat_res["RandomForest"]))
    th = out["threshold"]
    print(row(f"특징 하나의 문턱값 ({th['feature']} {'>' if th['sign'] == 1 else '<'} {th['thr']:.3g})", th))
    for m in ("SVM", "RandomForest"):
        cvr = feat_res[m].get("session_cv")
        if cvr:
            print(f"세션 교차검증 {m}: {cvr['n']}회 평균 {cvr['mean'] * 100:.1f} % (최소 {cvr['min'] * 100:.1f} – 최대 {cvr['max'] * 100:.1f})")
    if "pixel224" in out:
        px = out["pixel224"]
        print(f"픽셀 입력: SVM 접촉 {px['SVM']['touch_hit']}/{n_touch}, RF 접촉 {px['RandomForest']['touch_hit']}/{n_touch}")
    if "infer_ms" in out:
        print(f"추론시간(2초 창, 파이): 중앙값 {out['infer_ms']['median']} ms, p90 {out['infer_ms']['p90']} ms")

    path = os.path.join(HERE, "g_analysis_2s_result.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    print(f"\n저장: {path}")


if __name__ == "__main__":
    main()
