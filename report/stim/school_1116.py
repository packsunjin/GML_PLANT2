"""2026-11-16 학교 양식 본문(report/학교양식_본문_20261116.txt)을 제출본.hwpx 서식에 넣어 새 hwpx 를 만든다.
쓰는 법(저장소 루트): python3 -I report/stim/school_1116.py report/GML_결과보고서_제출본.hwpx 결과.hwpx
- 문단은 글자 앞부분으로 찾는다(제출본에서 한 번만 나와야 함). 새 글은 txt 에서 앞부분으로 찾는다.
- 바꾼 문단은 첫 run 글자 모양을 쓰고 줄 배치(linesegarray)를 지운다(한글이 다시 계산). header.xml 은 그대로.
- 표 줄 지우기: rowCnt·rowAddr·표 높이를 함께 고친다."""
import sys, re, zipfile
from xml.sax.saxutils import escape, unescape
import xml.dom.minidom

src, dst = sys.argv[1], sys.argv[2]
TXT = "report/학교양식_본문_20261116.txt"
zin = zipfile.ZipFile(src)
x = zin.read("Contents/section0.xml").decode("utf-8")
ENT = {"&quot;": '"', "&apos;": "'"}
esc = lambda s: escape(s, {'"': "&quot;", "'": "&apos;"})
LEAF = r'<hp:p [^>]*>(?:(?!<hp:p ).)*?</hp:p>'

new_lines = [l for l in open(TXT, encoding="utf-8-sig").read().split("\n")
             if l.strip() and not l.startswith("■") and not re.match(r"\[(그림|사진)", l)]


def nl(prefix):
    hits = [l for l in new_lines if l.startswith(prefix)]
    assert len(hits) == 1, ("txt", prefix, len(hits))
    return hits[0]


def ptext(p):
    return unescape(re.sub(r"<[^>]+>", "", "".join(re.findall(r"<hp:t>(.*?)</hp:t>", p, re.S))), ENT)


def find(prefix, exact=False):
    ms = [m for m in re.finditer(LEAF, x, re.S)
          if (ptext(m.group(0)) == prefix if exact else ptext(m.group(0)).startswith(prefix))]
    assert len(ms) == 1, ("hwpx", prefix, len(ms))
    return ms[0]


def build(p, new):
    assert "<hp:pic" not in p and "<hp:tbl" not in p and "<hp:ctrl" not in p, p[:80]
    head = re.match(r"<hp:p [^>]*>", p).group(0)
    cp = re.search(r'<hp:run charPrIDRef="(\d+)"', p).group(1)
    return f'{head}<hp:run charPrIDRef="{cp}"><hp:t>{esc(new)}</hp:t></hp:run></hp:p>'


DONE = set()


def setp(old, new, exact=False):
    global x
    DONE.add(new)
    m = find(old, exact)
    x = x[:m.start()] + build(m.group(0), new) + x[m.end():]


def delp(old):
    global x
    m = find(old)
    x = x[:m.start()] + x[m.end():]


nid = [max(int(i) for i in re.findall(r'<hp:p id="(\d+)"', x)) + 1000]


def insert_after(anchor, model, new):
    """anchor 문단 뒤에 model 문단 모양으로 새 문단."""
    global x
    p = build(find(model).group(0), new)
    DONE.add(new)
    nid[0] += 1
    p = re.sub(r'^<hp:p id="\d+"', f'<hp:p id="{nid[0]}"', p)
    m = find(anchor)
    x = x[:m.end()] + p + x[m.end():]


def delrow(first_cell):
    """첫 칸 글자가 first_cell 인 표 줄을 지운다."""
    global x
    trs = [m for m in re.finditer(r"<hp:tr>.*?</hp:tr>", x, re.S)
           if ptext(re.search(r"<hp:tc .*?</hp:tc>", m.group(0), re.S).group(0)) == first_cell]
    assert len(trs) == 1, ("row", first_cell, len(trs))
    m = trs[0]; row = m.group(0)
    assert 'rowSpan="1"' in row and not re.search(r'rowSpan="[02-9]', row)
    h = int(re.search(r'<hp:cellSz width="\d+" height="(\d+)"', row).group(1))
    t0 = x.rfind("<hp:tbl ", 0, m.start())
    t1 = x.find("</hp:tbl>", m.end())
    tbl = x[t0:m.start()] + x[m.end():t1]
    n = int(re.search(r'rowCnt="(\d+)"', tbl).group(1))
    tbl = tbl.replace(f'rowCnt="{n}"', f'rowCnt="{n - 1}"', 1)
    sz = re.search(r'<hp:sz width="(\d+)" widthRelTo="ABSOLUTE" height="(\d+)"', tbl)
    tbl = tbl[:sz.start(2)] + str(int(sz.group(2)) - h) + tbl[sz.end(2):]
    k = [0]

    def renum(mt):
        r = mt.group(0)
        r = re.sub(r'rowAddr="\d+"', f'rowAddr="{k[0]}"', r); k[0] += 1
        return r
    tbl = re.sub(r"<hp:tr>.*?</hp:tr>", renum, tbl, flags=re.S)
    x = x[:t0] + tbl + x[t1:]


def cells(title):
    """txt 의 표(제목 다음 줄부터 빈 줄까지)를 {첫 칸: [칸들]} 로."""
    L = open(TXT, encoding="utf-8-sig").read().split("\n")
    i = L.index(title) + 1; out = {}
    while i < len(L) and "\t" in L[i]:
        c = L[i].split("\t"); out[c[0]] = c; i += 1
    return out


# ── 본문 문단: (제출본 앞부분, txt 앞부분)  None = 지움
P = [
    ("라즈베리파이 5 + 16비트", "라즈베리파이 5, 16비트"),
    ("저가 부품으로 DC 결합 측정계와", "저가 부품으로 DC 결합 측정계와"),
    ("선행 연구는 은/염화은", "선행 연구는 은/염화은"),
    ("본 연구의 목표는 식물의", "본 연구의 목표는 식물의"),
    ("연구를 진행하며 분류에 앞서", "연구를 진행하며 분류에 앞서"),
    ("식물 세포는 세포막을", "식물 세포는 세포막을"),
    ("예비 실험의 자극은 줄기를", "예비 실험의 자극은 줄기를"),
    ("금속이 전해질에 닿으면", "금속이 전해질에 닿으면"),
    ("표류는 활동전위 측정에도", "표류는 활동전위 측정에도"),
    ("4. 이전 측정계(AD8232)의 제약", "4. AD8232 측정계의 제약"),
    ("본 연구는 처음에 심전도용", "본 연구는 처음에 심전도용"),
    ("고역통과를 없앤 대가는", "고역통과를 없애면"),
    ("측정 회로의 입력은 전류를", "측정 회로의 입력은 전류를"),
    ("측정 범위는 ADS1115의 PGA로", "측정 범위는 ADS1115의 PGA로"),
    ("· 표류 — ", "· 표류 — "),
    ("· 잡음 — ", "· 잡음 — "),
    ("· 상용전원 성분 — ", "· 상용전원 성분 — "),
    ("· 단극 점검 — ", "· 단극 점검 — "),
    ("· 교차 확인 — ", "· 분석 구간 — "),
    ("수집·전처리·학습·실시간 화면(웹", "수집·전처리·학습·실시간 화면(웹"),
    ("패러데이 상자 이전에 한 예비", "패러데이 상자 이전에 한 예비"),
    ("그림3(가)의 세로축", "그림3(가)의 세로축"),
    ("처음 측정계는 심전도용", "처음 측정계는 심전도용"),
    ("이 계단으로 접촉 감지 분류기를", "이 계단은 식물의 반응이 아니라"),
    ("(2) 손 접촉 신호와 접촉 감지 분류기", "(2) 손 접촉 신호"),
    ("은선 두 가닥을 1 cm 간격으로", "은선 두 가닥을 1 cm 간격으로"),
    ("상자에 넣기 전의 비교 기준", None),
    ("옛 식물을 상자에 넣고 망을", None),
    ("차폐 효과는 새 식물과 은선", "새 식물과 은선 전극을 그대로"),
    ("화상 자극(표3 ⑤)은 옛 식물에서", "화상 자극(표3 ⑤)은 옛 식물에서"),
    ("새 방울토마토 화분의 줄기", "새 방울토마토 화분의 줄기"),
    ("두 기록의 차이는 기준선보다", "두 기록의 차이는 기준선보다"),
    ("물을 끊은 지 3.6~4.2일째인", "정상 기록(204~219 mV)과 수분부족"),
    ("옛 식물의 상자 안 기록으로 학습한", "새 식물의 정상·수분부족 기록으로는"),
    ("· 연구문제 1 — ", "· 연구문제 1 — "),
    ("· 연구문제 2 — ", "· 연구문제 2 — "),
    ("처음 목표한 세 상태 분류는", "처음 목표한 세 상태 분류는"),
    ("연구 계획 단계의 가설은", None),
    ("주제로 삼은 실시간 식물", "실시간 식물 상태 분류 시스템"),
    ("① 저가 측정계의 한계를", "① 저가 측정계의 한계를"),
    ("② 측정값의 출처를 의심하고", "② 높은 정확도를 그대로"),
    ("③ 코드·원자료·측정 출처", "③ 코드·원자료·측정 조건"),
    ("· 전극 표류는 수돗물에서", "· 전극 표류는 수돗물에서"),
    ("· 손대지 않았는데 생긴", "· 손대지 않았는데 생긴"),
    ("· 기준 전압 단극 측정, 식물", None),
    ("· AD8232 기록은 그림만", "· AD8232 기록은 그림만"),
    ("· 본 실험은 식물 한 그루에서", "· 본 실험은 식물 한 그루에서"),
    ("① 자극 시각을 사람이", "① 자극 시각을 사람이"),
    ("② 자극과 동시에 생긴", "② 자극과 동시에 생긴"),
    ("③ 마른 가지에 같은 자극", "③ 물 주기 전후를"),
    ("④ 전극을 꽂은 뒤 표류가", "④ 전극을 꽂은 뒤 표류가"),
    ("⑤ 칩을 250 SPS로", None),
    ("⑥ 물 주기 전후를", None),
    ("[12] Adafruit", None),
    ("[13] de Toledo", "[12] de Toledo"),
    ("전체 소스코드는 GitHub 저장소[9]에 공개되어 있다. frontend", "전체 소스코드는 GitHub 저장소[9]에 공개되어 있다. frontend"),
    ("배선은 표7과 같다.", "배선은 표8과 같다."),
    ("웹 대시보드의 학습 기본값은", "학습 설정은 다음과 같다."),
    ("· 측정 전에 단극으로 기준", "· 측정 전에 단극 점검"),
    ("· 기록값을 같은 순간의", "· 같은 ADC를 두 프로그램이"),
    ("· 기록 프로그램은 한 번에", "· 긴 측정 전에 120초"),
    ("· 측정 파일의 출처를 확인", "· 측정 중에는 선과 식물에"),
]
for old, new in P:
    if new is None:
        delp(old)
    else:
        setp(old, nl(new))

# Ⅳ장 절 머리(2절을 새로 넣어 한 칸씩 밀림)
for old, new in [("2. 은선 전극의 표류", "3. 은선 전극의 표류"), ("3. 차폐와 전원에 따른 바깥 잡음", "4. 차폐와 전원에 따른 바깥 잡음"),
                 ("4. 새 식물의 정상·수분부족 기록", "5. 새 식물의 정상·수분부족 기록"), ("5. 분류기", "6. 정상·수분부족 분류"),
                 ("6. 종합", "7. 종합")]:
    setp(old, nl(new), exact=True)

# Ⅲ장 2절: 제출본은 한 문단 → txt 두 문단을 이어 한 문단으로
setp("측정값의 오차는 회로, 전극, 식물, 주변 환경", nl("측정값의 오차는 회로") + " " + nl("본 실험은 이 둘을 줄이는"))

# Ⅴ장 5절 활용(부스) 넣기
insert_after(nl("④ 전극을 꽂은 뒤 표류가"), "4. 후속 연구 제언", "5. 활용 — 페스티벌 체험 부스")
insert_after("5. 활용 — 페스티벌 체험 부스", nl("④ 전극을 꽂은 뒤 표류가"), nl("이 시스템을 2026 창의융합"))

# ── 표
delrow("⓪ 상자 전 기록")
for r in ("초기 학습 데이터", "기준 전압 결함", "채널 선택 오류"):
    delrow(r)
T3, T4, T5, T6, T7 = (cells(t) for t in ("표3. 본 실험 설계", "표4. 예비 실험 요약 (2026-06~10, 금속 차폐 없음)",
                                         "표6. 측정 대상별 판정", "표7. 당초 세부 목표의 달성 여부", "표8. 측정 회로 배선표"))
setp("옛 식물에서, 달군 인두기의", T3["⑤ 화상 자극 (예비 관찰)"][1])
setp("0.5 Hz 고역통과가 활동전위 대역을 지움", T4["AD8232 (06-08)"][1])
setp("예비: 물을 끊지 않음.", T5["수분부족"][2])
setp("손 접촉 계단이 문헌 활동전위의", T5["자극 반응"][2])
setp("같은 식물·전극에서 60 Hz", T5["상용전원 잡음"][2])
setp("전압 계단으로 뚜렷이 보임", T5["손 접촉"][2])
setp("표본화는 DC 결합 측정계로", T6["① AD8232·ADS1115로 250 Hz 안정 획득"][2])
setp("예비: 수분부족 미측정", T6["② 스펙트로그램·특징으로 세 상태 분류"][2])
setp("정상·자극: 랜덤 포레스트", T6["③ 분류 정확도 70 % 이상"][2])
setp("브레드보드 GND", T7["패러데이 상자 망"][1], exact=True)

# ── 옛 식물 사진(사진1·2) 빼기: 그림 문단·제목 문단, BinData·content.hpf 항목
DROP_BIN = ("image11", "image7")
for b in DROP_BIN:
    ms = [m for m in re.finditer(LEAF, x, re.S) if f'binaryItemIDRef="{b}"' in m.group(0)]
    assert len(ms) == 1, b
    x = x[:ms[0].start()] + x[ms[0].end():]
delp("사진1. 실험 장치 전체")
delp("사진2. 원줄기에 꽂은 전극과 선 고정")


# ── Ⅳ장 2절 손 접촉 감지 분류기 개발 넣기
def outer_tbl_para(first_cells):
    """첫 줄 칸 글자가 first_cells 인 표를 품은 문단(시작, 끝)."""
    for m in re.finditer(r"<hp:tbl ", x):
        tr = re.search(r"<hp:tr>.*?</hp:tr>", x[m.start():], re.S).group(0)
        cs = [ptext(c) for c in re.findall(r"<hp:tc .*?</hp:tc>", tr, re.S)]
        if cs == list(first_cells):
            a = x.rfind("<hp:p ", 0, m.start())
            e = x.find("</hp:tbl>", m.start())
            return a, x.find("</hp:p>", e) + len("</hp:p>")
    raise AssertionError(first_cells)


def cell_set(tc, text, width):
    sub = re.search(r"<hp:subList [^>]*>(.*)</hp:subList>", tc, re.S)
    p0 = re.search(r"<hp:p .*?</hp:p>", sub.group(1), re.S).group(0)
    nid[0] += 1
    np_ = re.sub(r'^<hp:p id="\d+"', f'<hp:p id="{nid[0]}"', build(p0, text))
    tc = tc[:sub.start(1)] + np_ + tc[sub.end(1):]
    return re.sub(r'<hp:cellSz width="\d+"', f'<hp:cellSz width="{width}"', tc)


def make_table(model_cells, rows, widths):
    a, e = outer_tbl_para(model_cells)
    para = x[a:e]
    trs = re.findall(r"<hp:tr>.*?</hp:tr>", para, re.S)
    out, total = [], 0
    for r, cs in enumerate(rows):
        tpl = trs[0] if r == 0 else trs[1]
        tcs = re.findall(r"<hp:tc .*?</hp:tc>", tpl, re.S)
        new = [cell_set(tc, c, w) for tc, c, w in zip(tcs, cs, widths)]
        tr = "<hp:tr>" + "".join(new) + "</hp:tr>"
        out.append(re.sub(r'rowAddr="\d+"', f'rowAddr="{r}"', tr))
        total += int(re.search(r'<hp:cellSz width="\d+" height="(\d+)"', tpl).group(1))
    s0 = para.find(trs[0]); s1 = para.rfind("</hp:tr>") + len("</hp:tr>")
    para = para[:s0] + "".join(out) + para[s1:]
    para = re.sub(r'rowCnt="\d+"', f'rowCnt="{len(rows)}"', para, count=1)
    para = re.sub(r'(<hp:tbl id=")\d+', lambda m: m.group(1) + "1900000077", para, count=1)
    para = re.sub(r'(<hp:tbl .*?<hp:sz width="\d+" widthRelTo="ABSOLUTE" height=")\d+', lambda m: m.group(1) + str(total), para, count=1, flags=re.S)
    para = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", para, flags=re.S)
    nid[0] += 1
    return re.sub(r'^<hp:p id="\d+"', f'<hp:p id="{nid[0]}"', para)


def caption_like(model, num, rest):
    p = find(model).group(0)
    head = re.match(r"<hp:p [^>]*>", p).group(0)
    c1, c2 = re.findall(r'<hp:run charPrIDRef="(\d+)"', p)[:2]
    nid[0] += 1
    head = re.sub(r'id="\d+"', f'id="{nid[0]}"', head, count=1)
    DONE.add(num + rest)
    return (f'{head}<hp:run charPrIDRef="{c1}"><hp:t>{esc(num)}</hp:t></hp:run>'
            f'<hp:run charPrIDRef="{c2}"><hp:t>{esc(rest)}</hp:t></hp:run></hp:p>')


def plain_like(model, text):
    nid[0] += 1
    DONE.add(text)
    return re.sub(r'^<hp:p id="\d+"', f'<hp:p id="{nid[0]}"', build(find(model).group(0), text))


L = open(TXT, encoding="utf-8-sig").read().split("\n")
i0 = L.index("2. 손 접촉 감지 분류기 개발"); i1 = L.index("3. 은선 전극의 표류")
H_SEC, H_SUB, BODY = "1. 예비 실험 요약", "(1) AD8232로 시작한 측정", nl("처음 측정계는 심전도용")
CAP = "표4. 예비 실험 요약"
T5N = cells("표5. 손 접촉 감지 분류기의 평가 결과 (평가 창 251개: 접촉 23개, 비접촉 228개)")
parts, i = [], i0
while i < i1:
    l = L[i]
    if not l.strip():
        i += 1; continue
    if l.startswith("표5. "):
        parts.append(caption_like(CAP, "표5.", " " + l[4:]))
        rows = []; i += 1
        while "\t" in L[i]:
            rows.append(L[i].split("\t")); i += 1
        parts.append(make_table(("대상", "판정", "근거"), rows, (9000, 12600, 26020)))
        for r in rows:
            DONE.update(r)
        continue
    model = H_SEC if re.match(r"\d\. ", l) else H_SUB if re.match(r"\(\d\) ", l) else BODY
    parts.append(plain_like(model, l)); i += 1
m = find("그림4. 손 접촉 기록")  # 그림4 제목 뒤 → 그 다음 문단(이 계단은 …) 뒤에 넣는다
m = find(nl("이 계단은 식물의 반응이 아니라"))
x = x[:m.end()] + "".join(parts) + x[m.end():]


# ── 번호 밀기(표5→6…, 사진3→1…, Ⅳ장 n절) — 새 글로 바꾸지 않은 문단만
def renum(s):
    s = re.sub(r"표([5-7])", lambda m: "표\x00" + str(int(m.group(1)) + 1), s)
    s = re.sub(r"사진([3-5])", lambda m: "사진\x00" + str(int(m.group(1)) - 2), s)
    s = re.sub(r"Ⅳ장 ([2-6])(·([2-6]))?절",
               lambda m: "Ⅳ장 \x00" + str(int(m.group(1)) + 1) + ("·" + str(int(m.group(3)) + 1) if m.group(2) else "") + "절", s)
    return s.replace("\x00", "")


def renum_para(m):
    p = m.group(0)
    if ptext(p) in DONE or "<hp:t>" not in p:
        return p
    return re.sub(r"<hp:t>(.*?)</hp:t>", lambda t: "<hp:t>" + renum(t.group(1)) + "</hp:t>", p, flags=re.S)


x = re.sub(LEAF, renum_para, x, flags=re.S)

# 참고문헌 번호 [13] → [12] (본문 인용)
x = x.replace("[13]", "[12]")
assert "[13]" not in x and "Adafruit" not in x

# 남으면 안 되는 말
for bad in ("−9", "96.9", "시뮬레이터", "커패시터", "채널 선택", "Adafruit"):
    left = [ptext(m.group(0))[:50] for m in re.finditer(LEAF, x, re.S) if bad in ptext(m.group(0))]
    print(f"남은 '{bad}':", left)

xml.dom.minidom.parseString(x.encode("utf-8"))
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        if any(info.filename.startswith(f"BinData/{b}.") for b in DROP_BIN):
            continue
        data = x.encode("utf-8") if info.filename == "Contents/section0.xml" else zin.read(info.filename)
        if info.filename == "Contents/content.hpf":
            hpf = data.decode("utf-8")
            for b in DROP_BIN:
                hpf = re.sub(rf'<opf:item id="{b}" [^>]*/>', "", hpf)
            data = hpf.encode("utf-8")
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = zipfile.ZIP_STORED if info.filename == "mimetype" else info.compress_type
        zi.external_attr = info.external_attr
        zout.writestr(zi, data)
z = zipfile.ZipFile(dst)
print("testzip:", z.testzip(), "| 첫 항목:", z.infolist()[0].filename, z.infolist()[0].compress_type,
      "| hp:pic:", z.read("Contents/section0.xml").decode().count("<hp:pic"))
