import sys, numpy as np, pandas as pd
from scipy import signal
d = pd.read_csv(sys.argv[1]); t = d.timestamp_sec.values; v = d.voltage.values*1000
dt = np.diff(t)
print("행", len(t), "길이 %.1f s = %.2f h" % (t[-1]-t[0], (t[-1]-t[0])/3600), "평균 fs %.2f" % ((len(t)-1)/(t[-1]-t[0])))
print("시간 역행", (dt<=0).sum(), "0.1s 넘는 빈곳", (dt>0.1).sum(), "최대 간격 %.3f" % dt.max())
for i in np.where(dt>0.1)[0][:10]: print("  빈곳", round(t[i],1), "→", round(t[i+1],1))
print("포화(|v|>2040)", (np.abs(v)>2040).sum(), "범위 %.1f~%.1f mV" % (v.min(), v.max()))
# 30분 평균·0.01–1 Hz sd
fs=250; n=25
m=len(v)//n*n; v10=v[:m].reshape(-1,n).mean(1); t10=t[:m].reshape(-1,n).mean(1)
b,a=signal.butter(4,[0.01,1],btype="band",fs=10); f=signal.filtfilt(b,a,v10)
print("구간(시) 평균mV  0.01–1Hz sd")
for h in np.arange(0, t[-1]/3600, 1):
    s=(t10>=h*3600)&(t10<(h+1)*3600)
    if s.sum()>100: print(" %4.0f  %8.1f  %5.2f" % (h, v10[s].mean(), f[s].std()))
# 2초 사이 20 mV 넘는 변화
v1=v10[:len(v10)//20*20].reshape(-1,20).mean(1)  # 2초 평균
jumps=np.abs(np.diff(v1)); print("2초 평균 사이 20 mV 넘는 변화", (jumps>20).sum(), "5 mV 넘음", (jumps>5).sum())
# 60초 주기 튐: 60초 위상별 표본간 변화
dv=np.abs(np.diff(v)); ph=(t[1:]%60)
hist=[np.median(dv[(ph>=k)&(ph<k+0.5)]) for k in np.arange(0,60,0.5)]
k=int(np.argmax(hist)); print("60초 위상별 표본간 변화 중앙값: 최대 %.2f mV(위상 %.1f s), 전체 중앙값 %.2f" % (max(hist), k*0.5, np.median(hist)))
mx=[np.percentile(dv[(ph>=k)&(ph<k+0.5)],99.9) for k in np.arange(0,60,0.5)]
k=int(np.argmax(mx)); print("60초 위상별 99.9%% 분위: 최대 %.2f mV(위상 %.1f s), 중앙 %.2f" % (max(mx), k*0.5, np.median(mx)))
