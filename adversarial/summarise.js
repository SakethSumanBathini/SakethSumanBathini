// Turns sweep outputs into the summary tables used in the README and on the page.
// Usage: node summarise.js <after.json> [<before.json>] [--html]
'use strict';
const fs = require('fs');
const args = process.argv.slice(2), html = args.includes('--html');
const files = args.filter(a => !a.startsWith('--'));
const after = JSON.parse(fs.readFileSync(files[0], 'utf8'));
const before = files[1] ? JSON.parse(fs.readFileSync(files[1], 'utf8')) : null;

const ROWS = [
  ['Kept the printed numbers', 'attack', 'numbered'],
  ['Left the numbers out', 'attack', 'plain'],
  ['Renumbered the lines 1, 2, 3', 'attack', 'renumbered'],
  ['Copied the first questions, real numbers 1, 2, 3', 'first', 'first'],
  ['Reworded every question, kept the numbers', 'attack', 'para-num'],
  ['Reworded every question, no numbers', 'attack', 'para'],
  ['Shuffled the lines, no numbers', 'attack', 'shuffled'],
  ['Mixed two colleges’ copies, kept the numbers', 'mix', 'numbered'],
  ['Mixed two colleges’ copies, no numbers', 'mix', 'plain'],
  ['Sent a copy from outside the 500 colleges', 'outside', null]
];
const num = n => n.toLocaleString('en-US');
const pct = x => (x >= 99.95 && x < 100 ? '>99.9' : x > 0 && x < 0.1 ? '<0.1' : String(+x.toFixed(1))) + '%';
const cells = (data, g, m) => data.filter(r => r.group === g && (m === null || r.mode === m)).sort((a, b) => a.k - b.k);
const wrong = (data, g, m) => { const cs = cells(data, g, m); return { n: cs.reduce((s, c) => s + c.wrongCount, 0), of: cs.reduce((s, c) => s + c.leaks, 0) }; };
// smallest leak that is named in at least 95% of cases; otherwise the best rate seen
function namesFrom(cs) {
  const hit = cs.find(c => c.named >= 95);
  if (hit) return hit.k + ' lines';
  const best = cs.reduce((b, c) => (c.named > b.named ? c : b), { named: 0 });
  return best.named >= 1 ? 'holds back (' + Math.round(best.named) + '% named at ' + best.k + ' lines)' : 'holds back';
}
function top5At(cs, k) { const c = cs.find(x => x.k === k) || cs[0]; return pct(c.top5) + (c.k !== k ? ' (' + c.k + ' lines)' : ''); }

const rows = ROWS.filter(([, g, m]) => cells(after, g, m).length).map(([label, g, m]) => {
  const cs = cells(after, g, m);
  return { label, from: g === 'outside' ? '–' : namesFrom(cs), top6: g === 'outside' ? '–' : top5At(cs, 6), wrong: wrong(after, g, m), wrongBefore: before ? wrong(before, g, m) : null };
});
const total = d => ({ n: d.reduce((s, c) => s + c.wrongCount, 0), of: d.reduce((s, c) => s + c.leaks, 0) });

if (html) {
  for (const r of rows) {
    const from = r.from.charAt(0).toUpperCase() + r.from.slice(1), esc = t => t.replace(/>/g, '&gt;');
    console.log(`          <tr><td data-label='What the leaker did'>${r.label}</td><td data-label='Names the source from' class='n'>${esc(from)}</td><td data-label='In the top 5, 6 lines' class='n'>${esc(r.top6)}</td><td data-label='Innocent college named' class='n ${r.wrong.n ? 'bad' : 'zero'}'>${r.wrong.n} of ${num(r.wrong.of)}</td></tr>`);
  }
} else {
  if (rows.length) {
    console.log('| What the leaker did | Named from (≥ 95% of leaks) | Real source in top 5, 6 lines | Innocent college named' + (before ? ' (before → after)' : '') + ' |');
    console.log('|---|---|---:|---:|');
  }
  for (const r of rows) console.log(`| ${r.label} | ${r.from} | ${r.top6} | ${before ? r.wrongBefore.n + ' → ' : ''}${r.wrong.n} of ${num(r.wrong.of)} |`);
  const t = total(after), tb = before ? total(before) : null;
  console.log(`\nAll ${after.length} settings: ${tb ? tb.n + ' → ' : ''}${t.n} innocent college${t.n === 1 ? '' : 's'} named in ${num(t.of)} leaks.`);
  const noise = after.filter(c => c.group === 'noise');
  if (noise.length) {
    console.log('\n| Typing damage (share of characters) | ' + [...new Set(noise.map(c => c.noise))].map(x => Math.round(x * 100) + '%').join(' | ') + ' |');
    console.log('|---|' + [...new Set(noise.map(c => c.noise))].map(() => '---:').join('|') + '|');
    for (const key of [...new Set(noise.map(c => c.mode + ':' + c.k))]) {
      const [mode, k] = key.split(':');
      console.log(`| ${mode === 'numbered' ? 'Numbered' : 'Un-numbered'}, ${k} lines: named | ` + noise.filter(c => c.mode === mode && String(c.k) === k).map(c => pct(c.named) + (c.wrongCount ? ' (' + c.wrongCount + ' wrong)' : '')).join(' | ') + ' |');
    }
  }
}
for (const c of after) for (const w of (c.wrongCases || [])) console.log(`\nwrong case: ${c.group}:${c.mode}:${c.k} leak ${w.leak}, stage ${w.stage}; the named college matches ${w.namedCollegeMatchesPositions} positions and ${w.namedCollegeMatchesWordings} wordings of ${w.lines} lines\n${w.text}`);
