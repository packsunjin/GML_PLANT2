# hwpx 의 글 문단 줄 배치 정보(<hp:linesegarray>)를 지운다. 그림(<hp:pic>)이 든 문단은 남긴다.
# 사용: python3 -I hwpx_noseg.py 원본.hwpx 결과.hwpx
# 한글(한컴)은 줄 배치의 vertpos 가 0 으로 돌아가면 새 쪽으로 읽는다. hwpx_fillseg·hwpx_autoseg 가 문단마다 vertpos 를 0 부터 써서
# 20쪽 문서가 한글에서 43~45쪽이 됐다(2026-11-02). 줄 배치를 전부 지우면 17쪽이 되지만 그림이 안 보인다(그림 문단은 줄 배치가 있어야
# 높이가 잡힌다, 2026-10-17 과 같은 증상) — 그래서 그림 문단 것은 남긴다. 맨 마지막 단계로 쓴다.
import sys, re, zipfile
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src); s = zi.read("Contents/section0.xml").decode("utf8")
kept = removed = 0
def fix(m):
    global kept, removed
    p = m.group(0)
    if "<hp:pic " in p:
        kept += 1; return p
    removed += p.count("<hp:linesegarray>")
    return re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)
# 맨 안쪽 문단 단위로 처리(문단 안에 다른 문단이 없는 것)
s = re.sub(r'<hp:p id="\d+"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', fix, s, flags=re.S)
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        d = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, d, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("지운 줄 배치", removed, "그림 문단 남김", kept, "testzip", zipfile.ZipFile(dst).testzip())
