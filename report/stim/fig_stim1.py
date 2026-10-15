import sys,numpy as np,pandas as pd,matplotlib,matplotlib.patches
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
ax.set_title("(나) 자극 1회차 — 세로 점선: 누른 시각",loc="left",fontsize=10)
from matplotlib.lines import Line2D
H=[Line2D([],[],color="#c05621",lw=1.2,ls="--",label="누른 순간 계단이 생김 (4번)"),Line2D([],[],color="#a0aec0",lw=1.2,ls="--",label="누른 순간 변화 없음 (6번)")]
ax.legend(handles=H,loc="upper left",fontsize=8,frameon=True)
ax.set_xlim(0,30); ax.set_ylabel("전위 (mV)"); ax.set_xlabel("시간 (분)")
ax=fig.add_subplot(gs[2]); tt=np.arange(-200,1200)/10
for p in presses[:9]:
    i=int(round(p*10)); seg=a[i-200:i+1200]-np.median(a[i-300:i-100])
    hit=(p in step_t)
    ax.plot(tt,seg,color="#c05621" if hit else "#a0aec0",lw=0.9 if hit else 0.7,zorder=3 if hit else 2)
ax.axvline(0,color="k",lw=0.8); ax.axvspan(-10,0,color="#fbd38d",alpha=0.5,lw=0)
ax.set_title("(다) 스톱워치에 기록한 시각을 0초에 맞춰 9번을 겹쳐 그림",loc="left",fontsize=10)
H2=[Line2D([],[],color="#c05621",lw=1.2,label="누른 순간 계단이 생김 (4번)"),Line2D([],[],color="#a0aec0",lw=1.2,label="누른 순간 변화 없음 (5번)"),matplotlib.patches.Patch(color="#fbd38d",alpha=0.6,label="실제로 누른 순간이 있는 구간 (기록이 최대 10초 늦음)")]
ax.set_ylim(-36,30); ax.legend(handles=H2,loc="lower center",ncol=2,fontsize=8,frameon=True)
ax.set_xlim(-20,120); ax.set_xlabel("스톱워치에 기록한 시각 뒤 시간 (초)"); ax.set_ylabel("변화 (mV)")
for ax in fig.axes: ax.grid(alpha=0.3,lw=0.5); ax.tick_params(labelsize=8)
fig.savefig(out,bbox_inches="tight")
