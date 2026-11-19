import fs from 'fs';
import { initSync, HwpDocument } from '@rhwp/core';
initSync({ module: fs.readFileSync('node_modules/@rhwp/core/rhwp_bg.wasm') });
const [src, out] = process.argv.slice(2);
const doc = new HwpDocument(new Uint8Array(fs.readFileSync(src)));
console.log('before', doc.pageCount(), 'reflowed', doc.reflowLinesegs(), 'after', doc.pageCount());
fs.writeFileSync(out + '.hwpx', doc.exportHwpx());
try { fs.writeFileSync(out + '.hwp', doc.exportHwp()); console.log('hwp ok'); } catch (e) { console.log('hwp fail', String(e).slice(0, 200)); }
fs.mkdirSync(out + '_svg', { recursive: true });
for (let i = 0; i < doc.pageCount(); i++) fs.writeFileSync(`${out}_svg/p${String(i + 1).padStart(2, '0')}.svg`, doc.renderPageSvg(i));
for (const ext of ['hwpx', 'hwp']) {
  try { const d2 = new HwpDocument(new Uint8Array(fs.readFileSync(out + '.' + ext))); console.log('reload', ext, d2.pageCount()); }
  catch (e) { console.log('reload fail', ext, String(e).slice(0, 120)); }
}
