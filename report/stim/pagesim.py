# 쪽수 대략 추정(줄 배치·표 칸 높이·그림 높이 합산). 2026-10-20 기준 모두의한글 실제 쪽수보다 약 1쪽 많게 나온다(사용자가 21쪽이라 한 판을 22.07 로 셈) — 판끼리 비교용으로만 쓴다.
import zipfile,re,sys
BODY=72852
def sim(f):
    z=zipfile.ZipFile(f); s=z.read('Contents/section0.xml').decode(); h=z.read('Contents/header.xml').decode()
    pp={}
    for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>',h,re.S):
        b=m.group(0)
        pv=re.search(r'<hc:prev value="(-?\d+)"',b); nx=re.search(r'<hc:next value="(-?\d+)"',b)
        pp[m.group(1)]=(int(pv.group(1)) if pv else 0,int(nx.group(1)) if nx else 0)
    top=re.findall(r'<hp:p id="\d+" paraPrIDRef="(\d+)"[^>]*pageBreak="(\d)"[^>]*>(.*?)</hp:p>(?=<hp:p id|</hs:sec>)',s,re.S)
    pages=1; y=0
    for pid,pb,b in top:
        pv,nx=pp.get(pid,(0,0))
        if pb=='1' and y>0: pages+=1; y=0
        items=[]
        if '<hp:tbl' in b:
            th=sum(int(x) for x in re.findall(r'<hp:tbl [^>]*>.*?<hp:sz width="\d+" widthRelTo="\w+" height="(\d+)"',b,re.S)[:1])
            # rows: use row heights
            rows=[]
            for tr in re.findall(r'<hp:tr>.*?</hp:tr>',b,re.S):
                hs=[int(x) for x in re.findall(r'<hp:cellSz width="\d+" height="(\d+)"',tr)]
                # content height estimate
                segs=[int(a)+int(c) for a,c in re.findall(r'vertsize="(\d+)"[^>]*spacing="(\d+)"',tr)]
                rows.append(max(max(hs) if hs else 0, 0))
            items=rows+[1700]
        elif '<hp:pic' in b:
            hgt=int(re.search(r'<hp:pic .*?<hp:sz width="\d+"[^>]*height="(\d+)"',b,re.S).group(1))
            items=[hgt+600]
        else:
            segs=[int(a)+int(c) for a,c in re.findall(r'<hp:lineseg [^>]*vertsize="(\d+)"[^>]*spacing="(\d+)"',b)]
            items=segs if segs else [1760]
        y+=pv
        for it in items:
            if y+it>BODY: pages+=1; y=0
            y+=it
        y+=nx
    return pages, round(y/BODY,2)
for f in sys.argv[1:]: print(f.split('/')[-1], sim(f))
