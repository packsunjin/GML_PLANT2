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
    ("bar", "Ⅰ. 서론"),
    ("p", "식물은 자극을 받으면 세포막 전위가 바뀌고, 그 변화가 줄기를 따라 전달된다[3]. 우리는 방울토마토 줄기의 미세 전기신호를 "
          "재는 측정계를 직접 만들고, 측정에서 가장 뚜렷하게 잡힌 손 접촉 신호를 감지하는 AI 를 개발했다."),
    ("bar", "Ⅱ. 이론적 배경 및 선행 연구"),
    ("li", "· 식물의 활동전위는 수십~100 mV, 수십 초 이어진다[3]."),
    ("li", "· 애기장대를 붓으로 건드리면 약 33.9 mV, 약 10.7초의 활동전위가 접촉보다 늦게 도착한다[6]."),
    ("bar", "Ⅲ. 연구방법"),
    ("fig", "PHOTO4_WIRING.png", 1.0, "사진1. 직접 만든 측정 회로 — 전압 폴로어(MCP6002), 16비트 ADC(ADS1115), 라즈베리파이 5"),
    ("li", "· 줄기에 점퍼선 핀 두 개를 3 cm 간격으로 꽂고, 두 전극의 전압 차를 250 S/s로 기록했다."),
    ("li", "· 손으로 줄기와 잎을 만지며 기록하고, 손이 닿은 구간과 닿지 않은 구간을 나눴다(접촉 17개·비접촉 30개)."),
    ("li", "· 구간을 파일 단위로 나눠 학습에 쓰지 않은 창으로 평가하고, 문턱 하나짜리 가장 단순한 기준과 비교했다."),
    ("fig", "PHOTO2_20261015_label_wide.jpg", 1.0, "사진2. 손 접촉 실험의 전극 — 줄기에 꽂은 위·아래 측정 핀과 흙의 기준 핀"),
]
pb.RIGHT = [
    ("bar", "Ⅳ. 연구결과"),
    ("call", "손이 닿는 순간 전압이 계단처럼 솟고, 떼면 돌아온다"),
    ("fig", "FIG_TOUCH.png", 1.0, "그림1. 손 접촉 기록 — (가) 기록 전체 (나) 접촉 한 번 확대 (다) 계단 높이 67건"),
    ("keys", [("67건", "35분 기록에서 찾은 손 접촉"),
              ("70·320 mV", "손이 닿을 때 솟은 크기 (두 무리, 약)"),
              ("251 / 251", "SVM — 학습에 안 쓴 평가 창 정답"),
              ("2.8 ms", "라즈베리파이 5 에서 판정 한 번")]),
    ("fig", "FIG_BOOTH_CLF.png", 0.9, "그림2. 방법별로 찾은 접촉 수 (평가 창 251개 중 접촉 23개)"),
    ("bar", "Ⅴ. 결론 및 제언"),
    ("li", "· 손 접촉은 문헌 활동전위의 약 2~9배로 크고, 손이 닿아 있는 동안만 유지되었다(중앙값 1.1초). 사람 몸의 전위가 전극에 더해진 것으로 본다."),
    ("li", "· 문턱 하나로도 250개를 맞혀, 이 AI 는 식물의 반응이 아니라 손이 닿았는지를 감지한다."),
    ("call", "부스에서 손을 대 보고, 나만의 손 접촉 AI 를 직접 만들어 보세요"),
    ("ref", "[3] Mudrilov et al. (2021). Int. J. Mol. Sci. 22(19), 10715.  [6] Degli Agosti (2014). Archives des Sciences 67, 125–138.  "
            "코드·원자료: github.com/packsunjin/GML_PLANT2"),
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
