# hwpx 그림 문단에 줄 배치(linesegarray)를 채운다. 파이·클라우드 어디서나.
#   python3 -I hwpx_picseg.py 원본.hwpx 결과.hwpx
# 이 문서는 rhwp 로 변환된 것이라, 보는 프로그램이 문단 높이를 linesegarray 에서 읽는다.
# 그림 문단에 이게 없으면 높이 0 으로 놓여 그림이 안 보인다(2026-10-17, 그림8 캡션만 보임).
# 원본 그림 문단(image1~5)과 같은 값을 쓰고 높이만 그림 높이로 맞춘다. vertpos 는 0(보는 쪽이 다시 계산).
import re, sys, zipfile
from xml.dom import minidom

def seg(height):
    return ('<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="%d" textheight="%d" '
            'baseline="%d" spacing="250" horzpos="0" horzsize="48190" flags="2147876864"/></hp:linesegarray>'
            % (height, height, round(height * 0.85)))

def fix(sec):
    out, pos, n = [], 0, 0
    for m in re.finditer(r'<hp:p id="[^"]*"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', sec, re.S):
        p = m.group(0)
        if "<hp:pic " in p and "<hp:linesegarray>" not in p and p.count("<hp:pic ") == 1:
            h = int(re.search(r'<hp:sz width="\d+"[^>]*height="(\d+)"', p).group(1))
            p = p[: -len("</hp:p>")] + seg(h) + "</hp:p>"
            n += 1
        out.append(sec[pos:m.start()]); out.append(p); pos = m.end()
    out.append(sec[pos:])
    return "".join(out), n

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    zin = zipfile.ZipFile(src)
    sec, n = fix(zin.read("Contents/section0.xml").decode("utf-8"))
    minidom.parseString(sec.encode("utf-8"))
    with zipfile.ZipFile(dst, "w") as zout:
        for info in zin.infolist():
            zout.writestr(info, sec.encode("utf-8") if info.filename == "Contents/section0.xml"
                          else zin.read(info.filename))
    z = zipfile.ZipFile(dst)
    print("줄 배치 채운 그림 문단:", n, "| testzip:", z.testzip(), "| 첫 항목:", z.infolist()[0].filename,
          z.infolist()[0].compress_type)
