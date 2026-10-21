"""부록 1절에 핀 단위 배선표(표7)를 넣는다(2026-10-21, 사용자 "보고서에 정확한 배선이 없잖아").
배선 문단(900069)은 표를 가리키는 짧은 글로 바꾼다. 값은 README 「DC 측정 회로 배선」·CLAUDE.md ㉞ 와 같다.
쓰기: python3 -I wiring_table.py 원본.hwpx 결과.hwpx (dht_wiring.py 다음) → hwpx_fillseg.py"""
import sys, zipfile, re, html

src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
assert "표7." not in s
NEXT = [max(int(x) for x in re.findall(r'<hp:p id="(\d+)"', s)) + 1]


def nid():
    NEXT[0] += 1
    return str(NEXT[0] - 1)


def esc(t):
    return html.escape(t, quote=False).replace("'", "&apos;").replace('"', "&quot;")


def noseg(p):
    return re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)


def leaf(pid):
    return re.search(rf'<hp:p id="{pid}"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', s, re.S)


def with_text(p, t):
    return noseg(re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(t) + "</hp:t>", p, count=1))


def lines(text, width, size=1000):
    w = sum(size * (1.0 if 0xAC00 <= ord(c) <= 0xD7A3 else 0.56 if c == " " else 0.52 if c.isascii() else 0.62) for c in text)
    return max(1, -(-int(w) // max(1, width)))


def table(rows, widths):
    """표5(405)를 본보기로 3열 표"""
    tpl = re.search(r'<hp:p id="405".*?</hp:tbl>.*?</hp:p>', s, re.S).group(0)
    trs = re.findall(r"<hp:tr>.*?</hp:tr>", tpl, re.S)
    out, total = [], 0
    for r, cells in enumerate(rows):
        tr = trs[0] if r == 0 else trs[1]
        tcs = re.findall(r"<hp:tc .*?</hp:tc>", tr, re.S)
        h = max(1800, max(lines(t, widths[c] - 1020) for c, t in enumerate(cells)) * 1600 + 400)
        total += h
        new = []
        for c, (tc, t) in enumerate(zip(tcs, cells)):
            p = re.search(r"<hp:p id=.*?</hp:p>", tc, re.S).group(0)
            tc = tc.replace(p, with_text(re.sub(r'<hp:p id="\d+"', f'<hp:p id="{nid()}"', p, count=1), t))
            tc = re.sub(r'rowAddr="\d+"', f'rowAddr="{r}"', tc)
            tc = re.sub(r'<hp:cellSz width="\d+" height="\d+"', f'<hp:cellSz width="{widths[c]}" height="{h}"', tc)
            new.append(tc)
        out.append("<hp:tr>" + "".join(new) + "</hp:tr>")
    body = tpl[:tpl.index("<hp:tr>")] + "".join(out) + tpl[tpl.rindex("</hp:tr>") + len("</hp:tr>"):]
    body = re.sub(r'<hp:p id="405"', f'<hp:p id="{nid()}"', body, count=1)
    body = re.sub(r'<hp:tbl id="\d+"', '<hp:tbl id="1900000201"', body, count=1)
    body = re.sub(r'rowCnt="\d+"', f'rowCnt="{len(rows)}"', body, count=1)
    return re.sub(r'(<hp:sz width="47620" widthRelTo="ABSOLUTE" height=")\d+', rf"\g<1>{total}", body, count=1)


ROWS = [["부품 · 핀", "연결", "역할"],
        ["MCP6002 1번(출력 A)·2번(입력 A−)", "두 핀을 묶어 ADS1115 A0", "전압 폴로어 A 출력"],
        ["MCP6002 3번(입력 A+)", "위 측정 전극", "줄기 위쪽 전극"],
        ["MCP6002 4번(VSS)", "GND", "음전원"],
        ["MCP6002 5번(입력 B+)", "아래 측정 전극", "줄기 아래쪽 전극"],
        ["MCP6002 6번(입력 B−)·7번(출력 B)", "두 핀을 묶어 ADS1115 A1", "전압 폴로어 B 출력"],
        ["MCP6002 8번(VDD)", "3.3 V, 8–4번 사이 0.1 µF", "양전원과 전원 잡음 거르기"],
        ["10 kΩ 두 개", "3.3 V – 10 kΩ – 중점 – 10 kΩ – GND", "중점 1.65 V를 흙의 기준 전극에 연결"],
        ["ADS1115 A2", "분압 중점", "기준 전압 점검용(bias_check.py)"],
        ["ADS1115 VDD·GND·SCL·SDA", "라즈베리파이 1·6·5·3번 핀", "전원과 I2C"],
        ["DHT11 + · out · −", "라즈베리파이 17·7(GPIO4)·9번 핀", "상자 안 온습도"],
        ["패러데이 상자 망", "브레드보드 GND", "차폐(기준 전극과는 닿지 않게)"]]

cap = leaf("389").group(0)
cap = noseg(re.sub(r'<hp:p id="389"', f'<hp:p id="{nid()}"', cap, count=1))
cap = re.sub(r'(<hp:run charPrIDRef="38"><hp:t>)[^<]*', r"\g<1>표7.", cap)
cap = re.sub(r'(<hp:run charPrIDRef="44"><hp:t>)[^<]*', r"\g<1> 측정 회로 배선표", cap)
tbl = table(ROWS, [13500, 18620, 15500])

m = leaf("900069")
p = m.group(0)
old = re.search(r"<hp:t>([^<]*)</hp:t>", p).group(1)
new = ("배선은 표7과 같다. 차동 입력 A0 − A1을 250 S/s로 읽고, 기준 전압은 흙의 기준 전극으로만 식물에 걸린다. "
       "DHT11은 라즈베리파이의 dht11 드라이버(설정 파일에 dtoverlay=dht11,gpiopin=4)로 읽는다. "
       "다시 구성한 회로와 조립 순서는 사진3과 같고, 재현 순서는 저장소[9] README의 「DC 측정 회로 배선」「보고서 실험 재현 순서」에 있다.")
p = with_text(p, new)
s = s[:m.start()] + p + cap + tbl + s[m.end():]

from xml.dom import minidom
minidom.parseString(s.encode("utf8"))
ids = re.findall(r'<hp:p id="(\d+)"', s)
assert len(ids) == len(set(ids))
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("ok, 바뀐 배선 문단 앞:", html.unescape(old)[:40])
