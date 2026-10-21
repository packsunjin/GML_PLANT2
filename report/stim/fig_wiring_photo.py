# 사진4: 다시 꽂은 측정 회로(메인, 부품 이름표) + 조립 순서 작은 사진 3장.
# 이름표 위치는 사진을 보고 정했다 — 사용자 확인을 받는다(사진2 와 같은 절차).
# 사용: python3 -I report/stim/fig_wiring_photo.py 완성.jpg 1단계.jpg 2단계.jpg 3단계.jpg report/PHOTO4_WIRING.png
import sys
from PIL import Image, ImageDraw, ImageFont
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
main_p, s1, s2, s3, out = sys.argv[1:6]

def label(im, marks, size):
    d = ImageDraw.Draw(im); font = ImageFont.truetype(FONT, size)
    for pts, (tx, ty), text in marks:
        x0, y0, x1, y1 = d.textbbox((tx, ty), text, font=font)
        box = (x0 - 14, y0 - 10, x1 + 14, y1 + 10)
        for px, py in pts:
            cx = min(max(px, box[0]), box[2]); cy = box[3] if py > box[3] else (box[1] if py < box[1] else py)
            d.line([(px, py), (cx, cy)], fill=(255, 200, 0), width=7)
            d.ellipse([px - 18, py - 18, px + 18, py + 18], outline=(255, 200, 0), width=7)
        d.rounded_rectangle(box, radius=10, fill=(255, 255, 255), outline=(30, 30, 30), width=3)
        d.text((tx, ty), text, font=font, fill=(20, 20, 20))

# 메인: 원본 3264×2448 에서 회로 부분만 자른다
X0, Y0 = 650, 300
main = Image.open(main_p).convert("RGB").crop((X0, Y0, 2450, 2150))
P = lambda x, y: (x - X0, y - Y0)
label(main, [
    ([P(1460, 450)], P(1700, 330), "ADS1115 (16비트 ADC)"),
    ([P(1840, 1550)], P(1780, 1980), "라즈베리파이 5"),
    ([P(1100, 1480)], P(700, 330), "MCP6002 (전압 폴로어)"),
    ([P(1070, 1440)], P(700, 470), "0.1 µF 커패시터"),
    ([P(1080, 1665), P(1350, 1640)], P(700, 2010), "10 kΩ 저항 2개 (기준 전압 1.65 V)"),
    ([P(760, 1925), P(1180, 1710)], P(700, 1750), "전극선 (식물·흙으로)"),
], 54)

# 작은 사진: 조립 순서
steps = [(s1, (1050, 760, 2120, 2250), "① 칩 꽂고 다리 묶기"),
         (s2, (1020, 680, 2000, 1950), "② 저항·커패시터·전원선"),
         (s3, (760, 480, 2380, 2110), "③ ADS1115·파이 연결")]
H = main.height
cell_h = (H - 2 * 20) // 3
thumbs = []
for path, box, text in steps:
    t = Image.open(path).convert("RGB").crop(box)
    t = t.resize((int(t.width * (cell_h - 70) / t.height), cell_h - 70))
    thumbs.append((t, text))
W2 = max(t.width for t, _ in thumbs)
canvas = Image.new("RGB", (main.width + 30 + W2, H), "white")
canvas.paste(main, (0, 0))
d = ImageDraw.Draw(canvas); f = ImageFont.truetype(FONT, 48)
y = 0
for t, text in thumbs:
    x = main.width + 30 + (W2 - t.width) // 2
    d.text((main.width + 30, y + 5), text, font=f, fill=(20, 20, 20))
    canvas.paste(t, (x, y + 70))
    d.rectangle([x, y + 70, x + t.width - 1, y + 70 + t.height - 1], outline=(150, 150, 150), width=3)
    y += cell_h + 20
canvas.save(out, dpi=(300, 300))
print(canvas.size)
