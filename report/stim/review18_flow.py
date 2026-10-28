"""18차: 상자 결과를 보고서 흐름에 잇는다(2026-10-28, 사용자 "검토에 검토까지 해서 자연스럽게 이어지게").
예비 실험의 한계를 둘로 나눈다 — 느린 표류(전극)와 빠른 흔들림(예비 때 원인 모름 → 차폐로 줄어 바깥 전기 잡음으로 확인).
- Ⅱ장 5절(외부 전기 잡음과 차폐) 새로, Ⅲ-2(188)·Ⅰ-2(89) 흐름, Ⅲ-3 분석 방법에 60 Hz·표본 간 변화
- Ⅳ-3: GND 연결 후 120초 문단(로컬 세션 ㉝ 표, data/faraday/상자후GND_시험120초_20261028.csv) + 정리 문단
- 표5 에 '빠른 흔들림' 줄, 결론 411·의의 439·한계 443·444, 요약 성과 76
쓰기: python3 -I review18_flow.py 원본 결과 → hwpx_fillseg"""
import sys, zipfile, re, html

src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
assert "외부 전기 잡음과 차폐" not in s
NEXT = [max(int(x) for x in re.findall(r'<hp:p id="(\d+)"', s)) + 1]


def nid():
    NEXT[0] += 1
    return str(NEXT[0] - 1)


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


def rep(pid, a, b):
    t = text_of(pid); assert t.count(a) == 1, (pid, a); set_text(pid, t.replace(a, b))


def clone_after(after_pid, model_pid, text):
    """model_pid 문단 양식을 복사해 after_pid 뒤에 넣는다."""
    global s
    p = re.sub(rf'<hp:p id="{model_pid}"', f'<hp:p id="{nid()}"', leaf(model_pid).group(0), count=1)
    p = noseg(re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(text) + "</hp:t>", p, count=1))
    m = leaf(after_pid)
    s = s[:m.end()] + p + s[m.end():]
    return re.search(r'<hp:p id="(\d+)"', p).group(1)


def add_row(cell_pid, texts):
    """cell_pid 가 든 표 행을 복제해 그 뒤에 넣고 rowAddr·rowCnt·높이를 맞춘다(faraday_design.py 와 같음)."""
    global s
    i = s.index(f'<hp:p id="{cell_pid}"')
    a = s.rfind("<hp:tr>", 0, i); b = s.index("</hp:tr>", i) + len("</hp:tr>")
    row = s[a:b]
    cells = re.findall(r"<hp:p id=\"\d+\"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>", row, re.S)
    assert len(cells) == len(texts)
    for old, t in zip(cells, texts):
        new = re.sub(r'<hp:p id="\d+"', f'<hp:p id="{nid()}"', old, count=1)
        new = noseg(re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(t) + "</hp:t>", new, count=1))
        row = row.replace(old, new, 1)
    s = s[:b] + row + s[b:]
    t0 = s.rfind("<hp:tbl ", 0, i); t1 = s.index("</hp:tbl>", t0); tbl = s[t0:t1]; k = [0]
    def renum(m):
        r = k[0]; k[0] += 1
        return re.sub(r'rowAddr="\d+"', f'rowAddr="{r}"', m.group(0))
    tbl = re.sub(r"<hp:tr>.*?</hp:tr>", renum, tbl, flags=re.S)
    tbl = re.sub(r'rowCnt="\d+"', f'rowCnt="{k[0]}"', tbl, count=1)
    tot = sum(max(int(h) for h in re.findall(r'<hp:cellSz width="\d+" height="(\d+)"', tr))
              for tr in re.findall(r"<hp:tr>.*?</hp:tr>", tbl, re.S))
    tbl = re.sub(r'(<hp:sz width="47620" widthRelTo="ABSOLUTE" height=")\d+', rf"\g<1>{tot}", tbl, count=1)
    s = s[:t0] + tbl + s[t1:]


# Ⅰ-2 연구 목적 끝 문단
rep("89", "측정을 제한하는 것이 전극 표류와 원인 모를 기준선 흔들림임을 확인하고(Ⅳ장 1절), 은/염화은 전극과 접지한 패러데이 상자로 조건을 바꾼 본 실험에서 화상 자극과 수분부족을 다시 측정했다.",
    "측정을 제한하는 것이 전극의 느린 표류와 원인 모를 빠른 흔들림 두 가지임을 확인했다(Ⅳ장 1절). 본 실험에서는 먼저 패러데이 상자로 빠른 흔들림이 바깥 전기 잡음인지 확인하고(Ⅳ장 3절), "
    "은/염화은 전극으로 느린 표류를 줄여 화상 자극과 수분부족을 다시 측정했다.")

# Ⅱ장 5절 새로
h = clone_after("148", "146", "5. 외부 전기 잡음과 차폐")
clone_after(h, "148",
    "측정 회로의 입력은 전류를 거의 흘리지 않고(폴로어 입력 바이어스 전류 ±1 pA[2]) 줄기와 흙의 저항도 커서, 주변 전원선의 전기장이 아주 작은 전류만 흘려도 측정 전압에 섞인다. "
    "이렇게 들어오는 잡음은 60 Hz 상용전원 성분으로 나타나고, 사람이 움직이거나 기기를 켜고 끌 때 주변 전기장이 바뀌면 느린 흔들림으로도 나타날 수 있다. "
    "금속 망으로 식물을 둘러싸면 바깥 전기장이 안으로 들어오지 못하므로, 선행 연구[5][13]도 식물을 금속 상자(패러데이 상자) 안에 두고 쟀다. "
    "본 실험은 같은 전극으로 상자에 넣기 전과 후를 재어, 예비 실험의 흔들림 중 얼마가 이 잡음이었는지 확인한다.")

# Ⅲ-2 실험 설계
rep("188", "그 결과 측정을 제한하는 것은 회로가 아니라 점퍼선 핀 전극과, 손대지 않아도 생기는 기준선 흔들림이었다. 본 실험은 이 둘을 바꾸어, ",
    "그 결과 측정을 제한하는 것은 회로가 아니라, 몇 시간에 걸쳐 기준선을 밀어내는 점퍼선 핀 전극의 표류와, 손대지 않아도 생기는 원인 모를 빠른 흔들림이었다. "
    "본 실험은 먼저 같은 전극으로 상자에 넣기 전·후를 비교해 흔들림이 바깥 전기 잡음인지 확인하고(표3 ⓪), 이어서 ")

# Ⅲ-3 분석 방법
clone_after("217", "217", "· 상용전원 성분 — 평균을 뺀 기록에 Hann 창을 씌운 푸리에 변환에서 59.5–60.5 Hz의 최대 진폭. "
                          "이웃한 두 표본 사이 변화의 중앙값도 함께 보아, 이 값이 ADC 한 칸(±2.048 V 범위에서 0.0625 mV)까지 내려가면 그보다 작은 잡음은 이 측정계로 구분할 수 없다고 본다")

# Ⅳ-3 GND 연결 문단 + 정리 문단
g = clone_after("900193", "900193",
    "같은 날 망을 라즈베리파이의 GND에 연결하고 다시 잰 120초 기록에서도 60 Hz 성분은 0.0018 mV로 낮게 유지됐다. 다만 이 기록에서는 기준선이 2분 동안 약 21 mV에서 37 mV로 "
    "분당 약 8.6 mV씩 올라 0.01–1 Hz 잡음이 1.24 mV로 커졌고, 두 측정 채널의 절대 전압도 약 1.62 V에서 1.89–1.91 V로 함께 올랐다. 망에 선을 붙이느라 상자 주변을 만진 "
    "직후의 기록이어서, 이 변화가 접지 때문인지 손댄 영향인지는 이 기록만으로 가릴 수 없어 긴 기록으로 확인한다.")
clone_after(g, "900193",
    "정리하면, 예비 실험에서 원인을 찾지 못했던 빠른 흔들림과 상용전원 잡음은 대부분 바깥 전기장이 식물과 선을 통해 들어온 것이며 차폐로 줄일 수 있다. 상자 안 0.01–1 Hz 잡음 "
    "0.060 mV는 예비 2단계에서 전극을 물에 담가 잰 값(0.06 mV)과 같아, 식물에서 커 보이던 잡음이 전극 때문이 아니었음을 뒷받침한다. 반면 느린 표류는 0.01–1 Hz 분석에서는 "
    "걸러져 자극 판정의 주된 걸림돌이 아니었지만, 수 시간 단위로 변하는 수분부족 판정에는 그대로 겹치므로 전극을 바꾸어 따로 확인한다(Ⅳ장 2절).")

# 표5 새 줄(자극 반응 줄 다음)
add_row("401", ["빠른 흔들림", "차폐로 줄어듦", "같은 전극에서 0.01–1 Hz 2.268 → 0.060 mV, 60 Hz 2.925 → 0.0013 mV (120초 비교, Ⅳ장 3절)"])

# 결론·의의·한계·요약
rep("411", "수 시간에 걸친 느린 신호는 전극 표류에 묻힌다. 정밀도를 제한하는 것은 회로가 아니라 전극이다.",
    "수 시간에 걸친 느린 신호는 전극 표류에 묻힌다. 식물에서는 이보다 큰 빠른 흔들림이 수십 초 신호를 가렸는데, 상자에 넣자 같은 전극에서 0.060 mV로 줄어 바깥 전기 잡음이었음을 확인했다. "
    "즉 정밀도를 제한하는 것은 회로가 아니라, 느린 신호에서는 전극 표류, 빠른 신호에서는 주변 전기 잡음이다.")
rep("439", "회로와 전극의 표류를 따로 재어, 개선해야 할 곳이 회로가 아니라 전극임을 보였다.",
    "회로·전극·주변 환경을 따로 재어, 느린 표류는 전극에서, 빠른 흔들림은 바깥 전기 잡음에서 온다는 것을 보이고 각각의 대책(전극 교체, 차폐)을 정했다.")
rep("443", "실제로 식물에 꽂은 뒤의 0.01–1 Hz 잡음(1.72 mV)은 물속(0.06 mV)보다 컸다.",
    "실제로 식물에 꽂은 뒤의 0.01–1 Hz 잡음(1.72 mV)은 물속(0.06 mV)보다 컸으나, 상자 안에서는 0.060 mV로 물속과 같아졌다(Ⅳ장 3절).")
rep("444", "는 원인을 찾지 못했다. 사람의 움직임·전원·전극·조명 변화·식물 자체 중 무엇 때문인지 가리지 못했다. ",
    "는 예비 실험에서는 원인을 찾지 못했다. ")
rep("444", "상자에 넣자 같은 전극에서 60 Hz 성분과 0.01–1 Hz 잡음이 크게 줄었으나(Ⅳ장 3절), 120초 비교라서 수 시간 단위의 기준선 흔들림이 함께 줄었는지는 아직 확인하지 못했다.",
    "상자에 넣자 같은 전극에서 60 Hz 성분과 0.01–1 Hz 잡음이 크게 줄어 바깥 전기 잡음이 주된 원인으로 보이나(Ⅳ장 3절), 비교는 120초 기록이고 망을 접지한 직후에는 느린 변화가 오히려 커져, "
    "수 시간 단위 흔들림의 원인까지 확인하려면 긴 기록이 필요하다.")
rep("76", "■ 본 실험 결과를 채울 자리",
    "본 실험에서는 같은 전극을 패러데이 상자에 넣자 0.01–1 Hz 흔들림이 2.268 mV에서 0.060 mV로 줄어, 이 흔들림이 바깥 전기 잡음이었음을 확인했다. ■ 본 실험 결과를 채울 자리")
assert len(text_of("76")) <= 600, len(text_of("76"))

from xml.dom import minidom
minidom.parseString(s.encode("utf8"))
ids = re.findall(r'<hp:p id="(\d+)"', s)
assert len(ids) == len(set(ids)), "문단 id 겹침"
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("ok", len(text_of("76")))
