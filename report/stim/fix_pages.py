# 모두의한글에서 3쪽이 빈 쪽 + 22쪽이던 것 정리(2026-10-19).
#  1) 목차 뒤 빈 문단 55~66 삭제 — 줄 배치가 없어 크게 잡혀 목차가 다음 쪽으로 넘치고, 67번의 쪽 나눔 때문에 3쪽이 통째로 빈다.
#  2) 연구 요약 제목 글상자(68) 줄 폭을 글상자 폭에 맞춤.
#  3) 그림 몇 장을 비율 그대로 줄인다(분량).
# 사용: python3 -I fix_pages.py 원본.hwpx 결과.hwpx image10=0.85 image12=0.85 ...
import re, sys, zipfile
from xml.dom import minidom
src, dst, specs = sys.argv[1], sys.argv[2], sys.argv[3:]
zin = zipfile.ZipFile(src)
x = zin.read("Contents/section0.xml").decode("utf-8")
n0 = len(x)
for pid in range(55, 67):
    m = re.search(rf'<hp:p id="{pid}"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', x, re.S)
    assert m and not "".join(re.findall(r"<hp:t>([^<]*)</hp:t>", m.group(0))).strip() and "<hp:tbl" not in m.group(0), pid
    x = x[:m.start()] + x[m.end():]
m = re.search(r'(<hp:p id="68".*?<hp:lineseg [^>]*?horzsize=")48190(")', x, re.S)
x = x[:m.start()] + m.group(1) + "19692" + m.group(2) + x[m.end():]
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
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        zout.writestr(info, x.encode("utf-8") if info.filename == "Contents/section0.xml" else zin.read(info.filename))
z = zipfile.ZipFile(dst)
print("빈 문단 12개 삭제, 첫 항목:", z.infolist()[0].filename, z.infolist()[0].compress_type)
