"""booth_poster_build.py — 페스티벌 부스 포스터(우리 연구 요약, 손 접촉 중심)를 양식 5-3 위에 만든다 (2026-11-17).

양식·XML 조각·배치·미리보기는 report/poster_build.py 것을 그대로 쓰고, 내용만 여기 둔다.
숫자는 학교 양식 보고서(Ⅳ장 1·2절, 표5)와 같게 쓴다.
쓰는 법(저장소 루트): python3 report/booth_poster_build.py → report/GML_부스포스터.hwpx, report/GML_부스포스터_미리보기.png
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import poster_build as pb

pb.DST = os.path.join(pb.REP, "GML_부스포스터.hwpx")
pb.PREVIEW = os.path.join(pb.REP, "GML_부스포스터_미리보기.png")

pb.STYLES.update({
    "body":  (2700, "#1A1A1A", 0, False),
    "cap":   (2000, "#404040", 0, False),
    "title": (5000, "#000000", 2, False),
    "sum":   (2300, "#1A1A1A", 2, False),
    "kbig":  (6000, "#905720", 2, False),
    "klab":  (2300, "#333333", 0, False),
    "call":  (3200, "#FFFFFF", 2, False),
})
pb.PARA["body"] = (19, 145, 0, 600)

pb.TITLE = "손이 닿으면 식물 전압이 솟는다 — 손 접촉을 알아채는 AI"
pb.SUMMARY = "방울토마토 줄기 전기신호를 직접 만든 측정계로 재고, 손 접촉을 감지하는 AI 를 만들었다"

pb.LEFT = [
    ("bar", "Ⅰ. 연구 소개"),
    ("p", "식물은 자극을 받으면 세포막 전위가 바뀐다. 우리는 방울토마토 줄기의 미세 전기신호를 재는 측정계를 직접 만들고, "
          "그 신호를 머신러닝으로 가르는 시스템을 구현했다."),
    ("fig", "PHOTO_POSTER_CAGE.jpg", 1.0, "사진1. (가) 방충망 차폐 상자 (나) 실험한 방울토마토 (다) 상자 밖 회로와 라즈베리파이"),
    ("bar", "Ⅱ. 손 접촉 실험"),
    ("call", "손이 닿는 순간 전압이 계단처럼 솟고, 떼면 돌아온다"),
    ("fig", "FIG_TOUCH.png", 1.0, "그림1. 손 접촉 기록 — (가) 기록 전체 (나) 접촉 한 번 확대 (다) 계단 높이 67건"),
    ("keys", [("67건", "35분 기록에서 찾은 손 접촉"),
              ("70·320 mV", "손이 닿을 때 솟은 크기 (두 무리, 약)")]),
    ("li", "· 줄기에 점퍼선 핀 두 개를 3 cm 간격으로 꽂고 손으로 줄기와 잎을 만졌다."),
    ("li", "· 솟은 상태는 손이 닿아 있는 동안만 유지되었다(중앙값 1.1초)."),
    ("li", "· 사람 몸도 도체라, 닿는 순간 몸의 전위가 전극 쪽에 더해진 것으로 본다."),
]
pb.RIGHT = [
    ("bar", "Ⅲ. 손 접촉 감지 AI"),
    ("keys", [("251 / 251", "SVM — 학습에 안 쓴 평가 창 정답"),
              ("2.8 ms", "라즈베리파이 5 에서 판정 한 번")]),
    ("li", "· 접촉 구간 17개·비접촉 구간 30개를 파일 단위로 나눠, 같은 구간이 학습과 평가에 함께 들어가지 않게 했다."),
    ("li", "· 창마다 시간·주파수 특징 17개를 계산해 SVM·랜덤 포레스트로 학습했다."),
    ("fig", "FIG_BOOTH_CLF.png", 1.0, "그림2. 방법별로 찾은 접촉 수 (평가 창 251개 중 접촉 23개)"),
    ("li", "· 문턱 하나로도 250개를 맞혔다 — 이 AI 는 식물의 반응이 아니라 손이 닿았는지를 감지한다."),
    ("li", "· 2초 창 모델로 손이 닿으면 바로 화면에 표시되는 실시간 판정을 만들었다."),
    ("bar", "Ⅳ. 직접 만든 측정계"),
    ("fig", "PHOTO4_WIRING.png", 1.0, "사진2. 직접 만든 측정 회로 — 전압 폴로어(MCP6002), 16비트 ADC(ADS1115), 라즈베리파이 5"),
    ("keys", [("0.02 mV", "은선 전극 1시간 표류 (핀 59.20 mV)"),
              ("약 1/27", "차폐 상자로 줄인 60 Hz 잡음")]),
    ("call", "부스에서 손을 대 보고, 나만의 손 접촉 AI 를 직접 만들어 보세요"),
]

_base = pb.layout
def _spread(blocks, col):
    """남는 높이를 절 사이와 블록 사이에 고르게 나눠 단을 채운다."""
    out, y = _base(blocks, col)
    room = pb.COL_BOT - pb.PAD - y
    glue = [i > 0 and ((out[i - 1][0] == "pic" and o[0] == "text") or out[i - 1][2] == o[2]) for i, o in enumerate(out)]
    gaps = sum(1 for i in range(1, len(out)) if not glue[i])
    if room <= 0 or gaps == 0:
        return out, y
    step, shift, res = room * 0.9 / gaps, 0.0, []
    for i, o in enumerate(out):
        if i and not glue[i]:
            shift += step
        res.append((o[0], o[1], round(o[2] + shift), *o[3:]))
    return res, y + room * 0.9
pb.layout = _spread

if __name__ == "__main__":
    pb.main()
