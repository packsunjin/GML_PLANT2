"""edit_1119.py — 11-17 판(GML_결과보고서_20261117.hwpx)에 11-19 최종 본문(최종보고서_본문_20261119.md)을 넣는다.
그림 12개를 캡션 바로 위 문단에 넣는다(report/보고서_그림_순서대로/ 의 JPG). 줄 배치는 모두 지우고, 그림은 문단에 붙은 개체(위아래 자리차지·가운데)로 둔다.
쓰는 법(저장소 루트): python3 report/stim/edit_1119.py report/GML_결과보고서_20261117.hwpx report/최종보고서_본문_20261119.md report/GML_결과보고서_최종_20261119.hwpx
문단 번호는 20261117.hwpx 기준(hwpx_para.Doc.P).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from hwpx_para import Doc, Q
from lxml import etree

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
C(192, M("사진1. 본 실험 장치")); C(195, "사진2. 줄기 밑동에 꽂은 은선 전극"); 
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
# 사진2·사진3 을 한 줄에 나란히(사용자 11-19): 두 사진을 같은 높이로 붙인 그림 한 장 + 캡션 한 줄에 두 번호
from PIL import Image
_a, _b = Image.open(F["04"]).convert("RGB"), Image.open(F["05"]).convert("RGB")
_H = min(_a.height, _b.height); _a = _a.resize((round(_a.width * _H / _a.height), _H)); _b = _b.resize((round(_b.width * _H / _b.height), _H))
_gap = round(_H * 0.04); _pair = Image.new("RGB", (_a.width + _gap + _b.width, _H), "white")
_pair.paste(_a, (0, 0)); _pair.paste(_b, (_a.width + _gap, 0))
F["04"] = os.path.join(os.path.dirname(dst), "_tmp_pair.jpg"); _pair.save(F["04"], quality=95)
PAIR_SPLIT = _a.width / _pair.width          # 왼쪽 사진이 차지하는 비율(캡션 간격용)
for i, k in ((143, "01"), (160, "02"), (191, "03"), (194, "04"), (272, "06"), (282, "08"), (293, "09"), (347, "12")):
    assert d.P[i].find(".//" + Q("pic")) is not None
    old = [n for n in d.zin.namelist() if n.startswith("BinData/" + ref(i) + ".")][0]
    src_img = F[k]
    if old.upper().endswith(".PNG"):          # 파일 이름·형식을 맞춘다(PNG 자리에는 PNG)
        from PIL import Image
        src_img = os.path.join(os.path.dirname(dst), "_tmp_%s.png" % k); Image.open(F[k]).save(src_img)
    d.repic(ref(i), src_img)
cap2 = d.P[195]
d.delete(196); d.delete(197)                  # 사진3 그림 문단과 캡션
_runs = [r for r in cap2.findall(Q("run")) if r.find(Q("t")) is not None]
_rb, _rr = copy.deepcopy(_runs[0]), copy.deepcopy(_runs[-1])
for _r, _txt_ in ((_rr, "　　　　　　"), (_rb, "사진3."), (copy.deepcopy(_runs[-1]), " 측정 회로의 배선")):
    for _t in _r.findall(Q("t")): _r.remove(_t)
    etree.SubElement(_r, Q("t")).text = _txt_; cap2.append(_r)
for _sa in cap2.findall(Q("linesegarray")): cap2.remove(_sa); cap2.append(_sa)
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
    keep = os.environ.get("INLINE") and p.find(".//" + Q("pic")) is not None   # 그림 문단은 줄 정보가 있어야 그려진다
    for sa in p.findall(Q("linesegarray")):
        if not keep: p.remove(sa)
# 표(개체) 바로 뒤에 그림(개체)이 오면 한글에서 둘이 겹친다(11-19 표6·그림7, rhwp 로 표2·사진1 도 재현).
# 그 그림 문단과 캡션을 표 제목 앞으로 옮긴다(표 뒤 빈 문단은 지운다).
def _pic_after_table():
    top = [p for p in d.root if p.tag == Q("p")]
    for k, p in enumerate(top):
        if p.find(".//" + Q("pic")) is None: continue
        j_ = k - 1
        while j_ >= 0 and top[j_].find(".//" + Q("tbl")) is None and not "".join(x.text or "" for x in top[j_].iter(Q("t"))).strip():
            j_ -= 1
        if j_ >= 1 and top[j_].find(".//" + Q("tbl")) is not None:
            return top, k, j_
    return None
while not os.environ.get("INLINE"):                # 옮기고 나면 다음 그림이 표 뒤에 올 수 있어 다시 본다
    r_ = _pic_after_table()
    if r_ is None: break
    top, k, j_ = r_; p = top[k]
    if True:
        tcap = top[j_ - 1]                       # 표 제목(표 위)
        assert re.match(r"^표\d+\.", "".join(x.text or "" for x in tcap.iter(Q("t")))), "표 제목 아님"
        for e in top[j_ + 1:k]: d.root.remove(e)  # 표와 그림 사이 빈 문단
        cap = top[k + 1]
        tcap.addprevious(p); tcap.addprevious(cap)
for pic in ([] if os.environ.get("INLINE") else d.root.iter(Q("pic"))):
    pic.set("textWrap", "TOP_AND_BOTTOM")
    pos = pic.find(Q("pos"))
    pos.set("treatAsChar", "0"); pos.set("flowWithText", "1"); pos.set("allowOverlap", "0")
    pos.set("vertRelTo", "PARA"); pos.set("vertAlign", "TOP"); pos.set("vertOffset", "0")
    pos.set("horzRelTo", "COLUMN"); pos.set("horzAlign", "CENTER"); pos.set("horzOffset", "0")
# 그림 가로를 39902(양식 기준, 본문 폭의 약 83 %)로 줄인다 — 20쪽 안에 넣으려고(rhwp 로 21쪽 확인).
W_FIG = 39902
# 세로로 긴 사진은 더 좁게(20쪽 안에 넣으려고): 사진2·사진4·사진5 30000, 사진3 32000
W_REF = {"image3": 36000, "image4": 48190, "image21": 28000, "image10": 28000}
for pic in d.root.iter(Q("pic")):
    sz = pic.find(Q("sz")); w0 = int(sz.get("width")); h0 = int(sz.get("height"))
    wt = W_REF.get(pic.find(".//{%s}img" % HC).get("binaryItemIDRef"), W_FIG)
    w, h = wt, round(h0 * wt / w0)
    # 좁은 그림은 양옆에 흰 여백을 붙여 본문 폭(48190)에 꽉 차게 — 한글에서 가운데 정렬이 안 먹어 왼쪽에 붙었다(11-19).
    # 보이는 사진 크기·높이(쪽수)는 그대로다.
    W_FULL = 48190
    if w < W_FULL:
        import io
        ref_ = pic.find(".//{%s}img" % HC).get("binaryItemIDRef")
        nb = getattr(d, "new_bins", {})
        key = "BinData/%s.JPEG" % ref_
        if key in nb: raw = nb[key][1]
        else:
            key = [n for n in d.zin.namelist() if n.startswith("BinData/" + ref_ + ".")][0]
            raw = d.bins.get(key) or d.zin.read(key)
        im = Image.open(io.BytesIO(raw)); fmt = im.format; im = im.convert("RGB")
        nw = round(im.width * W_FULL / w); canvas = Image.new("RGB", (nw, im.height), "white")
        canvas.paste(im, ((nw - im.width) // 2, 0)); buf = io.BytesIO(); canvas.save(buf, fmt, quality=95)
        if key in nb: nb[key] = (nb[key][0], buf.getvalue(), nb[key][2])
        else: d.bins[key] = buf.getvalue()
        c = pic.find(Q("imgClip")); c.set("right", str(nw * 75)); c.set("bottom", str(im.height * 75))
        w = W_FULL
    for tag in ("sz", "curSz", "orgSz"):
        e = pic.find(Q(tag))
        if e is not None: e.set("width", str(w)); e.set("height", str(h))
    for e in pic.iter("{%s}pt1" % HC): e.set("x", str(w))
    for e in pic.iter("{%s}pt2" % HC): e.set("x", str(w)); e.set("y", str(h))
    for e in pic.iter("{%s}pt3" % HC): e.set("y", str(h))
# 그림 원본 크기(imgDim)를 새 그림에 맞춘다 — 안 맞추면 잘라 보기(imgClip)가 원본보다 커서 그림이 안 그려진다(11-19).
for pic in d.root.iter(Q("pic")):
    c = pic.find(Q("imgClip")); dm = pic.find(Q("imgDim"))
    if c is not None and dm is not None:
        dm.set("dimwidth", c.get("right")); dm.set("dimheight", c.get("bottom"))
if os.environ.get("INLINE"):
    # 그림은 자기 문단(가운데, 글자처럼 취급)에 두고 Enter 로 캡션 문단과 나눈다(사용자 11-19 "엔터 쳐서 띄우는 방식").
    # 글자 없는 그림 문단은 줄 배치 정보가 없으면 한글이 안 그린다(B판) → 그림 뒤에 빈칸 한 글자를 넣어
    # 글자가 있는 문단으로 만들어 한글이 줄 배치를 새로 계산하게 한다.
    for pp in [p for p in d.root if p.tag == Q("p") and p.find(".//" + Q("pic")) is not None]:
        cap = pp.getnext()
        pp.set("paraPrIDRef", cap.get("paraPrIDRef"))          # 캡션과 같은 가운데 정렬
        run = [r for r in pp.findall(Q("run")) if r.find(".//" + Q("pic")) is not None][0]
        pic = run.find(".//" + Q("pic"))
        pos = pic.find(Q("pos")); pos.set("treatAsChar", "1"); pos.set("flowWithText", "0")
        pos.set("horzRelTo", "COLUMN"); pos.set("horzAlign", "CENTER")   # 한글에서 왼쪽에 붙어 나옴(11-19 사용자 화면)
        for c in list(run):
            if c.tag == Q("t"): run.remove(c)
        t = etree.SubElement(run, Q("t")); t.text = " "
        # 그림·사진 캡션 뒤에 빈 줄 하나(Enter) — 다음 그림·본문과 띄운다(사용자 11-19)
        if not "".join(x.text or "" for x in (cap.getnext().iter(Q("t")) if cap.getnext() is not None else [])).strip() \
                and cap.getnext() is not None and cap.getnext().find(".//" + Q("tbl")) is None and cap.getnext().find(".//" + Q("pic")) is None:
            pass                                               # 이미 빈 줄이 있음
        else:
            e = etree.Element(Q("p"), id="0", paraPrIDRef="0", styleIDRef="0", pageBreak="0", columnBreak="0", merged="0")
            r_ = etree.SubElement(e, Q("run"), charPrIDRef="44"); etree.SubElement(r_, Q("t")).text = ""
            cap.addnext(e)
        run.set("charPrIDRef", "35")
    for p in d.root.iter(Q("p")):
        for sa in p.findall(Q("linesegarray")): p.remove(sa)
# 표4 마지막 줄: 정상·자극은 다시 학습하지 않았고 손 접촉 기록으로 다시 학습했다(검토 11-19)
for t in d.root.iter(Q("t")):
    if t.text and t.text.strip() == "새 기록으로 다시 학습":
        t.text = "손 접촉 기록으로 다시 학습(Ⅳ장 6절)"
# ── 줄 정리·양식(11-19 사용자 "줄 정리하고 양식에 맞춰서") ──
def _txt(p): return "".join(x.text or "" for x in p.iter(Q("t")))
def _obj(p): return p.find(".//" + Q("tbl")) is not None or p.find(".//" + Q("pic")) is not None
top = [p for p in d.root if p.tag == Q("p")]
body0 = [i for i, p in enumerate(top) if _txt(p).strip() == "Ⅰ. 서론"][-1]       # 목차 다음 본문 시작
HEAD = re.compile(r"^\s*([ⅠⅡⅢⅣⅤ]\. |\d\. [^\d]|<참고문헌>|<부록>)")
empty_model = next(p for p in top[body0:] if not _txt(p).strip() and not _obj(p))
for i in range(body0, len(top)):
    p = top[i]; t = _txt(p)
    if HEAD.match(t) and len(t.strip()) < 45 and i > body0:
        prev = p.getprevious()
        if _txt(prev).strip() or _obj(prev):          # 장·절 제목 앞에는 빈 줄 하나
            e = copy.deepcopy(empty_model); e.set("id", "0"); p.addprevious(e)
# 빈 줄이 둘 이상 이어지면 하나만
top = [p for p in d.root if p.tag == Q("p")]
for a_, b_ in zip(top, top[1:]):
    if a_.getparent() is not None and not _txt(a_).strip() and not _obj(a_) and not _txt(b_).strip() and not _obj(b_) \
            and top.index(a_) > body0:
        d.root.remove(a_)
# 본문 문단 첫 칸: 공백 하나로 맞춘다(목록·제목·캡션·참고문헌·표 칸 제외)
SKIP = re.compile(r"^\s*([ⅠⅡⅢⅣⅤ]\.|\d\. |[·①②③④⑤]|\[\d+\]|<|(표|그림|사진)\d+\.)")
top = [p for p in d.root if p.tag == Q("p")]
body0 = [i for i, p in enumerate(top) if _txt(p).strip() == "Ⅰ. 서론"][-1]
for p in top[body0:]:
    t = _txt(p)
    if not t.strip() or _obj(p) or SKIP.match(t) or p.get("paraPrIDRef") == "19": continue
    ts = [x for x in p.iter(Q("t")) if x.text]
    first = ts[0]; first.text = " " + first.text.lstrip(" ")
# 양식 안내 글 지우기: Ⅲ 제목의 "(설계, 방법, 내용 등 서술)", 표지의 제출 안내 줄
for p in d.root.iter(Q("p")):
    for r in p.findall(Q("run")):
        tt = "".join(x.text or "" for x in r.iter(Q("t")))
        if tt.strip() in ("(설계, 방법, 내용 등 서술)",):
            p.remove(r)
for p in list(d.root.iter(Q("p"))):
    if "추후 공문 안내" in _txt(p) and "20페이지" in _txt(p):
        for r in p.findall(Q("run")):
            for x in r.findall(Q("t")): r.remove(x)
# 빈 줄에 빈칸 한 글자 — 글자 없는 빈 문단은 rhwp 가 높이 0 으로 그려 쪽수를 적게 셌다(한글은 한 줄로 친다)
_top = [p for p in d.root if p.tag == Q("p")]
_b0 = [i for i, p in enumerate(_top) if "".join(x.text or "" for x in p.iter(Q("t"))).strip() == "Ⅰ. 서론"][-1]
for p in _top[_b0:]:
    if not "".join(x.text or "" for x in p.iter(Q("t"))).strip() and p.find(".//" + Q("tbl")) is None and p.find(".//" + Q("pic")) is None:
        ts = list(p.iter(Q("t")))
        if ts: ts[0].text = " "
if os.environ.get("NOPIC"):   # 그림 없는 판(캡션만) — 사용자가 한글에서 그림을 직접 넣는다
    for p in [p for p in d.root if p.tag == Q("p") and p.find(".//" + Q("pic")) is not None]:
        d.root.remove(p)
    d.new_bins = {}
d.save(dst)
import zipfile as _z
_zi = _z.ZipFile(dst); _items = [(it, _zi.read(it.filename)) for it in _zi.infolist()]; _zi.close()
with _z.ZipFile(dst, "w") as _zo:
    for it, data in _items:
        if it.filename == "Contents/header.xml":
            h = data.decode("utf-8")
            h = re.sub(r'(<hh:paraPr id="19".*?<hh:breakSetting [^>]*?)keepLines="0"', r'\1keepLines="1"', h, count=1, flags=re.S)
            # 그림 문단·표 제목은 다음 문단(캡션·표)과 같은 쪽에(그림 문단과 캡션·표 제목이 같은 paraPr 19)
            h = re.sub(r'(<hh:paraPr id="19".*?<hh:breakSetting [^>]*?)keepWithNext="0"', r'\1keepWithNext="1"', h, count=1, flags=re.S)
            data = h.encode("utf-8")
        _zo.writestr(it, data, compress_type=_z.ZIP_STORED if it.filename == "mimetype" else _z.ZIP_DEFLATED)
print("saved", dst)
for n in os.listdir(os.path.dirname(dst)):
    if n.startswith("_tmp_") and n.endswith((".png", ".jpg")): os.remove(os.path.join(os.path.dirname(dst), n))
