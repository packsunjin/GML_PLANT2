"""photo_labels.py — 보고서 사진에 회로 사진(PHOTO4_WIRING)처럼 이름표·지시선을 단다 (2026-11-17).
이름표 위치는 사진을 눈으로 보고 정했다(픽셀 좌표). 확실하지 않은 부품은 이름을 붙이지 않았다.
쓰는 법: python3 report/stim/photo_labels.py → report/PHOTO_L_*.jpg
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
R = os.path.join(os.path.dirname(__file__), "..")
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
YEL, INK = (245, 196, 0), (25, 25, 25)


def label(src, dst, items, scale=0.026):
    im = ImageOps.exif_transpose(Image.open(os.path.join(R, src))).convert("RGB")
    d = ImageDraw.Draw(im)
    W = im.width
    f = ImageFont.truetype(FONT, max(18, int(W * scale)))
    lw = max(3, W // 500); r = max(5, W // 260); pad = max(6, W // 220)
    for text, (tx, ty), points in items:
        bb = d.textbbox((0, 0), text, font=f)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        box = (tx, ty, tx + w + 2 * pad, ty + h + 2 * pad)
        anchor = ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)
        for px, py in points:
            ax = min(max(px, box[0]), box[2]); ay = box[3] if py > box[3] else (box[1] if py < box[1] else anchor[1])
            d.line([(ax, ay), (px, py)], fill=YEL, width=lw)
            d.ellipse([px - r, py - r, px + r, py + r], fill=YEL, outline=INK, width=max(1, lw // 2))
        d.rounded_rectangle(box, radius=pad, fill="white", outline=INK, width=max(2, lw // 2))
        d.text((tx + pad - bb[0], ty + pad - bb[1]), text, font=f, fill=INK)
    im.save(os.path.join(R, dst), quality=92)
    print(dst, im.size)


# 사진: 본 실험 장치 (가)(나) 합친 사진 3224×1200
label("PHOTO4_CAGE_20261105.jpg", "PHOTO_L_CAGE.jpg", [
    ("방충망 패러데이 상자", (360, 160), [(700, 330)]),
    ("방울토마토 화분", (90, 960), [(800, 860)]),
    ("상자 밖 회로", (1180, 1000), [(1215, 860)]),
    ("상자 안 화분", (2380, 160), [(2230, 300)]),
    ("브레드보드 회로", (2380, 560), [(2830, 830)]),
    ("라즈베리파이 5", (2240, 1050), [(2900, 1040)]),
], scale=0.016)
# 사진: 줄기에 꽂은 은선 1800×1350
label("PHOTO_SILVER_STEM.jpg", "PHOTO_L_STEM.jpg", [
    ("은선 전극 두 가닥", (1120, 420), [(775, 650), (1012, 760)]),
    ("화분 흙", (90, 1180), [(300, 1000)]),
    ("회로로 가는 선", (1150, 1180), [(1330, 1000)]),
])
# 사진: 물에 담근 은선 1800×1350
label("PHOTO_SILVER_WATER.jpg", "PHOTO_L_SILVER_WATER.jpg", [
    ("은선 두 가닥", (1250, 230), [(850, 330), (1235, 650)]),
    ("기준 전극 (점퍼선)", (60, 560), [(805, 680)]),
    ("자른 페트병 · 수돗물", (1180, 1000), [(1000, 900)]),
])
# 사진: 물에 담근 점퍼선 핀(예비 2단계) 2000×1500
label("PHOTO_JUMPER_WATER.jpg", "PHOTO_L_JUMPER_WATER.jpg", [
    ("점퍼선 핀 3개 (수돗물에 담금)", (150, 1180), [(950, 1010), (1195, 905), (1290, 1215)]),
    ("자른 페트병", (1450, 1330), [(1270, 1380)]),
    ("라즈베리파이 5", (80, 140), [(560, 430)]),
    ("브레드보드 회로", (1500, 880), [(1250, 520)]),
    ("ADS1115", (1700, 520), [(1560, 380)]),
])
