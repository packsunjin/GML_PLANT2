"""booth_poster_build.py — 페스티벌 부스 앞 설명 포스터(머신러닝 체험)를 양식 5-3 위에 만든다 (2026-11-17).

양식·XML 조각·미리보기는 report/poster_build.py 것을 그대로 쓰고, 내용과 '단계' 배치(왼쪽 그림 + 오른쪽 글)만 여기 둔다.
화면 글자·단계 이름은 web/booth.html 과 같게 쓴다. 정확도 숫자는 쓰지 않는다(CLAUDE.md 6절 부스 계획).
그림: python3 report/stim/fig_booth_poster.py  → report/FIG_BOOTH_*.png
쓰는 법(저장소 루트): python3 report/booth_poster_build.py → report/GML_부스포스터.hwpx, report/GML_부스포스터_미리보기.png
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import poster_build as pb
from PIL import Image

pb.DST = os.path.join(pb.REP, "GML_부스포스터.hwpx")
pb.PREVIEW = os.path.join(pb.REP, "GML_부스포스터_미리보기.png")

pb.STYLES.update({
    "body":  (2700, "#1A1A1A", 0, False),
    "sub":   (3600, "#905720", 2, False),
    "call":  (3200, "#FFFFFF", 2, False),
    "cap":   (1900, "#404040", 0, False),
    "ref":   (2000, "#404040", 0, False),
    "title": (5200, "#000000", 2, False),
    "sum":   (2600, "#1A1A1A", 2, False),
})
pb.KIND.update({"sub0": ("sub", "body")})
pb.PARA["body"] = (19, 140, 0, 500)

pb.TITLE = "식물의 전기신호로 나만의 AI 모델 만들기"
pb.SUMMARY = "방울토마토 줄기 신호로 16초 만에 우리 학교 AI 모델 만들기"

S = "FIG_BOOTH_STEP{}.png"
LEFT = [
    ("bar", "Ⅰ. 체험 방법"),
    ("step", 1, S.format(1), "학교 이름 입력", ["'머신러닝 학습해보기' 누르기", "학교 이름 입력 → '다음'"]),
    ("step", 2, S.format(2), "정상 학습하기", ["손대지 마세요", "'기록 시작' → 8초"]),
    ("step", 3, S.format(3), "자극 학습하기", ["손가락으로 잎을 가볍게 잡으세요", "'기록 시작' → 8초"]),
    ("step", 4, S.format(4), "모델 생성", ["모델 학습 중입니다", "→ 모델이 생성되었습니다"]),
    ("step", 5, S.format(5), "모델 선택하기", ["학교 모델 순위에서 '선택'"]),
    ("step", 6, S.format(6), "실시간 판정", ["실시간 분류 판정: 정상 / 자극"]),
]
RIGHT = [
    ("bar", "Ⅱ. 화면 보는 법"),
    ("fig", "FIG_BOOTH_SCREEN.png", 1.0, "화면 예시 — 실측 손 접촉 기록"),
    ("li", "① 실시간 전압 (최근 30초) — 줄기 전극 미세전압"),
    ("li", "② 실시간 스펙트로그램 (최근 30초) — 파랑 약 · 빨강 강"),
    ("li", "③ 모델 입력 — 오른쪽 끝 2초, 모델이 보는 곳"),
    ("bar", "Ⅲ. 원리"),
    ("fig", "FIG_BOOTH_FLOW.png", 1.0, ""),
    ("li", "· 정상 8초 + 자극 8초를 2초씩 잘라 스펙트로그램으로"),
    ("li", "· SVM 이 정상 / 자극을 가르는 법을 배운다"),
    ("bar", "Ⅳ. 돈 규칙"),
    ("call", "모델을 만든 순간부터 1초마다 돈이 쌓인다 — 잘 가르는 모델일수록 빨리 번다"),
    ("li", "· 학교 모델 순위 = 번 돈 순"),
    ("ref", "* 은선 전극 접촉에 따른 물리적 전위 변화를 가르는 판정입니다."),
]

STEP_IMG, STEP_GAP = 32000, 1300
_base_layout = pb.layout


def layout(blocks, col):
    """배치한 뒤 단 아래 남는 높이의 80 % 를 절(왼쪽은 단계) 사이에 고르게 나눈다."""
    out, y = _layout(blocks, col)
    room = pb.COL_BOT - pb.PAD - y
    if room <= 0:
        return out, y
    kind = "pic" if any(b[0] == "step" for b in blocks) else "bar"
    starts = [i for i, o in enumerate(out) if o[0] == kind][1:]
    if not starts:
        return out, y
    step = min(round(room * 0.8 / len(starts)), 11000)
    res, shift = [], 0
    for i, o in enumerate(out):
        if i in starts and not (kind == "pic" and out[i - 1][0] != "box"):
            shift += step
        res.append((o[0], o[1], o[2] + shift, *o[3:]))
    return res, y + shift


def _layout(blocks, col):
    """'step' 블록(왼쪽 그림 + 오른쪽 번호·글)을 더한 배치. 나머지는 poster_build.layout 과 같다."""
    if not any(b[0] == "step" for b in blocks):
        out, y = _base_layout([b for b in blocks if not (b[0] == "fig" and not b[3])], col)
        return _drop_empty_caps(blocks, out, y)
    x0, y = pb.COLS[col] + pb.PAD, pb.COL_TOP + pb.PAD
    w = pb.COL_W - 2 * pb.PAD
    out = []
    for b in blocks:
        if b[0] == "bar":
            if out:
                y += pb.SEC_GAP
            out.append(("bar", x0, y, w, pb.BAR_H, b[1])); y += pb.BAR_H + pb.BAR_GAP
        else:
            _, n, img, title, lines = b
            p = os.path.join(pb.REP, img)
            out.append(("pic", x0, y, STEP_IMG, STEP_IMG, p))
            tx = x0 + STEP_IMG + 2000
            paras = [("sub0", f"{n}  {title}")] + [("li", t) for t in lines]
            out.append(("box", tx, y, w - (tx - x0), STEP_IMG, (paras, None)))
            y += STEP_IMG + STEP_GAP
    return out, y


def _drop_empty_caps(blocks, out, y):
    """설명 없는 그림(원리 그림)은 poster_build 가 설명 칸을 붙이므로, 그림을 따로 넣고 다시 배치한다."""
    # 설명 없는 그림 자리를 표시해 두고 base 배치 뒤 끼워 넣는 대신, 단순하게 직접 다시 쌓는다.
    x0, y = None, None
    res = []
    col = "R"
    x0, y = pb.COLS[col] + pb.PAD, pb.COL_TOP + pb.PAD
    w = pb.COL_W - 2 * pb.PAD
    run = []

    def flush():
        nonlocal y, run
        if run:
            h = sum(pb.para_height(k, t, w)[0] for k, t in run) * pb.SAFE
            res.append(("text", x0, y, w, round(h), list(run))); y += round(h); run = []
    for b in blocks:
        if b[0] == "bar":
            flush()
            if res:
                y += pb.SEC_GAP
            res.append(("bar", x0, y, w, pb.BAR_H, b[1])); y += pb.BAR_H + pb.BAR_GAP
        elif b[0] == "fig":
            flush()
            _, name, frac, cap = b
            p = os.path.join(pb.REP, name)
            wpx, hpx = Image.open(p).size
            fw = round(w * frac); fh = round(fw * hpx / wpx)
            y += pb.FIG_GAP
            res.append(("pic", x0 + (w - fw) // 2, y, fw, fh, p)); y += fh + 300
            if cap:
                ch = round(pb.STYLES["cap"][0] * 1.6 * pb.SAFE) + 300
                res.append(("text", x0, y, w, ch, [("cap", cap)])); y += ch
            y += pb.FIG_GAP
        elif b[0] == "call":
            flush()
            y += pb.FIG_GAP
            paras = [("call", b[1])]
            bw = w
            bh = round(sum(pb.para_height(k, t, bw - 2 * pb.KEY_PAD)[0] for k, t in paras) * pb.SAFE + 2 * pb.KEY_PAD)
            res.append(("box", x0, y, bw, bh, (paras, pb.FILL_CALL))); y += bh + pb.FIG_GAP
        else:
            run.append(b)
    flush()
    return res, y


pb.layout = layout
pb.LEFT, pb.RIGHT = LEFT, RIGHT

if __name__ == "__main__":
    pb.main()
