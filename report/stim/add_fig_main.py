"""본 실험 그림(그림4, report/FIG_MAIN.png)을 Ⅳ장 4절 끝(900141 뒤)에 넣는다. 옛 그림4(실시간 화면)는 그림5 로 민다.
쓰기: python3 -I add_fig_main.py 원본 중간 → hwpx_pics(중간 결과 "■ 그림4 넣을 자리=FIG_MAIN.png=34000", report 폴더) → hwpx_fillseg"""
import sys, zipfile, re, html
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src); s = zi.read("Contents/section0.xml").decode("utf8")
assert "그림5" not in s
s = s.replace("그림4", "그림5")
nid = max(int(x) for x in re.findall(r'<hp:p id="(\d+)"', s)) + 1
def leaf(pid):
    m = re.search(rf'<hp:p id="{pid}"[^>]*>(?:(?!<hp:p id=).)*?</hp:p>', s, re.S); assert m, pid; return m
def noseg(p): return re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)
def esc(t): return html.escape(t, quote=False)
cap = leaf("295").group(0)
ph = re.sub(r'<hp:p id="295"', f'<hp:p id="{nid}"', cap, count=1)
ph = re.sub(r'<hp:run charPrIDRef="38"><hp:t>[^<]*</hp:t></hp:run>', "", ph)
ph = noseg(re.sub(r"(<hp:run charPrIDRef=\"44\"><hp:t>)[^<]*", r"\1■ 그림4 넣을 자리", ph))
c2 = re.sub(r'<hp:p id="295"', f'<hp:p id="{nid+1}"', cap, count=1)
c2 = c2.replace(">그림3.<", ">그림4.<")
c2 = noseg(re.sub(r'(<hp:run charPrIDRef="44"><hp:t>)[^<]*',
                  r"\1 패러데이 상자 안 기준선 — (가) 차폐 전후, (나) 물을 끊은 지 약 2일째, (다) 5일째 물 주기 전후와 화상", c2))
m = leaf("900141"); s = s[:m.end()] + ph + c2 + s[m.end():]
def rep(pid, a, b):
    global s
    m = leaf(pid); p = m.group(0); assert p.count(esc(a)) == 1, (pid, a)
    s = s[:m.start()] + noseg(p.replace(esc(a), esc(b))) + s[m.end():]
rep("900193", "0.004 mV 이하로 줄었다.", "0.004 mV 이하로 줄었다(그림4(가)).")
rep("900141", "1시간 평균이 −6~+110 mV 사이를 오갔다(0.01–1 Hz", "1시간 평균이 −6~+110 mV 사이를 오갔다(그림4(나), 0.01–1 Hz")
rep("900141", "평평한 상태로 돌아오지는 않았다.", "평평한 상태로 돌아오지는 않았다(그림4(다)).")
rep("900139", "+22~+36 mV에 머물렀다(지지기", "+22~+36 mV에 머물렀다(그림4(다), 지지기")
import xml.dom.minidom; xml.dom.minidom.parseString(s.encode("utf8"))
ids = re.findall(r'<hp:p id="(\d+)"', s); assert len(ids) == len(set(ids))
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        data = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("ok", nid)
