# 표지 문단의 줄 배치(linesegarray)를 원본 정리본에서 되살린다(2026-10-19, "처음 2쪽이 빈칸").
# 글자를 고친 문단은 hwpx_edit 가 줄 배치를 지우는데, 이 문서를 보는 프로그램은 문단 높이를 줄 배치에서 읽는다(0절 3절 그림 문단과 같은 문제).
# 사용: python3 -I cover_lineseg.py 정리본.hwpx 원본.hwpx 결과.hwpx   — 정리본에는 있고 원본에는 없는 문단의 줄 배치를 채운다(앞 50문단).
import re, sys, zipfile
from xml.dom import minidom
ref, src, dst = sys.argv[1:4]
rx = zipfile.ZipFile(ref).read("Contents/section0.xml").decode("utf-8")
zin = zipfile.ZipFile(src)
x = zin.read("Contents/section0.xml").decode("utf-8")
PAT = r'<hp:p id="(\d+)"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>'
segs = {}
for m in list(re.finditer(PAT, rx, re.S))[:50]:
    s = re.search(r"<hp:linesegarray>.*?</hp:linesegarray>", m.group(0), re.S)
    if s:
        segs[m.group(1)] = s.group(0)
out, pos, fixed = [], 0, []
for m in list(re.finditer(PAT, x, re.S))[:50]:
    p = m.group(0)
    if "<hp:linesegarray>" not in p and m.group(1) in segs and "<hp:tbl" not in p and "<hp:pic " not in p:
        seg = segs[m.group(1)]
        seg = re.sub(r'textpos="\d+"', 'textpos="0"', seg, count=1)
        seg = re.sub(r"(</hp:lineseg>|/>)(?:<hp:lineseg .*?/>)+", r"\1", seg, flags=re.S)   # 한 줄만 남긴다
        p = p[:-len("</hp:p>")] + seg + "</hp:p>"
        fixed.append(m.group(1))
    out.append(x[pos:m.start()]); out.append(p); pos = m.end()
out.append(x[pos:])
x = "".join(out)
minidom.parseString(x.encode("utf-8"))
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        zout.writestr(info, x.encode("utf-8") if info.filename == "Contents/section0.xml" else zin.read(info.filename))
z = zipfile.ZipFile(dst)
print("줄 배치 되살린 문단:", fixed, "| 첫 항목:", z.infolist()[0].filename, z.infolist()[0].compress_type)
