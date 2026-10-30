// Adversarial breakdown sweep for Leak Trace.
// Uses the exact matcher and decoder that run in the live demo (app.js), loaded from the site files.
// Usage: node sweep.js <path-to-app.js> <leaks-per-cell> <out.json> [odds to name a college; default: as set in app.js] [seed]
// Optional: ONLY=<regex on group:mode:k> to run some cells only.
'use strict';
const fs = require('fs');
const [,, appPath, perCellArg, outPath, oddsArg, seedArg] = process.argv;
const PER = +perCellArg || 1000;
const ODDS = +oddsArg || 0;

// ---- load the demo's pure decoding code (question bank .. decoder) from app.js
const src = fs.readFileSync(appPath, 'utf8');
const a = src.indexOf('// ------------------------------------------------------------ question bank');
const b = src.indexOf('// ------------------------------------------------------------ helpers');
let core = src.slice(a, b).replace(/var REDUCE = [^\n]*\n/, '');
if (ODDS) {
  if (/var ODDS = [0-9]+/.test(core)) core = core.replace(/var ODDS = [0-9]+/, 'var ODDS = ' + ODDS);
  else if (core.indexOf('TAU = Math.log(1000)') >= 0) core = core.replace('TAU = Math.log(1000)', 'TAU = Math.log(' + ODDS + ')');
  else throw new Error('naming bar not found in ' + appPath);
}
const M = new Function(core + '\nreturn { BANK: BANK, N: N, Q: Q, V: V, POS: POS, VAR: VAR, TAU: TAU, parseLeak: parseLeak, decode: decode, shuffle: shuffle, range: range };')();
const { BANK, N, Q, V, POS, VAR, TAU, parseLeak, decode, shuffle, range } = M;
const oddsUsed = Math.round(Math.exp(TAU));

// ---- seeded RNG for repeatable runs
function mulberry32(s) { return function () { s |= 0; s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
let R = mulberry32(+seedArg || 20261018);
const ri = n => Math.floor(R() * n);

// ---- paraphrases that are NOT approved wordings (a leaker rewording to dodge the trace)
const PARA = [
  ['Explain an ADT and give an example of one.', 'What do we mean by an abstract data type? Illustrate with an example.'],
  ['Distinguish between stacks and queues.', 'List the differences between a queue and a stack.'],
  ['What is the running time of binary search?', 'How efficient is binary search in terms of time complexity?'],
  ['Describe a circular linked list.', 'Briefly explain circular linked lists.'],
  ['Change A + B * C into postfix notation.', 'Find the postfix expression for A + B * C.'],
  ['State two uses of priority queues.', 'Where are priority queues used? Give two examples.'],
  ['Explain the term height of a binary tree.', 'How is the height of a binary tree defined?'],
  ['Define hashing. Mention one way to resolve collisions.', 'What is meant by hashing? State a collision resolution method.'],
  ['Compare BFS and DFS.', 'Distinguish breadth-first search from depth-first search.'],
  ['Explain what a minimum spanning tree is.', 'Define the term minimum spanning tree.']
];

// ---- character-level damage at rate r (deletions, substitutions, duplications), plus sloppy case/punctuation
function damage(s, r) {
  const L = 'abcdefghijklmnopqrstuvwxyz'; let out = '';
  for (let i = 0; i < s.length; i++) {
    const u = R();
    if (u < r / 3) continue;
    if (u < 2 * r / 3) { out += L[ri(26)]; continue; }
    out += s[i]; if (u < r) out += s[i];
  }
  if (R() < 0.5) out = out.toLowerCase().replace(/[?.]/g, '');
  return out;
}

// ---- one leak
// mode: numbered | plain (no numbers, paper order) | renumbered (1..k in paper order) | shuffled (no numbers, random order)
//       para (paraphrased, no numbers) | para-num (paraphrased, real numbers) | first (the paper's first k questions, real numbers)
function makeLeak(opt) {
  const k = opt.k, r = opt.noise || 0;
  let sources, posOf, varOf;
  if (opt.outside) {                              // a copy from a college that is not in the codebook
    const p = shuffle(range(Q), R), v = range(Q).map(() => ri(V));
    sources = []; posOf = () => p; varOf = () => v;
  } else {
    const s0 = ri(N); sources = [s0];
    if (opt.mix) { let s1; do { s1 = ri(N); } while (s1 === s0); sources.push(s1); }
    posOf = s => POS[s]; varOf = s => VAR[s];
  }
  const qs = opt.mode === 'first' ? range(Q).filter(q => posOf(sources[0])[q] < k) : shuffle(range(Q), R).slice(0, k);
  let items = qs.map(q => { const s = sources.length ? sources[ri(sources.length)] : -1; return { q, slot: posOf(s)[q], v: varOf(s)[q] }; });
  items.sort((x, y) => x.slot - y.slot || x.q - y.q);
  if (opt.mode === 'shuffled') items = shuffle(items, R);
  const para = opt.mode === 'para' || opt.mode === 'para-num';
  const lines = items.map((it, i) => {
    let t = para ? PARA[it.q][ri(2)] : BANK[it.q][it.v];
    if (r > 0) t = damage(t, r);
    if (opt.mode === 'numbered' || opt.mode === 'para-num' || opt.mode === 'first') return (it.slot + 1) + '. ' + t;
    if (opt.mode === 'renumbered') return (i + 1) + '. ' + t;
    return t;
  });
  return { text: lines.join('\n'), sources };
}

function cell(opt) {
  let named = 0, wrong = 0, held = 0, top5 = 0, recog = 0, lines = 0, both = 0;
  const wrongCases = [];
  for (let i = 0; i < PER; i++) {
    const lk = makeLeak(opt), parsed = parseLeak(lk.text), res = decode(parsed);
    lines += parsed.length; recog += parsed.filter(p => p.q !== null).length;
    if (res.status === 'named') {
      if (res.named.some(n => lk.sources.indexOf(n) < 0)) {
        wrong++;
        // keep the evidence: does the named college's code match the leak exactly?
        const c = res.named.find(n => lk.sources.indexOf(n) < 0), items = parsed.filter(p => p.q !== null);
        const posMatch = items.filter(p => p.num !== null && POS[c][p.q] === p.num - 1).length, varMatch = items.filter(p => VAR[c][p.q] === p.v).length;
        wrongCases.push({ leak: i, text: lk.text, sources: lk.sources, named: res.named, stage: res.stage, lines: items.length, namedCollegeMatchesPositions: posMatch, namedCollegeMatchesWordings: varMatch });
      } else { named++; if (lk.sources.length > 1 && res.named.length > 1) both++; }
    } else held++;
    if (res.order && lk.sources.some(s => res.order.indexOf(s) < 5)) top5++;
  }
  const pc = x => +(100 * x / PER).toFixed(2);
  return Object.assign({}, opt, { leaks: PER, odds: oddsUsed, named: pc(named), wrong: pc(wrong), wrongCount: wrong, held: pc(held), top5: pc(top5), bothNamed: pc(both), recognisedLines: +(100 * recog / Math.max(1, lines)).toFixed(1), wrongCases });
}

const plan = [];
if (process.env.PLAN === 'noise') {
  // supplementary: typing damage at the smallest leaks the strict bar names (5 numbered, 7 or 8 un-numbered lines)
  for (const [mode, k] of [['numbered', 5], ['plain', 7], ['plain', 8]]) for (const noise of [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4]) plan.push({ group: 'noise', mode, k, noise });
} else {
for (const mode of ['numbered', 'plain']) for (const noise of [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4]) plan.push({ group: 'noise', mode, k: 6, noise });
for (const k of [4, 5, 6, 7, 8, 10]) for (const mode of ['numbered', 'plain', 'renumbered', 'shuffled', 'para', 'para-num']) plan.push({ group: 'attack', mode, k, noise: 0.04 });
for (const k of [4, 5, 6, 8]) plan.push({ group: 'first', mode: 'first', k, noise: 0.04 });
for (const k of [6, 8, 10]) plan.push({ group: 'mix', mode: 'numbered', k, noise: 0.04, mix: true });
plan.push({ group: 'mix', mode: 'plain', k: 10, noise: 0.04, mix: true });
for (const mode of ['numbered', 'plain', 'renumbered', 'para']) for (const k of [4, 6, 8, 10]) plan.push({ group: 'outside', mode, k, noise: 0.04, outside: true });
}
const only = process.env.ONLY ? new RegExp(process.env.ONLY) : null;
if (only) for (let i = plan.length - 1; i >= 0; i--) if (!only.test(plan[i].group + ':' + plan[i].mode + ':' + plan[i].k)) plan.splice(i, 1);

const out = [], t0 = Date.now();
plan.forEach((opt, i) => {
  const r = cell(opt); out.push(r);
  console.log(`[${i + 1}/${plan.length}] ${opt.group.padEnd(7)} ${opt.mode.padEnd(10)} k=${String(opt.k).padStart(2)} noise=${String(opt.noise).padEnd(4)} named=${r.named}% wrong=${r.wrong}% held=${r.held}% top5=${r.top5}% recog=${r.recognisedLines}% (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  fs.writeFileSync(outPath, JSON.stringify(out, null, 1));
});
