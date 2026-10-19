# 줄 배치(linesegarray)가 없는 글 문단 전부에 줄 배치를 계산해 넣는다(2026-10-19, 사용자 "보고서가 엉망").
#   python3 -I hwpx_fillseg.py 원본.hwpx 결과.hwpx
# 폭: 표 칸 안이면 칸 너비 − 칸 여백, 그 밖(본문)은 48190. 글상자 안 문단은 건드리지 않는다.
# 글자 폭·줄 나눔 계산은 hwpx_autoseg.py 와 같다.
import re, sys, zipfile, html
from xml.dom import minidom
sys.argv = sys.argv[:3]
src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
x = zin.read("Contents/section0.xml").decode("utf-8")
hdr = zin.read("Contents/header.xml").decode("utf-8")
BODY = 48190

def char_w(c, size):
    o = ord(c)
    if 0xAC00 <= o <= 0xD7A3 or 0x3130 <= o <= 0x318F or 0x4E00 <= o <= 0x9FFF:
        return size * 1.0
    if c == " ":
        return size * 0.56
    if c.isascii():
        return size * 0.52
    return size * 0.62

def breaks(text, width, size, keep_word):
    starts, cur, last_space, i = [0], 0.0, None, 0
    while i < len(text):
        c = text[i]
        w = char_w(c, size)
        if cur + w > width and i > starts[-1]:
            cut = last_space + 1 if (keep_word and last_space is not None and last_space + 1 > starts[-1]) else i
            starts.append(cut)
            cur = sum(char_w(ch, size) for ch in text[cut:i])
            last_space = None
            continue
        if c == " ":
            last_space = i
        cur += w
        i += 1
    return starts

# 표 칸 범위와 그 칸의 글 폭
cells = []
for tc in re.finditer(r"<hp:tc .*?</hp:tc>", x, re.S):
    b = tc.group(0)
    w = int(re.search(r'<hp:cellSz width="(\d+)"', b).group(1))
    mg = re.search(r'<hp:cellMargin left="(\d+)" right="(\d+)"', b)
    cells.append((tc.start(), tc.end(), w - (int(mg.group(1)) + int(mg.group(2)) if mg else 0)))
boxes = [(m.start(), m.end()) for m in re.finditer(r"<hp:drawText .*?</hp:drawText>", x, re.S)]

out, last, n = [], 0, 0
for m in re.finditer(r'<hp:p id="(\d+)"([^>]*)>((?:(?!<hp:p id=).)*?)</hp:p>', x, re.S):
    body = m.group(3)
    text = html.unescape("".join(re.findall(r"<hp:t>([^<]*)</hp:t>", body)))
    if "<hp:linesegarray>" in body or not text.strip() or "<hp:pic" in body or "<hp:tbl" in body:
        continue
    if any(a <= m.start() < b for a, b in boxes):
        continue
    inner = [c for c in cells if c[0] <= m.start() < c[1]]
    width = min(inner, key=lambda c: c[1] - c[0])[2] if inner else BODY
    if width < 1000:
        continue
    cpr = re.search(r'charPrIDRef="(\d+)"', body).group(1)
    size = int(re.search(rf'<hh:charPr id="{cpr}" height="(\d+)"', hdr).group(1))
    ppr = re.search(r'paraPrIDRef="(\d+)"', m.group(2)).group(1)
    blk = re.search(rf'<hh:paraPr id="{ppr}".*?</hh:paraPr>', hdr, re.S).group(0)
    pct = int(re.search(r'lineSpacing type="PERCENT" value="(\d+)"', blk).group(1))
    keep = 'breakNonLatinWord="KEEP_WORD"' in blk
    spacing = round(size * (pct - 100) / 100)
    st = breaks(text, width, size, keep)
    segs = "".join(
        f'<hp:lineseg textpos="{p}" vertpos="{k * (size + spacing)}" vertsize="{size}" textheight="{size}" '
        f'baseline="{round(size * 0.85)}" spacing="{spacing}" horzpos="0" horzsize="{width}" flags="2147876864"/>'
        for k, p in enumerate(st))
    out.append(x[last:m.end() - len("</hp:p>")] + "<hp:linesegarray>" + segs + "</hp:linesegarray></hp:p>")
    last = m.end()
    n += 1
    print(f"{m.group(1)}: {len(text)}자 → {len(st)}줄 (폭 {width})")
x = "".join(out) + x[last:]
minidom.parseString(x.encode("utf-8"))
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        data = x.encode("utf-8") if info.filename == "Contents/section0.xml" else zin.read(info.filename)
        zout.writestr(info, data, compress_type=zipfile.ZIP_STORED if info.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("채운 문단", n)
