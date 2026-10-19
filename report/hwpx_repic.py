# hwpx 안의 그림 하나를 다른 그림 파일로 바꾼다. 가로는 그대로 두고 세로를 새 그림 비율에 맞춘다.
#   python3 -I hwpx_repic.py 원본.hwpx 결과.hwpx image9 새그림.png
# (hwpx_edit.py 의 BinData 바꾸기는 같은 비율일 때만 쓴다 — 비율이 다르면 그림이 찌그러진다)
import re, sys, zipfile
from xml.dom import minidom
from PIL import Image
src, dst, ref, path = sys.argv[1:5]
zin = zipfile.ZipFile(src)
sec = zin.read("Contents/section0.xml").decode("utf-8")
w_px, h_px = Image.open(path).size
ms = [m for m in re.finditer(r'<hp:p id="[^"]*"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', sec, re.S)
      if f'binaryItemIDRef="{ref}"' in m.group(0)]
assert len(ms) == 1, len(ms)
p = ms[0].group(0)
width = int(re.search(r'<hp:sz width="(\d+)"', p).group(1))
height = round(width * h_px / w_px)
p = re.sub(r'(<hp:orgSz|<hp:curSz) width="\d+" height="\d+"', rf'\1 width="{width}" height="{height}"', p)
p = re.sub(r'<hp:sz width="\d+"(.*?)height="\d+"', rf'<hp:sz width="{width}"\1height="{height}"', p)
p = re.sub(r'<hc:pt2 x="\d+" y="\d+"/>', f'<hc:pt2 x="{width}" y="{height}"/>', p)
p = re.sub(r'<hc:pt3 x="0" y="\d+"/>', f'<hc:pt3 x="0" y="{height}"/>', p)
p = re.sub(r'<hp:imgClip [^>]*/>', f'<hp:imgClip left="0" right="{w_px * 75}" top="0" bottom="{h_px * 75}"/>', p)
p = re.sub(r'(<hp:lineseg [^>]*?)vertsize="\d+" textheight="\d+" baseline="\d+"',
           rf'\1vertsize="{height}" textheight="{height}" baseline="{round(height * 0.85)}"', p)
p = re.sub(r"<hp:shapeComment>.*?</hp:shapeComment>",
           f"<hp:shapeComment>그림입니다.\n원본 그림의 크기: 가로 {w_px}pixel, 세로 {h_px}pixel</hp:shapeComment>", p, flags=re.S)
sec = sec[:ms[0].start()] + p + sec[ms[0].end():]
minidom.parseString(sec.encode("utf-8"))
bins = [n for n in zin.namelist() if n.startswith("BinData/") and n.split("/")[-1].split(".")[0] == ref]
assert len(bins) == 1 and bins[0].endswith(".png") == path.lower().endswith(".png"), bins
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        data = (sec.encode("utf-8") if info.filename == "Contents/section0.xml"
                else open(path, "rb").read() if info.filename == bins[0] else zin.read(info.filename))
        zout.writestr(info, data)
z = zipfile.ZipFile(dst)
print(f"[성공] {ref} → {path} ({w_px}×{h_px}px, {width}×{height}) | 첫 항목:", z.infolist()[0].filename, z.infolist()[0].compress_type)
