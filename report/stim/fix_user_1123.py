"""fix_user_1123.py — 사용자가 한글에서 고친 보고서(GML_결과보고서_사용자수정_20261123.hwpx)에서 사실과 다른 문장만 고친다(2026-11-23).
사용자가 고친 것은 건드리지 않는다. 고친 문단만 줄 배치 정보(linesegarray)를 지워 한글이 다시 계산하게 한다.
쓰는 법: python3 report/stim/fix_user_1123.py <입력.hwpx> <출력.hwpx>"""
import sys, zipfile
from lxml import etree
src, dst = sys.argv[1:3]
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"; Q = lambda t: "{%s}%s" % (HP, t)
E = [("은선은 2시간 내내 1분 사이에 10~15 mV씩 오르내렸고", "은선은 1분 사이 변화가 최대 10~15 mV로 2시간 내내 오르내렸고"),
     ("또 정상_6과 11-09 기록의", "또 11-05 정상 기록과 11-09 기록의"),
     ("다만 이렇게 조용한 상태는 한 기록에서만 얻었고, 다른 긴 기록에는 60 Hz 성분과 함께 잡음이 수십 배 커지는 구간이 남았다.",
      "다만 이렇게 조용한 기록은 하나뿐이었고, 같은 화분의 다른 긴 기록 넷은 60 Hz 성분과 함께 잡음이 22~56배 컸다."),
     ("제시했고, 전극과 측정 환경을 바꿔 식물을 조용하게 잴 수 있는 조건과, 신호가 어디서 오는지 가르는 실험 방법을 만들었다.",
      "제시했다. 또 차폐와 전원을 바꿔 식물을 조용하게 잰 기록 하나를 얻었고, 신호가 어디서 오는지 가르는 실험 방법을 만들었다."),
     ("상태마다 기록이 한 회차뿐이고 기록마다, 시간대마다", "조용하게 잰 기록이 물 공급 중단 한 회차뿐이고 기록마다, 시간대마다"),
     ("본 실험은 식물 한 그루에서 정상과 물 공급 중단을 한 회차씩만 기록했고, 흙 수분을 재지 않았다.",
      "본 실험은 같은 화분에서 정상과 물 공급 중단을 두 회차씩 기록했으나 잡음이 기준 아래인 기록은 물 공급 중단 한 회차뿐이었고, 흙 수분을 재지 않았다."),
     ("브레드보드 GND", "라즈베리파이 GND(14번 핀)")]
z = zipfile.ZipFile(src)
root = etree.fromstring(z.read("Contents/section0.xml"))
done = {a: 0 for a, _ in E}
for p in root.iter(Q("p")):
    ts = [t for t in p.iter(Q("t")) if p is next(t.iterancestors(Q("p")))]
    for a, b in E:
        hit = [t for t in ts if t.text and a in t.text]
        if hit:
            hit[0].text = hit[0].text.replace(a, b); done[a] += 1
            for sa in p.findall(Q("linesegarray")): p.remove(sa)
        elif a in "".join(t.text or "" for t in ts):
            raise SystemExit("여러 조각에 걸침: " + a)
print({k[:20]: v for k, v in done.items()})
assert all(v >= 1 for v in done.values())
xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
with zipfile.ZipFile(dst, "w") as o:
    for it in z.infolist():
        data = xml if it.filename == "Contents/section0.xml" else z.read(it.filename)
        o.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("saved", dst)
