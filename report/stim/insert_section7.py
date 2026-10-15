import sys, zipfile, re, xml.dom.minidom
from xml.sax.saxutils import escape
src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src); x = zin.read("Contents/section0.xml").decode()
# 1. 번호 밀기 (새 표10·그림6 이 들어가므로)
def ren(old, new):
    global x
    x = re.sub(r"(<hp:t>[^<]*)" + old, lambda m: m.group(1) + new, x)
for o, n in [("표11", "표12"), ("표10", "표11"), ("그림6", "그림7")]:
    while re.search(r"<hp:t>[^<]*" + o, x): ren(o, n)
x = x.replace("표12과 같다", "표12와 같다")
nid = max(int(i) for i in re.findall(r'<hp:p id="(\d+)"', x)) + 1
def para(runs, pp, st=0):
    global nid
    r = "".join(f'<hp:run charPrIDRef="{c}"><hp:t>{escape(t)}</hp:t></hp:run>' for c, t in runs)
    s = f'<hp:p id="{nid}" paraPrIDRef="{pp}" styleIDRef="{st}" pageBreak="0" columnBreak="0" merged="0">{r}</hp:p>'
    nid += 1; return s
H = lambda t: para([(61, t)], 0); B = lambda t: para([(59, t)], 41)
CAP = lambda n, t: para([(38, n), (44, " " + t)], 19, 28)
# 2. 표 복제(표7 본보기)
i = x.find("2단계 구간별 표류"); t = x.find("<hp:tbl", i)
s = x.rfind("<hp:p ", 0, t); e = x.find("</hp:p>", x.find("</hp:tbl>", t)) + 7
tbl = x[s:e]
cells = ["구분", "결과",
         "정상 1회차 0~15분의 0.01–1 Hz 잡음", "약 0.5 mV",
         "정상 1회차 22~30분의 기준선 오르내림", "1~2분에 50~130 mV",
         "자극 1회차, 누른 뒤 1초 안의 계단", "10번 중 4번, +5~+25 mV",
         "자극 1회차, 누른 뒤 늦게 온 변화", "1번(누른 뒤 10~20초에 +12 mV), 판단 보류"]
ts = list(re.finditer(r"<hp:t>[^<]*</hp:t>", tbl)); assert len(ts) == 10, len(ts)
for m, c in reversed(list(zip(ts, cells))):
    tbl = tbl[:m.start()] + f"<hp:t>{escape(c)}</hp:t>" + tbl[m.end():]
tbl = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", tbl, flags=re.S)
def newid(m):
    global nid
    nid += 1; return f'<hp:p id="{nid}"'
tbl = re.sub(r'<hp:p id="\d+"', newid, tbl)
tbl = re.sub(r'<hp:tbl id="\d+"', '<hp:tbl id="1900000099"', tbl)
nid += 1
new = [H("7. 손이 닿지 않는 자극과 새 분석 대역(0.01–1 Hz)"),
 B("6절의 한계는 두 가지였다. 손이 닿아 생긴 약 70·320 mV 계단이 반응을 가렸고, 당시 전처리(0.5–20 Hz 대역통과, 10초 창)는 수십 초짜리 활동전위가 놓이는 0.01–0.1 Hz(그림1)를 지웠다. 그래서 분석 대역을 0.01–1 Hz로, 분석 창을 30초(5초 이동, 앞 90초는 필터 문맥)로 바꾸고, 손이 식물에 닿지 않는 자극으로 다시 측정했다(2026-10-15)."),
 B("측정 핀은 갈라지기 전 원줄기에 위아래 3 cm 간격으로 꽂고, 기준 핀은 흙에 꽂았다. 측정 범위는 ±2.048 V다. 정상 회차는 30분 동안 아무것도 하지 않았고, 자극 회차는 시작 약 2분 뒤부터 약 3분마다 핀이 없는 갈래를 비금속 안경통으로 2초 눌렀고(30분에 10번), 누른 직후 스톱워치에 시각을 기록했다(최대 10초 늦음). 측정자는 두 회차 모두 같은 자리에 앉아 있었다. 정상과 자극 회차는 번갈아 모으고, 분류기는 회차 단위로 평가 자료를 떼어 학습한다."),
 B("결과를 표10과 그림6에 정리했다. 정상 1회차는 처음 15분 동안 기준선이 129~136 mV에서 거의 평평했고 0.01–1 Hz 잡음은 약 0.5 mV였다(그림6(가)). 그러나 15분 뒤부터 기준선이 내려가기 시작해 22~30분에는 1~2분에 걸쳐 50~130 mV씩 오르내렸다. 뾰족한 튐은 없었고 원인은 확인하지 못했다."),
 B("자극 1회차에서는 10번 중 4번, 누른 지 1초 안에 기준선이 5~25 mV 솟은 뒤 수십 초에 걸쳐 일부만 돌아왔고, 나머지 6번은 변화가 없었다. 그림6(나)·(다)에서 주황색은 계단이 생긴 4번, 회색은 변화가 없던 누르기이며, (다)의 노란 띠는 스톱워치 기록이 최대 10초 늦어 실제로 누른 순간이 들어 있는 구간이다. 누른 곳에서 핀까지는 약 10 cm라, 토마토에서 보고된 가장 빠른 전파 속도(전기 자극, 3.5–4.5 mm/s)[5]로도 20초 넘게 걸려야 한다. 또 실제 활동전위는 자극보다 늦게 도착한다[6]. 따라서 1초 안에 나타난 이 변화는 활동전위가 아니라, 누를 때 줄기가 휘며 핀이 움직여 생긴 것으로 본다(해석). 한 번(4번째)은 누른 뒤 10~20초 사이에 다시 12 mV가량 올라 그대로 머물렀는데, 한 번뿐이고 기준선으로 돌아오지 않아 반응인지 판단을 보류한다. 28~29분에는 마지막 누르기 30초 전부터 약 40초에 걸쳐 기준선이 약 85 mV 내려갔는데, 기록 간격·값의 범위·상용전원 성분의 크기가 모두 그대로여서 기록 오류는 아니었다."),
 CAP("표10.", "손이 닿지 않는 자극 실험의 관찰 요약"), tbl,
 para([(56, "■ 그림6 넣을 자리")], 19, 28),
 CAP("그림6.", "정상·자극 1회차 기록과 누른 시각 전후의 변화"),
 B("이후 회차는 줄기가 휘지 않도록 갈래 끝을 살짝 대기만 하고, 누른 지 3초 안의 변화는 잡음으로 보아 제외한다. 사람이 없는 밤에도 기록해 느린 기준선 변화가 사람의 움직임 때문인지 확인한다."),
 B("■ 채울 자리 — 회차 수(정상·자극), 평가 정확도(SVM·Random Forest), 특징 하나 문턱값 비교, 자극 뒤 늦게 오는 변화의 유무")]
key = "<hp:t>7. 종합</hp:t>"; assert x.count(key) == 1
i = x.find(key); s = x.rfind("<hp:p ", 0, i)
x = x[:s] + "".join(new) + x[s:]
x = x.replace(key, "<hp:t>8. 종합</hp:t>")
xml.dom.minidom.parseString(x.encode())
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        data = x.encode() if info.filename == "Contents/section0.xml" else zin.read(info.filename)
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = zipfile.ZIP_STORED if info.filename == "mimetype" else info.compress_type
        zi.external_attr = info.external_attr; zout.writestr(zi, data)
print("ok")
