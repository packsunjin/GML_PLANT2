"""poster_1119.py — 발표 포스터(양식 report/포스터양식_5-3_SWAI.hwpx)에 최종 보고서 내용을 넣는다 (2026-11-19).
왼쪽 칸: Ⅰ·Ⅱ·Ⅲ, 오른쪽 칸: Ⅳ·Ⅴ. 본문 25pt 함초롬바탕(양식 charPr 7), 그림은 가운데(paraPr 20) 글자처럼 취급.
줄 배치 정보는 넣은 문단에 두지 않는다(한글이 계산). 글자 없는 문단은 한글이 그리지 않으므로 빈칸 한 글자를 둔다.
쓰는 법(저장소 루트): python3 report/stim/poster_1119.py report/포스터양식_5-3_SWAI.hwpx report/발표포스터_20261119.hwpx
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
for b in bars[3:]: lsl.remove(b); rsl.append(b)               # Ⅳ·Ⅴ 를 오른쪽으로
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
# 절 내용은 절마다 그림 한 장(report/stim/poster_sections.js 가 만든 JPG). 글상자 안에서 줄 배치 없는 글 문단은
# 겹쳐 나와(rhwp 확인), 그림 한 장 + 빈칸 한 글자 문단으로 넣는다.
SEC = os.environ.get("POSTER_SEC", os.path.join(os.path.dirname(dst), "poster_sec"))
def sec_img(name):
    jp = os.path.join(SEC, name + ".jpg")
    if not os.path.exists(jp):
        Image.open(os.path.join(SEC, name + ".png")).convert("RGB").save(jp, quality=92)
    F[name] = jp
    return pic_para(name, W)
# 왼쪽 칸: Ⅰ s1, Ⅱ s2, Ⅲ s3 / 오른쪽 칸: Ⅳ s4a(결과 1·2)·s4b(결과 3·4), Ⅴ s5
for k, name in ((0, "s1"), (1, "s2"), (2, "s3"), (4, "s5")):
    e = sec_img(name); bars[k].addnext(e)
    if k < 4: e.addnext(para(" "))
e1 = sec_img("s4a"); bars[3].addnext(e1); e2 = sec_img("s4b"); e1.addnext(e2); e2.addnext(para(" "))

# 저장
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
print("saved", dst, len(new_bins), "images")
