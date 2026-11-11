"""사진 두 장을 나란히 붙여 (가)(나) 표시를 넣는다. 보고서 사진4·사진5 용.
쓰는 법: python3 report/stim/photo_pair.py 왼쪽.jpg 오른쪽.jpg 결과.jpg"""
import sys
from PIL import Image, ImageOps, ImageDraw, ImageFont
a, b, out = sys.argv[1:4]
H, GAP = 1200, 24
ims = []
for f in (a, b):
    im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
    ims.append(im.resize((round(im.width * H / im.height), H), Image.LANCZOS))
W = sum(i.width for i in ims) + GAP
c = Image.new("RGB", (W, H), "white")
font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 64)
x = 0; d = ImageDraw.Draw(c)
for im, lab in zip(ims, ("(가)", "(나)")):
    c.paste(im, (x, 0))
    d.rectangle((x + 16, 16, x + 150, 104), fill="white")
    d.text((x + 28, 14), lab, fill="black", font=font)
    x += im.width + GAP
c.save(out, quality=90)
print(out, c.size)
