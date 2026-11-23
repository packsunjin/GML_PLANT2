// poster_sections.js — 발표 포스터 절 내용을 절마다 그림 한 장으로 만든다(2026-11-23 처음부터 다시).
// 포스터 글상자 안에서 줄 배치 없는 글 문단은 겹쳐 나와(rhwp 확인), 절 내용을 그림으로 넣는다.
// 쓰는 법(저장소 루트): node report/stim/poster_sections.js report/보고서_그림_순서대로 report/poster_sec
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [G, OUT] = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });
const PF = path.join(path.dirname(G), 'poster_fig');
const figFile = k => k.startsWith('P_') ? path.join(PF, k + '.jpg') : path.join(G, fs.readdirSync(G).find(n => n.startsWith(k)));
// EXPORT=<폴더>: 편집기(아티팩트)용으로 절 HTML 과 CSS 를 JSON 으로 내보낸다(그림은 fig/<키>.jpg 상대 경로).
// OVERRIDE=<json>: 편집기에서 저장한 절 HTML({s1:..}) 로 S 를 바꿔 그린다(fig/<키>.jpg 를 원본 그림으로 바꿈).
const EXPORT = process.env.EXPORT, OVERRIDE = process.env.OVERRIDE;
const src = k => EXPORT ? (fs.mkdirSync(path.join(EXPORT, 'fig'), { recursive: true }), fs.copyFileSync(figFile(k), path.join(EXPORT, 'fig', k + '.jpg')), 'fig/' + k + '.jpg')
  : 'data:image/jpeg;base64,' + fs.readFileSync(figFile(k)).toString('base64');
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
       ${fig('01', '그림1. 식물 전기신호의 주파수 위치와 분석 범위', 78)}`,
  // Ⅲ. 연구방법
  s3: `${fig('02', '그림2. 측정 시스템 구성 — 두 전극의 전위 차이를 재는 DC 결합 측정계')}
       <div class="prow"><figure><img src="${src('03')}">${cap('사진1. 실험 장치 — (가) 패러데이 상자, (나) 상자 밖 회로')}</figure><figure><img src="${src('05')}">${cap('사진2. 측정 회로의 배선')}</figure></div>
       <table class="ms"><tr><th>측정</th><th>길이</th><th>본 것</th></tr>
       <tr><td>회로만 (예비 1단계)</td><td>30분</td><td>회로 표류</td></tr>
       <tr><td>점퍼선 핀 전극, 물속 (예비 2단계)</td><td>60분</td><td>전극 표류</td></tr>
       <tr><td>은선 전극, 물속 (점퍼선 핀과 같은 조건)</td><td>2시간</td><td>전극 표류</td></tr>
       <tr><td>차폐 상자 · 전원 3가지</td><td>120초 × 3</td><td>60 Hz · 0.01–1 Hz 잡음</td></tr>
       <tr><td>정상 (물 준 뒤)</td><td>5.9시간</td><td>기준선 · 잡음</td></tr>
       <tr><td>물 공급 중단 4.0~4.6일째</td><td>14.5시간</td><td>기준선 · 잡음</td></tr>
       <tr><td>손 접촉 (콘센트 · 보조배터리)</td><td>600초 × 2</td><td>잡은 뒤 10초 변화, 감지 모델</td></tr></table>
       <div class="an"><b>분석</b> &nbsp;250 S/s 기록 · 잡음 = 대역 표준편차 · 60 Hz = 푸리에 진폭 ·
       모델 = 2초 조각 → 특징 17개 → SVM · 랜덤 포레스트, 균형 정확도로 평가</div>`,
  // Ⅳ. 연구결과 (앞)
  s4a: card('1. 잡음은 회로가 아니라 전극과 전원선에서',
         `<div class="nums">${num('59.2 · 82.9 mV', '전극 60분 표류 (점퍼선 핀 · 은선)')}${num('<span class="fr"><sup>1</sup><span>27</span></span>', '60 Hz 잡음 (상자 밖 → 차폐 상자 안)')}</div>
          ${fig('06', '그림3. 회로 영점과 전극 표류', 72)}
          ${fig('P_차폐전원_잡음', '그림4. 차폐 상자 · 전원별 잡음 (120초 기록)', 70)}`),
  s4b: card('2. 정상 · 물 공급 중단: 비교하지 못함',
         `<p>같은 화분 · 전극의 긴 기록 다섯 개를 처음 5.9시간씩 비교하면 잡음이 기준 아래인 기록은 <b>하나뿐</b>이었다(나머지 넷은 <b>22~56배</b>). 정상 · 물 공급 중단 어느 쪽에도 잡음이 큰 기록이 있어 같은 조건에서 비교할 수 없었다.</p>
          ${fig('09', '그림5. 긴 기록 다섯 개의 잡음 (처음 5.9시간, 2분마다)', 56)}`) +
       card('3. 손 접촉 감지 모델',
         `<p>손이 잎에 닿을 때 생기는 전압 계단으로 손 접촉 감지 모델을 만들었다(콘센트 전원 기록).</p>
          <div class="pipe"><div>전압 기록</div><i>→</i><div>2초씩 자르기</div><i>→</i><div>특징 17개</div><i>→</i><div>SVM ·<br>랜덤 포레스트</div><i>→</i><div class="o">접촉 /<br>비접촉</div></div>
          ${fig('P_스펙트로그램', '그림6. 손 접촉 기록의 전압과 스펙트로그램 (노란 띠 · 점선 = 잎을 잡은 시각)', 84)}
          <table class="cmp"><tr><th>모델 입력</th><th>SVM</th><th>랜덤 포레스트</th></tr>
          <tr><td>특징 추출 (17개)</td><td><b>99.8 · 95.5 %</b></td><td><b>98.7 · 95.5 %</b></td></tr>
          <tr><td>스펙트로그램 (65 × 31)</td><td>97.4 · 90.8 %</td><td>98.6 · 91.6 %</td></tr></table>
          <p class="note">손 접촉 반응 분류 정확도(균형 정확도), 앞·뒤 절반을 바꿔 2회 평가 · 두 방식 모두 잎을 잡은 9번을 찾았다.</p>`) +
       card('4. 정말 식물 신호일까? 전원을 바꿔 확인',
         `<p>식물 · 전극은 그대로 두고 전원만 보조배터리로 바꿔 봤다. 손 대신 비전도성 물체로 살짝 댄 기록도 같이 봤다.</p>
          <div class="nums">${num('9 / 9', '콘센트, 잎을 잡음<br>약 140 mV 계단')}${num('0 / 10', '콘센트, 비전도성 물체<br>변화 없음')}${num('0 / 10', '보조배터리, 잎을 잡음<br>변화 없음')}${num('0 / 80', '보조배터리<br>모델이 찾은 접촉')}</div>
          ${fig('P_전원별_겹쳐보기', '그림7. 잡은·댄 시각 기준으로 겹쳐 본 전압 (검은 선 = 중앙값)', 86)}
          ${fig('P_모델판정_전원별', '그림8. 같은 모델(특징 추출)의 판정 — (가) 콘센트, (나) 보조배터리', 48)}
          <p class="note">스펙트로그램 SVM은 잡음 수준이 다른 보조배터리 기록 전체를 '접촉'으로 판정했다(랜덤 포레스트는 0 / 80).</p>
          <p class="why">손 접촉 계단은 식물 반응이 아니라 <b>사람 몸과 콘센트 전원 사이의 전기 경로</b>였다. 정확도가 높아도 무엇을 감지하는지는 대조 실험으로 확인해야 한다.</p>`),
  // Ⅴ. 결론 및 제언
  s5: `<ul><li>측정을 제한하는 것은 회로가 아니라 <b>전극 표류와 바깥 전기 잡음</b>이다. 바깥 잡음은 차폐 상자로 줄였지만 전극 표류는 은선으로도 줄지 않았다.</li>
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
ul{margin:0;padding-left:38px} li{margin-bottom:10px}
.fr{display:inline-flex;flex-direction:column;align-items:center;line-height:1;vertical-align:middle;font-size:38px}.fr sup{border-bottom:4px solid #7a4a17;padding:0 10px 3px;vertical-align:baseline;font-size:38px}.fr span{padding-top:2px}
table.cmp{width:100%;border-collapse:collapse;margin:4px 0 6px;font-size:25px;text-align:center}.cmp th{background:#905720;color:#fff;padding:5px}.cmp td{padding:5px;border-bottom:1px solid #e2d6c6}.cmp td:first-child{text-align:left}
.note{font-size:23px;color:#555;margin:2px 0 10px}
table.ms{width:100%;border-collapse:collapse;margin:6px 0 10px;font-size:25px}.ms th{background:#905720;color:#fff;padding:5px 8px;font-weight:700}
.ms td{padding:5px 8px;border-bottom:1px solid #e2d6c6}.row{display:flex;gap:16px;align-items:flex-end}.row figure{flex:1;margin:6px 0 8px}.row img{width:100%;height:300px;object-fit:contain}
.prow{display:flex;gap:14px;justify-content:center;align-items:flex-start;margin:6px 0 12px}.prow figure{margin:0}.prow img{height:230px;width:auto}.prow figcaption{font-size:23px}
.pcap{display:flex;justify-content:center;gap:40px;margin:0 0 12px}.pcap figcaption{font-size:23px}
.ms td:nth-child(2){text-align:center;white-space:nowrap}
.an{font-size:24px;background:#f6efe5;border-radius:10px;padding:8px 12px;margin:0 0 12px;line-height:1.4}
.pipe{display:flex;align-items:center;gap:6px;margin:6px 0 12px}.pipe div{flex:1;background:#f6efe5;border-radius:10px;padding:8px 4px;text-align:center;font-size:23px;line-height:1.25}
.pipe i{font-style:normal;color:#905720;font-weight:700}.pipe .o{background:#905720;color:#fff;font-weight:700}`;
if (OVERRIDE) {
  const o = JSON.parse(fs.readFileSync(OVERRIDE, 'utf8'));
  for (const k of Object.keys(S)) if (typeof o[k] === 'string' && o[k].trim())
    S[k] = o[k].replace(/src="fig\/([^"]+)\.jpg"/g, (m, key) => `src="${src(key)}"`);
}
if (EXPORT) { fs.writeFileSync(path.join(EXPORT, 'sections.json'), JSON.stringify({ S, CSS })); console.log('exported', Object.keys(S).length); process.exit(0); }
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
