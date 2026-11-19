"""diff_list_1119.py — 11-03 사용자 HWP(hwpx 판)와 최종 hwpx 를 문단 단위로 비교해 수정 목록(txt)을 만든다.
쓰는 법: python3 report/stim/diff_list_1119.py"""
import sys, difflib, re, os
sys.path.insert(0, os.path.dirname(__file__))
from hwpx_para import Doc
def paras(f):
    d = Doc(f); return [d.text(i).strip() for i in range(len(d.P)) if d.text(i).strip()]
A = paras('report/GML_결과보고서_사용자수정_20261103.hwpx'); B = paras('report/GML_결과보고서_최종_20261119.hwpx')
def where(i):
    ch = sec = ''
    for k in range(i, -1, -1):
        t = A[k]
        if not sec and re.match(r'^(\d\. |표\d+\.|연구 (목표|내용|성과)$)', t): sec = t
        if re.match(r'^([ⅠⅡⅢⅣⅤ]\. |<부록>|연구 요약)', t) and k > 60: ch = t; break
    return (ch[:20] + ' / ' if ch else '') + sec[:40]
sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
out = ['보고서 수정 목록 (기준: GML_결과보고서_사용자수정_20261103.hwp)', '',
       '· 각 항목: [위치] → 원래 글(앞부분) → 바꿀 글. 표 칸도 같은 방식이다.',
       '· "지움"은 그 문단(또는 표 칸 글)을 지우는 것, "새로 넣음"은 바로 앞 문단 뒤에 넣는 것.',
       '· 표 제목이 "지움 + 새로 넣음"으로 나오면 표 위로 옮긴 것이다.',
       '· 그림·사진은 캡션 위에 report/보고서_그림_순서대로/ 의 JPG 를 번호대로 넣는다(그림1~7, 사진1~5).', '']
k = 0
for op, a0, a1, b0, b1 in sm.get_opcodes():
    if op == 'equal' or (op == 'delete' and all(len(t) <= 2 for t in A[a0:a1])): continue
    k += 1
    out.append(f'━━ {k}. [{where(min(a0, len(A) - 1))}]')
    if op in ('replace', 'delete'):
        for t in A[a0:a1]: out.append('  원래: ' + (t[:60] + '…' if len(t) > 60 else t))
    else:
        out.append('  앞 문단: ' + A[a0 - 1][:60] + '…')
    if op in ('replace', 'insert'):
        for t in B[b0:b1]: out.append(('  ▶ 바꿀 글: ' if op == 'replace' else '  ▶ 새로 넣음: ') + t)
    else:
        out.append('  ▶ 지움')
    out.append('')
open('report/보고서_수정목록_20261119.txt', 'w', encoding='utf-8').write('\n'.join(out)); print(k)
