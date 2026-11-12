"""
booth.py — 부스 체험·전시용 판정 (2026-11-12 다시 짬)
====================================================
대시보드의 실시간 루프(web_dashboard._worker)가 읽은 원신호를 그대로 받아 쓴다.
ADC 를 따로 읽지 않는다(같은 칩을 두 프로그램이 읽으면 안 된다 — CLAUDE.md 2절).

Booth     : /booth 머신러닝 체험. 흐름은 서버가 쥔다(화면은 phase 만 보고 그린다).
              main → (학교 이름 입력, start) → normal_ready → normal_rec → stim_ready → stim_rec → training → done → main
            정상·자극을 REC_SEC 초씩 기록 → 2초 창의 **스펙트로그램** 전부로 SVM 을 학습(나눠서 평가하지 않는다) →
            그 학교의 모델로 저장 → done("모델이 생성되었습니다") 에서 '모델 선택하기'(select) → 메인에서 실시간 판정을 본다.
            돈: 모델마다 만든 순간부터 초당 일정 금액이 쌓인다(먼저 만든 모델이 먼저 번다). 초당 금액은 교차검증 정확도로
            정한다 — 우연(50 %)이면 0원, 100 %면 MONEY_MAX 원. 최종 모델은 그대로 창 전부로 학습한다.
            모델은 data/booth/<id>.joblib 에 저장한다(서버를 다시 켜도 남는다, git 에는 안 넣는다).
FarmPump  : /farm 전시. 본 판정이 '수분부족'으로 일정 시간 이어지면 펌프를 켠다.
            펌프(마이크로비트) 연결은 아직 없다 — connected=False.

스펙트로그램: 창 앞 20초의 중앙값(기준선)을 뺀 원신호 2초(500표본)를 64표본 창·16표본 이동으로 STFT,
0–62.5 Hz(33칸, 1.95 Hz 간격) × 47칸(0.032초 간격), 로그 세기(dB). 11-12 사용자 지시로 17×28 에서 촘촘하게 바꿈 —
화면 그림과 모델 입력은 같은 배열이다. 평균이 아니라 기준선을 빼므로 손을 올린 동안의 전압 차이가 0 Hz 줄에 남는다.
"""
import glob
import json
import os
import re
import threading
import time

import numpy as np

WIN_SEC = 2.0            # 판정 창
HOP_SEC = 0.25           # 학습 창 이동
PRED_SEC = 0.5           # 판정 주기
BASE_SEC = 20.0          # 창 앞 이만큼의 중앙값을 기준선으로 본다
BASE_GAP_SEC = 0.5       # 기준선 구간과 창 사이 틈
KEEP_SEC = 180.0         # 원신호 보관
PLOT_SEC = 30.0          # 화면 전압 그래프 길이
PLOT_AVG_SEC = 0.1
REC_SEC = 8.0            # 정상·자극 기록 길이
LABELS = ("정상", "자극")
SPEC_NPERSEG, SPEC_HOP, SPEC_FMAX = 128, 8, 62.5
SPEC_VIEW_HOP = 32       # 화면용 30초 스펙트로그램의 이동(0.128초) — 보낼 양을 줄이려고 모델(8)보다 성기게
DB_FLOOR = -160.0        # 로그 세기 바닥(V^2 기준 dB)
CV_FOLDS = 4             # 교차검증: 기록마다 시간 순서로 이만큼 토막을 낸다
MONEY_MAX = 100          # 정확도 100 % 모델이 1초에 버는 돈(원). 50 %(우연)면 0원
STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "booth")


def spectrogram(win_v, base_v, fs, hop=None):
    """원신호(V)에서 기준선을 빼고 STFT → (주파수 × 시간) dB 배열과 주파수축.
    모델 입력은 2초 창·hop=SPEC_HOP 으로 33 × 47. 화면의 30초 그림은 같은 창 길이에 이동만 SPEC_VIEW_HOP."""
    hop = hop or SPEC_HOP
    from scipy import signal
    base = float(np.median(base_v)) if len(base_v) else float(np.median(win_v))
    f, _, s = signal.spectrogram(np.asarray(win_v) - base, fs=fs, nperseg=SPEC_NPERSEG,
                                 noverlap=SPEC_NPERSEG - hop, detrend=False, scaling="spectrum")
    keep = f <= SPEC_FMAX
    return np.maximum(10 * np.log10(s[keep] + 1e-30), DB_FLOOR), f[keep]


def money_rate(acc):
    """정확도(0~1) → 1초에 버는 돈(원). 우연(0.5) 이하면 0."""
    return int(round(max(0.0, (float(acc) - 0.5) * 2) * MONEY_MAX))


class Booth:
    def __init__(self, fs, store_dir=STORE_DIR):
        self.fs = float(fs)
        self.store_dir = store_dir
        self.n_keep = int(KEEP_SEC * self.fs)
        # 원신호(V). 같은 값을 두 자리(p, p+n)에 써서, 최근 n 개를 늘 이어진 한 토막으로 꺼낸다.
        self.buf = np.zeros(2 * self.n_keep)
        self.count = 0
        self.lock = threading.RLock()
        self._win = int(WIN_SEC * self.fs)
        self._hop = int(HOP_SEC * self.fs)
        self._pred_every = int(PRED_SEC * self.fs)
        self._base = int(BASE_SEC * self.fs)
        self._gap = int(BASE_GAP_SEC * self.fs)
        self._since_pred = 0
        # 체험 한 번의 진행 상태
        self.phase = "main"
        self.school = None
        self.rec = None                  # {"label", "start", "end"}
        self.segments = {}               # 라벨 → {"start", "end"}
        self.error = None
        self.new_id = None               # done 단계에서 보여 줄 방금 만든 모델
        # 저장된 모델
        self.models = {}                 # id → {"meta": {...}, "model": 분류기}
        self.selected = None
        self.pred = None
        self.spec = None                 # 마지막 판정에 쓴 창의 스펙트로그램(화면은 status() 의 30초 그림)
        self.spec_f = None
        self._shape = spectrogram(np.zeros(self._win), np.zeros(0), self.fs)[0].shape   # (주파수, 시간)
        self._load()

    # ── 저장 ───────────────────────────────────────────────────────
    def _load(self):
        import joblib
        for p in sorted(glob.glob(os.path.join(self.store_dir, "*.joblib"))):
            try:
                b = joblib.load(p)
                n = getattr(b["model"], "n_features_in_", None)
                if n is not None and n != int(np.prod(self._shape)):
                    # 스펙트로그램 크기가 바뀌기 전(11-12 이전 17×28)에 만든 모델 — 지금 입력으로는 판정할 수 없다
                    print(f"[booth] 스펙트로그램 크기가 달라 안 읽음: {p} (입력 {n}, 지금 {int(np.prod(self._shape))})")
                    continue
                self.models[b["meta"]["id"]] = b
            except Exception as e:                       # 깨진 파일 하나 때문에 서버가 안 뜨면 안 된다
                print(f"[booth] 모델 파일을 못 읽음: {p} ({type(e).__name__}: {e})")

    def _save(self, bundle):
        import joblib
        os.makedirs(self.store_dir, exist_ok=True)
        joblib.dump(bundle, os.path.join(self.store_dir, bundle["meta"]["id"] + ".joblib"))

    # ── 원신호 ─────────────────────────────────────────────────────
    def _recent(self):
        p = self.count % self.n_keep
        return self.buf[p:p + self.n_keep]

    def _slice(self, a, b):
        """표본 번호 [a, b) 의 원신호(V). 보관 범위를 벗어나면 None."""
        lo = self.count - self.n_keep
        if a < max(lo, 0) or b > self.count:
            return None
        return self._recent()[a - lo:b - lo]

    def _spec_at(self, end):
        """표본 번호 end 에서 끝나는 창의 스펙트로그램. 기준선 구간이 1초도 안 되면 창 자신의 중앙값을 쓴다."""
        win = self._slice(end - self._win, end)
        if win is None:
            return None, None
        b1 = end - self._win - self._gap
        b0 = max(b1 - self._base, self.count - self.n_keep, 0)
        base = self._slice(b0, b1) if b1 - b0 >= int(self.fs) else None
        return spectrogram(win, base if base is not None else win, self.fs)

    # ── 실시간 루프가 표본마다 부른다 ──────────────────────────────
    def feed(self, v):
        with self.lock:
            p = self.count % self.n_keep
            self.buf[p] = self.buf[p + self.n_keep] = v
            self.count += 1
            if self.rec and self.count >= self.rec["end"]:
                self._record_done()
            self._since_pred += 1
            if self._since_pred >= self._pred_every and self.count >= self._win:
                self._since_pred = 0
                self._predict()

    def _record_done(self):
        label = self.rec["label"]
        self.segments[label] = self.rec
        self.rec = None
        if label == LABELS[0]:
            self.phase = "stim_ready"
        else:
            self.phase = "training"
            threading.Thread(target=self._train, daemon=True).start()

    def _predict(self):
        s, f = self._spec_at(self.count)
        if s is None:
            return
        self.spec, self.spec_f = s, f
        b = self.models.get(self.selected)
        if b is None:
            self.pred = None
            return
        m = b["model"]
        p = m.predict_proba(s.reshape(1, -1))[0]
        k = int(np.argmax(p))
        self.pred = {"label": LABELS[int(m.classes_[k])], "proba": round(float(p[k]), 3),
                     "probs": {LABELS[int(c)]: round(float(q), 3) for c, q in zip(m.classes_, p)}}

    # ── 화면이 부르는 동작 ─────────────────────────────────────────
    def start(self, school):
        school = re.sub(r"\s+", " ", str(school or "")).strip()[:30]
        if not school:
            return False, "학교 이름을 입력하세요"
        with self.lock:
            if self.phase != "main":
                return False, "이미 진행 중입니다"
            self.school, self.segments, self.error = school, {}, None
            self.phase = "normal_ready"
        return True, None

    def record(self):
        """지금 단계의 기록을 시작한다(normal_ready → 정상, stim_ready → 자극)."""
        with self.lock:
            if self.phase not in ("normal_ready", "stim_ready"):
                return False, "지금은 기록할 단계가 아닙니다"
            label = LABELS[0] if self.phase == "normal_ready" else LABELS[1]
            self.rec = {"label": label, "start": self.count, "end": self.count + int(REC_SEC * self.fs)}
            self.phase = "normal_rec" if label == LABELS[0] else "stim_rec"
        return True, None

    def cancel(self):
        with self.lock:
            if self.phase == "training":
                return False, "학습 중에는 멈출 수 없습니다"
            self.phase, self.school, self.rec, self.segments, self.new_id = "main", None, None, {}, None
        return True, None

    def select(self, mid):
        """모델을 고른다. done 단계의 '모델 선택하기'도 이것을 부르고, 그러면 메인으로 돌아간다."""
        with self.lock:
            if mid is not None and mid not in self.models:
                return False, "없는 모델입니다"
            self.selected, self.pred = mid, None
            if self.phase == "done":
                self.phase, self.school, self.new_id = "main", None, None
        return True, None

    def delete(self, mid):
        with self.lock:
            if mid not in self.models:
                return False, "없는 모델입니다"
            del self.models[mid]
            if self.selected == mid:
                self.selected, self.pred = None, None
            p = os.path.join(self.store_dir, mid + ".joblib")
            if os.path.isfile(p):
                os.remove(p)
        return True, None

    # ── 학습 ───────────────────────────────────────────────────────
    def _windows(self, seg):
        """기록 한 번 → 창 스펙트로그램 목록 [(창 끝 표본 번호, 펼친 벡터)]. 창 전체가 기록 안에 드는 것만."""
        out = []
        for e in range(seg["start"] + self._win, seg["end"] + 1, self._hop):
            s, _ = self._spec_at(e)
            if s is not None:
                out.append((e, s.ravel()))
        return out

    def _cv_accuracy(self, segs):
        """시간 순서 토막 교차검증의 균형 정확도(0~1). 토막 하나를 빼고, 그 토막과 시간이 겹치는 창도 학습에서 뺀다
        (창이 겹치므로 섞어 나누면 정확도가 부풀려진다). 돈 버는 속도에만 쓴다."""
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVC
        with self.lock:
            wins = [self._windows(segs[label]) for label in LABELS]      # 라벨마다 [(창 끝, 벡터)]
        accs = []
        for k in range(CV_FOLDS):
            Xtr, ytr, Xte, yte = [], [], [], []
            for li, w in enumerate(wins):
                if not w:
                    continue
                n = len(w)
                lo_i, hi_i = k * n // CV_FOLDS, (k + 1) * n // CV_FOLDS
                if hi_i <= lo_i:
                    continue
                t0, t1 = w[lo_i][0] - self._win, w[hi_i - 1][0]           # 빼는 토막이 덮는 표본 범위
                for i, (e, x) in enumerate(w):
                    if lo_i <= i < hi_i:
                        Xte.append(x); yte.append(li)
                    elif e <= t0 or e - self._win >= t1:
                        Xtr.append(x); ytr.append(li)
            if len(set(ytr)) < 2 or len(set(yte)) < 2:
                continue
            yte = np.asarray(yte)
            m = make_pipeline(StandardScaler(), SVC(random_state=0)).fit(np.asarray(Xtr), ytr)
            pred = m.predict(np.asarray(Xte))
            accs.append(float(np.mean([np.mean(pred[yte == li] == li) for li in set(yte.tolist())])))
        return round(float(np.mean(accs)), 3) if accs else 0.5

    def _train(self):
        """정상·자극 기록에서 만든 창을 **전부** 학습에 쓴다(체험용이라 나눠서 평가하지 않는다). 분류기는 SVM."""
        try:
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler
            from sklearn.svm import SVC
            with self.lock:
                school, segs = self.school, dict(self.segments)
                X, y = [], []
                for li, label in enumerate(LABELS):
                    for _, x in self._windows(segs[label]):
                        X.append(x); y.append(li)
            if len(set(y)) < 2:
                raise RuntimeError("기록에서 창을 만들지 못했습니다")
            X, y = np.asarray(X), np.asarray(y)
            acc = self._cv_accuracy(segs)
            model = make_pipeline(StandardScaler(), SVC(probability=True, random_state=0)).fit(X, y)
            now = time.time()
            mid_ = time.strftime("%Y%m%d_%H%M%S", time.localtime(now))
            meta = {"id": mid_, "school": school, "created": now, "algo": "SVM",
                    "cv_acc": acc, "rate": money_rate(acc),
                    "n_windows": {LABELS[li]: int(np.sum(y == li)) for li in range(len(LABELS))},
                    "rec_sec": REC_SEC, "window_sec": WIN_SEC,
                    "spec": {"nperseg": SPEC_NPERSEG, "hop": SPEC_HOP, "fmax": SPEC_FMAX, "shape": list(self._shape)}}
            bundle = {"meta": meta, "model": model}
            self._save(bundle)
            with self.lock:
                self.models[mid_] = bundle
                self.new_id = mid_
                self.phase, self.segments = "done", {}
        except Exception as e:
            print(f"[booth] 학습 실패: {type(e).__name__}: {e}")
            with self.lock:
                self.error = f"학습하지 못했습니다 ({e})"
                self.phase, self.school, self.segments = "main", None, {}

    # ── 화면에 줄 값 ───────────────────────────────────────────────
    def status(self):
        with self.lock:
            fs = self.fs
            blk = max(1, int(round(PLOT_AVG_SEC * fs)))
            n = min(int(PLOT_SEC * fs), self.count, self.n_keep) // blk * blk
            sig = (self._recent()[-n:].reshape(-1, blk).mean(axis=1) * 1000.0) if n else np.zeros(0)
            rec = None
            if self.rec:
                rec = {"label": self.rec["label"], "total": REC_SEC,
                       "left": round(max(0.0, (self.rec["end"] - self.count) / fs), 1)}
            now = time.time()
            models = []
            for b in self.models.values():
                m = dict(b["meta"])
                m["rate"] = money_rate(m.get("cv_acc", m.get("balanced", 0.5)))   # 11-12 전 모델은 앞·뒤 절반 평가값
                m["money"] = int(m["rate"] * max(0.0, now - m["created"]))
                models.append(m)
            models.sort(key=lambda m: (-m["money"], -m["created"]))
            # 화면용: 최근 PLOT_SEC 초를 모델과 같은 STFT(창 128표본)로. 오른쪽 끝 WIN_SEC 초가 모델이 보는 구간이다.
            spec = None
            m = min(int(PLOT_SEC * fs), self.count, self.n_keep)
            if m >= SPEC_NPERSEG:
                x = self._recent()[-m:]
                db, f = spectrogram(x, x, fs, hop=SPEC_VIEW_HOP)
                spec = {"db": np.round(db, 1).tolist(), "fmax": SPEC_FMAX, "df": round(float(f[1] - f[0]), 4),
                        "sec": round(m / fs, 2), "view_sec": PLOT_SEC, "model_sec": WIN_SEC}
            new = self.models[self.new_id]["meta"] if self.new_id in self.models else None
            return {"ok": True, "phase": self.phase, "school": self.school, "recording": rec, "error": self.error,
                    "new_model": new,
                    "models": models, "selected": self.selected, "pred": self.pred, "labels": list(LABELS),
                    "signal_mv": np.round(sig, 3).tolist(), "signal_hz": round(fs / blk, 3), "plot_sec": PLOT_SEC,
                    "spec": spec, "rec_sec": REC_SEC, "window_sec": WIN_SEC}


class FarmPump:
    """본 판정이 '수분부족'으로 HOLD_SEC 이상 이어지면 펌프를 RUN_SEC 동안 켜고, REST_SEC 동안 쉰다.
    펌프로 보내는 부분(send)은 아직 없다 — 마이크로비트 연결이 정해지면 여기에 넣는다."""
    TARGET = "수분부족"
    HOLD_SEC, RUN_SEC, REST_SEC = 10.0, 5.0, 60.0
    TEST_SEC = 15.0

    def __init__(self):
        self.lock = threading.Lock()
        self.connected = False            # 펌프(마이크로비트)와 이어졌는가 — 지금은 늘 False
        self.since = None                 # '수분부족'이 이어지기 시작한 시각
        self.pump_until = 0.0
        self.rest_until = 0.0
        self.test_until = 0.0
        self.runs = 0
        self.last_state = None

    def test(self):
        with self.lock:
            self.test_until = time.time() + self.TEST_SEC

    def update(self, state, now=None):
        """실시간 루프가 판정이 나올 때마다 부른다."""
        now = time.time() if now is None else now
        with self.lock:
            testing = now < self.test_until
            eff = self.TARGET if testing else state
            self.last_state = state
            if eff == self.TARGET:
                self.since = self.since or now
            else:
                self.since = None
            if (self.since and now - self.since >= self.HOLD_SEC
                    and now >= self.pump_until and now >= self.rest_until):
                self.pump_until = now + self.RUN_SEC
                self.rest_until = self.pump_until + self.REST_SEC
                self.runs += 1

    def status(self, now=None):
        now = time.time() if now is None else now
        with self.lock:
            testing = now < self.test_until
            return {"ok": True, "connected": self.connected, "target": self.TARGET,
                    "state": self.last_state, "testing": testing,
                    "test_left": round(max(0.0, self.test_until - now), 1),
                    "held_sec": round(now - self.since, 1) if self.since else 0.0,
                    "pump_on": now < self.pump_until,
                    "pump_left": round(max(0.0, self.pump_until - now), 1),
                    "rest_left": round(max(0.0, self.rest_until - now), 1) if now >= self.pump_until else 0.0,
                    "runs": self.runs, "hold_sec": self.HOLD_SEC, "run_sec": self.RUN_SEC,
                    "rest_sec": self.REST_SEC}
