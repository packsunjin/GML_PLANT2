# 검토 2차(2026-10-17) — 글자 바꾸기로 안 되는 것 두 가지.
#   표5 머리 "판정" → "채널 오류 영향"(표12 의 "판정"은 그대로), 연구의 의의 ③ 문단 추가(② 문단 복제)
# 사용: python3 -I review2_struct.py 원본.hwpx 결과.hwpx
import re, sys, zipfile
from xml.dom import minidom
src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
x = zin.read("Contents/section0.xml").decode("utf-8")
i = x.find("표5."); j = x.find("</hp:tbl>", i)
seg = x[i:j]; assert seg.count("<hp:t>판정</hp:t>") == 1
x = x[:i] + seg.replace("<hp:t>판정</hp:t>", "<hp:t>채널 오류 영향</hp:t>") + x[j:]
m = [m for m in re.finditer(r'<hp:p id="(\d+)"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', x, re.S)
     if "② 측정값의 출처를 의심하고" in m.group(0)]
assert len(m) == 1; m = m[0]
nid = max(int(v) for v in re.findall(r'<hp:p id="(\d+)"', x)) + 1
p = m.group(0)
p = re.sub(r'<hp:p id="\d+"', f'<hp:p id="{nid}"', p, count=1)
p = re.sub(r"<hp:t>[^<]*</hp:t>", "<hp:t>③ 코드·원자료·측정 출처 기록(.meta.json)을 공개하고 재현 체크리스트(부록 2절)를 남겼다. "
           "다른 사람이 같은 결함을 피하고 결과를 직접 다시 계산해 볼 수 있다.</hp:t>", p, count=1)
assert p.count("<hp:t>") == 1
p = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)
x = x[:m.end()] + p + x[m.end():]
minidom.parseString(x.encode("utf-8"))
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        zout.writestr(info, x.encode("utf-8") if info.filename == "Contents/section0.xml" else zin.read(info.filename))
print("완료, 새 문단 id", nid)
