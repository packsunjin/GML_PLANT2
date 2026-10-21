"""
preprocess.py
=============
data/raw/*.csv 의 원시 전위 신호를 다음과 같이 처리합니다.

1. band_filter.py 의 대역통과(기본 0.01~1Hz)로 DC 드리프트·전원 노이즈 제거.
   원신호를 10Hz 로 줄여(25개 평균 = 60Hz·240Hz 를 0 으로 만드는 안티앨리어싱) 인과 필터를 걸고,
   창 앞 90초를 '문맥'으로 같이 필터링한다(느린 하한의 과도응답을 창 밖으로 밀어내려고).
2. 필터링된 신호를 일정 길이의 윈도우로 나누어 스펙트로그램(224x224, viridis) 이미지 생성
   + 동일한 윈도우에서 명시적 통계/주파수 특징 14개(feature_extraction.py) 추출
3. data/spectrogram/{정상,자극}/ 폴더에 상태별로 이미지 저장
4. data/features.csv 에 윈도우별 특징 벡터 저장 (train.py의 features/both 모드에서 사용)

data/raw/ 에 정상.csv, 자극.csv 중 일부만 있어도 있는 파일만으로 진행하며, 어떤 상태가 빠졌는지 안내만 출력합니다.

실행:
    python preprocess.py
    python preprocess.py --raw_dir ../data/raw --out_dir ../data/spectrogram
"""

import argparse
import json
import os

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import venv_boot; venv_boot.ensure()   # venv 를 안 켜도 알아서 갈아탄다

import numpy as np
import pandas as pd
from band_filter import (analysis_filter, analysis_rate, LOWCUT_HZ, HIGHCUT_HZ,
                         DECIM_HZ, CONTEXT_SEC)

from spectro_render import render_rgb_image, compute_spectrogram
import sensor_control
from sensor_control import ANALOG_HPF_HZ, ANALOG_LPF_HZ, FRONTEND_GAIN, FRONTEND
from feature_extraction import extract_features, FEATURE_NAMES

# 원시 파일명 -> 상태(클래스) 매핑. 정상/자극 두 상태를 각각 별도 클래스로 저장한다.
FILE_TO_STATE = {
    "정상.csv": "정상",
    "자극.csv": "자극",
}

# 상태마다 **여러 번 나눠 측정한 파일**을 받는다.
#   정상.csv, 정상_2.csv, 정상_20260825_1430.csv  →  전부 '정상'
#
# 왜 필요한가. 상태마다 세션이 하나뿐이면, 그 세션의 전극이 어느 방향으로 표류했는지가
# 곧 클래스 라벨이 되어 버린다. "그 상태라서 전위가 밀린 것"과 "그날 그 전극이 그렇게
# 표류한 것"을 구분할 방법이 없다. 실제로 이 프로젝트의 1차 학습에서 나온 높은 정확도가
# 식물 반응이 아니라 전극 부착 조건의 차이였다(보고서 Ⅳ장 2절 (4)).
# 세션을 여러 번 나눠 측정하고, 학습·평가를 **세션 단위로** 갈라야 그 혼동을 뺄 수 있다.
STATE_SUFFIX_SEP = "_"


def state_of(fname):
    """파일명에서 상태를 알아낸다. 모르는 파일이면 None.
    '정상.csv' 도 '정상_3.csv' 도 '정상' 이다.
    누른 시각 기록('자극_2.presses.csv')과 온습도 기록('정상_3.env.csv')은 상태 파일이 아니다
    — '_' 로 자르면 상태 이름이 되므로 먼저 뺀다."""
    if not fname.lower().endswith(".csv") or fname.endswith((".presses.csv", ".env.csv")):
        return None
    stem = fname[:-4]
    if stem + ".csv" in FILE_TO_STATE:
        return FILE_TO_STATE[stem + ".csv"]
    head = stem.split(STATE_SUFFIX_SEP)[0]
    return FILE_TO_STATE.get(head + ".csv")


def session_of(fname):
    """세션 이름(= 파일 이름에서 확장자 뺀 것). 학습/평가를 이 단위로 가른다."""
    return fname[:-4] if fname.lower().endswith(".csv") else fname

# ---- 품질 기준 --------------------------------------------------------
# 전극이 잘 안 붙으면 AD8232 출력이 전원 레일에 붙어버린다(3.3V 계통 기준 3.2V 근처).
# 그 구간은 증폭기 포화지 식물 신호가 아니므로 학습에서 제외한다.
RAIL_HIGH_V = 3.0   # 이 위로 평균이 올라간 창은 버림
RAIL_LOW_V = 0.3    # 이 아래로 내려간 창도 버림
# 필터 후 표준편차가 이보다 작으면 신호가 없다고 본다.
# ⚠️ 이 값은 **앞단의 이득에 따라 달라진다.** AD8232 는 1100배로 증폭해서 내보내지만
# DC 결합은 증폭하지 않으므로, 같은 전극 신호라도 ADC 가 보는 크기가 1100배 다르다.
# 그래서 전극 입력 환산으로 기준을 정하고(0.45µV), 앞단의 이득을 곱해 쓴다.
MIN_STD_INPUT_UV = 0.45
MIN_STD_V = MIN_STD_INPUT_UV * 1e-6 * FRONTEND_GAIN

# 위의 절대 문턱만으로는 포화를 못 잡는 경우가 있다. 실제로 이 프로젝트에서 수집한
# CSV 6개를 조사한 결과가 그랬다. 모든 파일의 최댓값이 2.57~2.60V, 최솟값이 -0.59~-0.61V로
# 일정했는데, 이는 이 보드의 실제 출력 한계다. 그런데 위 문턱은 3.0V/0.3V라서,
# 전 구간이 2.56~2.60V에 붙어 있던 파일(= 완전히 상단 포화)이 100% 통과해 버렸다.
#
# 그래서 문턱을 짐작하지 않고 신호에서 직접 찾는다. 증폭기가 포화하면 출력이 한 값에
# 머무르므로, 파일의 극값 근처에 샘플이 눈에 띄게 몰린다. 그 몰림이 보이면 그 극값을
# 레일로 인정하고, 창별로 레일에 붙은 샘플 비율을 재서 버린다.
# 포화되지 않은 파일은 극값을 한두 번만 스치므로 레일이 검출되지 않고, 따라서 아무것도
# 버리지 않는다(실측 6개 파일로 확인: 깨끗한 2개는 검출 0건, 포화된 2개는 전량 제외).
# AD8232의 fast-restore 는 전극 임피던스가 높으면 계속 재작동하면서 출력을 순간적으로
# 0V 근처까지 떨어뜨린다(실측: 168ms마다 약 20ms). 이건 식물 신호가 아니라 회로 동작이고,
# 창마다 여러 번씩 들어가 모든 창을 오염시키므로 창 단위로 거를 수가 없다.
# -> 그 구간만 찾아 양옆 값으로 이어 붙인다(심전도에서 페이스메이커 스파이크를 지우는 것과 같은 처리).
DROPOUT_FRAC = 0.5   # 창 중앙값의 이 비율보다 낮으면 강하로 본다
DROPOUT_MAX = 0.15   # 전체의 이 비율을 넘게 걸리면 신호 자체가 이상한 것이므로 손대지 않는다

# "자극"은 정상과 달리 지속 상태가 아니라 순간 이벤트다(파일 상단 주석 참고).
# 그런데 5분을 수집해도 실제로 반응이 담긴 구간은 짧고, 나머지 대부분은 조용한 baseline이다.
# 파일 하나를 통째로 "자극"이라 라벨링하면 그 조용한 구간까지 전부 "자극"으로 잘못 학습되어,
# 모델이 사실상 "자극 = 아무 신호"라고 배우고 실사용에서 계속 자극만 예측하게 된다.
# -> 자극 파일에서는 그 파일 안에서 상대적으로 튀는 창만 남기고 나머지 조용한 창은 버린다.
#    정상은 지속 상태라 이 필터를 적용하지 않는다.
# std가 아니라 peak-to-peak(최대-최소)으로 판단한다: 반응 스파이크는 보통 창 안에서
# 아주 짧게(수십 ms) 튀므로, std는 나머지 조용한 구간에 묻혀 거의 안 움직이지만 p2p는
# 그 짧은 스파이크 하나만으로도 확 뛴다.
EVENT_ONLY_STATE = "자극"
EVENT_P2P_MULT = 2.0
EVENT_MIN_WINDOWS = 10  # 이 미만이면 파일 내 편차가 별로 없다는 뜻이라 거르지 않는다

# 위의 '튀는 창만 남기기'는 정상 밤샘 기록에도 같은 크기의 자연 출렁임이 있어 맞지 않았다(0절 ㉓·㉗).
# 그래서 자극 회차 CSV 옆에 누른 시각 기록(<이름>.presses.csv)이 있으면 그것으로 라벨을 붙인다.
# 누른 시각이 든 창 = 자극, 나머지 = 정상. 이 경우 이벤트 선별은 하지 않는다.
NORMAL_STATE = "정상"
PRESS_SUFFIX = ".presses.csv"


def press_times(csv_path):
    """자극 회차의 누른(댄) 시각(파일 기준 초). 기록 파일이 없거나 열을 모르면 None.

    report/stim/ml_touch.py 의 touch_times() 와 같은 규칙이다.
      · file_sec 열이 있으면(1회차): 누르고 바로 기록(최대 10초 늦음) → file_sec − 5
      · 없고 lap_sec 만 있으면(2회차): 대고 약 5초 뒤 기록, 스톱워치 0~5초 늦게 켬 → lap_sec − 2.5
    """
    p = os.path.splitext(csv_path)[0] + PRESS_SUFFIX
    if not os.path.isfile(p):
        return None
    d = pd.read_csv(p, comment="#")
    if "file_sec" in d.columns:
        t = d["file_sec"] - 5.0
    elif "lap_sec" in d.columns:
        t = d["lap_sec"] - 2.5
    else:
        print(f"    ⚠️  {os.path.basename(p)} 에 file_sec·lap_sec 열이 없어 누른 시각을 못 읽습니다")
        return None
    return pd.to_numeric(t, errors="coerce").dropna().to_numpy(dtype=float)


RAIL_BAND_V = 0.03       # 극값에서 이 안이면 '레일에 붙었다'로 본다
RAIL_PILE_FRAC = 0.005   # 극값 근처에 이 비율 이상 몰려 있으면 그 극값은 레일이다
RAIL_WIN_FRAC = 0.20     # 창의 이 비율 이상이 레일에 붙어 있으면 그 창은 버린다


def detect_rails(signal, band=RAIL_BAND_V, pile=RAIL_PILE_FRAC):
    """신호에서 증폭기 출력 한계(레일)를 찾아 (하단, 상단)으로 돌려준다.

    포화가 없으면 해당 쪽은 None이다. 보드마다 다른 레일 전압을 미리 몰라도 되고,
    시뮬레이션처럼 0V 중심인 신호에도 잘못 걸리지 않는다."""
    v = np.asarray(signal, dtype=float)
    if len(v) < 100:
        return None, None
    mx = float(v.max()); mn = float(v.min())
    hi = mx if float((v >= mx - band).mean()) >= pile else None
    lo = mn if float((v <= mn + band).mean()) >= pile else None
    return lo, hi


def rail_fraction(win, lo, hi, band=RAIL_BAND_V):
    """창에서 레일에 붙어 있는 샘플의 비율.

    상단·하단을 각각 세어 더하면, 신호가 레일 폭보다 좁은 띠에 갇혔을 때 같은 샘플을
    두 번 세어 100%를 넘어 버린다(실측에서 190%가 나왔다). 합집합으로 센다."""
    w = np.asarray(win, dtype=float)
    mask = np.zeros(len(w), dtype=bool)
    if hi is not None:
        mask |= (w >= hi - band)
    if lo is not None:
        mask |= (w <= lo + band)
    return float(mask.mean())


def repair_dropouts(raw_win):
    """fast-restore 로 인한 순간적인 0V 강하를 양옆 값으로 보간해 없앤다.
    (고친 샘플 수, 고친 신호)를 돌려준다. 고칠 게 없으면 원본을 그대로 준다."""
    med = float(np.median(raw_win))
    if med <= 0.3:                      # 0V 중심 신호(시뮬레이션)에는 적용하지 않는다
        return 0, raw_win
    bad = raw_win < med * DROPOUT_FRAC
    n_bad = int(bad.sum())
    if n_bad == 0 or n_bad > len(raw_win) * DROPOUT_MAX:
        return 0, raw_win
    fixed = raw_win.copy()
    good = np.where(~bad)[0]
    if len(good) < 2:
        return 0, raw_win
    fixed[bad] = np.interp(np.where(bad)[0], good, raw_win[good])
    return n_bad, fixed

SAMPLE_RATE_HZ = 250.0  # sensor_control.py 기본 샘플링과 일치

# 분석 창 길이와 대역은 "무엇을 잡으려는 신호인가"로 정한다.
#
#  · 문헌의 식물 활동전위: 일반 식물 "수십 초"(Mudrilov 2021), 접촉 유발 AP 약 10.7초(Degli Agosti 2014)
#    → 주성분 0.01~0.1 Hz. 대역은 0.01~1 Hz (band_filter.py 에 이유).
#  · 창은 AP 한두 개가 통째로 들어가도록 30초. 예전 10초(2초) 창은 AP 한 번보다 짧았다.
#  · 이동 간격 5초. 창이 83% 겹치므로 학습·평가는 반드시 파일(세션) 단위로 가른다.
#  · 창마다 앞 CONTEXT_SEC(90초)가 더 필요하다. 그보다 앞에서 시작하는 창은 쓰지 않는다.
WINDOW_SEC = 30.0       # 스펙트로그램 1장을 만들 신호 구간 길이 (활동전위 수십 초)
STEP_SEC = 5.0          # 슬라이딩 윈도우 이동 간격
IMG_SIZE = 224


def bandpass_filter(signal, fs, low=LOWCUT_HZ, high=HIGHCUT_HZ, decim_hz=DECIM_HZ, **_ignored):
    """신호 전체를 필터링해 (분석 샘플레이트로 줄어든) 필터 통과 신호를 돌려준다.
    예전 호출부(report/*.py)용 얇은 껍데기다. 학습·추론은 band_filter.analysis_filter 를 쓴다.
    (예전의 notch_freq 등 인자는 받아서 버린다 — 25개 평균이 60Hz 를 이미 0 으로 만든다)"""
    sig = np.asarray(signal, dtype=float)
    out, _ = analysis_filter(sig, fs, len(sig) / fs, low=low, high=high, decim_hz=decim_hz)
    return out


def make_spectrogram_image(Sxx_db, out_path, img_size=IMG_SIZE):
    """이미 계산된 Sxx_db 배열을 224x224 viridis 컬러맵 스펙트로그램 PNG로 저장.

    matplotlib Figure 렌더링 대신 컬러맵 룩업 테이블 기반 render_rgb_image()를 사용한다
    (inference.py의 signal_to_feature()가 쓰는 render_gray_array()와 같은 색상 로직을
    공유하는 spectro_render 모듈이라 학습/추론 특징이 일치한다)."""
    img = render_rgb_image(Sxx_db, img_size=img_size)
    img.save(out_path)


def process_file(csv_path, out_root, fs=SAMPLE_RATE_HZ, window_sec=WINDOW_SEC, step_sec=STEP_SEC,
                 low=LOWCUT_HZ, high=HIGHCUT_HZ, notch_freq=0.0,
                 decim_hz=DECIM_HZ, context_sec=CONTEXT_SEC,
                 quality=True, rail_high=RAIL_HIGH_V, rail_low=RAIL_LOW_V, min_std=MIN_STD_V,
                 rail_frac=RAIL_WIN_FRAC,
                 repair=True, ref_subtract=True):
    """CSV 하나를 윈도우 단위로 나눠 스펙트로그램 PNG를 저장하고,
    (이미지 수, 특징 행 리스트, 실제로 사용한 노치 주파수)를 반환한다.
    노치는 신호에서 50/60Hz를 재서 자동 보정하므로 파일마다 다를 수 있고,
    추론이 같은 필터를 쓰도록 이 값을 메타에 기록해야 한다.
    low/high 로 대역을 조절한다. notch_freq 는 이제 쓰지 않는다(0 이 기본, 값을 주면 50/60Hz 판별만 한다).
    context_sec: 창 앞에 붙일 문맥 길이. 그보다 파일 앞쪽에서 시작하는 창은 버린다."""
    fname = os.path.basename(csv_path)
    if state_of(fname) is None:
        print(f"  [건너뜀] 매핑되지 않은 파일: {fname}")
        return 0, [], notch_freq

    cls = state_of(fname)
    out_dir = os.path.join(out_root, cls)
    os.makedirs(out_dir, exist_ok=True)

    # 자극 회차에 누른 시각 기록이 있으면 창마다 라벨을 붙인다(위 PRESS_SUFFIX 설명).
    presses = press_times(csv_path) if cls == EVENT_ONLY_STATE else None

    # 이전에 만든 이미지를 먼저 지운다. 새로 수집한 CSV가 더 짧으면 예전 이미지가
    # 남아 학습 데이터에 섞이기 때문이다(파일명이 시작 인덱스라 덮어쓰기가 안 됨).
    # 이 CSV 의 이미지만 지운다. 폴더 전체를 지우면 같은 상태의 다른 세션 파일이
    # 만든 이미지까지 사라져 마지막 파일 것만 남는다(0절 ⑲).
    # 누른 시각 라벨을 쓰면 한 회차의 이미지가 정상·자극 두 폴더에 나뉘므로 모든 상태 폴더를 본다.
    base_name = os.path.splitext(fname)[0]
    stale = 0
    for st in sorted(set(FILE_TO_STATE.values())):
        d = os.path.join(out_root, st)
        if not os.path.isdir(d):
            continue
        for n in os.listdir(d):
            if n.lower().endswith(".png") and n.startswith(base_name + "_"):
                os.remove(os.path.join(d, n))
                stale += 1
    if stale:
        print(f"  이전 이미지 {stale}장 정리")

    df = pd.read_csv(csv_path)
    raw_signal = df["voltage"].to_numpy(dtype=float)

    # ── 참조(더미) 채널 빼기 ────────────────────────────────────────
    # voltage_ref 는 식물 없이 전극쌍만 담근 채널이다. 거기 담긴 것은 전극 표류와
    # 주변 잡음뿐이므로, 빼고 남는 것이 식물에서 온 성분이다.
    if "voltage_ref" in df.columns:
        ref = df["voltage_ref"].to_numpy(dtype=float)
        if ref_subtract:
            before = float(np.std(raw_signal))
            raw_signal = raw_signal - ref
            print(f"  참조 채널 차감: 표준편차 {before*1e3:.3f} -> "
                  f"{float(np.std(raw_signal))*1e3:.3f} mV "
                  f"(참조 자체 {float(np.std(ref))*1e3:.3f} mV)")
        else:
            print(f"  참조 채널이 있으나 차감하지 않음(--no-ref-subtract). "
                  f"표류가 그대로 남아 있어 느린 신호 분류는 믿을 수 없다.")

    # 샘플레이트는 가정하지 않고 CSV의 timestamp 에서 실제로 계산한다.
    # 하드웨어가 목표 속도를 못 따라가면(ADS1115 가 느릴 때) 실제 250Hz가 아닌데,
    # 250Hz로 가정하면 필터 대역과 스펙트로그램 주파수축이 통째로 어긋난다.
    if "timestamp_sec" in df.columns and len(df) > 10:
        dt = float(np.median(np.diff(df["timestamp_sec"].to_numpy(dtype=float))))
        if dt > 0:
            # 부동소수 오차로 250이 249.9999... 로 나오면 창 길이가 1샘플 밀린다.
            # 소수 둘째 자리로 정리하고, 정수에 아주 가까우면 정수로 스냅한다.
            measured = round(1.0 / dt, 2)
            if abs(measured - round(measured)) < 0.05:
                measured = float(round(measured))
            if abs(measured - fs) / fs > 0.05:
                print(f"  [샘플레이트] CSV 실측 {measured:.1f}Hz (기본 {fs:.0f}Hz와 다름) -> 실측값 사용")
            fs = measured

    # 전원 노이즈 주파수를 신호에서 직접 찾는다. 한국은 60Hz, 유럽/시뮬레이션은 50Hz라
    # 고정값을 쓰면 한쪽이 항상 틀린다. 두 후보의 파워를 재서 센 쪽을 노치한다.
    if notch_freq and len(raw_signal) > int(fs) * 2:
        from scipy.signal import welch as _welch
        _f, _P = _welch(raw_signal - raw_signal.mean(), fs=fs, nperseg=min(4096, len(raw_signal)))
        def _at(hz):
            m = (_f > hz - 1.5) & (_f < hz + 1.5)
            return float(_P[m].sum()) if m.any() else 0.0
        p50, p60 = _at(50.0), _at(60.0)
        picked = 60.0 if p60 > p50 * 1.5 else (50.0 if p50 > p60 * 1.5 else notch_freq)
        if picked != notch_freq:
            tot = float(_P.sum()) or 1.0
            print(f"  [전원 노이즈] 50Hz {100*p50/tot:.1f}% / 60Hz {100*p60/tot:.1f}% "
                  f"-> 노치를 {picked:.0f}Hz 로 맞춤")
            notch_freq = picked

    # 레일 포화 검사는 단전원(0~3.3V) 하드웨어 신호에만 의미가 있다. 시뮬레이션 CSV는
    # 0V를 중심으로 흔들리므로 그대로 적용하면 전부 "바닥 레일"로 오판한다.
    # 파일의 중앙값이 0.5V보다 위면 하드웨어 신호로 보고 레일 검사를 켠다.
    hw_like = float(np.median(raw_signal)) > 0.5
    rail_check = quality and hw_like

    rail_lo = rail_hi = None
    if rail_check:
        rail_lo, rail_hi = detect_rails(raw_signal)
        if rail_lo is not None or rail_hi is not None:
            at = 100.0 * rail_fraction(raw_signal, rail_lo, rail_hi)
            print(f"    [레일 검출] 하단 {('%.2fV' % rail_lo) if rail_lo is not None else '—'} / "
                  f"상단 {('%.2fV' % rail_hi) if rail_hi is not None else '—'} "
                  f"— 전체 샘플의 {at:.1f}%가 레일에 붙어 있습니다.")

    win_len = int(round(window_sec * fs))
    step_len = int(round(step_sec * fs))
    ctx_len = int(round(context_sec * fs))
    fs_a = analysis_rate(fs, decim_hz)      # 필터·스펙트로그램·특징이 보는 샘플레이트

    count = 0
    skipped_rail = 0
    skipped_clip = 0
    skipped_flat = 0
    skipped_quiet = 0
    skipped_ctx = 0
    repaired_samples = 0
    repaired_windows = 0
    feature_rows = []
    base_name = os.path.splitext(fname)[0]
    # 필터는 각 윈도우를 개별적으로 적용한다. 실시간 추론(inference.py)은 스트리밍으로 들어온
    # 버퍼 하나만 필터링할 수 있으므로, 학습 특징도 반드시 "윈도우 단위 필터링"으로 만들어야
    # 필터 과도응답까지 포함해 학습/추론 특징이 일치한다. (전체 신호를 한 번에 필터링한 뒤
    # 잘라내면 윈도우 경계의 과도응답이 서로 달라 train/serve skew가 생긴다 — 특히 통계/주파수
    # 특징 14개는 이 차이에 민감하다.)
    # 1차 패스: 레일/보정/필터까지 끝낸 창과 그 std를 모아 둔다. '자극'의 이벤트 문턱값은
    # 이 파일 안의 std 분포를 봐야 정할 수 있어서(파일마다 baseline이 다름) 미리 다 훑는다.
    prepared = []
    for start in range(0, len(raw_signal) - win_len + 1, step_len):
        if start < ctx_len:         # 앞 문맥이 모자라면 추론(항상 문맥이 찬 버퍼)과 특징이 달라진다
            skipped_ctx += 1
            continue
        raw_win = raw_signal[start:start + win_len]

        # ---- 품질 검사 ----------------------------------------------------
        # 전극 접촉이 나쁘면 AD8232 출력이 전원 레일에 붙는다(3.3V 계통에서 3.2V 근처).
        # 그런 구간은 식물 신호가 아니라 증폭기 포화라서 학습에 넣으면 안 된다.
        # 스펙트로그램은 장마다 정규화되므로 이미지만 봐서는 구분이 안 된다 -> 여기서 거른다.
        if rail_check:
            m = float(np.mean(raw_win))
            if m > rail_high or m < rail_low:
                skipped_rail += 1
                continue
            # 평균이 정상 범위여도 파형이 레일에 붙어 있을 수 있다(위 RAIL_* 주석 참고).
            if (rail_lo is not None or rail_hi is not None) and \
                    rail_fraction(raw_win, rail_lo, rail_hi) > rail_frac:
                skipped_clip += 1
                continue

        # fast-restore 강하를 먼저 지우고 필터를 건다(필터 전에 지워야 링잉이 안 남는다).
        raw_ctx = raw_signal[start - ctx_len:start + win_len]      # 문맥 + 창(끝이 창 끝)
        if repair and hw_like:
            n_fix, raw_ctx = repair_dropouts(raw_ctx)
            raw_win = raw_ctx[-win_len:]
            if n_fix:
                repaired_samples += n_fix
                repaired_windows += 1

        segment, _ = analysis_filter(raw_ctx, fs, window_sec, low=low, high=high, decim_hz=decim_hz)
        std = float(np.std(segment))

        if quality and std < min_std:
            # 필터 후에도 거의 평평하면 신호가 없는 것(선 빠짐/전원만 잡힘).
            skipped_flat += 1
            continue

        p2p = float(segment.max() - segment.min())
        # 느린 특징은 필터 전 원신호에서만 볼 수 있으므로 함께 들고 간다.
        prepared.append((start, segment, p2p, raw_win))

    # 2차 패스: '자극' 파일은 이 파일 안에서 상대적으로 튀는 창만 남긴다(위 EVENT_ONLY_STATE 설명).
    event_thresh = None
    if presses is None and quality and cls == EVENT_ONLY_STATE and len(prepared) >= EVENT_MIN_WINDOWS:
        p2ps = np.array([p[2] for p in prepared])
        baseline = float(np.median(p2ps))
        thresh = baseline * EVENT_P2P_MULT
        if np.any(p2ps > thresh):   # 전부 baseline 근처면(계속 자극 중) 거르지 않는다
            event_thresh = thresh

    # 측정 시작 시점의 기준 전위. 느린 드리프트는 '시작 대비 얼마나 밀렸나'로 재야
    # 의미가 있어서, 파일 앞부분 평균을 기준선으로 삼는다.
    dc_baseline = float(np.mean(prepared[0][3])) if prepared else 0.0

    by_label = {}
    for start, segment, p2p, raw_seg in prepared:
        if event_thresh is not None and p2p <= event_thresh:
            skipped_quiet += 1
            continue

        win_cls = cls
        if presses is not None:
            a = start / fs
            win_cls = EVENT_ONLY_STATE if np.any((presses >= a) & (presses <= a + window_sec)) \
                else NORMAL_STATE
        win_dir = os.path.join(out_root, win_cls)
        os.makedirs(win_dir, exist_ok=True)

        # inference.py와 같은 함수(spectro_render.compute_spectrogram)를 쓴다.
        Sxx_db, f, t = compute_spectrogram(segment, fs_a, high=high)

        img_name = f"{base_name}_{start:06d}.png"
        img_path = os.path.join(win_dir, img_name)
        make_spectrogram_image(Sxx_db, img_path)

        feats = extract_features(segment, Sxx_db, f, t, fs=fs_a,
                                 raw_window=raw_seg, baseline=dc_baseline, raw_fs=fs)
        feature_rows.append([img_name, fname, win_cls] + feats.tolist())

        by_label[win_cls] = by_label.get(win_cls, 0) + 1
        count += 1

    if presses is not None:
        print(f"    [누른 시각 라벨] 누른 시각 {len(presses)}번 → 그 시각이 든 {window_sec:g}초 창 = 자극 "
              f"{by_label.get(EVENT_ONLY_STATE, 0)}창, 나머지 = 정상 {by_label.get(NORMAL_STATE, 0)}창")
    if event_thresh is not None:
        print(f"    [이벤트 선별] '{cls}'는 순간 이벤트라 조용한 창은 뺌 — "
              f"{skipped_quiet}창 제외, {count}창만 사용 (문턱값 p2p>{event_thresh:.4f}V)")
    if repaired_windows:
        print(f"    [보정] fast-restore 강하 제거 — {repaired_windows}창에서 {repaired_samples}샘플 보간")
    if quality and not hw_like:
        print("    [품질] 0V 중심 신호(DC 차동 앞단·시뮬레이션)라 레일 포화 검사는 건너뜁니다.")
    total_win = count + skipped_rail + skipped_clip + skipped_flat + skipped_quiet + skipped_ctx
    print(f"  {fname} -> 클래스 '{cls}': {count}개 스펙트로그램 이미지 생성"
          + (f"  (전체 {total_win}창 중 {100.0*count/total_win:.0f}% 사용)" if total_win else ""))
    if skipped_ctx:
        print(f"    [문맥] 앞 {context_sec:g}초 문맥이 모자라 {skipped_ctx}창 제외")
        if count == 0:
            print(f"    ⚠️  이 파일은 {window_sec + context_sec:g}초(창 {window_sec:g} + 문맥 {context_sec:g})보다 짧아 쓸 수 있는 창이 없습니다."
                  " 문맥을 포함해 더 길게 잘라 수집하세요.")
    if skipped_rail or skipped_flat or skipped_clip:
        print(f"    [품질] 건너뜀 — 전원 레일 포화 {skipped_rail}창"
              f"{f', 파형 잘림 {skipped_clip}창' if skipped_clip else ''}"
              f"{f', 신호 없음 {skipped_flat}창' if skipped_flat else ''}")
        if count == 0:
            print("    ⚠️  쓸 수 있는 구간이 하나도 없습니다. 전극 접촉을 확인하고 다시 수집하세요.")
        elif count < 10:
            print(f"    ⚠️  쓸 수 있는 창이 {count}개뿐입니다. 더 길게 수집하는 것이 좋습니다.")
    if event_thresh is not None and count < EVENT_MIN_WINDOWS:
        print(f"    ⚠️  이벤트 창이 {count}개뿐입니다. 수집할 때 더 자주(10~15초 간격) "
              "잎을 건드려 반응 구간을 늘려주세요.")
    return count, feature_rows, notch_freq


def main():
    parser = argparse.ArgumentParser(description="CSV 원시 신호 -> 대역통과필터 -> 스펙트로그램 이미지 + 특징")
    parser.add_argument("--raw_dir", default="../data/raw")
    parser.add_argument("--out_dir", default="../data/spectrogram")
    parser.add_argument("--features_csv", default="../data/features.csv")
    parser.add_argument("--lowcut", type=float, default=LOWCUT_HZ,
                        help="대역통과 하한(Hz). 기본 0.01 — 활동전위(수십 초)의 주성분 0.01~0.1Hz 를 살린다. "
                             "AD8232 는 0.5Hz 아래를 회로에서 이미 잘라내므로 DC 결합 앞단에서만 의미가 있다")
    parser.add_argument("--highcut", type=float, default=HIGHCUT_HZ,
                        help="대역통과 상한(Hz). 기본 1Hz. 분석 샘플레이트(기본 10Hz)의 나이퀴스트(5Hz) 미만이어야 한다")
    parser.add_argument("--decim_hz", type=float, default=DECIM_HZ,
                        help="필터를 거는 샘플레이트(Hz). 원신호를 이 속도로 평균해 줄인다")
    parser.add_argument("--context_sec", type=float, default=CONTEXT_SEC,
                        help="창 앞에 붙이는 문맥(초). 느린 고역통과의 과도응답을 창 밖으로 밀어낸다. "
                             "학습·추론이 같은 값을 써야 한다")
    parser.add_argument("--notch", type=float, default=0.0,
                        help="(쓰지 않음) 10Hz 로 줄이는 25개 평균이 60Hz·240Hz 를 이미 0 으로 만든다. "
                             "메타 호환용으로만 남겼다")
    parser.add_argument("--no-ref-subtract", action="store_true",
                        help="voltage_ref 열이 있어도 빼지 않는다. 참조 채널이 제대로 "
                             "동작하는지 따로 보고 싶을 때만 쓴다.")
    parser.add_argument("--no-repair", action="store_true",
                        help="fast-restore 강하 보간을 끄고 원신호 그대로 사용한다")
    parser.add_argument("--no-quality", action="store_true",
                        help="품질 검사를 끄고 모든 창을 그대로 변환한다(포화 구간 포함)")
    parser.add_argument("--rail-high", type=float, default=RAIL_HIGH_V,
                        help=f"평균이 이 값보다 높은 창은 포화로 보고 버림(기본 {RAIL_HIGH_V}V)")
    parser.add_argument("--rail-frac", type=float, default=RAIL_WIN_FRAC,
                        help=f"창의 이 비율 이상이 증폭기 출력 한계에 붙어 있으면 버림(기본 {RAIL_WIN_FRAC})")
    parser.add_argument("--min-std", type=float, default=MIN_STD_V,
                        help=f"필터 후 표준편차가 이보다 작으면 신호 없음으로 보고 버림(기본 {MIN_STD_V}V)")
    parser.add_argument("--window_sec", type=float, default=WINDOW_SEC,
                        help="분석 창 길이(초). 학습·추론이 같은 값을 써야 한다")
    parser.add_argument("--step_sec", type=float, default=STEP_SEC,
                        help="창 이동 간격(초)")
    parser.add_argument("--only", default=None, choices=sorted(set(FILE_TO_STATE.values())),
                        help="이 상태 하나만 변환한다. 나머지 상태의 결과는 그대로 둔다.")
    args = parser.parse_args()

    print(f"[preprocess] 원시 데이터: {args.raw_dir}")
    print(f"[preprocess] 출력(스펙트로그램): {args.out_dir}")
    print(f"[preprocess] 창 {args.window_sec}초 / 스텝 {args.step_sec}초")
    # AD8232의 아날로그 대역(0.5~40Hz) 밖을 지정하면 소프트웨어 필터는 헛돈다.
    if ANALOG_HPF_HZ > 0 and args.lowcut < ANALOG_HPF_HZ:
        print(f"[preprocess] ⚠️  하한 {args.lowcut}Hz 는 {FRONTEND.title}의 고역통과({ANALOG_HPF_HZ}Hz)보다 낮습니다.")
        print("    회로에서 이미 지워진 대역이라 하드웨어 데이터에서는 효과가 없습니다"
              " (시뮬레이션 데이터에는 적용됩니다).")
    # lpf_hz == 0 은 '설정된 저역통과 없음'(DC 결합)이라는 뜻이라 비교 대상이 아니다.
    if ANALOG_LPF_HZ > 0 and args.highcut > ANALOG_LPF_HZ:
        print(f"[preprocess] ⚠️  상한 {args.highcut}Hz 는 {FRONTEND.title}의 저역통과({ANALOG_LPF_HZ}Hz)보다 높습니다.")
        print("    그 위에는 회로가 통과시킨 신호가 없습니다.")
    print(f"[preprocess] 필터: 대역통과 {args.lowcut}~{args.highcut}Hz ({args.decim_hz:g}Hz 로 줄인 뒤 인과 필터, "
          f"문맥 {args.context_sec:g}초)")
    if args.highcut >= 0.5 * analysis_rate(SAMPLE_RATE_HZ, args.decim_hz):
        print("❌ 상한이 분석 샘플레이트의 나이퀴스트 이상입니다. --decim_hz 를 올리거나 --highcut 을 낮추세요.")
        return
    if args.only:
        print(f"[preprocess] 대상: '{args.only}' 하나만 변환")

    existing = set(os.listdir(args.raw_dir)) if os.path.isdir(args.raw_dir) else set()
    if args.only:
        # 한 상태만 돌릴 때는 그 파일만 본다.
        targets = {f for f in existing if state_of(f) == args.only}
        if not targets:
            print(f"❌ '{args.only}' 의 원시 CSV가 없습니다. 먼저 수집하세요.")
            return
    else:
        targets = existing
        # 상태별로 몇 세션이 모였는지 센다. '정상.csv' 하나만 보면 '정상_2.csv' 같은
        # 추가 세션을 못 알아보고 "수집 안 됨"이라고 잘못 알린다.
        by_state = {}
        for f in existing:
            st = state_of(f)
            if st:
                by_state.setdefault(st, []).append(f)
        all_states = sorted(set(FILE_TO_STATE.values()))
        missing_states = [st for st in all_states if st not in by_state]
        if missing_states:
            print(f"⚠️  다음 상태가 수집되지 않았습니다: {', '.join(missing_states)}")
            got = [f"{st}({len(v)}세션)" for st, v in sorted(by_state.items())]
            print(f"   ({' + '.join(got) if got else '수집된 상태 없음'} 데이터만으로 진행합니다)")
        single = [st for st, v in by_state.items() if len(v) == 1]
        if single and len(by_state) > 1:
            print(f"⚠️  세션이 하나뿐인 상태: {', '.join(sorted(single))}")
            print("    상태마다 세션이 하나면, 그 세션의 전극이 어느 방향으로 표류했는지가")
            print("    곧 클래스 라벨이 되어 버립니다. 높은 정확도가 나와도 식물 반응이")
            print("    아니라 측정 조건의 차이일 수 있습니다.")
            print("    → 상태마다 날짜·전극을 달리해 2회 이상 나눠 수집하세요")
            print("      (예: 정상.csv, 정상_2.csv, 정상_3.csv).")

    total = 0
    all_feature_rows = []
    used_notches = []
    # 시뮬레이터 출력이 실측으로 오해된 채 학습·보고서까지 올라간 적이 있다.
    # 수집기가 CSV 옆에 남긴 출처 파일을 여기서 읽어, 가짜가 섞이면 크게 알린다.
    # 상태 파일만 본다(자극.presses.csv 같은 누른 시각 기록은 수집기 출력이 아니다).
    simulated = [f for f in sorted(targets) if state_of(f)
                 and sensor_control.is_simulated(os.path.join(args.raw_dir, f)) is True]
    unknown = [f for f in sorted(targets) if state_of(f)
               and sensor_control.is_simulated(os.path.join(args.raw_dir, f)) is None]
    if simulated:
        print(f"[preprocess] ⛔ 시뮬레이터 출력이 섞여 있습니다: {', '.join(simulated)}")
        print("    실측 데이터가 아니므로 여기서 나온 정확도는 식물과 아무 관계가 없습니다.")
    if unknown:
        print(f"[preprocess] ⚠️  출처를 알 수 없는 파일: {', '.join(unknown)}")
        print("    .meta.json 이 없습니다. 수집기를 거치지 않았거나 옛 코드로 모은 파일입니다.")

    for fname in sorted(targets):
        if fname.endswith(".csv") and state_of(fname):
            csv_path = os.path.join(args.raw_dir, fname)
            count, feature_rows, used_notch = process_file(csv_path, args.out_dir,
                                               window_sec=args.window_sec, step_sec=args.step_sec,
                                               low=args.lowcut, high=args.highcut, notch_freq=args.notch,
                                               decim_hz=args.decim_hz, context_sec=args.context_sec,
                                               quality=not args.no_quality,
                                               ref_subtract=not args.no_ref_subtract,
                                               rail_high=args.rail_high, min_std=args.min_std, rail_frac=args.rail_frac,
                                               repair=not args.no_repair)
            total += count
            all_feature_rows.extend(feature_rows)
            if count:
                used_notches.append(used_notch)

    # 실제로 사용한 노치 주파수를 메타에 남긴다(자동 보정된 값). 파일마다 다르면
    # 가장 많이 쓰인 값을 쓰고 경고한다 - 서로 다른 전원 환경의 데이터가 섞였다는 뜻이다.
    meta_notch = args.notch
    if used_notches:
        meta_notch = max(set(used_notches), key=used_notches.count)
        if len(set(used_notches)) > 1:
            print(f"⚠️  파일마다 전원 주파수가 다릅니다: {sorted(set(used_notches))}")
            print(f"   -> 메타에는 {meta_notch:.0f}Hz 를 기록합니다. 같은 환경에서 다시 수집하는 것이 좋습니다.")
        elif meta_notch != args.notch:
            print(f"[preprocess] 노치 주파수 {meta_notch:.0f}Hz 를 메타에 기록합니다(자동 감지).")

    # 사용한 필터 대역을 사이드카로 기록 -> train.py가 읽어 모델 번들에 저장 -> inference가 동일 필터 사용.
    meta_path = os.path.join(os.path.dirname(args.features_csv) or ".", "preprocess_meta.json")

    # --only 로 한 상태만 다시 변환하면, 다른 상태의 스펙트로그램은 이전 설정으로 만들어진
    # 채로 남는다. 그런데 메타는 이번 실행 값으로 덮어써지므로, 학습·추론은 그 값을 쓴다.
    # 즉 데이터셋 안에 서로 다른 필터로 만든 이미지가 섞이는데 아무도 모르는 상태가 된다.
    # -> 상태별로 실제 사용한 설정을 누적해 두고, 서로 다르면 크게 경고한다.
    prev = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as mf:
                prev = json.load(mf)
        except Exception:
            prev = {}

    by_state = dict(prev.get("by_state") or {})
    this_run = {"lowcut": args.lowcut, "highcut": args.highcut, "notch_freq": meta_notch,
                "decim_hz": args.decim_hz, "context_sec": args.context_sec,
                "window_sec": args.window_sec, "step_sec": args.step_sec}
    for fname in sorted(targets):
        st = state_of(fname)
        if st:
            by_state[st] = dict(this_run)

    # 상태마다 설정이 다르면 데이터셋이 섞인 것이다.
    distinct = {json.dumps(v, sort_keys=True, ensure_ascii=False) for v in by_state.values()}
    if len(distinct) > 1:
        print("⚠️  상태마다 다른 설정으로 변환된 스펙트로그램이 섞여 있습니다.")
        for st, v in sorted(by_state.items()):
            print(f"     {st}: 대역 {v['lowcut']}~{v['highcut']}Hz, 문맥 {v.get('context_sec', '?')}초, "
                  f"창 {v['window_sec']}초/{v['step_sec']}초")
        print("     이 상태로 학습하면 모델이 상태 차이가 아니라 '전처리 설정 차이'를 배울 수 있습니다.")
        print("     전체를 다시 변환하세요:  python preprocess.py   (--only 없이)")

    with open(meta_path, "w", encoding="utf-8") as mf:
        json.dump({"lowcut": args.lowcut, "highcut": args.highcut,
                   "notch_freq": meta_notch, "notch_q": 30.0,
                   "decim_hz": args.decim_hz, "context_sec": args.context_sec,
                   "sample_rate": SAMPLE_RATE_HZ,
                   "window_sec": args.window_sec, "step_sec": args.step_sec,
                   "by_state": by_state}, mf, ensure_ascii=False)
    print(f"[preprocess] 필터 메타 저장 -> {meta_path}")

    print(f"[preprocess] 총 {total}개 스펙트로그램 이미지 생성 완료")

    if all_feature_rows:
        columns = ["img_name", "source_file", "label"] + FEATURE_NAMES
        feat_df = pd.DataFrame(all_feature_rows, columns=columns)

        # --only 로 한 상태만 돌렸으면 features.csv를 통째로 덮어쓰면 안 된다.
        # 이번에 다시 변환한 파일의 예전 행만 걷어내고 나머지는 그대로 둔 채 합친다.
        # (라벨로 거르면 안 된다 — 누른 시각 라벨을 쓴 자극 회차는 '정상' 행도 만든다.)
        if args.only and os.path.isfile(args.features_csv):
            try:
                old = pd.read_csv(args.features_csv)
                kept = old[~old["source_file"].isin(set(targets))]
                feat_df = pd.concat([kept, feat_df], ignore_index=True)
                print(f"[preprocess] 기존 특징 {len(kept)}행 유지 + '{args.only}' 새로 {len(all_feature_rows)}행")
            except Exception as e:
                print(f"⚠️  기존 features.csv를 합치지 못해 새로 만듭니다: {e}")

        feat_df.to_csv(args.features_csv, index=False, encoding="utf-8")
        counts = feat_df["label"].value_counts().to_dict()
        print(f"[preprocess] 명시적 특징 {len(feat_df)}개 행 -> {args.features_csv}")
        print(f"[preprocess] 클래스별 개수: {counts}")


if __name__ == "__main__":
    main()
