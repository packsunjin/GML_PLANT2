# 맨 바깥 문단 중 줄 배치 vertpos 가 0 부터 시작하는 문단(우리 도구가 쓴 것)만, 바로 앞 문단 다음 위치에서 이어지게 옮긴다(2026-11-02).
# 사용: python3 -I hwpx_monoseg.py 원본.hwpx 결과.hwpx
# 원래 정리본(한글로 만든 판)은 첫 줄 vertpos 가 0 인 문단이 1개뿐이다(문서 맨 처음). hwpx_fillseg·picseg·autoseg 는 문단마다 0 부터
# 써서 값이 뒤로 돌아갔고, 한글은 이를 새 쪽으로 읽어 43~45쪽이 됐다. 표 칸 안 문단(칸 기준 0 부터)은 건드리지 않는다. 맨 마지막 단계로 쓴다.
import sys, re, zipfile
src, dst = sys.argv[1:3]
zi = zipfile.ZipFile(src); s = zi.read("Contents/section0.xml").decode("utf8")
cur = 0; out = []; pos = 0; changed = 0
for m in re.finditer(r'<hp:p id="\d+"[^>]*>.*?</hp:p>(?=<hp:p id|</hs:sec>)', s, re.S):
    p = m.group(0)
    cut = p.rfind("</hp:tbl>") + 1  # 표가 있으면 그 뒤에 오는 줄 배치만 이 문단 것
    head, tail = p[:cut], p[cut:]
    segs = list(re.finditer(r'<hp:lineseg [^>]*/>', tail))
    if segs:
        vp = [int(re.search(r'vertpos="(\d+)"', x.group(0)).group(1)) for x in segs]
        base = vp[0]
        if base != 0 or cur == 0:   # 원래 문서가 쓴 값은 그대로 두고 그 뒤를 이어 센다
            last = segs[-1].group(0)
            cur = vp[-1] + int(re.search(r'vertsize="(\d+)"', last).group(1)) + int(re.search(r'spacing="(-?\d+)"', last).group(1))
            out.append((m.start(), m.end(), p)); continue
        def shift(mm):
            v = int(mm.group(1)); return 'vertpos="%d"' % (cur + v - base)
        tail2 = re.sub(r'(?<=<hp:lineseg )([^>]*)/>', lambda mm: re.sub(r'vertpos="(\d+)"', shift, mm.group(1)) + "/>", tail)
        last = segs[-1].group(0)
        vs = int(re.search(r'vertsize="(\d+)"', last).group(1)); sp = int(re.search(r'spacing="(-?\d+)"', last).group(1))
        cur = cur + (vp[-1] - base) + vs + sp
        changed += tail2 != tail
        p = head + tail2
    out.append((m.start(), m.end(), p))
for a, b, p in reversed(out):
    s = s[:a] + p + s[b:]
vs = [int(x) for x in re.findall(r'vertpos="(\d+)"', s)]
with zipfile.ZipFile(dst, "w") as zo:
    for it in zi.infolist():
        d = s.encode("utf8") if it.filename == "Contents/section0.xml" else zi.read(it.filename)
        zo.writestr(it, d, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
print("바꾼 문단", changed, "끝 위치", cur, "testzip", zipfile.ZipFile(dst).testzip())
