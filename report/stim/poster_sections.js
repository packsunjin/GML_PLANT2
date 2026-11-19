// poster_sections.js — 포스터 Ⅰ~Ⅴ 절 내용을 절마다 그림 한 장(JPG)으로 만든다(2026-11-19).
// 포스터 글상자 안에서는 줄 배치 정보 없는 글 문단이 겹쳐 나와(rhwp 확인), 절 내용을 그림으로 넣는다.
// 쓰는 법(저장소 루트): node report/stim/poster_sections.js report/보고서_그림_순서대로 report/poster_sec
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [G, OUT] = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });
const f = k => 'data:image/jpeg;base64,' + fs.readFileSync(path.join(G, fs.readdirSync(G).find(n => n.startsWith(k)))).toString('base64');
const fig = (k, cap, w = 100) => `<figure><img src="${f(k)}" style="width:${w}%"><figcaption><b>${cap.split(' ')[0]}</b> ${cap.split(' ').slice(1).join(' ')}</figcaption></figure>`;
const S = {
  s1: `<p>식물은 상처·온도 변화 같은 자극을 받으면 세포막 전위가 바뀌고, 그 변화가 줄기를 따라 전달된다. 이 신호로 식물의 상태(정상·자극·수분부족)를 실시간으로 알아내는 시스템을 만들고자 했다.</p>
       <p class="q"><b>연구문제 1.</b> 저가 부품으로 만든 측정계가 식물 전기신호를 잴 만큼 정밀한가?</p>
       <p class="q"><b>연구문제 2.</b> 그 측정계로 수분부족과 자극 반응을 정상 상태와 구분할 수 있는가?</p>`,
  s2: `<p>식물의 활동전위는 수십 mV 크기로 수십 초 이어진다. 잎을 붓으로 건드리면 33.9 mV의 활동전위가 접촉 뒤 늦게 도착한다(Degli Agosti, 2014). 수분 스트레스는 수 시간 이상에 걸친 느린 변화다.</p>
       ${fig('01', '그림1. 식물 전기신호의 주파수 위치와 측정계·분석 범위')}
       <p>물 공급 조건을 전기신호로 분류한 선행 연구는 1 cm 간격 전극과 접지한 금속 상자를 썼다(de Toledo 외, 2024).</p>`,
  s3: `${fig('02', '그림2. 측정 시스템 구성')}
       <ol><li>회로 → 전극 → 식물 순서로 하나씩 더해 오차의 출처를 쟀다(예비 실험).</li>
       <li>은선 전극, 패러데이 상자, 보조배터리 전원으로 잡음을 줄였다.</li>
       <li>정상과 물 공급 중단 상태를 각각 기록했다.</li>
       <li>같은 식물·전극에서 전원만 바꿔 잎을 잡는 손 접촉 실험을 하고, 손 접촉 감지 모델을 학습해 대조 기록에 적용했다.</li></ol>
       ${fig('03', '사진1. 본 실험 장치 — (가) 패러데이 상자, (나) 상자 밖 회로와 라즈베리파이', 92)}
       <div class="row"><figure><img src="${f('04')}"><figcaption><b>사진2.</b> 줄기에 꽂은 은선 전극</figcaption></figure>
       <figure><img src="${f('05')}"><figcaption><b>사진3.</b> 측정 회로의 배선</figcaption></figure></div>`,
  s4: `<h4>1. 전극과 잡음</h4>
       <p>점퍼선 핀 전극은 물속 60분에 <b>59.20 mV</b> 표류했고, 은선으로 바꾸자 <b>0.02 mV</b>로 줄었다. 60 Hz 잡음은 차폐 상자로 약 <b>27분의 1</b>로 줄어, 식물에서 14.5시간 동안 0.01–1 Hz 잡음 0.03 mV인 기록을 얻었다.</p>
       ${fig('06', '그림3. 회로 영점과 전극 표류')}
       <h4>2. 정상·물 공급 중단</h4>
       <p>기록한 날마다 잡음 수준이 약 47배 달라 같은 조건에서 비교하지 못했다.</p>
       <h4>3. 전원별 손 접촉</h4>
       <p>보조배터리 전원에서는 잎을 10번 잡아도 변화가 없었고, 콘센트 전원에서는 9번 모두 약 <b>140 mV</b> 계단이 생겼다. 손 접촉 신호는 식물이 아니라 사람 몸과 전원 사이의 전기 경로에서 왔다.</p>
       ${fig('10', '그림5. 전원별 손 접촉 기록 — (가) 보조배터리, (나) 콘센트')}
       <h4>4. 손 접촉 감지 모델</h4>
       <p>식물 신호가 아님을 확인한 뒤에도 모델을 만든 이유는 둘이다. 정확도가 높은 모델이 식물 반응을 읽는 것처럼 보일 수 있는지, 그리고 대조 기록으로 이를 가려낼 수 있는지 확인하고, 손이 닿았는지를 실시간 화면과 부스 체험에 쓰기 위해서다.</p>
       <p>균형 정확도 <b>95.5~99.8 %</b>로 손이 닿았는지를 감지했다. 같은 모델을 보조배터리 기록에 쓰면 잎을 잡은 창 80개 중 0개를 찾았다.</p>
       ${fig('11', '그림6. 손 접촉 감지 모델의 학습·평가')}`,
  s5: `<ul><li>측정을 제한하는 것은 회로가 아니라 전극 표류와 바깥 전기 잡음이며, 둘 다 저가 부품으로 줄일 수 있었다.</li>
       <li>손 접촉 신호는 식물의 반응이 아니라 전기 경로에서 온 것이었다. 정확도가 높은 모델도 무엇을 감지하는지 대조 실험으로 확인해야 한다.</li>
       <li>제언: 자극 시각 자동 기록, 흙만 재는 음성 대조와 화상 양성 대조, 상태마다 두 회차 이상 기록</li></ul>`,
};
const CSS = `body{margin:0;background:#fff}
.sec{width:1040px;padding:6px 4px;font-family:'Noto Serif CJK KR',serif;font-size:31px;line-height:1.55;color:#111;word-break:keep-all}
p{margin:0 0 14px;text-align:justify} .q{margin-bottom:6px}
h4{font-family:'Noto Sans CJK KR',sans-serif;font-size:32px;color:#905720;margin:18px 0 6px}
figure{margin:10px 0 18px;text-align:center} img{display:block;margin:0 auto}
figcaption{font-size:27px;}
.row{display:flex;gap:18px;align-items:flex-end}.row figure{flex:1;margin:6px 0 10px}.row img{width:100%;height:330px;object-fit:contain}
figcaption{margin-top:8px;line-height:1.35} ol,ul{margin:0 0 6px;padding-left:44px} li{margin-bottom:10px}`;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1060, height: 800 }, deviceScaleFactor: 3 });
  for (const [k, html] of Object.entries(S)) {
    await p.setContent(`<style>${CSS}</style><div class="sec" id="s">${html}</div>`);
    await p.waitForTimeout(300);
    const el = await p.$('#s'); const bb = await el.boundingBox();
    await el.screenshot({ path: path.join(OUT, k + '.png') });
    console.log(k, Math.round(bb.height), 'px');
  }
  await b.close();
})();
