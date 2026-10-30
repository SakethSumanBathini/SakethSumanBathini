// Check that the v2 page's decoder makes exactly the same decisions as the 18 Oct decoder (adversarial/app_after.js).
const fs = require('fs');
function load(path) {
  const src = fs.readFileSync(path, 'utf8');
  const a = src.indexOf('// ------------------------------------------------------------ question bank');
  const b = src.indexOf('// ------------------------------------------------------------ helpers');
  const body = src.slice(a, b).replace(/var REDUCE = [^\n]*\n/, '');
  return new Function('window', body + '\nreturn { makeLeak, parseLeak, decode, N };')({ matchMedia: null });
}
const A = load(__dirname + '/app_after.js');
const B = load(process.argv[2]);
let same = 0, total = 0;
const settings = [{ num: 'paper' }, { num: 'none' }, { num: 'own' }, { num: 'paper', reword: true }, { num: 'none', shuffle: true }, { num: 'paper', mix: true }];
let seed = 7; Math.random = function () { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
for (const o of settings) for (let k = 3; k <= 10; k++) for (let t = 0; t < 40; t++) {
  const lk = A.makeLeak(Math.floor(Math.random() * A.N), k, Object.assign({ typos: true }, o));
  const ra = A.decode(A.parseLeak(lk.text)), rb = B.decode(B.parseLeak(lk.text));
  total++;
  if (ra.status === rb.status && JSON.stringify(ra.named) === JSON.stringify(rb.named) && ra.order[0] === rb.order[0] && Math.abs(ra.gap - rb.gap) < 1e-9) same++;
}
console.log('identical decisions:', same, 'of', total);
