"""
band_filter.py
==============
학습(preprocess.py)과 추론(inference.py)이 **같이 쓰는** 필터 체인. 두 곳에 따로 두지 않는다.

대역: 0.01~1 Hz  (2026-10-13 변경. 예전 0.5~20 Hz)
------------------------------------------------------
이유 — 문헌이 확인해 준 식물 활동전위는 일반 식물에서 "수십 초"(Mudrilov 2021)이고
토마토/애기장대 접촉 AP 는 약 10초(Degli Agosti 2014)다. T초짜리 파형의 주성분은
대략 1/T Hz 이므로 0.01~0.1 Hz 에 있다. 0.5 Hz 하한은 그걸 통째로 지운다(CLAUDE.md 0절 ⑮).
상한 1 Hz 는 접촉 AP(10초)의 빠른 가장자리까지 넣고, 상용전원(60 Hz)과 그 고조파는 멀리 둔다.

왜 바로 필터를 걸지 않고 10 Hz 로 줄이나
------------------------------------------
250 Hz 에서 하한 0.01 Hz 는 정규화 주파수가 8e-5 라 (b, a) 형식 버터워스가 수치적으로
무너진다. 먼저 10 Hz 로 줄이고(25개씩 평균) 그 위에서 SOS 필터를 건다.

25개 평균은 안티앨리어싱을 겸한다. 길이 25 평균의 주파수 응답은 10 Hz 의 배수에서
정확히 0 이다 → 60 Hz 도, 예전에 10 Hz 로 접혀 들던 240 Hz(|240−250|)도 모두 0 이다.
그래서 노치 필터는 쓰지 않는다.

왜 창 앞에 '문맥(context)'을 붙이나
--------------------------------------
0.01 Hz 고역통과는 시정수가 수십 초라, 30초 창만 따로 필터링하면 창 안은 과도응답뿐이다.
창 앞 CONTEXT_SEC 만큼을 같이 필터링한 뒤 **마지막 창 구간만** 쓴다.

왜 영위상(filtfilt)이 아니라 인과 필터인가
-------------------------------------------
filtfilt 는 버퍼 양 끝에서 과도응답이 생기는데, 실시간에서 우리가 보는 곳이 바로 버퍼의
오른쪽 끝(창 끝)이다. 0.01 Hz 에서는 그 끝 오차가 신호 크기만큼 커서(3 Hz 사인을 넣어도
출력에 크기 1.4 짜리 느린 성분이 남는 것을 확인) 쓸 수 없다. 앞으로만 필터링하면 창 끝이
항상 유효하고, 위상 지연은 학습·추론이 똑같이 갖는다. 학습(preprocess)과
추론(inference)이 똑같이 "문맥+창 끝이 맞춰진 버퍼"를 이 함수에 넣으므로 두 특징이 일치한다.
그래서 실시간 판정은 문맥+창(기본 90+30=120초)이 쌓여야 시작하고, 학습은 파일 앞
CONTEXT_SEC 에 걸리는 창을 쓰지 않는다.
"""

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi

LOWCUT_HZ = 0.01
HIGHCUT_HZ = 1.0
DECIM_HZ = 10.0         # 필터를 거는 샘플레이트(목표). 실제 값은 fs/정수로 정해진다
ORDER = 4
CONTEXT_SEC = 90.0      # 창 앞에 붙이는 문맥 길이. 0.01 Hz 시정수(~16초)의 5배 이상


def decim_factor(fs, decim_hz=DECIM_HZ):
    """fs 를 decim_hz 에 가깝게 줄이는 정수 배수."""
    return max(1, int(round(float(fs) / float(decim_hz))))


def analysis_rate(fs, decim_hz=DECIM_HZ):
    """필터·스펙트로그램·특징이 보는 샘플레이트(Hz)."""
    return float(fs) / decim_factor(fs, decim_hz)


def block_mean(x, factor):
    """factor 개씩 평균해 샘플 수를 줄인다. **끝을 기준으로** 맞춰 남는 앞쪽을 버린다 —
    창 끝 시각이 학습과 추론에서 같아야 하기 때문이다."""
    x = np.asarray(x, dtype=float)
    if factor <= 1:
        return x
    n = len(x) // factor * factor
    return x[len(x) - n:].reshape(-1, factor).mean(axis=1)


def analysis_filter(raw_ctx, fs, window_sec, low=LOWCUT_HZ, high=HIGHCUT_HZ,
                    decim_hz=DECIM_HZ, order=ORDER):
    """문맥+창 원신호 -> (필터 통과한 마지막 창, 분석 샘플레이트).

    raw_ctx    : 원신호(V). **마지막 window_sec 초가 분석할 창**이고 그 앞은 문맥이다.
    반환 길이  : round(window_sec * 분석 샘플레이트) 샘플.
    """
    f = decim_factor(fs, decim_hz)
    fs_a = float(fs) / f
    y = block_mean(raw_ctx, f)
    n_win = int(round(window_sec * fs_a))
    if len(y) < max(n_win, 40):
        raise ValueError(f"신호가 너무 짧다: {len(y)}샘플 < 창 {n_win}샘플")
    if high >= 0.5 * fs_a:
        raise ValueError(f"상한 {high}Hz 가 분석 샘플레이트 {fs_a:g}Hz 의 나이퀴스트 이상이다")
    sos = butter(order, [low, high], btype="band", fs=fs_a, output="sos")
    # 인과(앞으로만) 필터 + 초기상태를 첫 값에 맞춤(직류 오프셋이 과도응답을 만들지 않게)
    out = sosfilt(sos, y, zi=sosfilt_zi(sos) * y[0])[0]
    return out[-n_win:], fs_a
