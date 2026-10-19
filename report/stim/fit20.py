"""21쪽 → 20쪽(2026-10-19). 쓰기: python3 -I fit20.py 원본.hwpx 결과.hwpx
1) 줄 배치 없는 빈 문단(모두의한글이 크게 잡는다): 407(406 과 겹친 빈 줄)은 지우고, 나머지는 11pt 한 줄 줄 배치를 넣는다.
2) 큰 그림을 비율 그대로 조금 줄인다(SCALE)."""
import sys, zipfile, re
from xml.dom import minidom
src, dst = sys.argv[1:3]
SCALE = {"image5": 0.88, "image9": 0.88, "image13": 0.92, "image10": 0.92, "image12": 0.92, "image1": 0.92, "image4": 0.92}
zi = zipfile.ZipFile(src)
x = zi.read("Contents/section0.xml").decode("utf-8")
EMPTY = '<hp:p id="{}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
m = re.search(r'<hp:p id="407" [^>]*>((?:(?!<hp:p id=).)*?)</hp:p>', x, re.S)
assert m and not re.findall(r"<hp:t>[^<]+", m.group(1)) and "lineseg" not in m.group(1)
x = x[:m.start()] + x[m.end():]
SEG = ('<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="1100" textheight="1100" baseline="935" '
       'spacing="660" horzpos="0" horzsize="48190" flags="2147876864"/></hp:linesegarray>')
for pid in ("310", "322", "354", "406", "435", "454", "468"):
    m = re.search(rf'<hp:p id="{pid}" [^>]*>((?:(?!<hp:p id=).)*?)</hp:p>', x, re.S)
    assert m and "lineseg" not in m.group(1) and not re.findall(r"<hp:t>[^<]+", m.group(1)), pid
    x = x[:m.end() - len("</hp:p>")] + SEG + x[m.end() - len("</hp:p>"):]
for ref, f in SCALE.items():
    ms = [m for m in re.finditer(r'<hp:p id="[^"]*"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', x, re.S) if f'binaryItemIDRef="{ref}"' in m.group(0)]
    assert len(ms) == 1, ref
    p = ms[0].group(0)
    w, h = map(int, re.search(r'<hp:sz width="(\d+)"[^>]*height="(\d+)"', p).groups())
    W, H = round(w * f), round(h * f)
    p = re.sub(r'(<hp:orgSz|<hp:curSz) width="\d+" height="\d+"', rf'\1 width="{W}" height="{H}"', p)
    p = re.sub(r'<hp:sz width="\d+"(.*?)height="\d+"', rf'<hp:sz width="{W}"\1height="{H}"', p)
    p = re.sub(r'<hc:pt1 x="\d+" y="0"/>', f'<hc:pt1 x="{W}" y="0"/>', p)
    p = re.sub(r'<hc:pt2 x="\d+" y="\d+"/>', f'<hc:pt2 x="{W}" y="{H}"/>', p)
    p = re.sub(r'<hc:pt3 x="0" y="\d+"/>', f'<hc:pt3 x="0" y="{H}"/>', p)
    p = re.sub(r'(<hp:lineseg [^>]*?)vertsize="\d+" textheight="\d+" baseline="\d+"',
               rf'\1vertsize="{H}" textheight="{H}" baseline="{round(H * 0.85)}"', p)
    x = x[:ms[0].start()] + p + x[ms[0].end():]
    print(f"{ref}: {w}×{h} → {W}×{H}")
minidom.parseString(x.encode("utf-8"))
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = x.encode("utf-8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
