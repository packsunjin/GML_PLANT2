# 표지의 양식 안내문 "(2026. 11. 1주(추후 공문 안내)까지 … 20페이지 이내 작성)" 과 혼자 남은 ")" 를 지운다.
# 문단은 남기고 글자만 비운다(표 칸 안일 수 있어 문단을 통째로 지우면 구조가 깨질 수 있다).
# 사용: python3 -I report/stim/cover_clean.py 원본.hwpx 결과.hwpx
import sys, re, zipfile, xml.dom.minidom
src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src); x = zin.read("Contents/section0.xml").decode()
def clear(pid, must):
    global x
    m = re.search(r'<hp:p id="' + pid + r'" [^>]*>.*?</hp:p>', x, re.S); assert m and must in m.group(0), pid
    p = re.sub(r"<hp:t>[^<]*</hp:t>", "<hp:t></hp:t>", m.group(0))
    p = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)
    x = x[:m.start()] + p + x[m.end():]
clear("4", "추후 공문 안내"); clear("12", "<hp:t>)</hp:t>")
xml.dom.minidom.parseString(x.encode())
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        zout.writestr(info, x.encode() if info.filename == "Contents/section0.xml" else zin.read(info.filename))
z = zipfile.ZipFile(dst); print("testzip", z.testzip(), z.infolist()[0].filename, z.infolist()[0].compress_type)
