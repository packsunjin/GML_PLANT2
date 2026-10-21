"""부록 배선 문단(900069)에 DHT11 핀 연결을 넣고, 사진3 캡션에 'DHT11 은 촬영 뒤 추가'를 밝힌다(2026-10-21, 사용자 "배선에 DHT 없").
쓰기: python3 -I dht_wiring.py 원본.hwpx 결과.hwpx → 그다음 hwpx_fillseg.py"""
import sys, zipfile, re, html

src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
assert "DHT11 모듈은" not in s


def esc(t):
    return html.escape(t, quote=False).replace("'", "&apos;").replace('"', "&quot;")


def edit(pid, a, b):
    global s
    m = re.search(rf'<hp:p id="{pid}"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', s, re.S)
    p = m.group(0)
    assert p.count(esc(a)) == 1, (pid, a)
    p = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p.replace(esc(a), esc(b)), flags=re.S)
    s = s[:m.start()] + p + s[m.end():]


edit("900069", "다시 구성한 회로와 조립 순서는",
     "상자 안 온습도 센서 DHT11 모듈은 +를 라즈베리파이 17번(3.3 V), out을 7번(GPIO4), −를 9번(GND)에 연결하고, "
     "라즈베리파이의 dht11 드라이버(설정 파일에 dtoverlay=dht11,gpiopin=4)로 읽는다. 다시 구성한 회로와 조립 순서는")
edit("900075", "2026-10-21 촬영)", "2026-10-21 촬영, DHT11은 촬영 뒤 추가)")
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("ok")
