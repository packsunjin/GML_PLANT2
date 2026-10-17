# 자극 2회차·밤샘·분류 결과를 보고서에 넣는다(2026-10-17).
#   python3 -I report/stim/finish_report.py 초안.hwpx 중간본.hwpx
# 그다음: python3 -I report/hwpx_pics.py 중간본.hwpx 최종.hwpx "■ 그림7 넣을 자리=report/FIG_PIPE.png=42000" "■ 그림8 넣을 자리=report/FIG_STIM2.png=40000"
#        → hwpx_edit.py … report/stim/fig8_caption.json → hwpx_edit.py … report/stim/summary_fit.json
# 하는 일
#  1) 번호 밀기: 표12→표13, 표11→표12, 그림7→그림9 (새 표11·그림7·그림8 이 들어가므로)
#  2) 표10 에 자극 2회차·밤샘 두 줄 추가
#  3) 7절 "이후 회차는…" 문단과 "■ 채울 자리" 를 2회차·밤샘·분류 원리·평가 문단, 표11, 그림7 자리로 바꿈
#  4) 표12·표13·결론·한계·요약의 해당 문장 갱신
import sys, zipfile, re, xml.dom.minidom
from xml.sax.saxutils import escape
src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src); x = zin.read("Contents/section0.xml").decode()

def ren(old, new):
    global x
    while re.search(r"<hp:t>[^<]*" + old, x):
        x = re.sub(r"(<hp:t>[^<]*)" + old, lambda m: m.group(1) + new, x)
for o, n in [("표12", "표13"), ("표11", "표12"), ("그림7", "그림9")]:
    ren(o, n)
x = x.replace("표13와 같다", "표13과 같다")

nid = max(int(i) for i in re.findall(r'<hp:p id="(\d+)"', x)) + 1
def para(runs, pp, st=0):
    global nid
    r = "".join(f'<hp:run charPrIDRef="{c}"><hp:t>{escape(t)}</hp:t></hp:run>' for c, t in runs)
    s = f'<hp:p id="{nid}" paraPrIDRef="{pp}" styleIDRef="{st}" pageBreak="0" columnBreak="0" merged="0">{r}</hp:p>'
    nid += 1; return s
B = lambda t: para([(59, t)], 0)                       # 본문(양쪽 정렬·160%)
CAP = lambda n, t: para([(38, n), (44, " " + t)], 19, 28)

def newids(s):
    global nid
    def f(m):
        global nid
        i = nid; nid += 1; return f'<hp:p id="{i}"'   # para() 와 같은 규칙: 지금 값을 쓰고 올린다
    return re.sub(r'<hp:p id="\d+"', f, s)

def build_table(tblp, rows, tbl_id=None):
    """표 문단(tblp)의 행을 rows(머리 행 포함 [(c0,c1),...])로 다시 만든다. 머리 행·본문 행 서식은 첫 두 행을 본보기로."""
    trs = re.findall(r"<hp:tr>.*?</hp:tr>", tblp, re.S)
    head, body = trs[0], trs[1]
    out = []
    for i, cells in enumerate(rows):
        tr = head if i == 0 else body
        ts = list(re.finditer(r"<hp:t>[^<]*</hp:t>", tr)); assert len(ts) == 2
        for m, c in reversed(list(zip(ts, cells))):
            tr = tr[:m.start()] + f"<hp:t>{escape(c)}</hp:t>" + tr[m.end():]
        tr = re.sub(r'rowAddr="\d+"', f'rowAddr="{i}"', tr)
        out.append(newids(re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", tr, flags=re.S)))
    a = tblp.find(trs[0]); b = tblp.rfind(trs[-1]) + len(trs[-1])
    hh = int(re.search(r'<hp:cellSz width="\d+" height="(\d+)"', head).group(1))
    bh = int(re.search(r'<hp:cellSz width="\d+" height="(\d+)"', body).group(1))
    t = tblp[:a] + "".join(out) + tblp[b:]
    t = re.sub(r'rowCnt="\d+"', f'rowCnt="{len(rows)}"', t, count=1)
    t = re.sub(r'(<hp:tbl [^>]*>\s*<hp:sz width="\d+" widthRelTo="\w+" height=")\d+', lambda m: m.group(1) + str(hh + bh * (len(rows) - 1)), t, count=1)
    if tbl_id:
        t = re.sub(r'<hp:tbl id="\d+"', f'<hp:tbl id="{tbl_id}"', t, count=1)
        t = newids(t[:t.find("<hp:tbl")]) + t[t.find("<hp:tbl"):]   # 표를 품은 바깥 문단 id 도 새로(복제 원본과 겹치지 않게)
    # 줄 배치 정보는 한글이 다시 계산하게 표 문단 전체에서 지운다
    return re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", t, flags=re.S)

def tbl_para(caption):
    i = x.find(caption); t = x.find("<hp:tbl", i)
    s = x.rfind("<hp:p ", 0, t); e = x.find("</hp:p>", x.find("</hp:tbl>", t)) + 7
    return s, e

# 2) 표10 두 줄 추가
s, e = tbl_para("손이 닿지 않는 자극 실험의 관찰 요약")
t10 = x[s:e]
rows10 = [("구분", "결과"),
          ("정상 1회차 0~15분의 0.01–1 Hz 잡음", "약 0.5 mV"),
          ("정상 1회차 22~30분의 기준선 오르내림", "1~2분에 50~130 mV"),
          ("자극 1회차(꾹 누름), 누른 뒤 1초 안의 계단", "10번 중 4번, +5~+25 mV"),
          ("자극 1회차, 누른 뒤 늦게 온 변화", "1번(누른 뒤 10~20초에 +12 mV), 판단 보류"),
          ("자극 2회차(살짝 댐), 댄 뒤의 계단·늦은 변화", "10번 모두 없음(2초 사이 변화 최대 2.1 mV)"),
          ("정상 밤샘 12.3시간, 손대지 않았을 때", "0.01–1 Hz 잡음 30분마다 1.5~9.9 mV, 20 mV 넘는 계단 20번")]
new10 = build_table(t10, rows10)
x = x[:s] + new10 + x[e:]

# 3) 7절 뒷부분
old_after = "이후 회차는 줄기가 휘지 않도록 갈래 끝을 살짝 대기만 하고"
old_fill = "■ 채울 자리 — 회차 수(정상·자극)"
def para_span(key):
    i = x.find(key); assert i > 0 and x.count(key) == 1, key
    return x.rfind("<hp:p ", 0, i), x.find("</hp:p>", i) + 7
t11 = build_table(new10, [
    ("평가·방법", "자극 창 찾음 / 오경보율 / 정확도"),
    ("A · Random Forest", "0/60 · 0.2 % · 90.9 %"),
    ("A · SVM", "0/60 · 27.5 % · 66.0 %"),
    ("A · 문턱 하나(2초 최대 변화)", "60/60 · 100 % · 8.9 %"),
    ("A · 모두 정상이라고 답함", "0/60 · 0 % · 91.1 %"),
    ("B · Random Forest", "1/60 · 13.5 % · 86.0 %"),
    ("B · SVM", "12/60 · 34.3 % · 65.4 %"),
    ("B · 문턱 하나(2초 최대 변화)", "0/60 · 22.5 % · 77.0 %"),
    ("B · 모두 정상이라고 답함", "0/60 · 0 % · 99.3 %")], tbl_id="1900000100")
new = [
 B("자극 2회차(2026-10-16)는 줄기가 휘지 않도록 같은 안경통을 갈래 윗부분에 2초 동안 살짝 대기만 했고(30분에 10번), 대고 약 5초 뒤 스톱워치에 시각을 기록했다. 30분 동안 1초 평균이 2초 사이에 5 mV 넘게 바뀐 곳이 한 번도 없었고(최대 2.1 mV), 댄 시각 근처의 변화(0.6~1.8 mV)는 이 기록 전체의 평소 흔들림과 같은 크기였다(그림8(가)). 댄 뒤 수십 초에 걸친 느린 오르내림은 댄 시각과 상관없이 방향이 제각각이었다. 같은 식물·같은 도구에서 누르는 힘만 줄이자 계단이 사라졌으므로, 1회차의 계단은 줄기가 휘어 생긴 잡음이라는 해석이 뒷받침된다. 0.01–1 Hz 잡음이 약 2 mV여서 문헌 크기(33.9 mV)[6]의 활동전위가 왔다면 보였겠지만, 댄 뒤 늦게 오는 변화는 나타나지 않았다."),
 B("사람이 없는 밤에도 12.3시간을 기록했다(정상 2회차, 2026-10-15~16). 아무도 건드리지 않았는데 0.01–1 Hz 잡음이 30분마다 1.5~9.9 mV였고, 1초 평균이 2초 사이에 20 mV 넘게 바뀐 계단이 20번 있었다(가까운 것은 하나로 셈). 이 계단은 오르고 내리는 방향이 섞여 있고 간격이 47초~2.7시간으로 일정하지 않아 1단계의 121초 주기 간섭과는 다르다. 물속 전극(0.06 mV, 표8)보다 훨씬 크므로 핀이 줄기에 꽂힌 자리에서 생기는 것으로 보이나(해석) 원인은 확인하지 못했다. 1회차의 계단(+5~+25 mV)과 크기가 같아, 계단의 크기만으로는 자극 때문인지 가를 수 없다."),
 B("분류기는 30초 창 하나를 입력으로 받는다. 창의 원신호를 0.01–1 Hz로 거른 뒤 스펙트로그램(시간 6칸 × 주파수 13칸)과 수치 특징 14개(최대–최소 폭, 실효값, 표준편차, 평균, 왜도, 첨도, 영점 교차율, 총 에너지, 저·중·고 대역 전력, 스펙트럼 중심·폭, 최대 주파수)를 계산한다. 직류 수준·기울기·표류는 핀을 다시 꽂으면 바뀌므로 뺐다. 랜덤 포레스트는 '어떤 특징이 기준값보다 크면 이쪽'이라는 질문을 이어 붙인 결정 트리 300개를 만들어 다수결로 판정하고, SVM은 특징 공간에서 두 무리를 가장 넓은 간격으로 가르는 경계를 찾는다(rbf 커널, C = 1). 자극 창이 정상 창보다 훨씬 적어 두 모델 모두 두 부류에 같은 비중을 주었다."),
 B("라벨은 창마다 붙였다. 자극 회차라도 누르지 않은 시간은 정상과 같으므로, 누른(댄) 시각이 든 30초 창만 자극(회차마다 60창)으로, 나머지는 정상으로 했다. 창이 5초씩 이동하며 겹쳐 무작위로 나누면 같은 순간이 학습과 평가에 함께 들어가므로 회차를 통째로 나누었다. 평가 A는 자극 2회차와 정상 밤샘으로 학습해 자극 1회차와 정상 1회차(674창)를, 평가 B는 반대로 학습해 자극 2회차와 정상 밤샘(9,181창)을 판정했다. 비교 기준으로 '창 안 2초 사이 최대 변화'에 문턱 하나를 둔 판정(학습 자료에서 가장 잘 가르는 값)과 모든 창을 정상이라고 답하는 판정을 함께 계산했다(표11). 그림7은 기록에서 창을 잘라 라벨을 붙이고 분류기 입력으로 바꾸는 과정을 자극 1회차의 한 창으로 보인 것이다."),
 para([(56, "■ 그림7 넣을 자리")], 19, 28),
 CAP("그림7.", "기록에서 분류기 입력을 만드는 과정 (자극 1회차, 655~685초 창)"),
 CAP("표11.", "회차를 나눈 정상·자극 분류 평가 (자극 창 60개)"), t11,
 B("어느 모델도 모든 창을 정상이라고 답하는 것보다 정확도가 높지 않았고, 자극 창을 60개 중 0~12개만 찾았다(표11, 그림8(라)·(마)). 자극 1회차로 학습한 랜덤 포레스트가 가장 많이 쓴 특징은 최대–최소 폭·실효값·표준편차(중요도 각 0.13)였다. 자극 창은 정상 창보다 최대–최소 폭이 약 2배(10.7 mV 대 5.5 mV)이고 스펙트럼 중심이 낮았다(0.18 Hz 대 0.31 Hz). 즉 모델은 '30초 안에 크고 느리게 흔들리면 자극'이라는 규칙을 배웠다. 그러나 2회차에서는 댄 뒤 흔들림이 커지지 않아 자극을 놓쳤고, 밤샘 기록에서는 손대지 않아도 생긴 크고 느린 흔들림을 자극으로 잘못 판정했다. 스펙트로그램에서도 계단은 창 전체가 밝아지는 모양으로만 나타나(그림8(다)) 같은 크기의 자연 흔들림과 구별되지 않는다."),
 para([(56, "■ 그림8 넣을 자리")], 19, 28),
 CAP("그림8.", "자극 2회차 기록과 분류기의 입력·판정"),
 B("정리하면, 손이 닿지 않는 자극에서 활동전위로 볼 만한 늦은 변화는 나타나지 않았고, 누를 때 생긴 잡음과 같은 크기의 자연 흔들림 때문에 분류기도 자극 창을 가르지 못했다(연구문제 2)."),
]
s, e = para_span(old_after); s2, e2 = para_span(old_fill); assert s2 >= e
x = x[:s] + "".join(new) + x[e2:]

# 4) 다른 절 문장
def rep(old, new, n=1):
    global x
    hits = [m for m in re.finditer(r"<hp:t>([^<]*)</hp:t>", x) if escape(old) in m.group(1)]
    assert len(hits) == n, (len(hits), old[:40])
    for m in reversed(hits):
        a, b = m.span(1); seg = x[a:b].replace(escape(old), escape(new)); x = x[:a] + seg + x[b:]
        endp = x.find("</hp:p>", a); ls = x.find("<hp:linesegarray", a)
        if 0 <= ls < endp:
            x = x[:ls] + x[x.find("</hp:linesegarray>", ls) + len("</hp:linesegarray>"):]
rep("다시 측정했다(2026-10-15).", "다시 측정했다(2026-10-15~16).")
rep("손이 닿지 않게 눌러도 늦게 오는 반응 미확인 (7절)",
    "손이 닿지 않게 눌러도 늦게 오는 반응 미확인, 분류기도 자극 창을 못 찾음 (7절, 표11)")
rep("세 상태 학습이 성립하지 않아 정확도를 낼 수 없었다",
    "정상·자극 두 상태로 줄여 학습했으나 모두 정상이라고 답한 경우(91.1·99.3 %)보다 낮았다 (표11)")
rep("손이 닿지 않게 갈래를 눌러 다시 잰 7절에서는 누르는 순간의 잡음만 보였고, 자극 뒤 늦게 오는 반응은 확인하지 못했다.",
    "손이 닿지 않게 다시 잰 7절에서는 꾹 누를 때만 순간의 잡음이 생기고 살짝 대면 아무 변화가 없었으며, 자극 뒤 늦게 오는 반응은 확인하지 못했다. 누른 시각으로 라벨을 붙여 학습한 분류기도 자극 창을 찾지 못했다(표11).")
rep("자극 반응이 손 접촉 신호에 가려져", "자극 반응이 손 접촉 신호와 자연 흔들림에 가려지거나 나타나지 않아")
rep("7절(1~2분에 50~130 mV)에서 손대지 않았는데 생긴 느린 기준선 변화는",
    "7절(1~2분에 50~130 mV, 밤샘 기록의 20 mV 넘는 계단 20번)에서 손대지 않았는데 생긴 기준선 변화는")
rep("· AD8232 기록은 그림만 남아 있어 다시 분석할 수 없다.",
    "· AD8232 기록은 그림만 남아 있어 다시 분석할 수 없다. 7절의 자극 실험은 식물 한 그루에서 자극 회차 2번만 했다.")
rep("자극 뒤 늦게 오는 반응은 확인하지 못했다. ■ 분류 결과를 채울 자리",
    "자극 뒤 늦게 오는 반응은 확인하지 못했다. 살짝 대기만 한 2회차에서는 아무 변화가 없었고, 손대지 않은 밤샘 12.3시간에도 같은 크기의 계단이 20번 생겼다. 누른 시각이 든 30초 창을 자극으로 라벨해 랜덤 포레스트·SVM을 회차를 나눠 평가했으나 자극 창을 60개 중 0~12개만 찾아, 모든 창을 정상이라고 답한 경우(정확도 91.1·99.3 %)보다 낫지 않았다.")

assert "■ 채울 자리" not in x and "■ 분류 결과" not in x
xml.dom.minidom.parseString(x.encode())
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        data = x.encode() if info.filename == "Contents/section0.xml" else zin.read(info.filename)
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = zipfile.ZIP_STORED if info.filename == "mimetype" else info.compress_type
        zi.external_attr = info.external_attr; zout.writestr(zi, data)
print("ok")
