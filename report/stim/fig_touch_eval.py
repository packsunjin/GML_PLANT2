"""fig_touch_eval.py — 손 접촉 감지 모델의 평가 방식(보고서 그림6, 2026-11-19 사용자 지시 '평가 방식이 이해되게').
(가) 2초 창에 라벨 붙이기(신호 한 번 확대) (나) 1회: 앞 절반 학습 → 뒤 절반 평가 (다) 2회: 뒤 학습 → 앞 평가 (라) 보조배터리 기록에 적용.
숫자: touch1117_ml.json. 쓰는 법: TOUCH_DIR=<csv 폴더> python3 report/stim/fig_touch_eval.py
"""
import sys, os, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle
sys.path.insert(0, os.path.dirname(__file__))
import touch1117_ml as T
for f in ("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"):
    fm.fontManager.addfont("/usr/share/fonts/opentype/noto/" + f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False, "font.size": 9})
J = json.load(open(os.path.join(os.path.dirname(__file__), "touch1117_ml.json")))
INK, GRAY, YEL = "#1d1d1d", "#707070", "#f2c94c"
TR, TE = "#cfe0f3", "#fde3cf"          # 학습 구간, 평가 구간 바탕
POS, NEG = "#c0504d", "#1f77b4"        # 접촉 창, 비접촉 창

ta, ma = T.series("자극_콘센트_20261117.csv"); sa = [189.28 + 30 * k for k in range(9)]
tb, mb = T.series("자극_배터리_20261117.csv"); sb = [129.75 + 30 * k for k in range(10)]
za, zb = np.median(ma), np.median(mb)

fig = plt.figure(figsize=(7.4, 7.2), dpi=300)
# (가) 라벨 붙이기 — 잡은 한 번(249.28초) 확대
ax = fig.add_axes([0.08, 0.81, 0.55, 0.14])
s = 249.28; k = (ta > s - 8) & (ta < s + 14)
ax.axvspan(0, 2, color=YEL, alpha=0.7, lw=0)
ax.plot(ta[k] - s, ma[k] - za, color=INK, lw=0.8)
ax.set_xlim(-8, 14); ax.set_ylim(-60, 170); ax.set_ylabel("전압 (mV)"); ax.grid(lw=0.3, color="#e3e3e3")
ax.set_title("(가) 2초씩 잘라 이름표 붙이기 (신호 한 번 확대)", loc="left", fontsize=9.2, fontweight="bold")
for j, x0 in enumerate(np.arange(-8, 12.01, 0.5)):
    x1 = x0 + 2
    pos = x0 >= 0 and x1 <= 6; neg = x1 <= -1 or x0 >= 8
    if j % 2: continue
    col = POS if pos else NEG if neg else "#bbbbbb"
    ax.add_patch(Rectangle((x0, -55 + (j // 2 % 3) * 9), 2, 7, fc=col, ec="white", lw=0.4))
ax.set_xlabel("신호 뒤 시간 (초)")
lg = fig.add_axes([0.66, 0.81, 0.33, 0.14]); lg.axis("off"); lg.set_xlim(0, 10); lg.set_ylim(0, 10)
for y, c, t in ((8.6, YEL, "잎을 잡으라고 신호한 2초"), (6.4, POS, "접촉 창 (신호 뒤 6초 안)"), (4.2, NEG, "비접촉 창"), (2.0, "#bbbbbb", "애매한 창은 뺌")):
    lg.add_patch(Rectangle((0, y - 0.7), 1.3, 1.4, fc=c, ec="none")); lg.text(1.8, y, t, va="center", fontsize=8)

def run(y0, title, t, m, z, sigs, train, test, res_lines):
    a = fig.add_axes([0.08, y0, 0.58, 0.13])
    for (x0, x1) in train: a.axvspan(x0, x1, color=TR, lw=0)
    for (x0, x1) in test: a.axvspan(x0, x1, color=TE, lw=0)
    for s in sigs: a.axvspan(s, s + 2, color=YEL, alpha=0.9, lw=0)
    a.plot(t, m - z, color=INK, lw=0.45)
    a.set_xlim(0, 600); a.set_ylim(-40, 170); a.set_yticks([0, 100]); a.grid(lw=0.3, color="#e3e3e3")
    a.set_title(title, loc="left", fontsize=9.2, fontweight="bold")
    for (x0, x1) in train: a.text((x0 + x1) / 2, 150, "학습", ha="center", va="top", fontsize=8.5, color="#2b5d8a", fontweight="bold")
    for (x0, x1) in test: a.text((x0 + x1) / 2, 150, "평가", ha="center", va="top", fontsize=8.5, color="#b5651d", fontweight="bold")
    r = fig.add_axes([0.68, y0, 0.33, 0.13]); r.axis("off"); r.set_xlim(0, 10); r.set_ylim(0, 10)
    r.add_patch(Rectangle((0, 0), 10, 10, fc="#f7f7f7", ec="#cccccc", lw=0.6))
    for i, (txt, bold) in enumerate(res_lines):
        r.text(0.5, 8.3 - i * 2.6, txt, va="center", fontsize=7.4, fontweight="bold" if bold else None)
    return a

def L(name, key):
    d = J[name][key]; return d
s1, r1 = L("SVM", "앞→뒤"), L("랜덤 포레스트", "앞→뒤")
run(0.575, "(나) 1회: 앞 절반으로 학습 → 뒤 절반으로 평가 (콘센트 전원)", ta, ma, za, sa, [(0, 310)], [(310, 600)],
    [("평가: 접촉 창 39개, 비접촉 창 473개", False), (f"SVM  접촉 {s1['접촉 찾음']} · 비접촉 {s1['비접촉 맞힘']}", False),
     (f"랜덤 포레스트  접촉 {r1['접촉 찾음']} · 비접촉 {r1['비접촉 맞힘']}", False)])
s2, r2 = L("SVM", "뒤→앞"), L("랜덤 포레스트", "뒤→앞")
run(0.375, "(다) 2회: 바꿔서 뒤 절반으로 학습 → 앞 절반으로 평가", ta, ma, za, sa, [(310, 600)], [(0, 310)],
    [("평가: 접촉 창 33개, 비접촉 창 405개", False), (f"SVM  접촉 {s2['접촉 찾음']} · 비접촉 {s2['비접촉 맞힘']}", False),
     (f"랜덤 포레스트  접촉 {r2['접촉 찾음']} · 비접촉 {r2['비접촉 맞힘']}", False)])
s3, r3 = J["SVM"]["배터리 기록에 적용"], J["랜덤 포레스트"]["배터리 기록에 적용"]
a = run(0.175, "(라) 콘센트 기록 전체로 학습한 모델 → 보조배터리 기록 평가", tb, mb, zb, sb, [], [(0, 600)],
    [("잎 잡은 창 80개를 접촉으로 판정", False), (f"SVM  {s3['만진 시각 창을 접촉으로']} · 랜덤 포레스트  {r3['만진 시각 창을 접촉으로']}", True),
     ("→ 손이 닿아도 감지 못 함", True)])
a.set_xlabel("시간 (초)")
# 맨 아래: 균형 정확도
b = fig.add_axes([0.08, 0.0, 0.91, 0.1]); b.axis("off"); b.set_xlim(0, 100); b.set_ylim(0, 10)
b.text(0, 8.2, "균형 정확도 = (접촉 창 맞힌 비율 + 비접촉 창 맞힌 비율) ÷ 2", fontsize=8.6, fontweight="bold")
rows = [("SVM", s1, s2), ("랜덤 포레스트", r1, r2)]
for i, (n, x, y) in enumerate(rows):
    b.text(0, 4.6 - i * 3.4, f"{n}:  1회 {x['균형정확도']} %   ·   2회 {y['균형정확도']} %", fontsize=8.6)
out = "report/보고서_그림_순서대로/11_그림6_모델_학습_평가.jpg"
fig.savefig(out, bbox_inches="tight", pad_inches=0.05, facecolor="white", pil_kwargs={"quality": 95}); print(out)
