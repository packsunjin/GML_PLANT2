"""검토 19차(2026-11-02, 새 에이전트 심사 반영). results_1102 다음 단계 → hwpx_fillseg.
받아들임: 화상·수분부족을 점퍼선 핀으로 쟀음을 명시(은/염화은 → 은선, 사용자가 염화 안 된 은선을 쓰기로 함),
정상 라벨 재정의(10-30 5분은 물 끊은 지 2일째라 정상에서 뺌 → 밤샘 12시간을 앞·뒤 6시간으로 나눠 다시 평가, ml_water.json),
위 핀 방향 문장 삭제(차동 부호만으로 전파 방향을 말할 수 없다), 2.925 mV 구간 표기, 선 빼 보기 확인 한 문장, 표6 ②③, 결론 흐름, '지진'→'지질 때', 습도 범위.
안 받아들임: 보조배터리 때문에 차폐 효과를 단정하지 말라(사용자 결정), 화상·수분부족 해석 약화(사용자 결정).
"""
import sys, zipfile, re, html

src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
assert "은선 전극의 표류" not in s


def esc(t):
    return html.escape(t, quote=False).replace("'", "&apos;").replace('"', "&quot;")


def leaf(pid):
    m = re.search(rf'<hp:p id="{pid}"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', s, re.S)
    assert m, pid
    return m


def noseg(p):
    return re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)


def text_of(pid):
    return html.unescape("".join(re.findall(r"<hp:t>([^<]*)</hp:t>", leaf(pid).group(0))))


def set_text(pid, t):
    global s
    m = leaf(pid); p = m.group(0)
    assert p.count("<hp:t>") == 1, pid
    p = noseg(re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(t) + "</hp:t>", p))
    s = s[:m.start()] + p + s[m.end():]


def replace_in(pid, a, b):
    t = text_of(pid); assert t.count(a) == 1, (pid, a); set_text(pid, t.replace(a, b))


def drop(pid):
    global s
    m = leaf(pid); s = s[:m.start()] + s[m.end():]



replace_in("89", "은/염화은 전극으로 느린 표류를 줄여 화상 자극과 수분부족을 다시 측정했다.",
           "같은 점퍼선 핀 전극으로 상자 안에서 화상 자극과 수분부족을 측정했다(은선 전극은 Ⅳ장 2절).")
set_text("176", "예비: 점퍼선 핀, 간격 3 cm / 상자 안: 점퍼선 핀, 원줄기 위·아래 약 1 cm (은선 전극은 Ⅳ장 2절)")
replace_in("188", "이어서 은/염화은 전극을 측정 하루 전에 줄기 밑동에 1 cm 간격으로 가로질러 꽂고, GND에 연결한 금속 망 상자(패러데이 상자, 사진4) 안에 식물만 넣어 측정한다(회로와 라즈베리파이는 상자 밖). 전극 배치와 차폐는",
           "이어서 GND에 연결한 금속 망 상자(패러데이 상자, 사진4) 안에 식물만 넣고(회로와 라즈베리파이는 상자 밖) 같은 점퍼선 핀 전극(원줄기 위·아래 약 1 cm)으로 정상·화상·수분부족을 쟀다. 전극 표류를 줄이려고 은선 전극은 따로 시험한다. 1 cm 전극 간격과 차폐는")
m = leaf("189"); p189 = m.group(0); assert p189.count(", 은/염화은 전극") == 1
s = s[:m.start()] + noseg(p189.replace(", 은/염화은 전극", "")) + s[m.end():]
replace_in("900080", "은/염화은 전극을", "은선 전극을")
replace_in("900119", "은/염화은", "은선")
set_text("900136", "2. 은선 전극의 표류")
replace_in("411", "■ 은/염화은 전극 결과 반영 자리", "■ 은선 전극 결과 반영 자리")
replace_in("900139", " 화상 부위에 가까운 위 핀 쪽이 +로 움직인 방향도 신호가 위에서 내려온 것과 맞다.", "")
replace_in("401", "지진 순간 변화 없이", "지질 때는 변화 없이")
replace_in("900193", "60 Hz 성분은 2.925 mV에서", "60 Hz 성분은 2.925 mV(상자 전 처음 120초)에서")
replace_in("900193", "이웃한 표본 사이 변화의 중앙값은 ADC 한 칸보다 작았다.",
           "이웃한 표본 사이 변화의 중앙값은 ADC 한 칸보다 작았다. 값이 매우 작아 전극 선을 잠깐 뽑아 보니 기록이 바로 바뀌어, 회로가 전극을 읽고 있음을 확인했다.")
replace_in("900141", "습도는 37~57 %였다", "습도는 37~58 %였다")
set_text("900143",
         "정상(물을 준 직후 12시간)과 수분부족(14시간, 5일째 30분) 기록을 30초 창으로 잘라 예비 실험과 같은 특징 14개로 "
         "랜덤 포레스트·SVM[10]을 학습했다. 정상 기록은 하나뿐이라 앞 6시간과 뒤 6시간으로 나누고, 수분부족은 회차를 통째로 나눴다. "
         "정상 앞 6시간·수분부족 14시간으로 학습해 정상 뒤 6시간·수분부족 30분(창 4,652개)으로 평가하자 균형 정확도가 랜덤 포레스트 "
         "99.8 %, SVM 99.9 %였고, 반대로 학습·평가하자(창 14,359개) 96.9 %·97.3 %였다. 다만 창 안 2초 사이 최대 변화 하나에 "
         "문턱 하나만 써도 99.7 %·97.2 %가 나와, 모델이 가른 것은 기준선이 평평한지 출렁이는지다. 같은 모델은 물을 준 뒤 1시간과 "
         "화상 기록의 창을 전부 수분부족으로, 물을 끊은 지 2일째지만 아직 평평했던 5분 기록은 전부 정상으로 판정했다.")
replace_in("430", "균형 정확도 90.8~100 %였으나 문턱 하나로도 95.1~100 %", "균형 정확도 96.9~99.9 %였으나 문턱 하나로도 97.2~99.7 %")
set_text("429", "정상·수분부족만 달성")
set_text("427", "예비: 수분부족 미측정, 자극 반응 확인 못 함 / 본 실험: 수분부족 뒤 느린 변동·화상 뒤 늦은 변화는 보였으나 세 상태 분류는 못 함 (표5)")
replace_in("412", "균형 정확도 90.8~100 %로 갈렸으나", "균형 정확도 96.9~99.9 %로 갈렸으나")
replace_in("76", "정상과 균형 정확도 90.8~100 %로 갈렸다.", "정상과 균형 정확도 96.9~99.9 %로 갈렸다(문턱 하나로도 97.2~99.7 %).")
assert len(text_of("76")) <= 600, len(text_of("76"))
replace_in("415", "이 가설을 맞다고도 틀리다고도 판정할 수 없었다.",
           "이 가설을 맞다고도 틀리다고도 판정할 수 없었다. 본 실험에서 차폐로 바탕 잡음을 없애자 물을 끊은 뒤의 느린 변동과 화상 뒤의 늦은 변화가 나타나, 식물 상태에 따라 신호가 달라지는 것을 관찰했다.")
replace_in("416", "그 시스템이 읽어 낸 것은", "예비 실험에서 그 시스템이 읽어 낸 것은")

import xml.dom.minidom
xml.dom.minidom.parseString(s.encode("utf8"))
ids = re.findall(r'<hp:p id="(\d+)"', s)
assert len(ids) == len(set(ids))
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("요약 성과", len(text_of("76")), "자")
