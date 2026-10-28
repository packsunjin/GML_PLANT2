"""2026-10-28 상자 후 측정은 망을 GND 에 잇지 않은 채였다(사용자 확인). 900193·사진4 캡션을 사실대로 고친다.
쓰기: python3 -I cage_nognd.py 원본 결과 → hwpx_fillseg"""
import sys, zipfile, re, html
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src); s = zi.read("Contents/section0.xml").decode("utf8")
def esc(t): return html.escape(t, quote=False).replace("'", "&apos;").replace('"', "&quot;")
def edit(pid, a, b):
    global s
    m = re.search(rf'<hp:p id="{pid}"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', s, re.S); p = m.group(0)
    assert p.count(esc(a)) == 1, (pid, a)
    p = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p.replace(esc(a), esc(b)), flags=re.S)
    s = s[:m.start()] + p + s[m.end():]
edit("900193", "같은 점퍼선 핀 전극을 그대로 두고, 상자 망을 라즈베리파이의 GND에 연결해 다시 쟀다(사진4).",
     "같은 점퍼선 핀 전극을 그대로 두고 다시 쟀다(사진4). 이때 상자 망은 GND에 연결하지 않은 상태였다.")
edit("900096", "GND에 연결한 패러데이 상자", "패러데이 상자")
from xml.dom import minidom; minidom.parseString(s.encode("utf8"))
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        zo.writestr(it, s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename),
                    compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("ok")
