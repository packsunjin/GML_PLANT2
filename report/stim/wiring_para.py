# 부록 1절에 배선 문단을 더한다(2026-10-19, 검토 "보고서만으로 재현 가능한가").
# 사용: python3 -I wiring_para.py 원본.hwpx 결과.hwpx   — "웹 대시보드의 학습 기본값" 문단 바로 앞에 넣는다.
import re, sys, zipfile
from xml.dom import minidom
src, dst = sys.argv[1], sys.argv[2]
TEXT = ("배선은 다음과 같다. MCP6002(DIP-8)의 1·2번 핀을 묶은 출력 A를 ADS1115 A0에, 6·7번 핀을 묶은 출력 B를 A1에 연결하고, "
        "3번(입력 A+)에 위 측정 전극, 5번(입력 B+)에 아래 측정 전극, 8번에 3.3 V, 4번에 GND를 연결하며 8–4번 사이에 0.1 µF를 둔다. "
        "3.3 V와 GND 사이에 10 kΩ 두 개를 직렬로 두고 그 중점(1.65 V)을 흙의 기준 전극에 연결한다. "
        "ADS1115는 VDD·GND·SCL·SDA를 라즈베리파이 1·6·5·3번 핀에 연결하고, A0·A1 신호선은 서로 꼬았다. "
        "핀 번호표와 재현 순서는 저장소[9] README의 「DC 측정 회로 배선」「보고서 실험 재현 순서」에 있다.")
zin = zipfile.ZipFile(src)
x = zin.read("Contents/section0.xml").decode("utf-8")
ms = [m for m in re.finditer(r'<hp:p id="(\d+)"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', x, re.S)
      if "웹 대시보드의 학습 기본값" in m.group(0)]
assert len(ms) == 1
m = ms[0]
nid = max(int(v) for v in re.findall(r'<hp:p id="(\d+)"', x)) + 1
p = re.sub(r'<hp:p id="\d+"', f'<hp:p id="{nid}"', m.group(0), count=1)
assert p.count("<hp:t>") == 1
p = re.sub(r"<hp:t>[^<]*</hp:t>", "<hp:t>" + TEXT + "</hp:t>", p, count=1)
p = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)
x = x[:m.start()] + p + x[m.start():]
minidom.parseString(x.encode("utf-8"))
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        zout.writestr(info, x.encode("utf-8") if info.filename == "Contents/section0.xml" else zin.read(info.filename))
z = zipfile.ZipFile(dst)
print("완료, 새 문단 id", nid, "| 첫 항목:", z.infolist()[0].filename, z.infolist()[0].compress_type)
