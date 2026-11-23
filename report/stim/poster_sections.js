// poster_sections.js — 발표 포스터 절 내용을 절마다 그림 한 장으로 만든다(2026-11-23 처음부터 다시).
// 포스터 글상자 안에서 줄 배치 없는 글 문단은 겹쳐 나와(rhwp 확인), 절 내용을 그림으로 넣는다.
// 쓰는 법(저장소 루트): node report/stim/poster_sections.js report/보고서_그림_순서대로 report/poster_sec
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [G, OUT] = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });
const src = k => 'data:image/jpeg;base64,' + fs.readFileSync(path.join(G, fs.readdirSync(G).find(n => n.startsWith(k)))).toString('base64');
const cap = c => { const [n, ...r] = c.split(' '); return `<figcaption><b>${n}</b> ${r.join(' ')}</figcaption>`; };
const fig = (k, c, w = 100) => `<figure><img src="${src(k)}" style="width:${w}%">${cap(c)}</figure>`;
const num = (v, l) => `<div class="num"><div class="v">${v}</div><div class="l">${l}</div></div>`;
const card = (t, body) => `<div class="card"><div class="ct">${t}</div>${body}</div>`;

const S = {
  // Ⅰ. 서론
  s1: `<p>식물은 자극을 받으면 세포막 전위가 바뀌고, 이 변화가 줄기를 따라 전달된다.
       이 전기신호로 식물의 상태를 실시간으로 알아내는 '식물 번역기'를 만들고자 했다.</p>
       <div class="goal">목표 &nbsp;|&nbsp; 전기신호로 <b>정상 · 자극 · 수분부족</b> 실시간 분류</div>
       <div class="rq"><span>연구문제 1</span>저가 부품 측정계가 식물 전기신호를 잴 만큼 정밀한가?</div>
       <div class="rq"><span>연구문제 2</span>수분부족과 자극 반응을 정상 상태와 구분할 수 있는가?</div>`,
  // Ⅱ. 이론적 배경 및 선행 연구
  s2: `<table class="kv">
       <tr><th>활동전위</th><td>수십 mV · 수십 초</td></tr>
       <tr><th>붓 접촉 반응</th><td>33.9 mV, 접촉 뒤 <b>늦게</b> 도착 (Degli Agosti, 2014)</td></tr>
       <tr><th>수분 스트레스</th><td>수 시간 이상 걸리는 느린 변화</td></tr>
       <tr><th>선행 연구 측정</th><td>1 cm 간격 전극 + 접지한 금속 상자 (de Toledo 외, 2024)</td></tr></table>
       ${fig('01', '그림1. 식물 전기신호의 주파수 위치와 분석 범위')}`,
  // Ⅲ. 연구방법
  s3: `${fig('02', '그림2. 측정 시스템 구성 — 두 전극의 전위 차이를 재는 DC 결합 측정계')}
       <div class="flow">
         <div><b>1</b>회로 → 전극 → 식물<br>순서로 오차 측정</div>
         <div><b>2</b>은선 전극 · 차폐 상자<br>· 보조배터리</div>
         <div><b>3</b>정상 · 물 공급 중단<br>기록</div>
         <div><b>4</b>전원 바꿔 손 접촉<br>+ 감지 모델</div></div>
       ${fig('03', '사진1. 본 실험 장치 — (가) 패러데이 상자, (나) 상자 밖 회로', 94)}`,
  // Ⅳ. 연구결과 (앞: 왼쪽 칸 아래)
  s4a: card('1. 잡음은 회로가 아니라 전극과 전원선에서',
         `<div class="nums">${num('59.20 → 0.02 mV', '전극 60분 표류 (점퍼선 핀 → 은선)')}${num('약 1/27', '60 Hz 잡음 (차폐 상자)')}</div>
          ${fig('06', '그림3. 회로 영점과 전극 표류')}`),
  // Ⅳ. 연구결과 (뒤: 오른쪽 칸 위)
  s4b: card('2. 정상 · 물 공급 중단: 비교하지 못함',
         `<p>기록한 날마다 잡음이 <b>약 47배</b> 달라 같은 조건에서 비교할 수 없었다.</p>
          ${fig('09', '그림4. 날짜별 잡음 수준')}`) +
       card('3. 손 접촉 신호의 정체: 전원을 바꿔 확인',
         `<div class="nums">${num('0 / 10', '보조배터리 전원 — 잎을 잡아도 변화 없음')}${num('9 / 9 · 약 140 mV', '콘센트 전원 — 잡을 때마다 계단')}</div>
          <p>식물·전극은 그대로 두고 전원만 바꿨는데 반응이 생기고 사라졌다. → 식물이 아니라 <b>사람 몸과 전원 사이의 전기 경로</b>.</p>
          ${fig('10', '그림5. 전원별 손 접촉 기록', 88)}`) +
       card('4. 손 접촉 감지 모델: 정확도와 대조',
         `<p class="why">왜 만들었나? 정확도가 높은 모델이 식물 반응을 읽는 것처럼 보일 수 있는지, 대조 기록으로 가려낼 수 있는지 확인하려고. 손이 닿았는지는 실시간 화면 · 부스 체험에도 쓸 수 있다.</p>
          <div class="nums">${num('95.5~99.8 %', '콘센트 기록 균형 정확도')}${num('0 / 80', '보조배터리 기록 — 잡은 창 판정')}</div>
          ${fig('11', '그림6. 손 접촉 감지 모델의 학습 · 평가')}`),
  // Ⅴ. 결론 및 제언
  s5: `<ul><li>측정을 제한하는 것은 회로가 아니라 <b>전극 표류와 바깥 전기 잡음</b>이며, 둘 다 저가 부품으로 줄일 수 있었다.</li>
       <li>손 접촉 신호는 식물이 아니라 <b>전기 경로</b>에서 왔다. 정확도가 높아도 무엇을 감지하는지는 <b>대조 실험</b>으로 확인해야 한다.</li>
       <li>제언: 자극 시각 자동 기록, 흙만 재는 음성 대조 · 화상 양성 대조, 상태마다 두 회차 이상 기록</li></ul>`,
};
const CSS = `body{margin:0;background:#fff}
.sec{width:1040px;padding:4px 4px 2px;font-family:'Noto Sans CJK KR',sans-serif;font-size:30px;line-height:1.5;color:#1c1c1c;word-break:keep-all}
p{margin:0 0 12px} b{color:#7a4a17}
.goal{margin:10px 0 14px;padding:14px 20px;border:3px solid #905720;border-radius:12px;font-size:32px;text-align:center}
.rq{margin:8px 0;display:flex;gap:16px;align-items:baseline}.rq span{flex:none;background:#905720;color:#fff;border-radius:8px;padding:2px 12px;font-size:26px;font-weight:700}
table.kv{width:100%;border-collapse:collapse;margin:4px 0 12px;font-size:28px}
.kv th{width:30%;text-align:left;color:#7a4a17;padding:7px 8px;border-bottom:1px solid #e2d6c6;font-weight:700;vertical-align:top}
.kv td{padding:7px 8px;border-bottom:1px solid #e2d6c6}
figure{margin:10px 0 14px;text-align:center} img{display:block;margin:0 auto}
figcaption{font-size:25px;margin-top:6px;line-height:1.35;color:#333} figcaption b{color:#1c1c1c}
.flow{display:flex;gap:10px;margin:8px 0 14px}.flow div{flex:1;background:#f6efe5;border-radius:10px;padding:10px 8px;text-align:center;font-size:24px;line-height:1.35}
.flow b{display:block;font-size:34px;color:#905720}
.card{border:2px solid #e2d6c6;border-radius:14px;padding:12px 16px 4px;margin:0 0 16px}
.ct{font-weight:700;font-size:32px;color:#905720;margin-bottom:8px}
.nums{display:flex;gap:12px;margin:4px 0 10px}.num{flex:1;background:#f6efe5;border-radius:10px;padding:10px 12px;text-align:center}
.num .v{font-size:40px;font-weight:700;color:#7a4a17;line-height:1.2}.num .l{font-size:23px;color:#444;line-height:1.3;margin-top:4px}
.why{font-size:26px;color:#444;background:#faf7f2;border-left:6px solid #905720;padding:8px 12px}
ul{margin:0;padding-left:38px} li{margin-bottom:10px}`;
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
