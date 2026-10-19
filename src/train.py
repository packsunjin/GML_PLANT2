"""
train.py
========
스펙트로그램 이미지/명시적 특징으로 SVM(Linear/RBF) + Random Forest 분류기를 학습·비교합니다.

특징 방식(--mode): 픽셀 / 특징 / 둘다
- 픽셀(기본): data/spectrogram/<상태>/*.png 이미지를 grayscale 224x224 -> flatten(50,176차원)
  픽셀 특징으로 사용, PCA로 차원 축소.
- 특징: data/features.csv (preprocess.py가 함께 생성하는 명시적 통계/주파수 특징 14개), PCA 없이 StandardScaler만.
- 둘다: 픽셀+특징 모두 학습 후 비교.

비교 과제(--task): 정상 vs 자극 2종 (기본)  -> models/best_model.joblib (기본 실시간 모델)

- GridSearchCV로 하이퍼파라미터 최적화, Accuracy/Precision/Recall 출력
- Confusion Matrix 이미지 저장, 최적 모델 저장(bundle에 classes/feature_mode 포함)

실행:
    python train.py                          # 정상-자극, 픽셀 (기본)
    python train.py --mode 둘다               # 정상-자극, 픽셀+특징
"""

import argparse
import glob
import json
import os
import sys
import math
import time

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import venv_boot; venv_boot.ensure()   # venv 를 안 켜도 알아서 갈아탄다

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

from font_utils import setup_korean_font
# 설치된 한글 폰트를 자동 지정(없으면 None). confusion matrix 라벨을 한글로 쓸지 여부에 사용.
_KOREAN_FONT = setup_korean_font()

from sklearn.model_selection import GridSearchCV
from joblib import Memory
import shutil
import tempfile

_CACHE_DIR = None
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, precision_score, recall_score,
                             confusion_matrix, ConfusionMatrixDisplay)
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from feature_extraction import FEATURE_NAMES

IMG_SIZE = 224

# 원시 상태(=preprocess.py가 만드는 폴더/라벨). 한글 폰트가 없을 때 confusion matrix용 영어 대체 라벨.
STATE_EN = {"정상": "Normal", "자극": "Stimulus"}

# 비교 과제 정의. 첫 원소가 label 0.
TASKS = {
    "정상-자극": ["정상", "자극"],   # 정상=지속 상태, 자극=순간 이벤트
}
DEFAULT_TASK = "정상-자극"
ALL_TASKS = "전체"

# preprocess.py가 사용한 필터 대역. 모델 번들에 저장해 inference가 동일 필터를 쓰게 한다.
# preprocess.py의 기본값과 같아야 한다(band_filter.py: 0.01~1Hz, 10Hz 로 줄여 인과 필터, 문맥 90초).
DEFAULT_FILTER = {"lowcut": 0.01, "highcut": 1.0, "notch_freq": 0.0, "notch_q": 30.0,
                  "decim_hz": 10.0, "context_sec": 90.0}
FILTER_META = dict(DEFAULT_FILTER)

# 창 길이도 학습·추론이 반드시 같아야 한다. 예전에는 이 값이 모델에 저장되지 않아
# inference.py가 자기 상수(2초)를 쓰는 바람에, preprocess의 창을 바꾸면 학습과 추론이
# 조용히 어긋났다. 이제 메타에서 읽어 모델 번들에 함께 저장한다.
DEFAULT_WINDOW = {"sample_rate": 250.0, "window_sec": 30.0, "step_sec": 5.0}
WINDOW_META = dict(DEFAULT_WINDOW)



def _pipeline_cache_dir():
    """GridSearchCV가 파이프라인 앞단(표준화·PCA)을 재사용하도록 둘 캐시 폴더.

    학습이 끝나면 지운다(다음 학습은 데이터가 달라 어차피 못 쓴다). 임시 폴더를 쓰므로
    저장소나 data/ 를 더럽히지 않는다."""
    global _CACHE_DIR
    if _CACHE_DIR is None:
        _CACHE_DIR = tempfile.mkdtemp(prefix="gml_train_cache_")
    return _CACHE_DIR


def _clear_pipeline_cache():
    global _CACHE_DIR
    if _CACHE_DIR is not None:
        shutil.rmtree(_CACHE_DIR, ignore_errors=True)
        _CACHE_DIR = None


def _load_meta(features_csv):
    """preprocess.py가 남긴 preprocess_meta.json을 읽는다(없거나 깨졌으면 빈 dict)."""
    p = os.path.join(os.path.dirname(features_csv) or ".", "preprocess_meta.json")
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def load_filter_meta(features_csv):
    """preprocess.py가 남긴 메타에서 필터 대역을 읽는다(없으면 기본값)."""
    m = _load_meta(features_csv)
    try:
        return {k: float(m.get(k, DEFAULT_FILTER[k])) for k in DEFAULT_FILTER}
    except Exception:
        return dict(DEFAULT_FILTER)


def load_window_meta(features_csv):
    """전처리에 쓴 창 길이/샘플레이트를 읽는다. 추론이 같은 창을 쓰도록 모델에 저장한다."""
    m = _load_meta(features_csv)
    try:
        return {k: float(m.get(k, DEFAULT_WINDOW[k])) for k in DEFAULT_WINDOW}
    except Exception:
        return dict(DEFAULT_WINDOW)


HISTORY_CAP = 50


def _append_history(models_dir, record):
    """학습할 때마다 결과를 models_dir/train_history.json에 누적한다.
    웹 관리자 패널의 '최근 학습 결과' 목록이 이 파일을 읽는다."""
    path = os.path.join(models_dir, "train_history.json")
    try:
        with open(path, encoding="utf-8") as f:
            hist = json.load(f)
    except Exception:
        hist = []
    hist.append(record)
    hist = hist[-HISTORY_CAP:]
    try:
        os.makedirs(models_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(hist, f, ensure_ascii=False)
    except OSError as e:
        print(f"[train] 학습 기록 저장 실패: {e}")

# --mode 한글 CLI 값 -> 내부 처리용 값. 파일명/표시에는 다시 한글(_특징 등)을 쓴다.
MODE_CHOICES = {"픽셀": "pixel", "특징": "features", "둘다": "both"}
MODE_KO = {"pixel": "픽셀", "features": "특징"}  # 내부값 -> 표시/파일명용 한글

CV_FOLDS_DEFAULT = 3


def _parse_img_name(img_name):
    """'정상_000123.png' -> ('정상', 123): 원본 소스 상태(그룹)와 윈도우 시작 오프셋.
    preprocess.py가 img_name을 f'{base_name}_{start:06d}.png'로 만들므로 마지막 '_' 기준으로 나눈다."""
    base = os.path.splitext(img_name)[0]
    src, _, off = base.rpartition("_")
    try:
        return src, int(off)
    except ValueError:
        return base, 0


def load_dataset(spectrogram_dir, classes):
    """픽셀 모드: data/spectrogram/<상태>/*.png -> grayscale flatten 특징.
    classes에 포함된 상태 폴더만 읽고, 라벨은 classes에서의 순서(index)로 매긴다.
    시간순 그룹 분할을 위해 (원본 상태, 윈도우 오프셋)도 함께 반환한다.
    밤샘 기록은 창이 수천 장이라, 리스트에 모았다가 np.array 로 바꾸면 메모리가 두 배로
    든다(파이 8 GB). float32 배열을 미리 잡아 바로 채운다."""
    items = []
    for label_idx, cls in enumerate(classes):
        cls_dir = os.path.join(spectrogram_dir, cls)
        items += [(p, label_idx) for p in sorted(glob.glob(os.path.join(cls_dir, "*.png")))]
    X = np.empty((len(items), IMG_SIZE * IMG_SIZE), dtype=np.float32)
    y, groups, order = [], [], []
    for i, (p, label_idx) in enumerate(items):
        img = Image.open(p).convert("L")  # grayscale, 고정 크기
        if img.size != (IMG_SIZE, IMG_SIZE):  # 저장 시 이미 IMG_SIZE로 렌더링되므로 보통 그대로 통과
            img = img.resize((IMG_SIZE, IMG_SIZE))
        X[i] = np.asarray(img, dtype=np.float32).ravel() / 255.0
        src, off = _parse_img_name(os.path.basename(p))
        y.append(label_idx)
        groups.append(src)
        order.append(off)
    return X, np.array(y), np.array(groups), np.array(order)


def session_labels(groups, y, classes):
    """창마다 '그 창이 속한 회차의 상태'를 돌려준다(분할용).

    누른 시각 라벨(preprocess.PRESS_SUFFIX)을 쓰면 자극 회차 안에도 정상 창이 생긴다.
    회차를 상태별로 나눠 평가 회차를 고를 때 창 라벨을 쓰면 회차 하나가 두 상태로
    갈라져 버리므로, 회차 이름('자극_2' → '자극')에서 상태를 읽는다. 모르는 이름이면 창 라벨."""
    idx = {c: i for i, c in enumerate(classes)}
    out = []
    for g, lab in zip(groups, y):
        head = os.path.splitext(str(g))[0].split("_")[0]
        out.append(idx.get(head, lab))
    return np.array(out)


def balance_train(X, y, seed=0):
    """학습 분할에서 많은 클래스를 가장 적은 클래스 수만큼 무작위로 줄인다.

    정상 밤샘 기록이 들어오면 정상 창이 자극 창의 100배가 넘는다. 그대로 학습하면
    '모두 정상'이라고만 답해도 정확도가 99% 라 모델이 자극을 배우지 않는다(0절 ㉗).
    평가 분할은 줄이지 않는다 — 실제 비율에서의 오경보율을 봐야 하기 때문이다."""
    rng = np.random.default_rng(seed)
    labs, counts = np.unique(y, return_counts=True)
    n_min = int(counts.min())
    keep = np.concatenate([rng.permutation(np.where(y == l)[0])[:n_min] for l in labs])
    keep.sort()
    return X[keep], y[keep]


def binary_report(y_true, y_pred):
    """2종(정상=0, 자극=1) 평가 지표. 자극 창을 몇 개 찾았는지·오경보율·균형 정확도."""
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    tp = int(((y_pred == 1) & (y_true == 1)).sum()); fn = int(((y_pred == 0) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum()); tn = int(((y_pred == 0) & (y_true == 0)).sum())
    return {"hits": tp, "positives": tp + fn, "false_alarms": fp, "negatives": fp + tn,
            "false_alarm_rate": fp / max(1, fp + tn),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred))
            if len(np.unique(y_true)) > 1 else None}


NO_SLOW = False


def load_feature_dataset(features_csv_path, classes):
    """특징 모드: data/features.csv -> 명시적 통계/주파수 특징 14개.
    classes에 포함된 상태만 골라 라벨을 classes 순서로 매핑한다(픽셀 로더와 순서 공유)."""
    df = pd.read_csv(features_csv_path)
    df = df[df["label"].isin(classes)].reset_index(drop=True)
    label_to_idx = {cls: i for i, cls in enumerate(classes)}
    X = df[FEATURE_NAMES].to_numpy(dtype=np.float64)
    if NO_SLOW:
        # 실시간 판정(inference.signal_to_feature)은 느린 특징 3개를 0 으로 넣는다.
        # 학습도 0 으로 맞춰야 학습/추론이 어긋나지 않는다(CLAUDE.md 0절 ⑳).
        X[:, -3:] = 0.0
    y = df["label"].map(label_to_idx).to_numpy()
    groups = df["source_file"].to_numpy()
    order = df["img_name"].map(lambda n: _parse_img_name(n)[1]).to_numpy()
    return X, y, groups, order


def chronological_group_split(X, y, groups, order, test_size=0.3, guard=1):
    """원본 상태(그룹)별로 윈도우를 시간순 정렬한 뒤, 앞부분을 train, 뒷부분을 test로 나눈다.

    preprocess.py가 창을 겹쳐 가며 슬라이딩하므로 인접 윈도우는 서로 겹친다.
    무작위 분할을 쓰면 겹치는 윈도우가 train과 test에 동시에 들어가 데이터 누수가 생겨
    정확도가 부풀려진다. 여기서는 그룹별로 시간축을 따라 나누고, train의 마지막 guard개
    윈도우를 버려 train/test 경계 윈도우가 시간적으로 겹치지 않게 한다.

    guard 는 반드시 창 길이와 스텝에서 계산해야 한다. 창 W초를 S초씩 밀면 거리가
    W/S 미만인 윈도우끼리 겹치므로, 버려야 할 개수는 ceil(W/S) - 1 이다.
      2초 창 / 1초 스텝 -> 1개    (예전 설정)
      10초 창 / 2초 스텝 -> 4개   (현재 설정)
    이 값을 1로 고정해 두면 창을 늘렸을 때 경계에서 겹침이 그대로 남아 누수가 생긴다.
    실제로 창을 2초에서 10초로 바꾸면서 한동안 그 상태였다.

    각 상태(소스)는 단일 클래스라, 상태마다 앞/뒤로 나누면 모든 클래스가 train과 test에
    비례적으로 포함된다(stratify 없이도 클래스 균형 유지)."""
    train_idx, test_idx = [], []
    for g in np.unique(groups):
        g_idx = np.where(groups == g)[0]
        g_idx = g_idx[np.argsort(order[g_idx])]  # 시간순
        n = len(g_idx)
        n_test = min(max(1, int(round(n * test_size))), n - 1)  # train도 최소 1개 확보
        split = n - n_test
        train_end = max(1, split - guard)  # guard 윈도우 제거(겹침 차단)
        train_idx.extend(g_idx[:train_end].tolist())
        test_idx.extend(g_idx[split:].tolist())
    train_idx = np.array(train_idx)
    test_idx = np.array(test_idx)
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def session_holdout_split(X, y, groups, labels, test_size=0.3, seed=0):
    """세션(파일)을 통째로 학습/평가로 갈라, 평가 세션은 모델이 한 번도 본 적 없게 한다.

    왜 이게 필요한가
    ---------------
    같은 세션의 창을 앞/뒤로만 나누면(chronological_group_split), 모든 세션이 학습과
    평가 양쪽에 들어간다. 그러면 모델이 '그 세션의 전극이 어느 방향으로 표류했는지'를
    외워서 맞힐 수 있다. 식물 상태를 배운 것이 아니라 측정 조건을 배운 것이다.

    실제로 이 프로젝트의 1차 학습에서 나온 높은 정확도가 그랬다 — 클래스마다 전극
    부착 조건이 달랐고 모델은 그 차이를 학습했다(보고서 Ⅳ장 2절 (4)).
    시뮬레이션으로도 확인했다: 상태당 세션이 하나면, 수분 스트레스를 원리적으로
    측정할 수 없는 AD8232 구성에서도 정확도 100% 가 나온다.

    평가 세션을 통째로 빼면 그 지름길이 막힌다. 대신 상태마다 세션이 2개 이상 있어야
    쓸 수 있어서, 조건을 못 채우면 None 을 돌려준다(호출한 쪽이 옛 방식으로 넘어간다).
    """
    rng = np.random.default_rng(seed)
    by_label = {}
    for g in np.unique(groups):
        lab = labels[np.where(groups == g)[0][0]]
        by_label.setdefault(lab, []).append(g)
    if any(len(v) < 2 for v in by_label.values()):
        return None                      # 세션이 하나뿐인 상태가 있다

    test_groups = set()
    for lab, gs in by_label.items():
        gs = sorted(gs)
        n_test = max(1, int(round(len(gs) * test_size)))
        n_test = min(n_test, len(gs) - 1)          # 학습용도 최소 하나 남긴다
        test_groups.update(rng.permutation(gs)[:n_test].tolist())

    te = np.isin(groups, list(test_groups))
    return X[~te], X[te], y[~te], y[te], sorted(test_groups)


def overlap_guard(window_sec=None, step_sec=None):
    """train/test 경계에서 버려야 할 윈도우 수. 창 W초를 S초씩 밀면 거리 ceil(W/S)-1 까지 겹친다."""
    w = float(window_sec if window_sec is not None else WINDOW_META["window_sec"])
    st = float(step_sec if step_sec is not None else WINDOW_META["step_sec"])
    if st <= 0:
        return 1
    return max(1, int(math.ceil(w / st)) - 1)


def validate_classes(y, classes, context="전체"):
    """클래스별 샘플 수를 검증한다. 학습이 근본적으로 불가능한 경우(클래스 누락/샘플 극소)는
    알아보기 힘든 sklearn 예외 대신 명확한 한국어 메시지로 즉시 종료한다."""
    counts = {cls: int(np.sum(y == i)) for i, cls in enumerate(classes)}
    missing = [cls for cls, c in counts.items() if c == 0]
    if missing:
        print(f"❌ '{', '.join(missing)}' 클래스에 샘플이 없습니다.")
        print("   data/raw/ 에 해당 상태의 CSV를 먼저 수집하고 preprocess.py를 실행한 뒤 다시 시도하세요.")
        sys.exit(1)

    smallest_cls = min(counts, key=counts.get)
    smallest_n = counts[smallest_cls]
    if smallest_n < 2:
        print(f"❌ '{smallest_cls}' 클래스 샘플이 {context} 기준 {smallest_n}개뿐이라 학습이 불가능합니다.")
        print("   최소 2개 이상 필요합니다. 데이터를 더 수집한 뒤 다시 시도하세요.")
        sys.exit(1)
    return counts


def cv_folds_for(y_train, classes, cv_default=CV_FOLDS_DEFAULT):
    """GridSearchCV(cv=...)에 실제로 전달할 폴드 수를, y_train(학습 분할 이후) 기준
    클래스별 샘플 수에 맞춰 정한다."""
    validate_classes(y_train, classes, context="학습 분할(train split)")
    counts = {cls: int(np.sum(y_train == i)) for i, cls in enumerate(classes)}
    smallest_n = min(counts.values())
    cv_folds = min(cv_default, smallest_n)
    if cv_folds < cv_default:
        print(f"⚠️  학습 분할 내 클래스별 최소 샘플 수({smallest_n})가 적어 GridSearchCV 폴드를 "
              f"{cv_default} -> {cv_folds}로 자동 축소합니다.")
    return cv_folds


MAX_CV_SESSION_FOLDS = 5      # 세션이 많아도 이 이상은 돌리지 않는다(학습 시간)


def cross_session_scores(model, X, y, groups, labels, max_folds=MAX_CV_SESSION_FOLDS):
    """세션을 돌아가며 하나씩 빼고 평가해, 정확도가 얼마나 흔들리는지 본다.

    왜 필요한가
    ----------
    분할을 한 번만 하면, 어느 세션이 평가로 빠졌느냐에 따라 결과가 통째로 달라진다.
    시뮬레이션으로 확인한 예 — 상태당 4세션에서 조합 16가지를 모두 돌렸을 때

        AD8232 : 평균 85.5%, 범위 50.0~98.9%, 표준편차 20.6%p   ← 우연에 좌우
        DC 결합 : 평균 98.1%, 범위 98.0~98.3%, 표준편차  0.1%p   ← 안정

    AD8232 는 수분 스트레스를 원리적으로 측정할 수 없는데도 어떤 조합에서는 98.9%가
    나온다. 그 한 번을 보고 '분류에 성공했다'고 하면 틀린 결론에 이른다.
    그래서 한 숫자가 아니라 **흔들리는 폭**을 함께 봐야 한다.

    반환: (정확도 배열, 평가에 쓴 세션쌍 목록). 세션이 모자라면 (None, None).
    """
    from sklearn.base import clone
    by_label = {}
    for g in np.unique(groups):
        lab = labels[np.where(groups == g)[0][0]]
        by_label.setdefault(lab, []).append(g)
    if len(by_label) < 2 or any(len(v) < 2 for v in by_label.values()):
        return None, None

    # 클래스마다 세션을 하나씩 짝지어 돌린다(모든 조합을 다 돌면 세션 수의 곱이 된다).
    n_folds = min(max_folds, min(len(v) for v in by_label.values()))
    picks = {lab: sorted(v) for lab, v in by_label.items()}
    accs, used = [], []
    for i in range(n_folds):
        held = [picks[lab][i % len(picks[lab])] for lab in sorted(picks)]
        te = np.isin(groups, held)
        if te.all() or not te.any():
            continue
        Xtr, ytr = balance_train(X[~te], y[~te])
        if len(np.unique(ytr)) < 2 or len(np.unique(y[te])) < 2:
            continue
        m = clone(model)
        m.fit(Xtr, ytr)
        # 정상 창이 훨씬 많아 그냥 정확도는 '모두 정상'만으로도 높게 나온다 → 균형 정확도
        accs.append(float(balanced_accuracy_score(y[te], m.predict(X[te]))))
        used.append(held)
    return (np.array(accs), used) if accs else (None, None)


def _scores(model, best_params, y_test, y_pred, avg):
    res = {
        "model": model,
        "best_params": best_params,
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, average=avg, zero_division=0),
        "recall": recall_score(y_test, y_pred, average=avg, zero_division=0),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, y_pred)),
        "y_pred": y_pred,
    }
    if avg == "binary":
        res.update(binary_report(y_test, y_pred))
    return res


def train_and_eval(X_train, X_test, y_train, y_test, out_dir, classes, mode="pixel",
                   cv_folds=CV_FOLDS_DEFAULT, task=DEFAULT_TASK):
    results = {}
    # 2종은 양성 클래스(정상 아닌 상태) 기준 binary, 3종 이상이면 macro 평균.
    avg = "binary" if len(classes) == 2 else "macro"
    mode_file = "" if mode == "pixel" else "_특징"
    task_file = "" if task == DEFAULT_TASK else f"_{task}"
    file_suffix = mode_file + task_file        # 파일명용 (예: _특징_정상-자극)
    tag = f"{MODE_KO[mode]}·{task}"            # 화면 표시용 (예: 특징·정상-자극)

    if mode == "pixel":
        # PCA로 차원 축소 (224*224=50176차원 -> 계산 효율화). 특징은 여전히 "이미지 픽셀 기반".
        smallest_fold_train = int(X_train.shape[0] * (cv_folds - 1) / cv_folds)
        n_components = max(2, min(30, smallest_fold_train - 1, X_train.shape[1]))
        pca_step = [("pca", PCA(n_components=n_components, random_state=42))]
    else:
        # 명시적 특징(14차원)은 이미 저차원이라 PCA로 더 축소하면 해석성만 잃는다.
        pca_step = []

    # ---- SVM (Linear vs RBF) via GridSearchCV ----
    # 전처리 단계(표준화·PCA)는 분류기 하이퍼파라미터와 무관한데도, 캐시가 없으면
    # GridSearchCV가 후보를 바꿀 때마다 처음부터 다시 계산한다. 픽셀 방식은 이 앞단이
    # 50,176차원 PCA라 전체 학습 시간의 대부분을 차지한다(후보 12개 x 5겹이면 PCA를
    # 60번 계산). memory= 를 주면 같은 폴드의 앞단 결과를 재사용해 5번만 계산한다.
    cache = Memory(location=_pipeline_cache_dir(), verbose=0)
    # 학습 분할은 balance_train 으로 이미 1:1 이지만, 그래도 남는 치우침에 대비해 class_weight 를 건다.
    svm_pipe = Pipeline([("scaler", StandardScaler())] + pca_step
                        + [("svm", SVC(probability=True, class_weight="balanced"))],
                        memory=cache)
    svm_param_grid = {
        "svm__kernel": ["linear", "rbf"],
        "svm__C": [0.1, 1, 10],
        "svm__gamma": ["scale", "auto"],
    }
    n_svm = np.prod([len(v) for v in svm_param_grid.values()])
    print(f"[train] ({tag}) SVM GridSearchCV 시작: 후보 {n_svm}개 x {cv_folds}겹 = {n_svm*cv_folds}회 학습…")
    # verbose=1: 학습기가 fold 하나 끝날 때마다 한 줄씩 찍는다. 이게 없으면 GridSearchCV가
    # 몇 분씩 아무 출력 없이 도는 동안 웹 로그가 멈춘 것처럼 보인다.
    svm_grid = GridSearchCV(svm_pipe, svm_param_grid, cv=cv_folds, n_jobs=-1, verbose=1,
                            scoring="balanced_accuracy")
    svm_grid.fit(X_train, y_train)
    svm_best = svm_grid.best_estimator_
    y_pred_svm = svm_best.predict(X_test)
    print(f"[train] ({tag}) SVM 완료 -> 최적 파라미터 {svm_grid.best_params_}")

    results["SVM"] = _scores(svm_best, svm_grid.best_params_, y_test, y_pred_svm, avg)

    # ---- Random Forest via GridSearchCV ----
    rf_pipe = Pipeline([("scaler", StandardScaler())] + pca_step
                       + [("rf", RandomForestClassifier(random_state=42, class_weight="balanced"))],
                       memory=cache)
    rf_param_grid = {
        "rf__n_estimators": [100, 200],
        "rf__max_depth": [None, 10, 20],
    }
    n_rf = np.prod([len(v) for v in rf_param_grid.values()])
    print(f"[train] ({tag}) RandomForest GridSearchCV 시작: 후보 {n_rf}개 x {cv_folds}겹 = {n_rf*cv_folds}회 학습…")
    rf_grid = GridSearchCV(rf_pipe, rf_param_grid, cv=cv_folds, n_jobs=-1, verbose=1,
                           scoring="balanced_accuracy")
    rf_grid.fit(X_train, y_train)
    rf_best = rf_grid.best_estimator_
    y_pred_rf = rf_best.predict(X_test)
    print(f"[train] ({tag}) RandomForest 완료 -> 최적 파라미터 {rf_grid.best_params_}")

    results["RandomForest"] = _scores(rf_best, rf_grid.best_params_, y_test, y_pred_rf, avg)

    # ---- 리포트 출력 + confusion matrix 저장 ----
    os.makedirs(out_dir, exist_ok=True)
    display_labels = classes if _KOREAN_FONT else [STATE_EN.get(c, c) for c in classes]
    for name, res in results.items():
        print(f"\n=== {name} ({tag}) ===")
        print(f"Best params: {res['best_params']}")
        print(f"Accuracy : {res['accuracy']:.4f}")
        print(f"Precision: {res['precision']:.4f}  ({avg})")
        print(f"Recall   : {res['recall']:.4f}  ({avg})")
        if res.get("hits") is not None:
            ba = res["balanced_accuracy"]
            print(f"자극 창 찾음: {res['hits']}/{res['positives']} · 오경보 {res['false_alarms']}/{res['negatives']}"
                  f" ({res['false_alarm_rate']*100:.1f}%) · 균형 정확도 "
                  f"{'—' if ba is None else f'{ba:.4f}'}")

        cm = confusion_matrix(y_test, res["y_pred"], labels=list(range(len(classes))))
        title = (f"{name} 혼동행렬" if _KOREAN_FONT else f"{name} Confusion Matrix") + f" ({tag})"
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=display_labels)
        fig, ax = plt.subplots(figsize=(4.5, 4.5))
        disp.plot(ax=ax, cmap="viridis", colorbar=False)
        ax.set_title(title)
        fig.tight_layout()
        cm_path = os.path.join(out_dir, f"confusion_matrix_{name}{file_suffix}.png")
        fig.savefig(cm_path)
        plt.close(fig)
        print(f"Confusion matrix saved -> {cm_path}")

    return results, file_suffix, tag


def run_pipeline(X, y, groups, order, models_dir, mode, classes, task):
    t0 = time.time()
    tag_prefix = f"{MODE_KO[mode]}·{task}"
    counts = {c: int(np.sum(y == i)) for i, c in enumerate(classes)}
    dist = ", ".join(f"{c}={n}" for c, n in counts.items())
    print(f"[train] ({tag_prefix}) 총 샘플 수: {len(y)}  [{dist}]")
    validate_classes(y, classes)

    # 분할 방식은 두 가지고, 가능하면 강한 쪽을 쓴다.
    #
    #  ① 세션 홀드아웃 — 평가 세션을 통째로 뺀다. 모델이 그 세션의 전극 조건을
    #     외워서 맞히는 지름길이 막힌다. 상태마다 세션이 2개 이상 있어야 쓸 수 있다.
    #  ② 시간순 그룹 분할 — 세션이 하나뿐일 때의 차선책. 창 겹침에 의한 누수는
    #     막지만, 같은 세션이 학습·평가 양쪽에 들어가는 것 자체는 못 막는다.
    guard = overlap_guard()
    # labels 는 **클래스**여야 한다. 여기에 groups 를 넘기면 세션마다 라벨이 달라져
    # '상태마다 세션이 하나뿐'으로 잘못 판단한다. 누른 시각 라벨을 쓰면 자극 회차 안에도
    # 정상 창이 있으므로, 창 라벨이 아니라 회차의 상태(session_labels)로 나눈다.
    sess_lab = session_labels(groups, y, classes)
    split = session_holdout_split(X, y, groups, sess_lab, test_size=0.3)
    if split is not None:
        X_train, X_test, y_train, y_test, held = split
        print(f"[train] ({tag_prefix}) Train={len(y_train)}, Test={len(y_test)} "
              f"(세션 홀드아웃 — 평가 세션: {', '.join(held)})")
    else:
        X_train, X_test, y_train, y_test = chronological_group_split(X, y, groups, order,
                                                                     test_size=0.3, guard=guard)
        print(f"[train] ({tag_prefix}) Train={len(y_train)}, Test={len(y_test)} "
              f"(시간순 그룹 분할, 경계에서 겹치는 {guard}창 제거)")
        print(f"[train] ⚠️  상태마다 세션이 하나뿐이라 세션 홀드아웃을 쓸 수 없습니다.")
        print(f"[train]     이 정확도는 식물 상태가 아니라 그 세션의 측정 조건을 학습한")
        print(f"[train]     결과일 수 있습니다. 상태마다 2회 이상 나눠 수집하세요.")

    validate_classes(y_test, classes, context="평가 분할(test split)")
    before = {c: int(np.sum(y_train == i)) for i, c in enumerate(classes)}
    X_train, y_train = balance_train(X_train, y_train)
    after = {c: int(np.sum(y_train == i)) for i, c in enumerate(classes)}
    print(f"[train] ({tag_prefix}) 학습 분할 균형 맞춤: {before} -> {after} "
          f"(많은 쪽을 무작위로 줄임, 평가 분할은 그대로)")

    cv_folds = cv_folds_for(y_train, classes)
    results, file_suffix, tag = train_and_eval(X_train, X_test, y_train, y_test, models_dir,
                                                classes, mode=mode, cv_folds=cv_folds, task=task)

    # 정상이 대부분인 평가 분할에서는 '모두 정상'도 정확도가 높다. 균형 정확도로 고른다.
    best_name = max(results, key=lambda k: results[k]["balanced_accuracy"])
    best_res = results[best_name]
    best_model = best_res["model"]
    best_acc = best_res["accuracy"]
    best_bal = best_res["balanced_accuracy"]

    # 비교 기준: '모두 정상'이라고만 답했을 때(자극 0개 찾음, 오경보 0, 균형 정확도 0.5)
    baseline = None
    if len(classes) == 2:
        all_normal = np.zeros(len(y_test), dtype=int)
        baseline = {"accuracy": float(accuracy_score(y_test, all_normal)),
                    **binary_report(y_test, all_normal)}
        print(f"[train] ({tag_prefix}) 비교 — '모두 정상'이라고만 답하면: 정확도 {baseline['accuracy']*100:.1f}% · "
              f"자극 0/{baseline['positives']} · 오경보 0% · 균형 정확도 0.5000")
        print(f"[train] ({tag_prefix}) 최적 {best_name}: 자극 창 {best_res['hits']}/{best_res['positives']} 찾음 · "
              f"오경보율 {best_res['false_alarm_rate']*100:.1f}% · 균형 정확도 {best_bal:.4f} "
              f"(정확도 {best_acc*100:.1f}%)")
        if best_bal <= 0.5:
            print(f"[train] ⚠️  균형 정확도가 0.5 이하 — '모두 정상'보다 나을 것이 없습니다(자극 창을 가르지 못함).")

    # 분할을 한 번만 하면 어느 세션이 평가로 빠졌느냐에 따라 결과가 통째로 달라진다.
    # 흔들리는 폭을 함께 봐야 그 한 숫자를 믿어도 되는지 알 수 있다.
    cv_acc, cv_used = cross_session_scores(best_model, X, y, groups, sess_lab)
    cv_summary = None
    if cv_acc is not None and len(cv_acc) >= 2:
        cv_summary = {"mean": float(cv_acc.mean()), "min": float(cv_acc.min()),
                      "max": float(cv_acc.max()), "std": float(cv_acc.std()),
                      "folds": len(cv_acc), "metric": "balanced_accuracy"}
        print(f"[train] ({tag_prefix}) 세션 교차검증(균형 정확도) {len(cv_acc)}회: "
              f"평균 {cv_acc.mean()*100:.1f}% · 범위 {cv_acc.min()*100:.1f}~{cv_acc.max()*100:.1f}% "
              f"· 표준편차 {cv_acc.std()*100:.1f}%p")
        if cv_acc.std() > 0.10:
            print(f"[train] ⚠️  세션에 따라 정확도가 크게 흔들립니다({cv_acc.std()*100:.0f}%p).")
            print(f"[train]     식물 상태가 아니라 그날의 측정 조건을 학습했을 가능성이 큽니다.")
            print(f"[train]     위의 단일 분할 정확도({best_acc*100:.1f}%)만 보고 판단하지 마세요.")

    feature_mode = "pixel" if mode == "pixel" else "explicit"
    os.makedirs(models_dir, exist_ok=True)

    bundle = {"model": best_model, "classes": classes, "name": best_name,
              "feature_mode": feature_mode, "filter": FILTER_META,
              # 추론이 같은 길이의 창으로 잘라야 특징이 일치한다.
              "window_sec": WINDOW_META["window_sec"],
              "sample_rate": WINDOW_META["sample_rate"]}
    if mode == "pixel":
        bundle["img_size"] = IMG_SIZE
    else:
        bundle["feature_names"] = FEATURE_NAMES
        bundle["slow_features"] = not NO_SLOW

    best_path = os.path.join(models_dir, f"best_model{file_suffix}.joblib")
    joblib.dump(bundle, best_path)
    joblib.dump(results["SVM"]["model"], os.path.join(models_dir, f"svm_model{file_suffix}.joblib"))
    joblib.dump(results["RandomForest"]["model"], os.path.join(models_dir, f"rf_model{file_suffix}.joblib"))

    duration_sec = time.time() - t0
    print(f"\n[train] ({tag}) 최적 모델: {best_name} (균형 정확도={best_bal:.4f}, Accuracy={best_acc:.4f}, "
          f"{duration_sec:.1f}초) -> {best_path}")
    # 정확도 70% 기준은 정상이 대부분인 평가에서 '모두 정상'만으로도 넘는다 → 균형 정확도로 본다.
    if best_bal >= 0.70:
        print(f"[train] ({tag}) ✅ 균형 정확도 70% 이상")
    else:
        print(f"[train] ({tag}) ⚠️ 균형 정확도가 70% 미만입니다.")

    _append_history(models_dir, {
        "cross_session": cv_summary,
        "task": task, "mode": MODE_KO[mode], "trained_at": time.time(),
        "best_name": best_name, "accuracy": best_acc,
        "balanced_accuracy": best_bal,
        "hits": best_res.get("hits"), "positives": best_res.get("positives"),
        "false_alarms": best_res.get("false_alarms"), "negatives": best_res.get("negatives"),
        "false_alarm_rate": best_res.get("false_alarm_rate"),
        "baseline_all_normal": baseline,
        "precision": best_res["precision"], "recall": best_res["recall"],
        "classes": classes, "counts": counts,
        "train_n": len(y_train), "test_n": len(y_test),
        "duration_sec": round(duration_sec, 1),
        "model_file": os.path.basename(best_path),
    })

    return results, best_name, best_bal


def run_task(task, mode, args):
    """하나의 비교 과제(task)에 대해 mode(pixel/features/both)를 학습한다."""
    classes = TASKS[task]
    print(f"\n########## 과제: {task}  (클래스: {' vs '.join(classes)}) ##########")

    summary = {}
    if mode in ("pixel", "both"):
        print(f"[train] 데이터 로딩 중 (픽셀, {task})...")
        X, y, groups, order = load_dataset(args.spectrogram_dir, classes)
        _, best_name, best_acc = run_pipeline(X, y, groups, order, args.models_dir, "pixel", classes, task)
        summary[("픽셀", task)] = (best_name, best_acc)

    if mode in ("features", "both"):
        if not os.path.exists(args.features_csv):
            print(f"❌ {args.features_csv} 가 없습니다. 먼저 preprocess.py를 실행해 생성하세요.")
            sys.exit(1)
        print(f"[train] 데이터 로딩 중 (특징, {task})...")
        X, y, groups, order = load_feature_dataset(args.features_csv, classes)
        _, best_name, best_acc = run_pipeline(X, y, groups, order, args.models_dir, "features", classes, task)
        summary[("특징", task)] = (best_name, best_acc)
    return summary


def main():
    parser = argparse.ArgumentParser(description="스펙트로그램 이미지/명시적 특징 기반 식물 상태 분류 학습")
    parser.add_argument("--spectrogram_dir", default="../data/spectrogram")
    parser.add_argument("--features_csv", default="../data/features.csv")
    parser.add_argument("--models_dir", default="../models")
    parser.add_argument("--mode", choices=list(MODE_CHOICES), default="픽셀",
                         help="픽셀(기본) / 특징(명시적 특징) / 둘다")
    parser.add_argument("--task", choices=list(TASKS) + [ALL_TASKS], default=DEFAULT_TASK,
                         help="정상-자극(기본) / 전체. 정상은 항상 포함")
    parser.add_argument("--no_slow", action="store_true",
                        help="느린 특징 3개(dc_level·dc_slope·dc_drift)를 0 으로 두고 학습. "
                             "실시간 판정에 쓸 모델은 반드시 이것으로 학습한다")
    args = parser.parse_args()

    global FILTER_META, WINDOW_META, NO_SLOW
    NO_SLOW = args.no_slow
    _m = _load_meta(args.features_csv)
    if _m and "decim_hz" not in _m:
        # 예전 필터(0.5~20Hz)로 만든 features.csv 를 새 필터 모델로 저장하면 학습/추론이
        # 조용히 어긋난다. 막는다.
        print("❌ features.csv 가 예전 필터(0.5~20Hz, 10초 창)로 만들어졌습니다. "
              "새 필터(0.01~1Hz, 30초 창)로 다시 변환하세요:  python preprocess.py")
        sys.exit(1)
    FILTER_META = load_filter_meta(args.features_csv)
    WINDOW_META = load_window_meta(args.features_csv)
    print(f"[train] 필터 대역: 대역통과 {FILTER_META['lowcut']}~{FILTER_META['highcut']}Hz, "
          f"{FILTER_META['decim_hz']:g}Hz 로 줄여 인과 필터, 문맥 {FILTER_META['context_sec']:g}초 "
          f"(모델에 저장 -> 추론과 자동 일치)")
    print(f"[train] 분석 창: {WINDOW_META['window_sec']}초 @ {WINDOW_META['sample_rate']:.0f}Hz "
          f"(모델에 저장 -> 추론과 자동 일치)")

    mode = MODE_CHOICES[args.mode]  # 내부 처리용(pixel/features/both)
    tasks = list(TASKS) if args.task == ALL_TASKS else [args.task]

    summary = {}
    try:
        for task in tasks:
            summary.update(run_task(task, mode, args))
    finally:
        # 앞단 캐시는 이번 학습에서만 쓸모가 있다(데이터가 바뀌면 무효).
        _clear_pipeline_cache()

    if len(summary) > 1:
        print("\n=== 전체 비교 (과제 x 방식) ===")
        for (mode_ko, task), (name, acc) in summary.items():
            print(f"  [{task:10s}] {mode_ko:4s}: 최적 모델={name:14s} 균형 정확도={acc:.4f}")


if __name__ == "__main__":
    main()
