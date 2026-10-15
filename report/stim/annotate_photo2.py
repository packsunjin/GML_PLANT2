# 사진2 에 전극 이름을 표시한다. 위치는 사진을 보고 정했고 색(파랑·주황·빨강)은 사용자 확인을 받는다.
# 사용: python3 -I report/stim/annotate_photo2.py report/PHOTO2_20261015.jpg report/PHOTO2_20261015_label.jpg
import sys
from PIL import Image, ImageDraw, ImageFont
im = Image.open(sys.argv[1]).convert("RGB"); d = ImageDraw.Draw(im)
font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 46)
# (가리킬 점, 글자 상자 왼쪽 위, 글자)
marks = [((822, 652), (230, 480), "위 측정 핀 (줄기 관통)"),
         ((822, 740), (200, 860), "아래 측정 핀 (줄기 관통)"),
         ((1060, 765), (1020, 900), "기준 핀 (흙)"),
         ((1365, 640), (1450, 430), "선 고정 (절연 테이프)")]
for (px, py), (tx, ty), text in marks:
    x0, y0, x1, y1 = d.textbbox((tx, ty), text, font=font)
    box = (x0 - 14, y0 - 10, x1 + 14, y1 + 10)
    cx = min(max(px, box[0]), box[2]); cy = box[3] if py > box[3] else box[1]
    d.line([(px, py), (cx, cy)], fill=(255, 220, 0), width=6)
    d.ellipse([px - 16, py - 16, px + 16, py + 16], outline=(255, 220, 0), width=6)
    d.rounded_rectangle(box, radius=10, fill=(255, 255, 255), outline=(30, 30, 30), width=3)
    d.text((tx, ty), text, font=font, fill=(20, 20, 20))
im.save(sys.argv[2], quality=92)
