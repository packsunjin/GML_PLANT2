"""
booth.py — 부스 체험·전시용 판정 (2026-11-11)
================================================
대시보드의 실시간 루프(web_dashboard._worker)가 읽은 원신호를 그대로 받아 쓴다.
ADC 를 따로 읽지 않는다(같은 칩을 두 프로그램이 읽으면 안 된다 — CLAUDE.md 2절).

BoothTouch  : /booth "손 접촉 머신러닝 체험". 관람객이 '손 뗀 상태'와 '손 올린 상태'를 몇 초씩
              기록 → 그 자리에서 학습 → 모델을 골라 실시간 판정을 본다.
              본 판정(30초 창 + 문맥 90초)은 120초 뒤에야 나와 체험에 못 쓰므로 2초 창을 쓴다.
              기록·모델은 메모리에만 둔다(data/ 를 건드리지 않는다, 서버를 끄면 사라진다).
FarmPump    : /farm "스마트팜 전시". 본 판정이 '수분부족'으로 일정 시간 이어지면 펌프를 켠다.
              펌프(마이크로비트) 연결은 아직 없다 — connected=False 로 화면에 그대로 알린다.

모델은 세 가지를 같이 만든다: 문턱 하나(특징 하나에 기준값 하나), SVM, 랜덤 포레스트.
문턱 하나를 같이 두는 이유 = 높은 정확도가 나왔을 때 가장 단순한 기준과 견주어 보기 위해서다(보고서 Ⅳ장 1절).
"""
import threading
import time

import numpy as np

WIN_SEC = 2.0            # 판정 창
HOP_SEC = 0.5            # 창 이동(학습) · 판정 주기
BASE_SEC = 20.0          # 창 앞 이만큼의 중앙값을 기준선으로 본다(손을 10초쯤 올려도 기준선이 안 따라간다)
BASE_GAP_SEC = 0.5       # 기준선 구간과 창 사이 틈
KEEP_SEC = 180.0         # 원신호 보관
PLOT_SEC = 40.0          # 화면 그래프 길이
PLOT_AVG_SEC = 0.1
MIN_REC_SEC, MAX_REC_SEC = 4.0, 30.0
LABELS = ("비접촉", "접촉")
FEATURES = ("기준선에서 벗어난 크기(mV)", "기준선 차이(mV, 부호 있음)", "창 안 흔들림(mV)",
            "창 안 최대-최소(mV)", "0.1초 사이 최대 변화(mV)", "표본 사이 잔떨림(mV)")
MODEL_NAMES = ("문턱 하나", "SVM", "랜덤 포레스트")


def window_features(win_mv, base_mv, fs):
    """2초 창(원신호 mV) + 기준선 구간 → 특징 6개."""
    base = float(np.median(base_mv)) if len(base_mv) else float(np.median(win_mv))
    d = float(np.mean(win_mv)) - base
    blk = max(1, int(round(0.1 * fs)))
    m = len(win_mv) // blk * blk
    avg = np.asarray(win_mv[:m]).reshape(-1, blk).mean(axis=1)
    step = float(np.max(np.abs(np.diff(avg)))) if len(avg) > 1 else 0.0
    return [abs(d), d, float(np.std(win_mv)), float(np.ptp(win_mv)), step,
            float(np.std(np.diff(win_mv)))]


class BoothTouch:
    def __init__(self, fs):
        self.fs = float(fs)
        self.n_keep = int(KEEP_SEC * self.fs)
        # 원신호(V). 같은 값을 두 자리(p, p+n)에 써서, 최근 n 개를 늘 이어진 한 토막으로 꺼낸다(표본마다 배열을 밀지 않는다).
        self.buf = np.zeros(2 * self.n_keep)
        self.count = 0                            # 지금까지 받은 표본 수
        self.lock = threading.Lock()
        self.rec = None                           # {"label", "start", "end"} — 표본 번호
        self.segments = []                        # [{"label", "start", "end"}]
        self.models = {}                          # 이름 → {"model", "acc", ...}
        self.selected = None
        self.train_info = None
        self.pred = None
        self._since_pred = 0
        self._win = int(WIN_SEC * self.fs)
        self._hop = int(HOP_SEC * self.fs)
        self._base = int(BASE_SEC * self.fs)
        self._gap = int(BASE_GAP_SEC * self.fs)

    # ── 실시간 루프가 표본마다 부른다 ──────────────────────────────
    def feed(self, v):
        with self.lock:
            p = self.count % self.n_keep
            self.buf[p] = self.buf[p + self.n_keep] = v
            self.count += 1
            if self.rec and self.count >= self.rec["end"]:
                self.segments.append(self.rec)
                self.rec = None
            self._since_pred += 1
            if self._since_pred >= self._hop:
                self._since_pred = 0
                self._predict()

    def _slice(self, a, b):
        """표본 번호 [a, b) 의 원신호(mV). 보관 범위를 벗어나면 None."""
        lo = self.count - self.n_keep
        if a < max(lo, 0) or b > self.count:
            return None
        return self._recent()[a - lo:b - lo] * 1000.0

    def _recent(self):
        """최근 n_keep 개(오래된 것 → 최근). 표본 번호 count - n_keep 부터."""
        p = self.count % self.n_keep
        return self.buf[p:p + self.n_keep]

    def _feat_at(self, end):
        """표본 번호 end 에서 끝나는 창의 특징. 기준선 구간이 모자라면 있는 만큼 쓴다."""
        win = self._slice(end - self._win, end)
        if win is None:
            return None
        b1 = end - self._win - self._gap
        b0 = max(b1 - self._base, self.count - self.n_keep, 0)
        base = self._slice(b0, b1) if b1 - b0 >= int(self.fs) else None
        return window_features(win, base if base is not None else win, self.fs)

    def _predict(self):
        if not self.selected or self.selected not in self.models or self.count < self._win:
            self.pred = None
            return
        f = self._feat_at(self.count)
        if f is None:
            self.pred = None
            return
        m = self.models[self.selected]["model"]
        p = m.predict_proba(np.asarray([f]))[0]
        k = int(np.argmax(p))
        self.pred = {"label": LABELS[int(m.classes_[k])], "proba": round(float(p[k]), 3),
                     "probs": {LABELS[int(c)]: round(float(q), 3) for c, q in zip(m.classes_, p)},
                     "feature0": round(f[0], 2)}

    # ── 화면이 부르는 동작 ─────────────────────────────────────────
    def start_record(self, label, seconds):
        if label not in LABELS:
            return False, "라벨은 비접촉 또는 접촉"
        seconds = float(min(max(seconds, MIN_REC_SEC), MAX_REC_SEC))
        with self.lock:
            if self.rec:
                return False, "이미 기록 중입니다"
            self.rec = {"label": label, "start": self.count, "end": self.count + int(seconds * self.fs)}
        return True, None

    def reset(self):
        with self.lock:
            self.rec, self.segments, self.models = None, [], {}
            self.selected, self.train_info, self.pred = None, None, None

    def select(self, name):
        with self.lock:
            if name not in self.models:
                return False, "아직 학습하지 않은 모델입니다"
            self.selected = name
        return True, None

    def _windows(self, seg):
        """기록 한 번 → (창 끝 표본 번호 목록). 창 전체가 기록 안에 들어오는 것만."""
        return list(range(seg["start"] + self._win, seg["end"] + 1, self._hop))

    def train(self):
        """기록한 구간으로 세 모델을 학습한다. 평가는 학습에 안 쓴 구간으로 한다:
        라벨마다 기록이 2번 이상이면 마지막 기록을, 1번뿐이면 그 기록의 뒤 절반을 평가에 쓴다
        (창이 겹치므로 무작위로 나누면 정확도가 부풀려진다)."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVC
        from sklearn.tree import DecisionTreeClassifier
        with self.lock:
            segs = list(self.segments)
            Xtr, ytr, Xte, yte = [], [], [], []
            split_how = []
            for li, label in enumerate(LABELS):
                mine = [s for s in segs if s["label"] == label]
                if not mine:
                    return False, f"'{label}' 기록이 없습니다"
                if len(mine) >= 2:
                    parts = [(s, "train") for s in mine[:-1]] + [(mine[-1], "test")]
                    split_how.append(f"{label}: 마지막 기록으로 평가")
                else:
                    parts = [(mine[0], "half")]
                    split_how.append(f"{label}: 기록 뒤 절반으로 평가")
                for s, how in parts:
                    ends = self._windows(s)
                    feats = [(e, self._feat_at(e)) for e in ends]
                    feats = [(e, f) for e, f in feats if f is not None]
                    if how == "half":
                        mid = (s["start"] + s["end"]) // 2
                        for e, f in feats:
                            if e <= mid:
                                Xtr.append(f); ytr.append(li)
                            elif e - self._win >= mid:          # 앞 절반과 겹치지 않는 창만
                                Xte.append(f); yte.append(li)
                    else:
                        for e, f in feats:
                            (Xtr if how == "train" else Xte).append(f)
                            (ytr if how == "train" else yte).append(li)
        if len(set(ytr)) < 2 or len(set(yte)) < 2:
            return False, "기록이 너무 짧거나 오래돼 창을 만들지 못했습니다. 다시 기록해 주세요"
        Xtr, ytr, Xte, yte = map(np.asarray, (Xtr, ytr, Xte, yte))
        made = {}
        specs = {"문턱 하나": DecisionTreeClassifier(max_depth=1, random_state=0),
                 "SVM": make_pipeline(StandardScaler(), SVC(probability=True, random_state=0)),
                 "랜덤 포레스트": RandomForestClassifier(n_estimators=100, random_state=0)}
        for name, model in specs.items():
            model.fit(Xtr, ytr)
            pred = model.predict(Xte)
            hit = [int(np.sum((pred == li) & (yte == li))) for li in range(len(LABELS))]
            tot = [int(np.sum(yte == li)) for li in range(len(LABELS))]
            info = {"model": model, "correct": int(np.sum(pred == yte)), "total": int(len(yte)),
                    # 균형 정확도 = 라벨별 맞힌 비율의 평균
                    "balanced": round(float(np.mean([h / t for h, t in zip(hit, tot)])), 3),
                    "per_label": {LABELS[li]: [hit[li], tot[li]] for li in range(len(LABELS))}}
            if name == "문턱 하나":
                tr = model.tree_
                info["rule"] = (f"{FEATURES[int(tr.feature[0])]} > {float(tr.threshold[0]):.2f} 이면 "
                                f"{LABELS[int(np.argmax(tr.value[2]))]}") if tr.feature[0] >= 0 else "나눌 기준을 찾지 못함"
            made[name] = info
        with self.lock:
            self.models = made
            if self.selected not in made:
                self.selected = "문턱 하나"
            self.train_info = {"n_train": int(len(ytr)), "n_test": int(len(yte)), "split": split_how,
                               "window_sec": WIN_SEC, "features": list(FEATURES)}
        return True, None

    def status(self):
        with self.lock:
            fs = self.fs
            blk = max(1, int(round(PLOT_AVG_SEC * fs)))
            n = min(int(PLOT_SEC * fs), self.count, self.n_keep) // blk * blk
            sig = (self._recent()[-n:].reshape(-1, blk).mean(axis=1) * 1000.0) if n else np.zeros(0)
            t_now = self.count
            def rel(s):      # 지금으로부터 몇 초 전인지(음수 = 과거)
                return [round((s["start"] - t_now) / fs, 2), round((min(s["end"], t_now) - t_now) / fs, 2)]
            segs = [{"label": s["label"], "t": rel(s), "sec": round((s["end"] - s["start"]) / fs, 1),
                     "usable": s["start"] >= t_now - self.n_keep} for s in self.segments]
            rec = None
            if self.rec:
                rec = {"label": self.rec["label"], "t": rel(self.rec),
                       "left": round(max(0.0, (self.rec["end"] - t_now) / fs), 1),
                       "total": round((self.rec["end"] - self.rec["start"]) / fs, 1)}
            models = [{"name": k, **{a: b for a, b in self.models[k].items() if a != "model"}}
                      for k in MODEL_NAMES if k in self.models]
            return {"ok": True, "signal_mv": np.round(sig, 3).tolist(), "signal_hz": round(fs / blk, 3),
                    "plot_sec": PLOT_SEC, "recording": rec, "segments": segs,
                    "counts": {lb: sum(1 for s in self.segments if s["label"] == lb) for lb in LABELS},
                    "models": models, "selected": self.selected, "train": self.train_info,
                    "pred": self.pred, "labels": list(LABELS), "window_sec": WIN_SEC,
                    "rec_default_sec": 8, "keep_sec": KEEP_SEC}


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
