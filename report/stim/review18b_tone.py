"""18차 다시 읽기: 120초 비교로 '확인했다' 단정 → '~으로 보인다', 한계 444 중복·121초 튐(회로만, 상자 안에서 안 잼) 분리.
쓰기: python3 -I review18b_tone.py 원본 결과 → hwpx_fillseg (review18_flow 다음)"""
import sys, zipfile, re, html
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src); s = zi.read("Contents/section0.xml").decode("utf8")
def esc(t): return html.escape(t, quote=False).replace("'", "&apos;").replace('"', "&quot;")
def leaf(pid):
    m = re.search(rf'<hp:p id="{pid}"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', s, re.S); assert m, pid; return m
def text_of(pid): return html.unescape("".join(re.findall(r"<hp:t>([^<]*)</hp:t>", leaf(pid).group(0))))
def set_text(pid, t):
    global s
    m = leaf(pid); p = m.group(0); assert p.count("<hp:t>") == 1, pid
    p = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", re.sub(r"<hp:t>[^<]*</hp:t>", lambda _: "<hp:t>" + esc(t) + "</hp:t>", p), flags=re.S)
    s = s[:m.start()] + p + s[m.end():]
def rep(pid, a, b):
    t = text_of(pid); assert t.count(a) == 1, (pid, a); set_text(pid, t.replace(a, b))

rep("411", "상자에 넣자 같은 전극에서 0.060 mV로 줄어 바깥 전기 잡음이었음을 확인했다. 즉 정밀도를 제한하는 것은 회로가 아니라, 느린 신호에서는 전극 표류, 빠른 신호에서는 주변 전기 잡음이다.",
    "상자에 넣자 같은 전극에서 0.060 mV로 줄어(120초 비교) 바깥 전기 잡음이 주된 원인으로 보인다. 즉 정밀도를 제한하는 것은 회로가 아니라, 느린 신호에서는 전극 표류, 빠른 신호에서는 주변 전기 잡음이다.")
rep("76", "2.268 mV에서 0.060 mV로 줄어, 이 흔들림이 바깥 전기 잡음이었음을 확인했다.",
    "2.268 mV에서 0.060 mV로 줄어(120초 비교), 이 흔들림은 주로 바깥 전기 잡음으로 보인다.")
rep("439", "빠른 흔들림은 바깥 전기 잡음에서 온다는 것을 보이고 각각의 대책(전극 교체, 차폐)을 정했다.",
    "빠른 흔들림은 주로 바깥 전기 잡음에서 온다는 근거를 얻고 각각의 대책(전극 교체, 차폐)을 정했다.")
rep("900198", "대부분 바깥 전기장이 식물과 선을 통해 들어온 것이며 차폐로 줄일 수 있다.",
    "대부분 바깥 전기장이 식물과 선을 통해 들어온 것으로 보이며 차폐로 줄일 수 있다.")
set_text("444", "· 손대지 않았는데 생긴 기준선 변화(1단계의 121초 주기 튐, 밤샘 기록의 20 mV 넘는 계단 약 20번 등)는 예비 실험에서 원인을 찾지 못했다. "
         "예비 실험은 모두 금속 차폐 없이 했다(선행 연구[5]는 패러데이 상자 안에서 쟀다). 식물을 상자에 넣자 같은 전극에서 60 Hz 성분과 0.01–1 Hz 잡음이 크게 줄어 "
         "식물 기록의 흔들림은 바깥 전기 잡음이 주된 원인으로 보이나(Ⅳ장 3절), 비교는 120초 기록이고 망을 접지한 직후에는 느린 변화가 오히려 커졌다. "
         "회로만 잰 1단계의 121초 주기 튐은 상자 안에서 다시 재지 않았다. 수 시간 단위 흔들림의 원인까지 확인하려면 긴 기록이 필요하다.")
from xml.dom import minidom; minidom.parseString(s.encode("utf8"))
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        zo.writestr(it, s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename),
                    compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("ok")
