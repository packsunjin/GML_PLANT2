import sys,numpy as np,pandas as pd,matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
plt.rcParams["font.family"]="WenQuanYi Zen Hei"; plt.rcParams["axes.unicode_minus"]=False
def load(p): return pd.read_csv(p).iloc[:,1].values.reshape(-1,25).mean(1)*1000  # 0.1 s, mV
n=load(sys.argv[1]); a=load(sys.argv[2]); out=sys.argv[3]
import csv
presses=[float(r[2]) for r in csv.reader(l for l in open(sys.argv[4],encoding="utf-8") if not l.startswith("#")) if r[0]!="n"]
step_t=[138.3,672.3,853.9,1033.5]
fig=plt.figure(figsize=(9.4,7.2),dpi=300)
gs=fig.add_gridspec(3,1,height_ratios=[1,1,1.15],hspace=0.55)
t=np.arange(len(n))/600
ax=fig.add_subplot(gs[0]); ax.plot(t,n,color="#2b6cb0",lw=0.6)
ax.set_title("(가) 정상 1회차 — 아무것도 하지 않음",loc="left",fontsize=10)
ax.set_xlim(0,30); ax.set_ylabel("전위 (mV)"); ax.set_xlabel("시간 (분)")
ax=fig.add_subplot(gs[1]); ax.plot(np.arange(len(a))/600,a,color="#2b6cb0",lw=0.6)
for p in presses: ax.axvline(p/60,color="#c05621" if (p in step_t) else "#a0aec0",lw=0.8,ls="--")
ax.set_title("(나) 자극 1회차 — 세로 점선이 누른 시각 (주황: 직후 계단이 생긴 4번)",loc="left",fontsize=10)
ax.set_xlim(0,30); ax.set_ylabel("전위 (mV)"); ax.set_xlabel("시간 (분)")
ax=fig.add_subplot(gs[2]); tt=np.arange(-200,1200)/10
for p in presses[:9]:
    i=int(round(p*10)); seg=a[i-200:i+1200]-np.median(a[i-300:i-100])
    hit=(p in step_t)
    ax.plot(tt,seg,color="#c05621" if hit else "#a0aec0",lw=0.9 if hit else 0.7,zorder=3 if hit else 2)
ax.axvline(0,color="k",lw=0.8); ax.axvspan(-10,0,color="#fbd38d",alpha=0.5,lw=0)
ax.set_title("(다) 누른 시각 기준으로 겹친 9번 (기록 시각 30~10초 전 중앙값을 0으로 맞춤, 노란 띠: 기록 지연으로 실제로 누른 시각일 수 있는 10초)",loc="left",fontsize=10)
ax.set_xlim(-20,120); ax.set_xlabel("스톱워치에 기록한 시각 뒤 시간 (초)"); ax.set_ylabel("변화 (mV)")
for ax in fig.axes: ax.grid(alpha=0.3,lw=0.5); ax.tick_params(labelsize=8)
fig.savefig(out,bbox_inches="tight")
