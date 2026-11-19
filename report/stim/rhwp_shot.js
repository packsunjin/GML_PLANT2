// SVG 쪽들을 PNG 로 찍고 한 장에 모아 본다. node shot.js <svg 폴더> <출력 png>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [dir, out] = process.argv.slice(2);
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.svg')).sort();
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 2400, height: 1800 }, deviceScaleFactor: 1 });
  const cells = files.map(f => `<div style="display:inline-block;margin:6px;border:1px solid #999;width:340px;vertical-align:top;background:#fff">
     <img src="data:image/svg+xml;base64,${fs.readFileSync(path.join(dir, f)).toString('base64')}" style="width:340px"><div style="font:14px sans-serif;text-align:center">${f}</div></div>`).join('');
  await p.setContent(`<body style="margin:0;background:#ddd;width:2400px">${cells}</body>`);
  await p.waitForTimeout(1500);
  await p.screenshot({ path: out, fullPage: true });
  for (const f of files) {           // 쪽마다 크게도 저장
    await p.setContent(`<body style="margin:0;background:#fff"><img src="data:image/svg+xml;base64,${fs.readFileSync(path.join(dir, f)).toString('base64')}" style="width:900px"></body>`);
    await p.waitForTimeout(300);
    await p.screenshot({ path: path.join(dir, f.replace('.svg', '.png')), fullPage: true });
  }
  await b.close();
})();
