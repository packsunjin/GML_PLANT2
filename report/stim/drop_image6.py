"""본문에서 안 쓰는 옛 그림(image6, 0.5–20 Hz·10초 창)을 파일에서 지운다(2026-10-19 검토자가 그림5로 착각).
쓰기: python3 -I drop_image6.py 원본.hwpx 결과.hwpx"""
import sys, zipfile, re
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
assert 'binaryItemIDRef="image6"' not in zi.read("Contents/section0.xml").decode()
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        if it.filename == "BinData/image6.png":
            continue
        data = zi.read(it.filename)
        if it.filename == "Contents/content.hpf":
            data = re.sub(rb'<opf:item id="image6"[^>]*/>', b"", data)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
