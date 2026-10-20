"""그림을 비율 그대로 줄인다(fit20.py 의 그림 부분만 따로). 쓰기: python3 -I pic_scale.py 원본 결과 image5=0.9 image7=0.8 …"""
import sys, zipfile, re
from xml.dom import minidom
src, dst, specs = sys.argv[1], sys.argv[2], sys.argv[3:]
zi = zipfile.ZipFile(src)
x = zi.read("Contents/section0.xml").decode("utf-8")
for spec in specs:
    ref, f = spec.split("="); f = float(f)
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
