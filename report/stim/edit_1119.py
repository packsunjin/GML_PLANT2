"""edit_1119.py — 11-17 판(GML_결과보고서_20261117.hwpx)에 11-19 최종 본문(최종보고서_본문_20261119.md)을 넣는다.
그림 12개를 캡션 바로 위 문단에 넣는다(report/보고서_그림_순서대로/ 의 JPG). 줄 배치는 모두 지우고, 그림은 문단에 붙은 개체(위아래 자리차지·가운데)로 둔다.
쓰는 법(저장소 루트): python3 report/stim/edit_1119.py report/GML_결과보고서_20261117.hwpx report/최종보고서_본문_20261119.md report/GML_결과보고서_최종_20261119.hwpx
문단 번호는 20261117.hwpx 기준(hwpx_para.Doc.P).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from hwpx_para import Doc, Q

src, mdp, dst = sys.argv[1:4]
L = [l.rstrip("\n") for l in open(mdp, encoding="utf-8")]
def M(prefix):
    hit = [l for l in L if l.startswith(prefix)]
    assert len(hit) == 1, (prefix, len(hit))
    return hit[0]
d = Doc(src)
def lead(i):
    return re.match(r"^\s*", d.text(i)).group(0)
def S(i, prefix, keep_lead=True):
    d.set(i, (lead(i) if keep_lead else "") + M(prefix))
def C(i, text):
    d.set(i, text)

# 요약·Ⅰ·Ⅱ
S(75, "라즈베리파이 5, 16비트 ADC(ADS1115)"); S(77, "저가 부품으로 DC 결합 측정계와")
S(90, "연구를 진행하며 분류에 앞서")
d.replace_all("수분부족을 판단하는 기준", "물 공급 중단 상태를 판단하는 기준")
d.replace_all("수분부족처럼", "물 공급 중단처럼")
# Ⅲ
S(163, "측정 범위는 ADS1115의 PGA로 정하며")
C(192, M("사진1. 본 실험 장치")); C(195, M("사진2. 줄기 밑동")); 
S(199, "측정값의 오차는 회로, 전극, 식물")
C(207, "식물·은선 전극을 상자 밖·콘센트, 상자 안·콘센트, 상자 안·보조배터리 전원으로 120초씩 기록")
C(213, "물을 준 식물을 상자 안에서 손대지 않고 기록(5.9시간)")
C(218, "④ 손 접촉(전원별)")
C(219, "같은 식물·전극에서 보조배터리 전원 600초, 콘센트 전원 600초 기록. 30초마다 신호에 맞춰 잎을 2초씩 잡음")
C(220, "손 접촉 반응이 식물에서 오는지, 전기 경로에서 오는지")
C(222, "④의 콘센트 기록을 2초 창으로 잘라 특징 추출 모델 학습, 기록의 앞·뒤 절반으로 나눠 평가, 보조배터리 기록에 적용")
S(230, "· 단극 점검", False); S(232, "· 분석 범위와 특징 추출", False)
d.insert_after(232, 231, M("· 균형 정확도"))
# Ⅳ-1·2·3
S(240, "패러데이 상자 이전에 한 예비 실험의 결과를")
C(257, "계단 67건(약 70·320 mV), 손이 닿는 순간 생겨 닿아 있는 동안만 유지")
C(258, "전원을 바꿔 원인 확인(Ⅳ장 6절)")
C(273, M("그림3. (가) 예비 1단계")); C(275, M("그림3(가)의 세로축"))
cap_p4 = d.insert_after(275, 283, M("사진4. 수돗물에 담가"))
C(277, "2. 예비 실험의 손 접촉 계단"); S(278, "예비 3단계에서 점퍼선 핀 두 개를"); d.delete(279)
S(281, "은선 두 가닥을 1 cm 간격으로"); C(283, M("사진5. 물에 담가"))
# Ⅳ-4·5
S(285, "식물과 은선 전극을 그대로 두고"); S(286, "전극을 다시 세팅한 뒤의 120초"); S(287, "정리하면, 식물 기록의")
S(288, "화상 자극은 본 실험 이전에")
C(289, "5. 정상·물 공급 중단 기록"); S(290, "화분의 방울토마토 줄기 밑동에"); S(291, "두 기록의 차이는 기준선보다")
C(294, M("그림4. 날짜·시간대별"))
# Ⅳ-6 새로
C(296, "6. 전원별 손 접촉 실험과 손 접촉 감지 모델")
S(297, "예비 실험의 손 접촉 계단(Ⅳ장 2절)이")
ld = lead(297)
d.insert_after(297, 297, ld + M("보조배터리 전원에서는 잎을 10번"))
cap_f5 = d.insert_after(297, 294, M("그림5. 전원별 손 접촉"))
d.insert_after(297, 297, ld + M("콘센트 전원 기록으로 손 접촉 감지 모델을"))
cap_f6 = d.insert_after(297, 294, M("그림6. 손 접촉 감지 모델"))
d.insert_after(298, 290, ld + "측정 대상별 판정을 표5에 정리했다.")
# 표5 (행 순서: 측정 회로, 물 공급 중단, 자극 반응, 상용전원 잡음, 손 접촉)
C(309, "4.0~4.6일째 밤 14.5시간 기준선 243~247 mV로 평평. 정상 기록은 잡음이 약 47배 커서 같은 조건에서 비교하지 못함 (Ⅳ장 5절)")
C(312, "보조배터리 전원에서 잎을 10번 잡아도 대조와 같은 크기(+2.2~+5.1 mV), 늦게 도착하는 변화 없음 (Ⅳ장 6절). 예비 누르기·상처 뒤 늦은 반응 미확인, 화상 1회는 판정하지 않음 (표4, Ⅳ장 4절)")
C(314, "차폐 상자로 줄어듦")
C(317, "감지 가능(전기 경로)")
C(318, "콘센트 전원에서만 +138~+155 mV 계단, 감지 모델 균형 정확도 95.5~99.8 %, 보조배터리 기록에서는 0/80 (Ⅳ장 6절)")
# Ⅴ
S(323, "· 연구문제 1", False); S(324, "· 연구문제 2", False)
S(325, "처음 목표한 세 상태 분류는"); S(326, "연구 계획 단계의 가설"); S(327, "주제로 삼은 실시간 식물 상태")
C(339, "정상·물 공급 중단은 날마다 잡음 수준이 달라 비교 못 함, 자극 반응 확인 못 함 (표5)")
C(342, "예비 정상·자극: 자극 창 60개 중 0~12개 (표4). 손 접촉 감지: 균형 정확도 95.5~99.8 % (Ⅳ장 6절)")
C(345, "수집·변환·학습 화면과 실시간 판정 (그림7, 부록 1절)")
C(348, M("그림7. 실시간 판정 화면"))
S(351, "① 저가 측정계의 한계를"); S(352, "② 반응처럼 보이는 신호의")
S(357, "· 본 실험은 식물 한 그루에서", False)
d.insert_after(357, 357, M("· 손 접촉 실험은 같은 날"))
S(358, "· AD8232 기록은 그림만", False)
S(360, "① 자극 시각을 사람이"); S(361, "② 자극과 동시에 생긴"); S(363, "④ 전극을 꽂은 뒤")
# 부록
C(382, M("본 실험 회로와 조립 순서는"))
S(420, "웹 대시보드의 학습 기본값은")
C(424, M("· 같은 ADC를 두 프로그램이")); d.delete(425)
d.insert_after(426, 426, M("· 자극 실험은 전원을 기록해"))
# 그림: 있던 9개는 새 JPG 로 바꾸고, 3개(사진4·그림5·그림6)는 그림 문단을 복사해 캡션 바로 위에 넣는다(글자처럼 취급 그대로).
import copy, random
HC = "http://www.hancom.co.kr/hwpml/2011/core"
G = os.path.join(os.path.dirname(dst), "보고서_그림_순서대로")
F = {n[:2]: os.path.join(G, n) for n in os.listdir(G) if n.endswith(".jpg")}
def ref(i):
    return d.P[i].find(".//" + Q("pic")).find(".//{%s}img" % HC).get("binaryItemIDRef")
for i, k in ((143, "01"), (160, "02"), (191, "03"), (194, "04"), (196, "05"), (272, "06"), (282, "08"), (293, "09"), (347, "12")):
    assert d.P[i].find(".//" + Q("pic")) is not None
    old = [n for n in d.zin.namelist() if n.startswith("BinData/" + ref(i) + ".")][0]
    src_img = F[k]
    if old.upper().endswith(".PNG"):          # 파일 이름·형식을 맞춘다(PNG 자리에는 PNG)
        from PIL import Image
        src_img = os.path.join(os.path.dirname(dst), "_tmp_%s.png" % k); Image.open(F[k]).save(src_img)
    d.repic(ref(i), src_img)
d.new_bins = {}
def pic_before(cap, k, n):
    pp = copy.deepcopy(d.P[272]); pp.set("id", "0")
    pic = pp.find(".//" + Q("pic")); pic.set("id", str(random.randint(10**9, 2 * 10**9)))
    if pic.get("instid"): pic.set("instid", str(random.randint(10**8, 9 * 10**8)))
    r = "image%d" % n
    pic.find(".//{%s}img" % HC).set("binaryItemIDRef", r)
    cap.addprevious(pp)
    d.new_bins["BinData/%s.JPEG" % r] = (r, open(F[k], "rb").read(), "image/jpeg")
    from PIL import Image
    wpx, hpx = Image.open(F[k]).size
    w = int(pic.find(Q("sz")).get("width")); h = round(w * hpx / wpx)
    for tag in ("sz", "curSz", "orgSz"):
        e = pic.find(Q(tag))
        if e is not None: e.set("width", str(w)); e.set("height", str(h))
    for e in pic.iter("{%s}pt2" % HC): e.set("x", str(w)); e.set("y", str(h))
    for e in pic.iter("{%s}pt3" % HC): e.set("y", str(h))
    c = pic.find(Q("imgClip"))
    if c is not None: c.set("right", str(wpx * 75)); c.set("bottom", str(hpx * 75))
    for ls in pp.iter(Q("lineseg")):
        ls.set("vertsize", str(h)); ls.set("textheight", str(h)); ls.set("baseline", str(round(h * 0.85)))
pic_before(cap_p4, "07", 21); pic_before(cap_f5, "10", 22); pic_before(cap_f6, "11", 23)
# 줄 배치: 모두 지운다(한글이 다시 계산). 그림 문단의 세로 위치를 0 으로 두면 한글이 '새 쪽 맨 위'로 읽어
# 그림마다 쪽이 넘어간다(11-19 한글 31쪽 확인). 그래서 그림은 줄에 묶지 않고 문단에 붙은 개체(위아래 자리차지,
# 가운데)로 바꾼다 — 개체는 줄 배치 정보 없이도 한글이 자리를 잡는다.
for p in d.root.iter(Q("p")):
    for sa in p.findall(Q("linesegarray")):
        p.remove(sa)
# 표(개체) 바로 뒤 빈 문단 다음에 그림 문단이 오면 한글에서 표와 그림이 겹친다(11-19 표6·그림7 확인).
# 표 문단 바로 뒤에 그림 문단이 오는 사진1 은 안 겹쳤으므로, 그 사이 빈 문단을 지워 같은 모양으로 만든다.
top = [p for p in d.root if p.tag == Q("p")]
for k, p in enumerate(top):
    if p.find(".//" + Q("pic")) is not None and k >= 2:
        mid = top[k - 1]
        if top[k - 2].find(".//" + Q("tbl")) is not None and mid.find(".//" + Q("tbl")) is None \
                and not "".join(x.text or "" for x in mid.iter(Q("t"))).strip():
            d.root.remove(mid)
for pic in d.root.iter(Q("pic")):
    pic.set("textWrap", "TOP_AND_BOTTOM")
    pos = pic.find(Q("pos"))
    pos.set("treatAsChar", "0"); pos.set("flowWithText", "1"); pos.set("allowOverlap", "0")
    pos.set("vertRelTo", "PARA"); pos.set("vertAlign", "TOP"); pos.set("vertOffset", "0")
    pos.set("horzRelTo", "COLUMN"); pos.set("horzAlign", "CENTER"); pos.set("horzOffset", "0")
d.save(dst); print("saved", dst)
for n in os.listdir(os.path.dirname(dst)):
    if n.startswith("_tmp_") and n.endswith(".png"): os.remove(os.path.join(os.path.dirname(dst), n))
