# 그림 문단 줄 배치의 vertpos 를 고친다(2026-11-02). 사용: python3 -I hwpx_picpos.py 원본.hwpx 결과.hwpx [estimate|one]
#   estimate: 문서를 위에서부터 대략 흘려 그 그림이 쪽 안에서 놓일 높이를 넣는다(글 문단 줄 수는 hwpx_fillseg 의 글자 폭으로 셈)
#   one     : 0 이던 vertpos 를 1 로만 바꾼다
# 배경: 한글(한컴)은 vertpos 가 0 으로 돌아가면 새 쪽으로 읽는다. 글 문단 줄 배치는 hwpx_noseg 로 지우고, 그림 문단은 줄 배치가 있어야 보인다.
import re, sys, zipfile, html
src, dst = sys.argv[1:3]; mode = sys.argv[3] if len(sys.argv) > 3 else "estimate"
zi = zipfile.ZipFile(src); s = zi.read("Contents/section0.xml").decode("utf8"); h = zi.read("Contents/header.xml").decode("utf8")
BODY_H, BODY_W, LINE = 72852, 48190, 1760
pp = {}
for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', h, re.S):
    b = m.group(0)
    pv = re.search(r'<hc:prev value="(-?\d+)"', b); nx = re.search(r'<hc:next value="(-?\d+)"', b)
    pp[m.group(1)] = (int(pv.group(1)) if pv else 0, int(nx.group(1)) if nx else 0)
def cw(c):
    o = ord(c)
    if 0xAC00 <= o <= 0xD7A3 or 0x3130 <= o <= 0x318F or 0x4E00 <= o <= 0x9FFF: return 1100
    return 616 if c == " " else (572 if c.isascii() else 682)
def nlines(t):
    w = sum(cw(c) for c in t); return max(1, -(-int(w) // BODY_W))
top = list(re.finditer(r'<hp:p id="(\d+)" paraPrIDRef="(\d+)"[^>]*pageBreak="(\d)"[^>]*>(.*?)</hp:p>(?=<hp:p id|</hs:sec>)', s, re.S))
y, fixes = 0, {}
for m in top:
    pid, ppr, pb, b = m.groups(); pv, nx = pp.get(ppr, (0, 0))
    if pb == "1" and y > 0: y = 0
    y += pv
    if "<hp:tbl" in b:
        hgt = sum(max([int(x) for x in re.findall(r'<hp:cellSz width="\d+" height="(\d+)"', tr)] or [0])
                  for tr in re.findall(r"<hp:tr>.*?</hp:tr>", b, re.S)) + 1700
    elif "<hp:pic " in b:
        hgt = int(re.search(r'<hp:pic .*?<hp:sz width="\d+"[^>]*height="(\d+)"', b, re.S).group(1)) + 600
        if y + hgt > BODY_H: y = 0
        fixes[pid] = y
    else:
        t = html.unescape("".join(re.findall(r"<hp:t>([^<]*)</hp:t>", b)))
        hgt = nlines(t) * LINE
    if y + hgt > BODY_H and "<hp:pic " not in b: y = (y + hgt) - BODY_H
    else: y += hgt
    y += nx
n = 0
def fix(m):
    global n
    pid = m.group(1); p = m.group(0)
    if pid in fixes:
        new = fixes[pid] if mode == "estimate" else None
        def r(mm):
            v = int(mm.group(1))
            if mode == "one": return 'vertpos="%d"' % (1 if v == 0 else v)
            return 'vertpos="%d"' % new
        p2 = re.sub(r'vertpos="(\d+)"', r, p, count=1); n += p2 != p; return p2
    return p
s = re.sub(r'<hp:p id="(\d+)"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', fix, s, flags=re.S)
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        d = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, d, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print(mode, "그림 문단", len(fixes), "바꿈", n, {k: v for k, v in fixes.items()})
