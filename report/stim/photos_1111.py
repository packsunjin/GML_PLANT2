"""2026-11-11 사진 갈기: 사진4 제목을 새 식물 사진에 맞추고, 사진5(은선 전극) 자리를 넣고, 화분 설명 한 문장을 고친다.
쓰는 법(저장소 루트):
  python3 -I report/stim/photos_1111.py 원본.hwpx 중간.hwpx
  python3 -I report/hwpx_repic.py 중간.hwpx 중간2.hwpx image13 report/PHOTO4_CAGE_20261105.jpg
  (cd report && python3 hwpx_pics.py 중간2.hwpx 결과.hwpx "사진5 넣을 자리=PHOTO5_SILVER_20261103.jpg=39902")"""
import sys, re, zipfile, xml.dom.minidom
from xml.sax.saxutils import escape
src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src); x = zin.read("Contents/section0.xml").decode("utf-8")
def span(pid):
    ms = list(re.finditer(r'<hp:p id="%s" [^>]*>(?:(?!<hp:p id=).)*?</hp:p>' % pid, x, re.S)); assert len(ms) == 1, pid
    return ms[0]
def run2(pid, num, t):
    return (f'<hp:p id="{pid}" paraPrIDRef="19" styleIDRef="28" pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="38"><hp:t>{escape(num)}</hp:t></hp:run><hp:run charPrIDRef="44"><hp:t> {escape(t)}</hp:t></hp:run></hp:p>')
nid = max(int(i) for i in re.findall(r'<hp:p id="(\d+)"', x)) + 1000
m = span("900096")
new = (run2("900096", "사진4.", "패러데이 상자(방충망 6면) — (가) 새 식물을 넣은 상자, (나) 상자 밖에 둔 회로와 라즈베리파이")
       + f'<hp:p id="{nid+1}" paraPrIDRef="19" styleIDRef="28" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="56"><hp:t>■ 사진5 넣을 자리</hp:t></hp:run></hp:p>'
       + run2(nid + 2, "사진5.", "은선 전극 — (가) 새 식물의 줄기에 꽂은 은선, (나) 물에 담가 표류를 잰 모습"))
x = x[:m.start()] + new + x[m.end():]
for old, rep in (("본 실험은 새 방울토마토 화분 한 그루로 했고,", "본 실험은 새 화분에 심긴 방울토마토 가운데 한 그루로 했고(사진5),"),
                 ("은선 전극으로 정상과 수분부족 상태를 길게 기록했다(표3 ③④).", "은선 전극(사진5)으로 정상과 수분부족 상태를 길게 기록했다(표3 ③④).")):
    assert x.count(old) == 1, old
    x = x.replace(old, rep)
xml.dom.minidom.parseString(x.encode("utf-8"))
with zipfile.ZipFile(dst, "w") as zout:
    for info in zin.infolist():
        data = x.encode("utf-8") if info.filename == "Contents/section0.xml" else zin.read(info.filename)
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = zipfile.ZIP_STORED if info.filename == "mimetype" else info.compress_type
        zi.external_attr = info.external_attr; zout.writestr(zi, data)
print("ok")
