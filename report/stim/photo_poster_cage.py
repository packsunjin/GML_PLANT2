"""포스터 사진1 — 새 식물 실험 장치 세 장을 한 줄로(2026-11-12).
(가) 방충망 패러데이 상자 전체 20261105_03, (나) 실험한 새 방울토마토 20261105_06, (다) 상자 밖 회로·라즈베리파이 20261105_08
(모두 2026-11-05 다시 세팅한 날 측정자가 찍은 사진, report/photos/README.md).
자르기·자동 대비·약간의 채도만 손대고 내용은 바꾸지 않는다.
쓰는 법(저장소 루트): python3 report/stim/photo_poster_cage.py report/PHOTO_POSTER_CAGE.jpg"""
import sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

H, GAP, R = 1400, 36, 28
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SHOTS = [  # 파일, 자르기(가로 시작·끝, 세로 시작·끝 비율), 이름표
    ("20261105_03", (0.20, 0.86, 0.00, 1.00), "(가) 방충망 패러데이 상자"),
    ("20261105_06", (0.10, 0.90, 0.00, 1.00), "(나) 실험한 방울토마토"),
    ("20261105_08", (0.18, 1.00, 0.12, 1.00), "(다) 상자 밖 회로·라즈베리파이"),
]

tiles = []
for name, (x0, x1, y0, y1), label in SHOTS:
    im = ImageOps.exif_transpose(Image.open(f"report/photos/{name}.jpg")).convert("RGB")
    w, h = im.size
    im = im.crop((round(w * x0), round(h * y0), round(w * x1), round(h * y1)))
    im = im.resize((round(im.width * H / im.height), H), Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=1)
    im = ImageEnhance.Color(im).enhance(1.15)
    im = ImageEnhance.Brightness(im).enhance(1.04)
    # 둥근 모서리
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=R, fill=255)
    tile = Image.new("RGB", im.size, "white"); tile.paste(im, (0, 0), mask)
    d = ImageDraw.Draw(tile)
    f = ImageFont.truetype(FONT, 58, index=1)
    tw = d.textlength(label, font=f)
    d.rounded_rectangle([24, 24, 24 + tw + 48, 24 + 96], radius=20, fill="#905720")
    d.text((48, 34), label, font=f, fill="white")
    tiles.append(tile)

out = Image.new("RGB", (sum(t.width for t in tiles) + GAP * (len(tiles) - 1), H), "white")
x = 0
for t in tiles:
    out.paste(t, (x, 0)); x += t.width + GAP
out.save(sys.argv[1], quality=90)
print("saved", sys.argv[1], out.size)
