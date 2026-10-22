"""Ⅳ장 3절 앞에 상자 전 정상 기록(표3 ⓪의 '전', 2026-10-21~22, 20.35시간) 문단을 넣는다.
값: data/faraday/상자전_정상_20261021.csv.gz·.env.csv (CLAUDE.md ㉝). 0.01–1 Hz sd 는 보고서 분석 방법(25개 평균 → 10 S/s, 4차 앞뒤 필터)으로 30분마다.
쓰기: python3 -I pre_cage_para.py 원본.hwpx 결과.hwpx → hwpx_fillseg.py"""
import sys, zipfile, re, html

src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
assert "20.35시간" not in s
nid = max(int(x) for x in re.findall(r'<hp:p id="(\d+)"', s)) + 1


def esc(t):
    return html.escape(t, quote=False).replace("'", "&apos;").replace('"', "&quot;")


TEXT = ("상자에 넣기 전의 비교 기준(표3 ⓪)으로, 예비 실험과 같은 점퍼선 핀 전극을 원줄기 위·아래 약 1 cm 간격으로 꽂고 "
        "손대지 않은 채 20.35시간(2026-10-21~22)을 기록했다. 기록은 끊긴 곳 없이 250 S/s를 유지했다. "
        "0.01–1 Hz 잡음은 30분마다 0.4~16.5 mV(중앙값 5.3 mV)로, 전극 간격이 3 cm였던 예비 밤샘 기록(1.3~8.8 mV, 중앙값 4.3 mV)보다 "
        "작지 않았고, 30분 평균 기준선은 −168~−11 mV 사이를 오갔다. 같은 시간 온습도(DHT11)는 20.6~24.5 °C, 25~42 %였으며, "
        "10분 평균 기준선은 온도와 함께 오르내렸다(상관계수 0.61, 습도는 −0.14). 온습도 센서를 읽는 순간의 전압 변화는 "
        "다른 때와 0.3 mV 안으로 같아, 센서가 측정에 끼어들지 않았다. 상자 안 기록은 이 값과 비교한다.")

m = re.search(r'<hp:p id="900139"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', s, re.S)
p = m.group(0)
new = re.sub(r'<hp:p id="900139"', f'<hp:p id="{nid}"', p, count=1)
new = re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(TEXT) + "</hp:t>", new, count=1)
new = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", new, flags=re.S)
ph = re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(
    "■ 채울 자리 — 표3 ②·③ 결과. 상자 안에서 손대지 않은 기록의 흔들림(위 상자 전 기록과 비교)과 화상 뒤 변화") + "</hp:t>", p, count=1)
ph = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", ph, flags=re.S)
s = s[:m.start()] + new + ph + s[m.end():]

from xml.dom import minidom
minidom.parseString(s.encode("utf8"))
ids = re.findall(r'<hp:p id="(\d+)"', s)
assert len(ids) == len(set(ids))
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("ok", nid)
