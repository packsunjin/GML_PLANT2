"""상처(가지 끝 자르기) 양성 대조 문단을 7절 밤샘 문단(900058) 뒤에 넣고, 한계(446)에 한 문장을 붙인다(2026-10-19).
쓰기: python3 -I cut_para.py 원본.hwpx 결과.hwpx
기록: data/ds/stim/_extra/자르기_20261019.csv (파이 이름 정상_6.csv, 360초, 자른 시각 약 14초 — 측정자 확인)"""
import sys, zipfile, re
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
NEW = ("식물이 반응할 수 있는 상태였는지 보려고, 변동전위를 일으킨다고 알려진 상처 자극을 한 번 주었다[3](2026-10-19). "
       "핀이 없는 갈래 끝을 가위로 자르고(기록 약 14초) 360초를 기록했다. 자른 순간 1초 안에 3.8 mV가 솟았다가 약 10초에 걸쳐 돌아왔고, "
       "그 뒤 346초 동안은 기준선이 분당 약 7.5 mV로 한 방향으로 내려갔을 뿐 이를 뺀 흔들림이 0.5 mV를 넘지 않았다. "
       "상처 뒤에도 늦게 오는 변화가 없었으므로, 자극에 반응이 없었던 것이 식물의 상태 때문인지 측정계가 보지 못해서인지는 가를 수 없다.")
m = re.search(r'<hp:p id="900058"[^>]*>.*?</hp:p>', s, flags=re.S)
assert m and "900070" not in s
p = m.group(0)
newp = re.sub(r'id="900058"', 'id="900070"', p, count=1)
newp = re.sub(r"<hp:t>[^<]*</hp:t>", "<hp:t>" + NEW + "</hp:t>", newp, count=1)
newp = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", newp, flags=re.S)
s = s[:m.end()] + newp + s[m.end():]
old = "늦게 오는 반응을 노린다면 누른 뒤 20~50초 구간을 자극으로 라벨해 다시 평가해야 한다."
assert s.count(old) == 1
s = s.replace(old, old + " 상처 자극(가지 끝 자르기) 한 번에도 늦은 변화가 없어, 식물 상태와 측정계 중 무엇이 원인인지 가리지 못했다.")
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
