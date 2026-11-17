"""hwpx_para.py — hwpx 문단 단위 편집 도구 (2026-11-17).
문단 번호 = section0.xml 에서 hp:p 를 문서 순서로 센 번호(표 안 문단 포함, 0부터).
  set(i, 글)        문단 i 의 글을 바꾼다(첫 글 run 의 글자 모양 유지, 나머지 글 run 은 지움)
  delete(i)         문단 i 를 지운다
  delete_row(i)     문단 i 가 든 표의 줄(hp:tr)을 지운다(rowCnt·rowAddr·표 높이 맞춤)
  insert_after(i, 본보기, 글)  본보기 문단을 복사해 글을 넣고 문단 i 뒤에 붙인다
  replace_all(정규식, 함수/글)  모든 hp:t 글에 적용
바꾼 문단의 linesegarray 는 지운다(한글이 다시 계산).
"""
import copy, re, zipfile
from lxml import etree
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
NS = {"hp": HP}
Q = lambda t: "{%s}%s" % (HP, t)


class Doc:
    def __init__(self, path):
        self.zin = zipfile.ZipFile(path)
        self.root = etree.fromstring(self.zin.read("Contents/section0.xml"))
        self.P = list(self.root.iter(Q("p")))
        self.bins = {}

    def _clear_seg(self, p):
        for s in p.findall(Q("linesegarray")):
            p.remove(s)

    def _set(self, p, text):
        runs = [r for r in p.findall(Q("run")) if r.find(Q("t")) is not None]
        assert runs, "글 run 없음"
        m = re.match(r"^((?:표|그림|사진)\d+\.)(.*)$", text, re.S)
        t0 = "".join(runs[0].xpath("./hp:t//text()", namespaces=NS))
        if m and len(runs) >= 2 and re.match(r"^(?:표|그림|사진)\d+\.$", t0.strip()):
            # 표·그림 제목: 번호(굵게)와 나머지 글의 글자 모양을 따로 둔다
            self._put(runs[0], m.group(1)); self._put(runs[1], m.group(2))
            for r in runs[2:]:
                p.remove(r)
            self._clear_seg(p)
            return
        first = True
        for r in runs:
            for t in r.findall(Q("t")):
                if first:
                    for c in list(t):
                        t.remove(c)
                    t.text = text
                    first = False
                else:
                    r.remove(t)
            if not first and r is not runs[0] and len(r) == 0:
                p.remove(r)
        self._clear_seg(p)

    def _put(self, r, text):
        ts = r.findall(Q("t"))
        for t in ts[1:]:
            r.remove(t)
        for c in list(ts[0]):
            ts[0].remove(c)
        ts[0].text = text

    def move_before(self, i, j):
        """문단 i 를 문단 j 바로 앞으로 옮긴다(표 제목을 표 위로)."""
        self.P[j].addprevious(self.P[i])

    def set(self, i, text):
        self._set(self.P[i], text)

    def text(self, i):
        return "".join(self.P[i].xpath("./hp:run/hp:t//text()", namespaces=NS))

    def delete(self, i):
        p = self.P[i]
        p.getparent().remove(p)

    def delete_row(self, i):
        tr = self.P[i].xpath("ancestor::hp:tr[1]", namespaces=NS)[0]
        tbl = tr.getparent()
        rows = tbl.findall(Q("tr"))
        k = rows.index(tr)
        h = max(int(c.find(Q("cellSz")).get("height")) for c in tr.findall(Q("tc")))
        for r in rows[k + 1:]:
            for c in r.findall(Q("tc")):
                a = c.find(Q("cellAddr"))
                a.set("rowAddr", str(int(a.get("rowAddr")) - 1))
        tbl.remove(tr)
        tbl.set("rowCnt", str(int(tbl.get("rowCnt")) - 1))
        sz = tbl.find(Q("sz"))
        sz.set("height", str(int(sz.get("height")) - h))

    def insert_after(self, i, model, text):
        p = copy.deepcopy(self.P[model])
        for r in p.findall(Q("run")):          # 본보기의 글자 아닌 조각(구역 설정 등)은 뺀다
            for c in list(r):
                if c.tag != Q("t"):
                    r.remove(c)
        p.set("id", "0")
        self._set(p, text)
        anchor = getattr(self, "_last_ins", {}).get(i, self.P[i])
        anchor.addnext(p)
        self._last_ins = {**getattr(self, "_last_ins", {}), i: p}
        return p

    def replace_all(self, pat, repl):
        for t in self.root.iter(Q("t")):
            if t.text and re.search(pat, t.text):
                t.text = re.sub(pat, repl, t.text)

    def repic(self, ref, path):
        """그림 ref(binaryItemIDRef) 를 새 그림으로. 가로는 그대로, 세로를 새 비율로."""
        from PIL import Image
        HC = "http://www.hancom.co.kr/hwpml/2011/core"
        wpx, hpx = Image.open(path).size
        pic = [x for x in self.root.iter(Q("pic"))
               if x.find(".//{%s}img" % HC).get("binaryItemIDRef") == ref][0]
        w = int(pic.find(Q("sz")).get("width")); h = round(w * hpx / wpx)
        for tag in ("sz", "curSz", "orgSz"):
            e = pic.find(Q(tag))
            if e is not None:
                e.set("width", str(w)); e.set("height", str(h))
        for e in pic.iter("{%s}pt2" % HC):
            e.set("x", str(w)); e.set("y", str(h))
        for e in pic.iter("{%s}pt3" % HC):
            e.set("y", str(h))
        c = pic.find(Q("imgClip"))
        if c is not None:
            c.set("left", "0"); c.set("top", "0"); c.set("right", str(wpx * 75)); c.set("bottom", str(hpx * 75))
        par = pic.xpath("ancestor::hp:p[1]", namespaces=NS)[0]
        for ls in par.iter(Q("lineseg")):
            ls.set("vertsize", str(h)); ls.set("textheight", str(h)); ls.set("baseline", str(round(h * 0.85)))
        name = [n for n in self.zin.namelist() if n.startswith("BinData/" + ref + ".")][0]
        self.bins[name] = open(path, "rb").read()
        return name

    def add_pic_after(self, i, pic_model, cap_model, new_ref, path, caption):
        """그림 문단(pic_model)과 설명 문단(cap_model)을 복사해 문단 i 뒤에 새 그림 new_ref 로 넣는다."""
        HC = "http://www.hancom.co.kr/hwpml/2011/core"
        pp = copy.deepcopy(self.P[pic_model])
        pp.set("id", "0")
        pic = pp.find(".//" + Q("pic"))
        import random
        pic.set("id", str(random.randint(10**9, 2 * 10**9)))
        if pic.get("instid"):
            pic.set("instid", str(random.randint(10**8, 9 * 10**8)))
        pic.find(".//{%s}img" % HC).set("binaryItemIDRef", new_ref)
        self.P[i].addnext(pp)
        cp = copy.deepcopy(self.P[cap_model]); cp.set("id", "0")
        self._set(cp, caption)
        pp.addnext(cp)
        ext = ".PNG" if path.lower().endswith(".png") else ".JPEG"
        name = "BinData/" + new_ref + ext
        self.new_bins = getattr(self, "new_bins", {})
        self.new_bins[name] = (new_ref, open(path, "rb").read(), "image/png" if ext == ".PNG" else "image/jpeg")
        self.repic_new = (new_ref, path)
        # 크기 맞추기는 repic 과 같은 방식(새 그림은 아직 zin 에 없으니 직접)
        from PIL import Image
        wpx, hpx = Image.open(path).size
        w = int(pic.find(Q("sz")).get("width")); h = round(w * hpx / wpx)
        for tag in ("sz", "curSz", "orgSz"):
            e = pic.find(Q(tag))
            if e is not None:
                e.set("width", str(w)); e.set("height", str(h))
        for e in pic.iter("{%s}pt2" % HC):
            e.set("x", str(w)); e.set("y", str(h))
        for e in pic.iter("{%s}pt3" % HC):
            e.set("y", str(h))
        c = pic.find(Q("imgClip"))
        if c is not None:
            c.set("left", "0"); c.set("top", "0"); c.set("right", str(wpx * 75)); c.set("bottom", str(hpx * 75))
        for ls in pp.iter(Q("lineseg")):
            ls.set("vertsize", str(h)); ls.set("textheight", str(h)); ls.set("baseline", str(round(h * 0.85)))

    def set_bin(self, name, path):
        self.bins[name] = open(path, "rb").read()

    def save(self, dst):
        xml = etree.tostring(self.root, xml_declaration=True, encoding="UTF-8", standalone=True)
        with zipfile.ZipFile(dst, "w") as z:
            for it in self.zin.infolist():
                if it.filename == "Contents/content.hpf" and getattr(self, "new_bins", None):
                    hpf = self.zin.read(it.filename).decode("utf-8")
                    add = "".join(f'<opf:item id="{r}" href="{n}" media-type="{mt}" isEmbeded="1"/>'
                                  for n, (r, _, mt) in self.new_bins.items())
                    data = hpf.replace("</opf:manifest>", add + "</opf:manifest>").encode("utf-8")
                elif it.filename == "Contents/section0.xml":
                    data = xml
                elif it.filename in self.bins:
                    data = self.bins[it.filename]
                else:
                    data = self.zin.read(it.filename)
                ct = zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED
                z.writestr(it.filename, data, compress_type=ct)
            for n, (_, b, _) in getattr(self, "new_bins", {}).items():
                z.writestr(n, b, compress_type=zipfile.ZIP_DEFLATED)
