"""표10 끝에 상처 자극 줄을 하나 더한다(2026-10-19 검토). 쓰기: python3 -I cut2_table.py 원본.hwpx 결과.hwpx"""
import sys, zipfile, re
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
assert 'id="900072"' not in s
i = s.index('<hp:p id="900036"')
a = s.rfind("<hp:tr>", 0, i); b = s.index("</hp:tr>", i) + len("</hp:tr>")
row = s[a:b]
row = row.replace('id="900036"', 'id="900072"').replace('id="900037"', 'id="900073"').replace('rowAddr="6"', 'rowAddr="7"')
row = row.replace("정상 밤샘 12.3시간, 손대지 않았을 때", "상처 자극(가지 끝 절단, 핀까지 약 26 cm)")
row = row.replace("0.01–1 Hz 잡음 30분마다 1.5~9.9 mV, 20 mV 넘는 계단 20번", "자른 순간·이후 25분 변화 없음")
row = re.sub(r'<hp:lineseg textpos="(?!0")[^/]*/>', "", row)   # 오른쪽 칸은 한 줄
s = s[:b] + row + s[b:]
t = s.rfind("<hp:tbl ", 0, i)
head = s[t:s.index(">", t) + 1]
assert 'rowCnt="7"' in head
s = s[:t] + head.replace('rowCnt="7"', 'rowCnt="8"') + s[t + len(head):]
s = s.replace('<hp:sz width="47620" widthRelTo="ABSOLUTE" height="12600"', '<hp:sz width="47620" widthRelTo="ABSOLUTE" height="14400"', 1)
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
