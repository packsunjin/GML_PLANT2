"""패러데이 상자 후 차폐 확인(표3 ⓪ '후', 2026-10-28)을 Ⅳ장 3절에 넣는다.
값: data/bench/bias_check_20261028_상자후.txt, CLAUDE.md ㉝ '2026-10-28 상자 후'(로컬 세션 계산, 120초 시험 기록 정상_7 = 파이 _extra).
- 900192(상자 전 문단) 뒤에 상자 후 문단, 표2 차폐 칸 크기 60×60×100 cm(실제 제작), 한계 444 의 자리 표시 채움, 사진4 캡션에 (가)(나)
쓰기: python3 -I cage_after.py 원본 결과 → hwpx_pics("■ 사진4 넣을 자리=PHOTO4_CAGE_20261028.jpg=39902", report 폴더에서 -I 없이) → hwpx_fillseg"""
import sys, zipfile, re, html

src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
assert "0.0013 mV" not in s
nid = max(int(x) for x in re.findall(r'<hp:p id="(\d+)"', s)) + 1


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


AFTER = ("상자에 넣은 뒤(2026-10-28)에는 같은 점퍼선 핀 전극을 그대로 두고, 상자 망을 라즈베리파이의 GND에 연결해 다시 쟀다(사진4). "
         "단극 점검에서 측정 채널(A0)의 20초 흔들림(최대–최소)은 약 70 mV에서 2.3 mV로 줄었다. 120초 시험 기록을 상자 전 기록의 처음 120초와 "
         "같은 방법으로 비교하면 60 Hz 상용전원 성분은 2.925 mV에서 0.0013 mV로, 이웃한 표본 사이 변화의 중앙값은 5.125 mV에서 ADC 한 칸(0.0625 mV)으로, "
         "0.01–1 Hz 잡음은 2.268 mV에서 0.060 mV로 줄었다. 전극을 바꾸지 않았으므로 이 차이는 주로 차폐에서 온 것으로 본다(측정한 날과 상자를 놓은 자리는 달랐다). "
         "다만 상자 후 기록은 120초뿐이어서, 수 시간 단위의 기준선 흔들림까지 줄었는지는 긴 기록으로 확인한다.")
m = leaf("900192")
p = re.sub(r'<hp:p id="900192"', f'<hp:p id="{nid}"', m.group(0), count=1)
p = noseg(re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(AFTER) + "</hp:t>", p, count=1))
s = s[:m.end()] + p + s[m.end():]

set_text("900145", "금속 방충망 60×60×100 cm 6면(틀은 PVC 관), GND 연결")
replace_in("444", "■ 본 실험에서 차폐로 줄었는지 반영 자리",
           "상자에 넣자 같은 전극에서 60 Hz 성분과 0.01–1 Hz 잡음이 크게 줄었으나(Ⅳ장 3절), 120초 비교라서 수 시간 단위의 기준선 흔들림이 함께 줄었는지는 아직 확인하지 못했다.")
m = leaf("900096")
cap = noseg(re.sub(r'(<hp:run charPrIDRef="44"><hp:t>)[^<]*',
                   r"\g<1> GND에 연결한 패러데이 상자(방충망 6면) — (가) 빈 상자, (나) 식물을 넣고 선을 상자 밖으로 뺀 모습", m.group(0)))
s = s[:m.start()] + cap + s[m.end():]

from xml.dom import minidom
minidom.parseString(s.encode("utf8"))
ids = re.findall(r'<hp:p id="(\d+)"', s)
assert len(ids) == len(set(ids))
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("ok", nid)
