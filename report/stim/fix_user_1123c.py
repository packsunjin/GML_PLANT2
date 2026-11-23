"""fix_user_1123c.py — 파이프라인 성과를 의의 맨 앞(①)과 결론 한 문장에 넣는다(2026-11-23, 사용자 "dd").
의의 ①~③ 은 ②~④ 로 번호만 바꾸고, 새 ① 문단은 기존 ① 문단을 복사해 글만 바꾼다. 바꾼 문단은 줄 배치를 지운다.
쓰는 법: python3 report/stim/fix_user_1123c.py <입력.hwpx> <출력.hwpx>"""
import sys, copy, zipfile
from lxml import etree
src, dst = sys.argv[1:3]
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"; Q = lambda t: "{%s}%s" % (HP, t)
z = zipfile.ZipFile(src); root = etree.fromstring(z.read("Contents/section0.xml"))
own = lambda p: [t for t in p.iter(Q("t")) if next(t.iterancestors(Q("p"))) is p]
def text(p): return "".join(t.text or "" for t in own(p))
def put(p, s):
    ts = own(p); ts[0].text = s
    for t in ts[1:]: t.text = ""
    for sa in p.findall(Q("linesegarray")): p.remove(sa)
ps = [p for p in root if p.tag == Q("p")]
find = lambda pre: [p for p in ps if text(p).lstrip().startswith(pre)]
a1, a2, a3 = find("① 저가 측정계의 한계"), find("② 반응처럼 보이는"), find("③ 코드·원자료")
assert len(a1) == len(a2) == len(a3) == 1 and not find("① 식물 전기신호를 재는 회로부터")
for p, (o, n) in ((a3[0], ("③", "④")), (a2[0], ("②", "③")), (a1[0], ("①", "②"))):
    put(p, text(p).replace(o, n, 1))
new = copy.deepcopy(a1[0])
put(new, " ① 식물 전기신호를 재는 회로부터 수집·변환·학습·실시간 판정까지 브라우저 하나로 하는 파이프라인을 직접 만들었다. "
         "이 시스템으로 손 접촉 반응 분류 모델(정확도 95.5~99.8 %)을 학습했고, 관람객이 손 접촉으로 직접 모델을 학습시켜 보는 부스 체험 화면도 만들었다.")
a1[0].addprevious(new)
c = find("처음 목표한 세 상태 분류는 이루지 못했지만,"); assert len(c) == 1
s = text(c[0]); k = "이루지 못했지만, "
assert "파이프라인" not in s
put(c[0], s.replace(k, k + "측정 회로부터 학습·실시간 판정까지 하는 파이프라인을 직접 만들었고, ", 1))
print(text(new)[:40]); print(text(c[0])[:90])
xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
with zipfile.ZipFile(dst, "w") as o:
    for it in z.infolist():
        o.writestr(it, xml if it.filename == "Contents/section0.xml" else z.read(it.filename),
                   compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("saved", dst)
