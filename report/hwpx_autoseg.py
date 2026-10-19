# 줄 배치(linesegarray)가 없는 글 문단에 줄 배치를 계산해 넣는다(2026-10-19, 모두의한글에서 3쪽이 백지).
#   python3 -I hwpx_autoseg.py 원본.hwpx 결과.hwpx 문단id=가로폭 [문단id=가로폭 ...]
# 모두의한글(rhwp 계열)은 문단 높이·줄 나눔을 저장된 줄 배치에서 읽는다. 없으면 그 문단(표 안이면 표 전체)이 안 그려질 수 있다.
# 글자 폭은 이 문서의 기존 줄 나눔 93줄로 맞춘 값(한글 ≈ 글자 크기, 공백·영숫자 ≈ 절반)을 조금 넉넉하게 잡았다.
# 줄 간격은 paraPr 의 비율(160 % → 글자 크기의 60 %), 글자 크기는 첫 run 의 charPr height.
import re, sys, zipfile, html
from xml.dom import minidom
src, dst, specs = sys.argv[1], sys.argv[2], sys.argv[3:]
zin = zipfile.ZipFile(src)
x = zin.read("Contents/section0.xml").decode("utf-8")
hdr = zin.read("Contents/header.xml").decode("utf-8")

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
    starts, cur, last_space = [0], 0.0, None
    i = 0
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

for spec in specs:
    pid, width = spec.split("=")
    width = int(width)
    m = re.search(rf'<hp:p id="{pid}"([^>]*)>((?:(?!<hp:p id=).)*?)</hp:p>', x, re.S)
    assert m, pid
    body = m.group(2)
    assert "<hp:linesegarray>" not in body, f"{pid} 에 이미 줄 배치가 있음"
    text = html.unescape("".join(re.findall(r"<hp:t>([^<]*)</hp:t>", body)))
    cpr = re.search(r'charPrIDRef="(\d+)"', body).group(1)
    size = int(re.search(rf'<hh:charPr id="{cpr}" height="(\d+)"', hdr).group(1))
    ppr = re.search(r'paraPrIDRef="(\d+)"', m.group(1)).group(1)
    blk = re.search(rf'<hh:paraPr id="{ppr}".*?</hh:paraPr>', hdr, re.S).group(0)
    pct = int(re.search(r'lineSpacing type="PERCENT" value="(\d+)"', blk).group(1))
    keep = 'breakNonLatinWord="KEEP_WORD"' in blk
    spacing = round(size * (pct - 100) / 100)
    st = breaks(text, width, size, keep) if text else [0]
    segs = "".join(
        f'<hp:lineseg textpos="{p}" vertpos="{k * (size + spacing)}" vertsize="{size}" textheight="{size}" '
        f'baseline="{round(size * 0.85)}" spacing="{spacing}" horzpos="0" horzsize="{width}" flags="2147876864"/>'
        for k, p in enumerate(st))
    new = m.group(0)[:-len("</hp:p>")] + "<hp:linesegarray>" + segs + "</hp:linesegarray></hp:p>"
    x = x[:m.start()] + new + x[m.end():]
    print(f"{pid}: {len(text)}자 → {len(st)}줄 (글자 {size}, 줄간격 {pct}%, 폭 {width})")
minidom.parseString(x.encode("utf-8"))
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        zout.writestr(info, x.encode("utf-8") if info.filename == "Contents/section0.xml" else zin.read(info.filename))
z = zipfile.ZipFile(dst)
print("첫 항목:", z.infolist()[0].filename, z.infolist()[0].compress_type)
