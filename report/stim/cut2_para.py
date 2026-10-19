"""상처 양성 대조 2차(2026-10-19, 30분) 문단을 7절 밤샘 문단(900058) 뒤에 넣는다. 한계·결론·제언 문장은 cut2_edit.json.
쓰기: python3 -I cut2_para.py 원본.hwpx 결과.hwpx
기록: data/ds/stim/_extra/자르기2_20261019.csv (파이 자극_3.csv, 8:27 수집 시작, 약 5분째 자름, 자른 곳→가장 가까운 측정 핀 줄기 따라 약 20 cm — 측정자)"""
import sys, zipfile, re
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src)
s = zi.read("Contents/section0.xml").decode("utf8")
NEW = ("반응이 없었던 것이 측정계 때문인지 식물 때문인지 보려고, 변동전위를 일으킨다고 알려진 상처 자극[3]을 한 번 주었다(2026-10-19). "
       "30분 기록의 약 5분째에 핀이 없는 갈래 끝을 가위로 잘랐고, 자른 곳에서 가장 가까운 측정 핀까지는 줄기를 따라 약 20 cm였다. "
       "자른 순간에도 1초 평균의 2초 사이 변화는 0.8 mV를 넘지 않았고, 그 뒤 25분 동안 0.01–1 Hz 잡음은 5분 구간마다 0.5~1.0 mV로 자르기 전(1.0 mV)과 같았으며 늦게 오는 변화도 없었다. "
       "기준선은 30분 동안 −148 mV에서 −116 mV로 천천히 올라갔을 뿐이다. 상처에도 반응이 잡히지 않았으므로, 누르기에 반응이 없었던 것이 식물의 상태 때문인지 이 측정계가 식물 반응을 잡지 못하기 때문인지는 가를 수 없다.")
m = re.search(r'<hp:p id="900058"[^>]*>.*?</hp:p>', s, flags=re.S)
assert m and 'id="900071"' not in s
newp = re.sub(r'id="900058"', 'id="900071"', m.group(0), count=1)
newp = re.sub(r"<hp:t>[^<]*</hp:t>", "<hp:t>" + NEW + "</hp:t>", newp, count=1)
newp = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", newp, flags=re.S)
s = s[:m.end()] + newp + s[m.end():]
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
