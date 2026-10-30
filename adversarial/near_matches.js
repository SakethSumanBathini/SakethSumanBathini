// How often could a random copy from outside the codebook (k numbered lines, approved wordings) clear the bar
// for naming some college? Counts copies for which at least one college's evidence beats the outside-copy null
// by ln(ODDS) + ln(N), the decoder's second test. It ignores the runner-up test and typing damage, so it is an
// upper bound on how often the decoder would name an innocent college for such copies.
// Usage: node near_matches.js <app.js> <k> <copies> [odds, default 10000]
'use strict';
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const a = src.indexOf('// ------------------------------------------------------------ question bank');
const b = src.indexOf('// ------------------------------------------------------------ helpers');
const M = new Function(src.slice(a, b).replace(/var REDUCE = [^\n]*\n/, '') + '\nreturn { N, Q, V, POS, VAR, EPS, EPS_V, shuffle, range };')();
const { N, Q, V, POS, VAR, EPS, EPS_V, shuffle, range } = M;
const k = +process.argv[3], copies = +process.argv[4], odds = +process.argv[5] || 10000;
const bar = Math.log(odds) + Math.log(N);
// log-likelihood ratio against the outside-copy null, per line
const posHit = Math.log(1 - EPS) - Math.log(1 / Q), posMiss = Math.log(EPS / (Q - 1)) - Math.log(1 / Q);
const varHit = Math.log(1 - EPS_V) - Math.log(1 / V), varMiss = Math.log(EPS_V / (V - 1)) - Math.log(1 / V);
function mulberry32(s) { return function () { s |= 0; s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const R = mulberry32(424242), ri = n => Math.floor(R() * n);
let hits = 0;
for (let t = 0; t < copies; t++) {
  const p = shuffle(range(Q), R), v = range(Q).map(() => ri(V)), qs = shuffle(range(Q), R).slice(0, k);
  for (let c = 0; c < N; c++) {
    let lr = 0;
    for (const q of qs) lr += (POS[c][q] === p[q] ? posHit : posMiss) + (VAR[c][q] === v[q] ? varHit : varMiss);
    if (lr >= bar) { hits++; break; }
  }
}
console.log(`k=${k}: ${hits} of ${copies} outside copies clear ${odds}-to-1 for some college` + (hits ? ` (about 1 in ${Math.round(copies / hits).toLocaleString('en-US')})` : ''));
