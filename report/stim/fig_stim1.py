import sys,numpy as np,pandas as pd,matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
plt.rcParams["font.family"]="WenQuanYi Zen Hei"; plt.rcParams["axes.unicode_minus"]=False
def load(p): return pd.read_csv(p).iloc[:,1].values.reshape(-1,25).mean(1)*1000  # 0.1 s, mV
n=load(sys.argv[1]); a=load(sys.argv[2]); out=sys.argv[3]
presses=[126+180*k for k in range(10)]; step={126,665,848,1027}
step_t=[126,665,848,1027]
fig=plt.figure(figsize=(9.4,7.2),dpi=300)
gs=fig.add_gridspec(3,1,height_ratios=[1,1,1.15],hspace=0.55)
t=np.arange(len(n))/600
ax=fig.add_subplot(gs[0]); ax.plot(t,n,color="#2b6cb0",lw=0.6)
ax.set_title("(가) 정상 1회차 — 아무것도 하지 않음",loc="left",fontsize=10)
ax.set_xlim(0,30); ax.set_ylabel("전위 (mV)"); ax.set_xlabel("시간 (분)")
ax=fig.add_subplot(gs[1]); ax.plot(np.arange(len(a))/600,a,color="#2b6cb0",lw=0.6)
for p in presses: ax.axvline(p/60,color="#c05621" if any(abs(p-s)<=3 for s in step_t) else "#a0aec0",lw=0.8,ls="--")
ax.set_title("(나) 자극 1회차 — 세로 점선이 누른 시각 (주황: 직후 계단이 생긴 4번)",loc="left",fontsize=10)
ax.set_xlim(0,30); ax.set_ylabel("전위 (mV)"); ax.set_xlabel("시간 (분)")
ax=fig.add_subplot(gs[2]); tt=np.arange(-200,1200)/10
for p in presses[:9]:
    i=int(p*10); seg=a[i-200:i+1200]-np.median(a[i-200:i])
    hit=any(abs(p-s)<=3 for s in step_t)
    ax.plot(tt,seg,color="#c05621" if hit else "#a0aec0",lw=0.9 if hit else 0.7,zorder=3 if hit else 2)
ax.axvline(0,color="k",lw=0.8); ax.axvspan(0,3,color="#fbd38d",alpha=0.5,lw=0)
ax.set_title("(다) 누른 시각 기준으로 겹친 9번 (누르기 전 20초 중앙값을 0으로 맞춤, 노란 띠: 누른 뒤 3초)",loc="left",fontsize=10)
ax.set_xlim(-20,120); ax.set_xlabel("누른 뒤 시간 (초)"); ax.set_ylabel("변화 (mV)")
for ax in fig.axes: ax.grid(alpha=0.3,lw=0.5); ax.tick_params(labelsize=8)
fig.savefig(out,bbox_inches="tight")
