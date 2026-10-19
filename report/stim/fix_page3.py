"""3쪽 빈 쪽 제거: 쪽 나눔만 가진 빈 문단(id 67)을 지우고 쪽 나눔을 요약 표 문단(id 77)으로 옮긴다.
모두의한글은 id 67 을 3쪽에 두고, 요약 상자+표(id 77)가 그 아래 안 들어가 4쪽으로 넘겨 3쪽이 비었다.
쓰기: python3 -I fix_page3.py 원본.hwpx 결과.hwpx"""
import sys, zipfile
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
old = ('<hp:p id="67" paraPrIDRef="36" styleIDRef="0" pageBreak="1" columnBreak="0" merged="0">'
       '<hp:run charPrIDRef="43"><hp:t></hp:t></hp:run></hp:p>')
assert s.count(old) == 1
s = s.replace(old, "")
a = '<hp:p id="77" paraPrIDRef="36" styleIDRef="0" pageBreak="0"'
assert s.count(a) == 1
s = s.replace(a, a.replace('pageBreak="0"', 'pageBreak="1"'))
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
