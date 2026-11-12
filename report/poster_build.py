"""poster_build.py — 페스티벌 발표 포스터(양식 5-3 SW·AI)를 채운다 (2026-11-12).

양식 report/포스터양식_5-3_SWAI.hwpx 는 위에 제목·요약·출품자 칸, 아래에 두 단(글상자 두 개)이 있고
왼쪽 단 안에 Ⅰ~Ⅴ 절 머리띠가 줄지어 있다. 이 스크립트는
  · 제목·요약·출품자·지도교사·자문위원 글자를 바꾸고
  · 왼쪽 단 안의 머리띠를 비운 뒤, 두 단 위에 절 머리띠·본문 글상자·그림을 종이 기준 위치로 올린다.
배치는 여기서 계산한다(한글이 없어 결과를 볼 수 없으므로). 글 높이는 Noto Sans CJK 로 재어 넉넉히 잡고,
단 아래로 넘치면 실패로 멈춘다. 같은 배치로 미리보기 PNG 도 그린다(한글 화면과 글꼴·줄바꿈이 조금 다르다).

쓰는 법(저장소 루트): python3 report/poster_build.py  → report/GML_포스터.hwpx, report/GML_포스터_미리보기.png
본문 글자 크기만 header.xml 에 charPr 로 새로 더한다(양식에는 9~11pt 와 25pt 이상만 있다).
새 문단에는 줄 배치(linesegarray)를 넣지 않는다 — 한글이 열 때 다시 계산한다(0절: 줄 배치를 잘못 쓰면 한글이 깨진다).
"""
import os, re, sys, zipfile
from xml.dom import minidom
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REP = os.path.join(ROOT, "report")
SRC = os.path.join(REP, "포스터양식_5-3_SWAI.hwpx")
DST = os.path.join(REP, "GML_포스터.hwpx")
PREVIEW = os.path.join(REP, "GML_포스터_미리보기.png")

# ── 글자 모양(새로 더할 charPr). 글꼴 번호: 0 함초롬돋움, 2 HY헤드라인M ──
STYLES = {            # 이름: (높이 1/100pt, 색, 글꼴, 굵게)
    "body":  (1600, "#1A1A1A", 0, False),
    "sub":   (1900, "#905720", 2, False),
    "cap":   (1500, "#404040", 0, False),
    "ref":   (1300, "#404040", 0, False),
    "title": (4200, "#000000", 2, False),
    "sum":   (1600, "#1A1A1A", 0, False),
    "key":   (1500, "#905720", 0, True),
}
# 문단 모양(양식에 있는 것): 19 = 양쪽 150%·뒤 800, 10 = 양쪽 130%·내어쓰기, 12 = 왼쪽 160%·앞 1200 뒤 300, 20 = 가운데 160%
PARA = {"body": (19, 150, 0, 800), "bullet": (10, 130, 0, 500), "sub": (12, 160, 1200, 300), "cap": (20, 160, 0, 0)}

TITLE = "머신러닝 모델 기반의 식물 전기 신호 시각화 및 패턴 분석을 활용한 실시간 상태 분류 시스템 구현"
SUMMARY = ("라즈베리파이·16비트 ADC·전압 폴로어로 식물 전기신호 측정계와, 수집–학습–실시간 판정을 브라우저에서 하는 시스템을 만들었다. "
           "오차를 회로·전극·식물 순으로 나눠 실측한 결과, 측정을 제한한 것은 회로(30분 표류 −0.0003 mV)가 아니라 "
           "전극(60분 59.20 mV)과 바깥 전기 잡음이었고, 은선 전극(1시간 0.02 mV)과 패러데이 상자(60 Hz 약 27분의 1)·보조배터리 전원으로 줄였다. "
           "손 접촉 분류기의 높은 정확도는 식물의 반응이 아니라 손이 닿았는지를 가른 것이었고, 정상·수분부족 분류는 상태마다 기록이 하나뿐이라 판정을 보류했다.")
TEXT_FIX = {   # 양식의 자리 글자 → 바꿀 글자
    "OO학교 O학년 OOO, OOO, OOO, OOO": "영천고등학교 1학년 박선진·유도혁·이유찬·박소미",
    "000": "이민정",
    "OO대학교 OOO": "㈜에이포랩 김민재",
    "SW‧AI(초)": "SW‧AI(고)",
}

# ── 본문: 단마다 블록 목록. ("bar", 절 이름) ("sub", 글) ("p", 글) ("li", 글) ("fig", 파일, 가로 비율, 설명) ("ref", 글)
LEFT = [
    ("bar", "Ⅰ. 서론"),
    ("sub", "1. 연구의 필요성"),
    ("p", "식물은 신경이 없지만 상처·온도 변화 같은 자극을 받으면 세포막 전위가 바뀌고, 그 변화가 줄기를 따라 전달된다[3]. "
          "선행 연구는 식물 측정용 전극과 장비를 쓰고 "
          "접지한 금속 상자 안에서 쟀다[5][13]. 학생이 구할 수 있는 저가 부품으로 같은 측정을 할 때 무엇이 측정을 제한하는지는 직접 재 보아야 알 수 있다."),
    ("sub", "2. 연구 목적"),
    ("p", "식물의 전기신호로 정상·자극·수분부족 세 상태를 실시간 분류하는 시스템('식물 번역기')을 구현한다. "
          "초기 학습 데이터가 시뮬레이터 출력이었던 것을 알게 된 뒤, 분류에 앞서 측정값이 실제로 식물에서 온 것인지부터 단계별 실측으로 확인했다."),
    ("sub", "3. 연구 문제"),
    ("li", "· 연구문제 1. 저가 부품으로 만든 측정계가 식물 전기신호를 잴 만큼 정밀한가? 그렇지 않다면 어느 부분이 정밀도를 제한하는가?"),
    ("li", "· 연구문제 2. 그 측정계로 식물의 수분부족과 자극 반응을 정상 상태와 구분할 수 있는가?"),
    ("bar", "Ⅱ. 이론적 배경 및 선행 연구"),
    ("sub", "1. 식물의 전기신호"),
    ("p", "자극을 받은 식물 세포는 막전위가 잠시 무너졌다 돌아온다. 활동전위는 수십~100 mV로 일반 식물에서 수십 초 이어지고, "
          "손상으로 생기는 변동전위는 수 분, 화상에서는 최대 수십 분 이어진다[3]. 애기장대 잎을 붓으로 건드린 실험에서는 33.9 mV, "
          "약 10.7초의 활동전위가 접촉보다 늦게 도착했고, 접촉과 동시에 나타나는 변화는 전극이 밀려 생긴 잡음으로 구분했다[6]."),
    ("sub", "2. 신호의 시간 규모와 주파수"),
    ("p", "T초 동안 이어지는 신호의 주요 성분은 대략 1/T Hz 근처에 놓인다. 수십 초짜리 활동전위는 약 0.01–0.1 Hz, "
          "수분 스트레스는 0.0001 Hz 이하이므로, 0.5 Hz 고역통과가 있는 심전도용 증폭기(AD8232)로는 볼 수 없다(그림1)."),
    ("fig", "FIG_BAND.png", 0.70, "그림1. 식물 전기신호의 주파수 위치와 필터 통과대역"),
    ("sub", "3. 전극 표류와 바깥 전기 잡음"),
    ("p", "금속 전극이 전해질에 닿으면 반쪽전지 전위가 생기고, 두 전극의 차이가 시간에 따라 변하는 것이 전극 표류다[7]. "
          "느린 신호를 보려면 표류가 그보다 작아야 한다. 또 측정 입력은 전류를 거의 흘리지 않아 주변 전원선의 60 Hz 전기장이 섞이므로, "
          "선행 연구는 식물을 금속 망 상자(패러데이 상자) 안에 두고 쟀다[5][13]."),
    ("bar", "Ⅲ. 연구방법"),
    ("sub", "1. 측정 시스템"),
    ("p", "라즈베리파이 5, 16비트 ADC(ADS1115), 전압 폴로어(MCP6002)로 고역통과 필터가 없는 DC 결합 측정계를 만들었다. "
          "줄기에 꽂은 두 전극의 전압 차를 250 S/s로 기록하고, 10 kΩ 두 개로 만든 1.65 V를 흙에 꽂은 기준 전극에 걸었다(그림2). "
          "수집·학습·실시간 판정은 모두 브라우저에서 한다."),
    ("fig", "FIG_SYS.png", 0.70, "그림2. DC 결합 측정 시스템 구성"),
    ("sub", "2. 실험 설계"),
    ("li", "· 예비 실험 — 회로만(1단계), 회로+점퍼선 핀 전극(2단계), 회로+전극+식물(3단계) 순으로 하나씩 더해 오차의 출처를 재고, 손 접촉·누르기·상처 자극을 시험했다."),
    ("li", "· 본 실험 — 은선 전극으로 바꾸고, GND에 연결한 방충망 상자(60×60×100 cm) 안에 새 방울토마토만 넣었다(회로와 라즈베리파이는 상자 밖, 보조배터리 전원, 사진1)."),
    ("li", "· ① 은선 전극을 물에 담가 1시간 표류 ② 상자 밖·안, 콘센트·보조배터리 전원으로 120초씩 바깥 잡음 비교 ③ 물을 준 정상 기록 ④ 물을 끊은 지 3.6일째부터 수분부족 기록"),
    ("fig", "PHOTO4_CAGE_20261105.jpg", 0.82, "사진1. 패러데이 상자 — (가) 새 식물을 넣은 상자, (나) 상자 밖에 둔 회로와 라즈베리파이"),
]
RIGHT = [
    ("sub", "3. 분석 방법 (Ⅲ장 이어서)"),
    ("li", "· 표류(처음·마지막 30초 평균의 차), 잡음(0.01–1 Hz 대역만 남긴 신호의 표준편차), 60 Hz 상용전원 성분의 진폭으로 비교했다."),
    ("li", "· 차동값만으로는 기준 전압 결함이 드러나지 않아 각 채널을 따로 읽는 단극 점검을 했고, 높은 정확도가 나오면 문턱 하나짜리 가장 단순한 기준과 견주어 모델이 무엇을 가른 것인지 확인했다."),
    ("bar", "Ⅳ. 연구결과"),
    ("sub", "1. 측정을 제한한 것은 회로가 아니라 전극"),
    ("p", "회로만의 30분 표류는 −0.0003 mV로 ADC 한 칸보다 작았으나, 점퍼선 핀 전극을 물에 담그자 60분에 59.20 mV가 표류했다. "
          "은선 전극으로 바꾸자 1시간 표류가 +0.02 mV(약 3천분의 1), 0.01–1 Hz 잡음이 0.004 mV로 줄었다."),
    ("sub", "2. 손 접촉 신호와 접촉 감지 분류기"),
    ("p", "줄기와 잎을 손으로 만지자 닿는 순간 전압이 계단처럼 솟고 떼면 돌아왔다(67건, 약 70·320 mV). 문헌 활동전위(33.9 mV)의 약 2~9배이고 "
          "손이 닿아 있는 동안만 유지되어, 사람 몸의 전위가 더해진 것으로 해석했다(그림3). 접촉 감지 분류기(SVM)는 평가 창 251개를 모두 맞혔지만 "
          "문턱 하나로도 250개를 맞혀, 분류기가 가른 것은 식물의 반응이 아니라 손이 닿았는지였다."),
    ("fig", "FIG_TOUCH.png", 0.70, "그림3. 손 접촉 기록 — (가) 기록 전체, (나) 접촉 한 번 확대, (다) 계단 높이 67건"),
    ("sub", "3. 차폐와 전원에 따른 바깥 잡음"),
    ("p", "같은 식물·전극에서 60 Hz 상용전원 성분은 상자 밖·콘센트 전원 0.080 mV, 상자 안·콘센트 0.003 mV(약 27분의 1), "
          "상자 안·보조배터리 0.001~0.002 mV였다. 이후 기록은 모두 상자 안에서 보조배터리 전원으로 쟀다."),
    ("sub", "4. 새 식물의 정상·수분부족 기록"),
    ("p", "물을 끊은 지 3.6~4.2일째 밤 14.5시간 동안 기준선은 242 → 247 mV(시간당 약 0.3 mV), 0.01–1 Hz 잡음은 0.027 mV로 조용했다(그림4). "
          "정상 기록(물 준 지 약 4~10시간)은 잡음이 1.2 mV로 약 40배 컸는데, 잡음이 클 때는 늘 60 Hz 성분이 함께 커져 바깥 전기 기기에서 온 것으로 본다. "
          "두 기록의 기준선은 약 30 mV 달랐지만 상태마다 한 회차뿐이라 전극 변화와 구분할 수 없다."),
    ("fig", "FIG_NEWPLANT.png", 0.58, "그림4. 새 식물의 정상·수분부족 기록 — (가) 기준선, (나) 0.01–1 Hz 잡음, (다) 60 Hz 상용전원 성분"),
    ("sub", "5. 그럴듯한 숫자를 버린 경우"),
    ("p", "옛 식물의 상자 안 기록으로 학습한 정상·수분부족 분류기는 균형 정확도 96.9~99.9 %를 냈지만, 정상 기록이 두 전극이 같은 전위에 묶여 "
          "(−9 mV 고정) 식물을 재지 못한 기록으로 드러나 결과를 버렸다. 기준 전압 결함·채널 선택 오류도 단극 점검으로 찾아 고쳤다."),
    ("bar", "Ⅴ. 결론 및 제언"),
    ("sub", "1. 결론"),
    ("li", "· 연구문제 1 — 정밀도를 제한한 것은 회로가 아니라 전극과 주변 전기 잡음이었고, 둘 다 저가 부품(은선 전극, 방충망 상자, 보조배터리)으로 줄였다. "
           "다만 60 Hz 성분과 함께 잡음이 20~30배 커지는 구간이 남았고 원인은 찾지 못했다."),
    ("li", "· 연구문제 2 — 아직 구분하지 못했다. 손 접촉은 감지했지만 식물의 반응이 아니었고, 새 식물의 정상·수분부족은 한 회차씩이며 잡음 수준이 달라 분류기를 학습하지 않았다."),
    ("p", "시스템은 동작했지만, 무엇을 읽고 있는지 확인하지 않으면 동작하는 시스템도 '식물 번역기'가 아니다."),
    ("sub", "2. 의의와 제언"),
    ("li", "· 측정값의 출처를 의심하고 확인하는 절차(단극 점검, 문턱 하나 기준과 비교)를 남기고 코드·원자료를 공개했다[9]."),
    ("li", "· 상태마다 두 회차 이상을 같은 잡음 수준에서 기록하고, 화상(양성 대조)과 은선을 흙에만 꽂은 음성 대조를 더해 평가한다."),
    ("li", "· 자극 시각을 프로그램이 자동으로 기록하고, 하루 넘게 버티는 전원으로 긴 기록을 얻는다."),
    ("ref", "[3] Mudrilov et al. (2021). Int. J. Mol. Sci. 22(19), 10715.  [5] Volkov & Shtessel (2018). Bioelectrochemistry 124, 195–205.  "
            "[6] Degli Agosti (2014). Archives des Sciences 67, 125–138.  [7] Ademoglu. Bioelectrodes (Lecture Notes), Bogazici Univ.  "
            "[9] Green Mind Lab. GML_PLANT2. github.com/packsunjin/GML_PLANT2  [13] de Toledo et al. (2024). Plant Signal. Behav. 19(1), 2333144."),
]

# ── 배치(HWPUNIT, 1 pt = 100) ──
COLS = {"L": 8263, "R": 97071}
COL_W, COL_TOP, COL_BOT = 81921, 78285, 303356
PAD = 1300                   # 단 안쪽 여백
BAR_H, BAR_GAP, SEC_GAP, FIG_GAP = 4748, 800, 1400, 400
SAFE = 1.06                  # 글 높이 여유(한글과 글꼴 너비가 달라서)

FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
_fonts = {}
def font(style, scale):
    h, _, f, bold = STYLES[style]
    key = (style, scale)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FONT_B if (f == 2 or bold) else FONT_R, max(1, round(h * scale)), index=1)  # index 1 = KR
    return _fonts[key]

def wrap(text, style, width):
    """어절(띄어쓰기) 단위로 줄을 나눈다. 너비는 HWPUNIT."""
    sc = 0.05
    f = font(style, sc)
    lim = width * sc / SAFE
    lines, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w) if cur else w
        if f.getlength(t) <= lim:
            cur = t
            continue
        if cur:
            lines.append(cur)
        cur = w
        while f.getlength(cur) > lim:          # 한 어절이 줄보다 길면 글자 단위로 자른다
            k = len(cur)
            while k > 1 and f.getlength(cur[:k]) > lim:
                k -= 1
            lines.append(cur[:k]); cur = cur[k:]
    if cur:
        lines.append(cur)
    return lines

KIND = {"p": ("body", "body"), "li": ("body", "bullet"), "sub": ("sub", "sub"), "ref": ("ref", "body")}

def para_height(kind, text, width):
    style, pk = KIND[kind]
    _, pct, prev, nxt = PARA[pk]
    h = STYLES[style][0]
    n = len(wrap(text, style, width))
    return prev + n * h * pct / 100 + nxt, n

def layout(blocks, col):
    """블록을 위에서부터 쌓아 [(종류, x, y, w, h, 내용)] 을 돌려준다."""
    x0, y = COLS[col] + PAD, COL_TOP + PAD
    w = COL_W - 2 * PAD
    out, run = [], []
    def flush():
        nonlocal y, run
        if not run:
            return
        h = sum(para_height(k, t, w)[0] for k, t in run) * SAFE
        out.append(("text", x0, y, w, round(h), list(run)))
        y += round(h); run = []
    for b in blocks:
        if b[0] == "bar":
            flush()
            if out:
                y += SEC_GAP
            out.append(("bar", x0, y, w, BAR_H, b[1])); y += BAR_H + BAR_GAP
        elif b[0] == "fig":
            flush()
            _, name, frac, cap = b
            p = os.path.join(REP, name)
            wpx, hpx = Image.open(p).size
            fw = round(w * frac); fh = round(fw * hpx / wpx)
            y += FIG_GAP
            out.append(("pic", x0 + (w - fw) // 2, y, fw, fh, p)); y += fh + 300
            ch = round(para_height("p", cap, w)[1] * STYLES["cap"][0] * 1.6 * SAFE) + 300
            out.append(("text", x0, y, w, ch, [("cap", cap)])); y += ch + FIG_GAP
        else:
            run.append(b)
    flush()
    return out, y

# ── XML 조각 ──
_ids = [1990892000, 917150000, 60]
def next_ids():
    _ids[0] += 1; _ids[1] += 1; _ids[2] += 1
    return _ids[0], _ids[1], _ids[2]

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

CP = {}   # 이름 → charPr id (header 에 더한 뒤 채움)

def para_xml(kind, text):
    if kind == "cap":
        style, pk = "cap", "cap"
    else:
        style, pk = KIND[kind]
    ppr = PARA[pk][0]
    runs = []
    if kind == "cap":            # "그림1." 처럼 번호만 굵게(색으로 구분)
        m = re.match(r"^(\S+\.)(\s.*)$", text)
        if m:
            runs.append((CP["key"], m.group(1))); text = m.group(2)
    runs.append((CP[style], text))
    body = "".join(f'<hp:run charPrIDRef="{c}"><hp:t>{esc(t)}</hp:t></hp:run>' for c, t in runs)
    return f'<hp:p id="0" paraPrIDRef="{ppr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">{body}</hp:p>'

def placement(x, y, w, h):
    return (f'<hp:sz width="{w}" widthRelTo="ABSOLUTE" height="{h}" heightRelTo="ABSOLUTE" protect="0"/>'
            f'<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="0" allowOverlap="1" holdAnchorAndSO="0" '
            f'vertRelTo="PAPER" horzRelTo="PAPER" vertAlign="TOP" horzAlign="LEFT" vertOffset="{y}" horzOffset="{x}"/>'
            f'<hp:outMargin left="0" right="0" top="0" bottom="0"/>')

def geometry(w, h):
    return (f'<hp:offset x="0" y="0"/><hp:orgSz width="{w}" height="{h}"/><hp:curSz width="{w}" height="{h}"/>'
            f'<hp:flip horizontal="0" vertical="0"/><hp:rotationInfo angle="0" centerX="{w // 2}" centerY="{h // 2}" rotateimage="1"/>'
            '<hp:renderingInfo><hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
            '<hc:scaMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/><hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/></hp:renderingInfo>')

def textbox_xml(x, y, w, h, paras):
    rid, inst, z = next_ids()
    inner = "".join(para_xml(k, t) for k, t in paras)
    return (f'<hp:rect id="{rid}" zOrder="{z}" numberingType="PICTURE" textWrap="IN_FRONT_OF_TEXT" textFlow="BOTH_SIDES" lock="0" '
            f'dropcapstyle="None" href="" groupLevel="0" instid="{inst}" ratio="0">' + geometry(w, h) +
            '<hp:lineShape color="#000000" width="33" style="NONE" endCap="FLAT" headStyle="NORMAL" tailStyle="NORMAL" headfill="1" '
            'tailfill="1" headSz="SMALL_SMALL" tailSz="SMALL_SMALL" outlineStyle="NORMAL" alpha="0"/>'
            '<hp:shadow type="NONE" color="#B2B2B2" offsetX="0" offsetY="0" alpha="0"/>'
            f'<hp:drawText lastWidth="{w}" name="" editable="0"><hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" '
            'vertAlign="TOP" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
            f'{inner}</hp:subList><hp:textMargin left="0" right="0" top="0" bottom="0"/></hp:drawText>'
            f'<hc:pt0 x="0" y="0"/><hc:pt1 x="{w}" y="0"/><hc:pt2 x="{w}" y="{h}"/><hc:pt3 x="0" y="{h}"/>'
            + placement(x, y, w, h) + '<hp:shapeComment>사각형입니다.</hp:shapeComment></hp:rect>')

def bar_xml(tpl_bar, title, x, y):
    """양식의 절 머리띠(글자 안 든 줄 속 도형)를 종이 기준 위치로 옮긴 사본."""
    rid, inst, z = next_ids()
    s = re.sub(r'<hp:rect id="\d+" zOrder="\d+"', f'<hp:rect id="{rid}" zOrder="{z}"', tpl_bar, count=1)
    s = re.sub(r'instid="\d+"', f'instid="{inst}"', s, count=1)
    s = re.sub(r"<hp:t>[^<]*</hp:t>", f"<hp:t>{esc(title)}</hp:t>", s, count=1)
    s = re.sub(r'textWrap="\w+"', 'textWrap="IN_FRONT_OF_TEXT"', s, count=1)
    w, h = (int(v) for v in re.search(r'<hp:sz width="(\d+)"[^>]*height="(\d+)"', s).groups())
    s = re.sub(r"<hp:sz [^>]*/><hp:pos [^>]*/><hp:outMargin [^>]*/>", placement(x, y, w, h), s, count=1)
    return s

def pic_xml(tpl_pic, binid, path, x, y, w, h):
    rid, inst, z = next_ids()
    wpx, hpx = Image.open(path).size
    s = tpl_pic
    s = re.sub(r'<hp:pic id="\d+" zOrder="\d+"', f'<hp:pic id="{rid}" zOrder="{z}"', s, count=1)
    s = re.sub(r'textWrap="\w+"', 'textWrap="IN_FRONT_OF_TEXT"', s, count=1)
    s = re.sub(r'lock="\d"', 'lock="0"', s, count=1)
    s = re.sub(r'instid="\d+"', f'instid="{inst}"', s, count=1)
    s = re.sub(r"<hp:offset .*?</hp:renderingInfo>", geometry(w, h), s, count=1, flags=re.S)
    s = re.sub(r"<hp:imgRect>.*?</hp:imgRect>", f'<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="{w}" y="0"/><hc:pt2 x="{w}" y="{h}"/>'
               f'<hc:pt3 x="0" y="{h}"/></hp:imgRect>', s, count=1, flags=re.S)
    s = re.sub(r"<hp:imgClip [^>]*/>", f'<hp:imgClip left="0" right="{wpx * 75}" top="0" bottom="{hpx * 75}"/>', s, count=1)
    s = re.sub(r"<hp:imgDim [^>]*/>", f'<hp:imgDim dimwidth="{wpx * 75}" dimheight="{hpx * 75}"/>', s, count=1)
    s = re.sub(r'binaryItemIDRef="\w+"', f'binaryItemIDRef="{binid}"', s, count=1)
    s = re.sub(r"<hp:sz [^>]*/><hp:pos [^>]*/><hp:outMargin [^>]*/>", placement(x, y, w, h), s, count=1)
    s = re.sub(r"<hp:shapeComment>.*?</hp:shapeComment>",
               f"<hp:shapeComment>그림입니다. 원본 그림의 크기: 가로 {wpx}pixel, 세로 {hpx}pixel</hp:shapeComment>", s, count=1, flags=re.S)
    return s

def add_charprs(header):
    base_dotum = re.search(r'<hh:charPr id="6" .*?</hh:charPr>', header, re.S).group(0)
    n = int(re.search(r'<hh:charProperties itemCnt="(\d+)"', header).group(1))
    new = []
    for i, (name, (h, color, f, bold)) in enumerate(STYLES.items()):
        cid = n + i
        s = re.sub(r'id="6" height="\d+" textColor="[^"]+"', f'id="{cid}" height="{h}" textColor="{color}"', base_dotum, count=1)
        s = re.sub(r'<hh:fontRef [^>]*/>', f'<hh:fontRef hangul="{f}" latin="{f}" hanja="{f}" japanese="{f}" other="{f}" symbol="{f}" user="{f}"/>', s)
        if bold:
            s = s.replace("<hh:underline", "<hh:bold/><hh:underline", 1)
        new.append(s); CP[name] = cid
    i = header.index("</hh:charProperties>")
    header = header[:i] + "".join(new) + header[i:]
    return header.replace(f'<hh:charProperties itemCnt="{n}"', f'<hh:charProperties itemCnt="{n + len(STYLES)}"', 1)

def set_text(sec, old, new, charpr=None):
    m = [x for x in re.finditer(r"<hp:t>([^<]*)</hp:t>", sec) if x.group(1) == old]
    if len(m) != 1:
        sys.exit(f"[실패] '{old}' 자리 {len(m)}곳")
    m = m[0]
    p0 = sec.rfind("<hp:p ", 0, m.start()); p1 = sec.find("</hp:p>", m.end())
    para = sec[p0:p1].replace(m.group(0), f"<hp:t>{esc(new)}</hp:t>", 1)
    para = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", para, flags=re.S)
    if charpr is not None:
        para = re.sub(r'(<hp:run charPrIDRef=")\d+(">\s*<hp:t>)', rf"\g<1>{charpr}\2", para, count=1)
    return sec[:p0] + para + sec[p1:]

# ── 미리보기 ──
def preview(L, R, tpl_png):
    sc = 1870 / 187086
    W, H = 1870, round(311811 * sc)
    im = Image.open(tpl_png).convert("RGB").resize((W, H))
    d = ImageDraw.Draw(im)
    def X(v): return round(v * sc)
    # 양식의 자리 글자·머리띠 가리기(미리보기 그림에 박혀 있다)
    d.rectangle([X(COLS["L"]), X(COL_TOP), X(COLS["L"] + COL_W), X(COL_BOT)], fill="white")
    d.rectangle([X(COLS["R"]), X(COL_TOP), X(COLS["R"] + COL_W), X(COL_BOT)], fill="white")
    d.rectangle([X(39443), X(25546), X(39443 + 140200), X(25546 + 17400)], fill="white")
    d.rectangle([X(41000), X(51000), X(41000 + 142380), X(51000 + 13352)], fill="white")
    def para_draw(x, y, w, kind, text):
        if kind == "cap":
            style, pk = "cap", "cap"
        else:
            style, pk = KIND[kind]
        _, pct, prev, nxt = PARA[pk]
        h = STYLES[style][0]
        f = font(style, sc)
        y += prev
        col = STYLES[style][1]
        for ln in wrap(text, style, w):
            tx = x + (w - f.getlength(ln) / sc) / 2 if pk == "cap" else x
            d.text((X(tx), X(y)), ln, font=f, fill=col)
            y += h * pct / 100
        return y + nxt
    for items in (L, R):
        for kind, x, y, w, h, c in items:
            if kind == "bar":
                d.rounded_rectangle([X(x), X(y), X(x + w), X(y + h)], radius=X(h / 2), fill="#905720")
                d.text((X(x + 2800), X(y + 900)), c, font=ImageFont.truetype(FONT_B, X(2500), index=1), fill="white")
            elif kind == "pic":
                im.paste(Image.open(c).convert("RGB").resize((X(w), X(h))), (X(x), X(y)))
            else:
                yy = y
                for k, t in c:
                    yy = para_draw(x, yy, w, k, t)
                d.rectangle([X(x), X(y), X(x + w), X(y + h)], outline="#dddddd")
    # 제목·요약
    tf = font("title", sc)
    yy = 25546 + (17400 - 2 * 4200 * 1.6) / 2
    for ln in wrap(TITLE, "title", 140200 - 566):
        d.text((X(39443 + (140200 - tf.getlength(ln) / sc) / 2), X(yy)), ln, font=tf, fill="black"); yy += 4200 * 1.6
    yy = 51000
    for ln in wrap(SUMMARY, "sum", 142380 - 566):
        d.text((X(41300), X(yy)), ln, font=font("sum", sc), fill="black"); yy += 1600 * 1.6
    im.save(PREVIEW)

def main():
    zin = zipfile.ZipFile(SRC)
    sec = zin.read("Contents/section0.xml").decode("utf-8")
    header = zin.read("Contents/header.xml").decode("utf-8")
    hpf = zin.read("Contents/content.hpf").decode("utf-8")
    prv_png = zin.read("Preview/PrvImage.png")
    header = add_charprs(header)

    # 1) 왼쪽 단 안의 머리띠 문단을 비운다(오른쪽 단처럼 빈 문단 하나)
    lpos = sec.index('<hp:rect id="1990889987"')
    s0 = sec.index("<hp:subList", lpos)
    depth = 0                                    # 안쪽 머리띠 도형에도 subList 가 있으니 짝을 센다
    for m in re.finditer(r"<hp:subList|</hp:subList>", sec[s0:]):
        depth += 1 if m.group(0) == "<hp:subList" else -1
        if depth == 0:
            s1 = s0 + m.start(); break
    tpl_bar = re.search(r'<hp:rect id="1990890087".*?</hp:rect>', sec, re.S).group(0)
    rpos = sec.index('<hp:rect id="1990889989"')
    empty = re.search(r"(<hp:subList[^>]*>)(.*?)</hp:subList>", sec[rpos:], re.S).group(2)
    sec = sec[:sec.index(">", s0) + 1] + empty + sec[s1:]

    # 2) 제목·요약·출품자 글자
    sec = set_text(sec, "제목기입란", TITLE, CP["title"])
    sec = set_text(sec, "요약설명기입", SUMMARY, CP["sum"])
    for a, b in TEXT_FIX.items():
        sec = set_text(sec, a, b)

    # 3) 배치 계산
    L, yl = layout(LEFT, "L"); R, yr = layout(RIGHT, "R")
    for name, y in (("왼쪽", yl), ("오른쪽", yr)):
        room = COL_BOT - PAD - y
        print(f"{name} 단: 아래 남은 공간 {room} HWPUNIT ({room / 7200 * 2.54:.1f} cm)")
        if room < 0:
            sys.exit(f"[실패] {name} 단이 {-room} HWPUNIT 넘친다 — 글을 줄이거나 그림을 줄여라")

    # 4) 도형·그림 XML
    tpl_pic = re.search(r"<hp:pic .*?</hp:pic>", sec, re.S).group(0)
    n_img = max(int(x) for x in re.findall(r'id="image(\d+)"', hpf))
    shapes, bins = [], []
    for items in (L, R):
        for kind, x, y, w, h, c in items:
            if kind == "bar":
                shapes.append(bar_xml(tpl_bar, c, x, y))
            elif kind == "text":
                shapes.append(textbox_xml(x, y, w, h, c))
            else:
                n_img += 1
                ext = "png" if c.lower().endswith(".png") else "jpg"
                binid = f"image{n_img}"
                shapes.append(pic_xml(tpl_pic, binid, c, x, y, w, h))
                mt = "image/png" if ext == "png" else "image/jpeg"
                last = list(re.finditer(r'<opf:item id="image\d+"[^>]*/>', hpf))[-1]
                hpf = hpf[:last.end()] + f'<opf:item id="{binid}" href="BinData/{binid}.{ext}" media-type="{mt}" isEmbeded="1"/>' + hpf[last.end():]
                bins.append((f"BinData/{binid}.{ext}", c))
    # 오른쪽 단 상자 바로 뒤(같은 run 안)에 넣는다
    end_r = sec.index("</hp:rect>", sec.index('<hp:rect id="1990889989"')) + len("</hp:rect>")
    sec = sec[:end_r] + "".join(shapes) + sec[end_r:]

    for doc in (sec, header, hpf):
        minidom.parseString(doc.encode("utf-8"))
    infos = zin.infolist()
    last_bin = max(i for i, x in enumerate(infos) if x.filename.startswith("BinData/"))
    with zipfile.ZipFile(DST, "w") as zout:
        for i, info in enumerate(infos):
            data = {"Contents/section0.xml": sec.encode("utf-8"), "Contents/header.xml": header.encode("utf-8"),
                    "Contents/content.hpf": hpf.encode("utf-8")}.get(info.filename) or zin.read(info.filename)
            zout.writestr(info, data)
            if i == last_bin:
                for arc, p in bins:
                    zi = zipfile.ZipInfo(arc, date_time=info.date_time)
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zout.writestr(zi, open(p, "rb").read())
    z = zipfile.ZipFile(DST)
    first = z.infolist()[0]
    print("testzip:", z.testzip(), "| 첫 항목:", first.filename, "무압축" if first.compress_type == 0 else "압축(!)",
          "| 그림", len(bins), "| 글상자", sum(1 for s in shapes if s.startswith("<hp:rect")))
    tmp = os.path.join(os.path.dirname(PREVIEW), ".poster_tpl_preview.png")
    open(tmp, "wb").write(prv_png)
    preview(L, R, tmp); os.remove(tmp)
    print("→", DST, "\n→", PREVIEW)

if __name__ == "__main__":
    main()
