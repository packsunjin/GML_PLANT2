"""재구성판의 본 실험 설계 부분 바로잡기(2026-10-21, 사용자 "수정해야 할 게 있지 않니").
- 188·사진4: 망을 GND 에 연결하는 것이고 회로·파이는 상자 밖이다("측정 회로를 GND에 연결한 상자 안"은 틀림)
- 본 실험 방식(하루 전 꽂음, 줄기 밑동 1 cm 가로 관통, 접지한 상자, 상자 안 온습도)의 출처 [13] de Toledo et al. 2024 추가
- 표2 에 차폐·온습도 행과 본 실험 전극 배치, 표3 에 ⓪ 차폐 효과(상자 전·후) 행, 부록에 env_sensor.py
쓰기: python3 -I faraday_design.py 원본.hwpx 결과.hwpx  → 그다음 hwpx_fillseg.py"""
import sys, zipfile, re, html

src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
assert "Common bean" not in s
NEXT = [max(int(x) for x in re.findall(r'<hp:p id="(\d+)"', s)) + 1]


def nid():
    NEXT[0] += 1
    return str(NEXT[0] - 1)


def esc(t):
    return html.escape(t, quote=False).replace("'", "&apos;").replace('"', "&quot;")


def leaf_m(pid):
    m = re.search(rf'<hp:p id="{pid}"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', s, re.S)
    assert m, pid
    return m


def noseg(p):
    return re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)


def set_text(pid, text):
    global s
    m = leaf_m(pid)
    p = m.group(0)
    assert len(re.findall("<hp:t>", p)) == 1, pid
    p = noseg(re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(text) + "</hp:t>", p))
    s = s[:m.start()] + p + s[m.end():]


def text_of(pid):
    return html.unescape("".join(re.findall(r"<hp:t>([^<]*)</hp:t>", leaf_m(pid).group(0))))


def replace_in(pid, a, b):
    t = text_of(pid)
    assert t.count(a) == 1, (pid, a)
    set_text(pid, t.replace(a, b))


def add_row(cell_pid, texts, before=False, height=1800):
    """cell_pid 가 든 행을 복제해 그 뒤(앞)에 넣고, 표의 rowAddr·rowCnt·높이를 다시 맞춘다."""
    global s
    i = s.index(f'<hp:p id="{cell_pid}"')
    a = s.rfind("<hp:tr>", 0, i)
    b = s.index("</hp:tr>", i) + len("</hp:tr>")
    row = s[a:b]
    cells = re.findall(r"<hp:p id=\"\d+\"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>", row, re.S)
    assert len(cells) == len(texts)
    for old, t in zip(cells, texts):
        new = re.sub(r'<hp:p id="\d+"', f'<hp:p id="{nid()}"', old, count=1)
        new = noseg(re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(t) + "</hp:t>", new, count=1))
        row = row.replace(old, new, 1)
    row = re.sub(r'(<hp:cellSz width="\d+" height=")\d+', rf"\g<1>{height}", row)
    s = (s[:a] + row + s[a:]) if before else (s[:b] + row + s[b:])
    # 표 다시 맞추기
    t0 = s.rfind("<hp:tbl ", 0, i)
    t1 = s.index("</hp:tbl>", t0)
    tbl = s[t0:t1]
    k = [0]

    def renum(m):
        tr = m.group(0)
        r = k[0]; k[0] += 1
        return re.sub(r'rowAddr="\d+"', f'rowAddr="{r}"', tr)
    tbl = re.sub(r"<hp:tr>.*?</hp:tr>", renum, tbl, flags=re.S)
    tbl = re.sub(r'rowCnt="\d+"', f'rowCnt="{k[0]}"', tbl, count=1)
    tot = sum(max(int(h) for h in re.findall(r'<hp:cellSz width="\d+" height="(\d+)"', tr))
              for tr in re.findall(r"<hp:tr>.*?</hp:tr>", tbl, re.S))
    tbl = re.sub(r'(<hp:sz width="47620" widthRelTo="ABSOLUTE" height=")\d+', rf"\g<1>{tot}", tbl, count=1)
    s = s[:t0] + tbl + s[t1:]


# 1. 틀린 문장
replace_in("188", "본 실험은 이 둘을 바꾸어, 은/염화은 전극을 쓰고 식물과 측정 회로를 GND에 연결한 금속 망 상자(패러데이 상자, 사진4) 안에 넣어 측정한다(표3).",
           "본 실험은 이 둘을 바꾸어, 은/염화은 전극을 측정 하루 전에 줄기 밑동에 1 cm 간격으로 가로질러 꽂고, GND에 연결한 금속 망 상자"
           "(패러데이 상자, 사진4) 안에 식물만 넣어 측정한다(회로와 라즈베리파이는 상자 밖). 전극 배치와 차폐는 강낭콩의 물 공급 조건을 "
           "전기신호로 분류한 선행 연구[13]를 따랐다(표3).")
m = leaf_m("900096")
cap = m.group(0)
cap2 = noseg(re.sub(r'(<hp:run charPrIDRef="44"><hp:t>)[^<]*', r"\g<1> GND에 연결한 패러데이 상자(방충망 6면)와 그 안의 식물", cap))
s = s[:m.start()] + cap2 + s[m.end():]

# 1-2. 157(측정 범위·식물 문단)은 본문인데 캡션 양식(paraPr 19 = 가운데 정렬, 빈 캡션 글자 묶음)으로 들어가 있었다 → 본문 양식으로
m = leaf_m("157")
p = m.group(0).replace('<hp:p id="157" paraPrIDRef="19" styleIDRef="28"', '<hp:p id="157" paraPrIDRef="0" styleIDRef="0"', 1)
p = p.replace('<hp:run charPrIDRef="44"><hp:t></hp:t></hp:run>', "", 1)
assert 'paraPrIDRef="0"' in p and 'charPrIDRef="44"' not in p
s = s[:m.start()] + noseg(p) + s[m.end():]

# 2. 인용·설명 추가
replace_in("82", "직접 재 보아야 알 수 있다.",
           "직접 재 보아야 알 수 있다. 물 공급 조건에 따른 식물 전기신호를 머신러닝으로 분류한 연구[13]도 접지한 금속 상자 안에서 쟀다.")
replace_in("157", "회로의 배선과 조립 순서는 사진3과 같다(핀 연결은 부록 1절).",
           "회로의 배선과 조립 순서는 사진3과 같다(핀 연결은 부록 1절). 본 실험에서는 상자 안 온도·습도를 DHT11 센서로 60초마다 함께 기록한다(표2).")
replace_in("471", "bias_check.py(기준 전압 단극 점검), ",
           "bias_check.py(기준 전압 단극 점검), env_sensor.py(상자 안 온습도), ")

# 3. 표2
replace_in("176", "예비: 점퍼선 핀, 간격 3 cm / 본 실험: 은선에 염화은을 입힘",
           "예비: 점퍼선 핀, 간격 3 cm / 본 실험: 은선에 염화은, 줄기 밑동 1 cm 가로 관통")
replace_in("177", "보유·구입 부품", "보유·구입 부품, [13]")
add_row("175", ["차폐", "알루미늄 방충망 60×60×120 cm 6면, GND 연결", "[13]의 방식"])
add_row("175", ["온습도", "DHT11, 60초마다 (1 °C·1 % 단위)", "보유 부품"])
# 순서: 전극 → 온습도 → 차폐 가 되므로(뒤에 넣은 것이 바로 아래) 그대로 둔다

# 4. 표3
add_row("900079", ["⓪ 차폐 효과", "같은 점퍼선 핀 전극으로 상자에 넣기 전·후를 이어서 기록",
                   "손대지 않을 때의 흔들림·상용전원 잡음이 차폐로 줄었는지(상자 전 단극 흔들림 약 70 mV)"],
        before=True, height=3600)
set_text("900084", "화상·수분부족·분류의 비교 기준(손대지 않을 때 기준선)")

# 5. 참고문헌 [13]
m = leaf_m("467")
ref = re.sub(r'<hp:p id="467"', f'<hp:p id="{nid()}"', m.group(0), count=1)
ref = noseg(re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(
    "[13] de Toledo, G. R. A., Reissig, G. N., Senko, L. G. S., Pereira, D. R., da Silva, A. F., & Souza, G. M. (2024). "
    "Common bean under different water availability reveals classifiable stimuli-specific signatures in plant electrome. "
    "Plant Signaling & Behavior, 19(1), 2333144. doi:10.1080/15592324.2024.2333144") + "</hp:t>", ref))
s = s[:m.end()] + ref + s[m.end():]

from xml.dom import minidom
minidom.parseString(s.encode("utf8"))
ids = re.findall(r'<hp:p id="(\d+)"', s)
assert len(ids) == len(set(ids)), "문단 id 겹침"
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("ok")
