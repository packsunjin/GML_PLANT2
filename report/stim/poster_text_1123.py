"""poster_text_1123.py — 발표 포스터를 글자로(2026-11-23, 사용자 "글자 ㄱㄱ"). poster_1119.py 는 절마다 그림 한 장이었다.
글은 양식 글자 모양만 쓴다: 본문 charPr 7(함초롬바탕), 강조 charPr 11(갈색 헤드라인), 결과 소제목 charPr 12. 본문 크기는 BODY_PT.
그림·사진은 가운데(paraPr 20) 글자처럼 취급, 캡션도 가운데. 줄 배치 정보는 넣지 않는다(한글이 계산).
쓰는 법(저장소 루트): python3 report/stim/poster_text_1123.py report/포스터양식_5-3_SWAI.hwpx report/발표포스터_20261123.hwpx
"""
import sys, os, re, copy, random, zipfile
from lxml import etree
from PIL import Image

src, dst = sys.argv[1:3]
G = os.path.join(os.path.dirname(dst), "보고서_그림_순서대로")
F = {n[:2]: os.path.join(G, n) for n in os.listdir(G) if n.endswith(".jpg")}
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"; HC = "http://www.hancom.co.kr/hwpml/2011/core"
Q = lambda t: "{%s}%s" % (HP, t)
zin = zipfile.ZipFile(src)
root = etree.fromstring(zin.read("Contents/section0.xml"))
hdr = zin.read("Contents/header.xml").decode("utf-8")
hpf = zin.read("Contents/content.hpf").decode("utf-8")

def txt(e): return "".join(x.text or "" for x in e.iter(Q("t")))
def set_text(rect_text, new):
    for rc in root.iter(Q("rect")):
        sl = rc.find(".//" + Q("subList"))
        if sl is not None and txt(sl).strip() == rect_text:
            ts = [t for t in sl.iter(Q("t"))]
            ts[0].text = new
            for t in ts[1:]: t.text = ""
            for sa in sl.iter(Q("linesegarray")): sa.getparent().remove(sa)
            return
    raise KeyError(rect_text)

# ── 머리말 칸 ──
set_text("제목기입란", "머신러닝 모델 기반의 식물 전기 신호 시각화 및 패턴 분석을 활용한 실시간 상태 분류 시스템 구현")
set_text("요약설명기입", "저가 측정계로 방울토마토의 전기신호를 재며 잡음의 출처를 하나씩 가렸고, 손 접촉 신호가 식물이 아니라 사람 몸과 전원 사이의 전기 경로에서 온다는 것을 밝혔다.")
set_text("OO학교 O학년 OOO, OOO, OOO, OOO", "영천고등학교 1학년 박선진, 유도혁, 이유찬, 박소미")
set_text("000", "이민정")
set_text("OO대학교 OOO", "㈜에이포랩 김민재")
# 제목 글자: 68pt 로는 세 줄이 넘어 칸을 벗어난다 → 양식의 제목 글자 모양(charPr 9) 크기만 40pt 로
hdr = re.sub(r'(<hh:charPr id="9" height=")\d+(")', r"\g<1>4000\2", hdr, count=1)

# ── 본문 칸 ──
cols = [rc for rc in root.iter(Q("rect")) if rc.find(Q("sz")).get("height") == "225071"]
left, right = sorted(cols, key=lambda r: int(r.find(Q("pos")).get("horzOffset")))
lsl, rsl = left.find(".//" + Q("subList")), right.find(".//" + Q("subList"))
bars = [p for p in lsl.findall(Q("p"))]                       # 막대 문단 5개
assert len(bars) == 5 and "Ⅰ" in txt(bars[0]) and "Ⅴ" in txt(bars[4])
for p in list(rsl): rsl.remove(p)                             # 오른쪽 칸 빈 문단
for b in bars[4:]: lsl.remove(b); rsl.append(b)               # Ⅴ 만 오른쪽(Ⅳ 는 왼쪽 아래 결과 1 → 오른쪽 위 결과 2~4)
for b in bars:                                                # 막대 문단: 줄 배치 지우고 빈칸 한 글자
    for sa in b.findall(Q("linesegarray")): b.remove(sa)
    last_t = b.findall(Q("run"))[-1].findall(Q("t"))[-1]; last_t.text = " "

PIC = etree.fromstring(zipfile.ZipFile(os.path.join(os.path.dirname(dst), "GML_결과보고서_최종_20261119.hwpx"))
                       .read("Contents/section0.xml")).find(".//" + Q("pic"))
new_bins = []
def para(text, ppr="0", cpr="7"):
    p = etree.Element(Q("p"), id="0", paraPrIDRef=ppr, styleIDRef="0", pageBreak="0", columnBreak="0", merged="0")
    r = etree.SubElement(p, Q("run"), charPrIDRef=cpr); t = etree.SubElement(r, Q("t")); t.text = text
    return p
def pic_para(key, width):
    n = len(new_bins) + 2; ref = "image%d" % n
    pic = copy.deepcopy(PIC); pic.set("id", str(random.randint(10**9, 2 * 10**9))); pic.set("instid", str(random.randint(10**8, 9 * 10**8)))
    pic.find(".//{%s}img" % HC).set("binaryItemIDRef", ref)
    wpx, hpx = Image.open(F[key]).size; h = round(width * hpx / wpx)
    for tg in ("sz", "curSz", "orgSz"):
        e = pic.find(Q(tg)); e.set("width", str(width)); e.set("height", str(h))
    for e in pic.iter("{%s}pt1" % HC): e.set("x", str(width))
    for e in pic.iter("{%s}pt2" % HC): e.set("x", str(width)); e.set("y", str(h))
    for e in pic.iter("{%s}pt3" % HC): e.set("y", str(h))
    pic.find(Q("imgClip")).attrib.update({"left": "0", "top": "0", "right": str(wpx * 75), "bottom": str(hpx * 75)})
    pic.find(Q("imgDim")).attrib.update({"dimwidth": str(wpx * 75), "dimheight": str(hpx * 75)})
    sc = pic.find(Q("shapeComment"))
    if sc is not None: sc.text = "그림입니다."
    pos = pic.find(Q("pos")); pos.set("treatAsChar", "1")
    p = para(" ", "20"); r = p.find(Q("run")); r.insert(0, pic)
    new_bins.append(("BinData/%s.jpg" % ref, ref, open(F[key], "rb").read()))
    return p

W = 74000   # 칸 안쪽 폭(칸 81921 − 여백)
import os as _os
BODY_PT = float(_os.environ.get("BODY_PT", "19"))
hdr = re.sub(r'(<hh:charPr id="7" height=")\d+(")', r"\g<1>%d\2" % round(BODY_PT * 100), hdr, count=1)
PF = os.path.join(os.path.dirname(dst), "poster_fig")
for n in os.listdir(PF):
    if n.endswith(".jpg"): F[n[:-4]] = os.path.join(PF, n)

def P(*runs, ppr=None):
    """runs: 문자열이면 본문, (글, 글자모양) 이면 그 모양. 문단 모양은 기본 paraPr 10(줄 간격 130 %, 내어쓰기)."""
    ppr = ppr or "10"
    p = etree.Element(Q("p"), id="0", paraPrIDRef=ppr, styleIDRef="0", pageBreak="0", columnBreak="0", merged="0")
    for r in runs:
        text, cpr = (r, "7") if isinstance(r, str) else r
        run = etree.SubElement(p, Q("run"), charPrIDRef=cpr); t = etree.SubElement(run, Q("t")); t.text = text
    return p
B = lambda s: (s, "11")          # 갈색 강조
H = lambda s: (s, "12")          # 결과 소제목
def FIG(key, cap, pct=100):
    return [pic_para(key, round(W * pct / 100)), P(*cap, ppr="20") if isinstance(cap, tuple) else P(B(cap.split(" ", 1)[0] + " "), cap.split(" ", 1)[1], ppr="20")]
BL = lambda: P(" ")

SEC = {
 0: [P("식물은 자극을 받으면 세포막 전위가 바뀌고, 이 변화가 줄기를 따라 전달된다. 이 전기신호로 식물의 상태를 실시간으로 알아내는 '식물 번역기'를 만들고자 했다."),
     P(B("목표  "), "전기신호로 정상 · 자극 · 수분부족 실시간 분류"),
     P(B("연구문제 1  "), "저가 부품 측정계가 식물 전기신호를 잴 만큼 정밀한가?"),
     P(B("연구문제 2  "), "수분부족과 자극 반응을 정상 상태와 구분할 수 있는가?"), BL()],
 1: [P(B("활동전위  "), "수십 mV · 수십 초"),
     P(B("붓 접촉 반응  "), "33.9 mV, 접촉 뒤 늦게 도착 (Degli Agosti, 2014)"),
     P(B("수분 스트레스  "), "수 시간 이상 걸리는 느린 변화"),
     P(B("선행 연구 측정  "), "1 cm 간격 전극 + 접지한 금속 상자 (de Toledo 외, 2024)"),
     *FIG("01", "그림1. 식물 전기신호의 주파수 위치와 분석 범위", 60), BL()],
 2: [*FIG("02", "그림2. 측정 시스템 구성 — 두 전극의 전위 차이를 재는 DC 결합 측정계", 85),
     *FIG("P_사진_장치_회로", (B("사진1. "), "실험 장치 (가) 패러데이 상자, (나) 상자 밖 회로   ", B("사진2. "), "측정 회로의 배선"), 80),
     P(B("측정 (길이, 본 것)")),
     P("· 회로만(예비 1단계): 30분, 회로 표류"),
     P("· 점퍼선 핀 전극, 물속(예비 2단계): 60분, 전극 표류"),
     P("· 은선 전극, 물속(점퍼선 핀과 같은 조건): 2시간, 전극 표류"),
     P("· 차폐 상자 · 전원 3가지: 120초씩, 60 Hz · 0.01–1 Hz 잡음"),
     P("· 정상(물 준 뒤): 5.9시간, 기준선 · 잡음"),
     P("· 물 공급 중단 4.0~4.6일째: 14.5시간, 기준선 · 잡음"),
     P("· 손 접촉(콘센트 · 보조배터리): 600초씩, 잡은 뒤 10초 변화 · 감지 모델"),
     P(B("분석  "), "250 S/s 기록, 잡음 = 대역 표준편차, 60 Hz = 푸리에 진폭, 모델 = 2초 조각 → 특징 17개 → SVM · 랜덤 포레스트, 균형 정확도로 평가"), BL()],
 3: [P(H("1. 잡음은 회로가 아니라 전극과 전원선에서")),
     P(B("59.2 · 82.9 mV  "), "전극 60분 표류(점퍼선 핀 · 은선)"),
     P(B("1/27  "), "60 Hz 잡음(상자 밖 → 차폐 상자 안)"),
     *FIG("06", "그림3. 회로 영점과 전극 표류", 60),
     *FIG("P_차폐전원_잡음", "그림4. 차폐 상자 · 전원별 잡음 (120초 기록)", 58)],
}
RIGHT = [P(H("2. 정상 · 물 공급 중단: 비교하지 못함")),
     P("같은 화분 · 전극의 긴 기록 다섯 개를 처음 5.9시간씩 비교하면 잡음이 기준 아래인 기록은 ", B("하나뿐"), "이었다(나머지 넷은 ", B("22~56배"), "). 정상 · 물 공급 중단 어느 쪽에도 잡음이 큰 기록이 있어 같은 조건에서 비교할 수 없었다."),
     *FIG("09", "그림5. 긴 기록 다섯 개의 잡음 (처음 5.9시간, 2분마다)", 58), BL(),
     P(H("3. 손 접촉 감지 모델")),
     P("손이 잎에 닿을 때 생기는 전압 계단으로 손 접촉 감지 모델을 만들었다(콘센트 전원 기록)."),
     P(B("전압 기록 → 2초씩 자르기 → 특징 17개 → SVM · 랜덤 포레스트 → 접촉 / 비접촉"), ppr="20"),
     *FIG("P_스펙트로그램", "그림6. 손 접촉 기록의 전압과 스펙트로그램 (노란 띠 · 점선 = 잎을 잡은 시각)", 54),
     P(B("손 접촉 반응 분류 정확도 "), "(균형 정확도, 앞 · 뒤 절반을 바꿔 2회 평가, 두 방식 모두 잎을 잡은 9번을 찾음)"),
     P("· 특징 추출(17개): SVM ", B("99.8 · 95.5 %"), ", 랜덤 포레스트 ", B("98.7 · 95.5 %")),
     P("· 스펙트로그램(65 × 31): SVM 97.4 · 90.8 %, 랜덤 포레스트 98.6 · 91.6 %"),
     BL(),
     P(H("4. 정말 식물 신호일까? 전원을 바꿔 확인")),
     P("식물 · 전극은 그대로 두고 전원만 보조배터리로 바꿔 봤다. 손 대신 비전도성 물체로 살짝 댄 기록도 같이 봤다."),
     P("· 콘센트, 잎을 잡음: ", B("9 / 9"), " 약 140 mV 계단"),
     P("· 콘센트, 비전도성 물체: ", B("0 / 10"), " 변화 없음"),
     P("· 보조배터리, 잎을 잡음: ", B("0 / 10"), " 변화 없음"),
     P("· 보조배터리, 모델이 찾은 접촉: ", B("0 / 80")),
     *FIG("P_전원별_겹쳐보기", "그림7. 잡은 · 댄 시각 기준으로 겹쳐 본 전압 (검은 선 = 중앙값)", 68),
     *FIG("P_모델판정_전원별", "그림8. 같은 모델(특징 추출)의 판정 (가) 콘센트, (나) 보조배터리", 44),
     P("스펙트로그램 SVM은 잡음 수준이 다른 보조배터리 기록 전체를 '접촉'으로 판정했다(랜덤 포레스트는 0 / 80)."),
     P("손 접촉 계단은 식물 반응이 아니라 ", B("사람 몸과 콘센트 전원 사이의 전기 경로"), "였다. 정확도가 높아도 무엇을 감지하는지는 대조 실험으로 확인해야 한다."), BL()]
CONC = [P("· 측정을 제한하는 것은 회로가 아니라 ", B("전극 표류와 바깥 전기 잡음"), "이다. 바깥 잡음은 차폐 상자로 줄였지만 전극 표류는 은선으로도 줄지 않았다."),
        P("· 손 접촉 신호는 식물이 아니라 ", B("전기 경로"), "에서 왔다. 정확도가 높아도 무엇을 감지하는지는 ", B("대조 실험"), "으로 확인해야 한다."),
        P("· 제언: 자극 시각 자동 기록, 흙만 재는 음성 대조 · 화상 양성 대조, 상태마다 두 회차 이상 기록")]
for k, els in SEC.items():
    at = bars[k]
    for e in els: at.addnext(e); at = e
for e in RIGHT: bars[4].addprevious(e)
at = bars[4]
for e in CONC: at.addnext(e); at = e

for n, ref, _ in new_bins:
    hpf = hpf.replace("</opf:manifest>", f'<opf:item id="{ref}" href="{n}" media-type="image/jpeg" isEmbeded="1"/></opf:manifest>')
xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
with zipfile.ZipFile(dst, "w") as z:
    for it in zin.infolist():
        data = {"Contents/section0.xml": xml, "Contents/header.xml": hdr.encode("utf-8"),
                "Contents/content.hpf": hpf.encode("utf-8")}.get(it.filename) or zin.read(it.filename)
        z.writestr(it.filename, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
    for n, _, b in new_bins:
        z.writestr(n, b, compress_type=zipfile.ZIP_DEFLATED)
print("saved", dst, len(new_bins), "images", "body", BODY_PT, "pt")
