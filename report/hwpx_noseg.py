# hwpx 의 줄 배치 정보(<hp:linesegarray>)를 전부 지운다. 사용: python3 -I hwpx_noseg.py 원본.hwpx 결과.hwpx
# 한글(한컴)은 줄 배치의 vertpos 가 0 으로 돌아가면 새 쪽으로 읽는다. hwpx_fillseg·hwpx_picseg 가 문단마다 vertpos 를 0 부터 써서
# 20쪽 문서가 한글에서 43~45쪽이 됐다(2026-11-02). 줄 배치가 없으면 한글이 스스로 다시 계산한다(17쪽 확인). 맨 마지막 단계로 쓴다.
import sys, re, zipfile
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src); s = zi.read("Contents/section0.xml").decode("utf8")
n = s.count("<hp:linesegarray>")
s = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", s, flags=re.S)
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        d = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, d, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("지운 줄 배치", n, "testzip", zipfile.ZipFile(dst).testzip())
