"""fix_user_1123b.py — 표5(측정 대상별 판정)에 '전극' 줄을 넣는다(2026-11-23, 사용자 "종합에 안 고쳐졌다").
'측정 회로' 줄 바로 아래에 같은 모양으로 한 줄을 복사해 넣고 행 번호·표 높이를 고친다.
표 뒤 문단 가운데 글자가 있는 문단은 줄 배치 정보를 지워 한글이 다시 계산하게 한다(그림만 있는 문단은 그대로).
쓰는 법: python3 report/stim/fix_user_1123b.py <입력.hwpx> <출력.hwpx>"""
import sys, copy, zipfile
from lxml import etree
src, dst = sys.argv[1:3]
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"; Q = lambda t: "{%s}%s" % (HP, t)
z = zipfile.ZipFile(src); root = etree.fromstring(z.read("Contents/section0.xml"))
txt = lambda e: "".join(x.text or "" for x in e.iter(Q("t")))
tb = next(t for t in root.iter(Q("tbl")) if txt(t).startswith("대상판정근거"))
assert "전극" not in [txt(tr.findall(Q("tc"))[0]) for tr in tb.findall(Q("tr"))]
rows = tb.findall(Q("tr")); base = rows[1]; assert txt(base).startswith("측정 회로")
new = copy.deepcopy(base)
for tc, s in zip(new.findall(Q("tc")), ["전극", "줄이지 못함", "물속 60분 표류 점퍼선 핀 −59.20 mV, 은선 −82.91 mV"]):
    ts = list(tc.iter(Q("t"))); ts[0].text = s
    for t in ts[1:]: t.text = ""
    for p in tc.iter(Q("p")):
        for sa in p.findall(Q("linesegarray")): p.remove(sa)
base.addnext(new)
for i, tr in enumerate(tb.findall(Q("tr"))):
    for tc in tr.findall(Q("tc")): tc.find(Q("cellAddr")).set("rowAddr", str(i))
tb.set("rowCnt", str(len(tb.findall(Q("tr")))))
h = int(base.find(Q("tc")).find(Q("cellSz")).get("height"))
sz = tb.find(Q("sz")); sz.set("height", str(int(sz.get("height")) + h))
# 표 뒤 글자 있는 문단의 줄 배치 지우기
tp = next(tb.iterancestors(Q("p")))
while tp.getparent() is not root: tp = tp.getparent()
after = False; n = 0
for p in root:
    if p is tp: after = True; continue
    if not after or p.tag != Q("p"): continue
    own = "".join(t.text or "" for t in p.iter(Q("t")) if next(t.iterancestors(Q("p"))) is p)
    if own != "":
        for sa in p.findall(Q("linesegarray")): p.remove(sa); n += 1
print("rows", tb.get("rowCnt"), "height", sz.get("height"), "linesegs removed", n)
xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
with zipfile.ZipFile(dst, "w") as o:
    for it in z.infolist():
        o.writestr(it, xml if it.filename == "Contents/section0.xml" else z.read(it.filename),
                   compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("saved", dst)
