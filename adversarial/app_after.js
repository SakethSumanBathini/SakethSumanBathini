(function () {
  'use strict';

  // ------------------------------------------------------------ question bank
  // Part A of a Data Structures paper: 10 questions, 4 approved wordings each.
  var BANK = [
    ['Define an abstract data type and give one example.', 'What is an abstract data type? Give one example.', 'Give one example of an abstract data type after defining it.', 'Define the term abstract data type, with one example.'],
    ['Compare a stack and a queue.', 'Compare a queue and a stack.', 'Bring out the differences between a stack and a queue.', 'How does a stack differ from a queue?'],
    ['State the time complexity of binary search.', 'What is the time complexity of binary search?', 'Give the time complexity of binary search.', 'Write down the time complexity of a binary search.'],
    ['What is a circular linked list?', 'Define a circular linked list.', 'Explain what a circular linked list is.', 'What do you mean by a circular linked list?'],
    ['Convert the infix expression A + B * C to postfix.', 'Convert A + B * C from infix to postfix form.', 'Write the postfix form of the infix expression A + B * C.', 'Give the postfix equivalent of A + B * C.'],
    ['List any two applications of a priority queue.', 'Give two applications of a priority queue.', 'Mention any two uses of a priority queue.', 'Write two applications of priority queues.'],
    ['Define the height of a binary tree.', 'What is meant by the height of a binary tree?', 'State what the height of a binary tree is.', 'What is the height of a binary tree?'],
    ['What is hashing? Name one collision resolution technique.', 'Define hashing and name one collision resolution technique.', 'Name one collision resolution technique and define hashing.', 'Explain hashing briefly and name one collision resolution method.'],
    ['Differentiate between BFS and DFS.', 'Differentiate between DFS and BFS.', 'Compare breadth-first search with depth-first search.', 'How does BFS differ from DFS?'],
    ['What is a minimum spanning tree?', 'Define a minimum spanning tree.', 'Explain the term minimum spanning tree.', 'What do you understand by a minimum spanning tree?']
  ];
  var TOPIC = ['abstract data types', 'stacks and queues', 'binary search', 'circular linked lists', 'infix to postfix', 'priority queues', 'binary tree height', 'hashing', 'BFS and DFS', 'minimum spanning trees'];
  var LETTERS = 'ABCDEFGHIJ';
  var N = 500, Q = 10, V = 4;
  var EPS = 0.02, EPS_V = 0.05, EPS_SWAP = 0.03;
  var ODDS = 10000, ODDS_TEXT = '10,000', TAU = Math.log(ODDS);   // name a college only at these odds
  var CLEAR_R = 0.8, CLEAR_GAP = 0.05, CLEAR_REL = 0.4;              // when a line's wording counts (see bestMatch)
  var RHO = 0.1;   // chance that numbers running 1, 2, 3 ... were typed by the leaker rather than printed
  var LOG_N = Math.log(N), LOG_PAIRS = Math.log(N + N * (N - 1) / 2);
  var PBUF = new Float64Array(N * N);
  var SVGNS = 'http://www.w3.org/2000/svg';
  var NL = String.fromCharCode(10);
  var REDUCE = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  // ------------------------------------------------------------ seeded codebook
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function shuffle(arr, r) {
    for (var i = arr.length - 1; i > 0; i--) { var j = Math.floor(r() * (i + 1)); var x = arr[i]; arr[i] = arr[j]; arr[j] = x; }
    return arr;
  }
  function range(n) { var a = []; for (var i = 0; i < n; i++) a.push(i); return a; }
  var seed = mulberry32(2026);
  var POS = [];   // POS[c][q] = printed slot (0-based) of question q in college c's paper
  while (POS.length < N) {
    var perm = shuffle(range(Q), seed), ok = true;
    for (var p = 0; p < POS.length && ok; p++) {
      var agree = 0;
      for (var i = 0; i < Q; i++) if (POS[p][i] === perm[i]) agree++;
      if (agree > 4) ok = false;
    }
    if (ok) POS.push(perm);
  }
  var VAR = [];   // VAR[c][q] = which approved wording college c gets
  for (var c0 = 0; c0 < N; c0++) { var row = []; for (var q0 = 0; q0 < Q; q0++) row.push(Math.floor(seed() * V)); VAR.push(row); }
  function slotList(c) { var s = new Array(Q); for (var q = 0; q < Q; q++) s[POS[c][q]] = q; return s; }
  function code(c) { return 'College ' + String(c + 1).padStart(3, '0'); }

  // ------------------------------------------------------------ text matching
  function norm(s) { return s.toLowerCase().replace(/[^a-z0-9+* ]/g, ' ').replace(/ +/g, ' ').trim(); }
  function bigrams(s) { var m = new Map(); for (var i = 0; i < s.length - 1; i++) { var g = s.slice(i, i + 2); m.set(g, (m.get(g) || 0) + 1); } return m; }
  function dice(a, b) {
    var inter = 0, na = 0, nb = 0;
    a.forEach(function (v) { na += v; }); b.forEach(function (v) { nb += v; });
    a.forEach(function (v, g) { var w = b.get(g); if (w) inter += Math.min(v, w); });
    return na + nb ? 2 * inter / (na + nb) : 0;
  }
  function lcsRatio(a, b) {
    var n = a.length, m = b.length; if (!n || !m) return 0;
    var prev = new Uint16Array(m + 1), cur = new Uint16Array(m + 1);
    for (var i = 1; i <= n; i++) {
      for (var j = 1; j <= m; j++) cur[j] = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? prev[j - 1] + 1 : Math.max(prev[j], cur[j - 1]);
      var t = prev; prev = cur; cur = t;
    }
    return 2 * prev[m] / (n + m);
  }
  var FLAT = [];
  BANK.forEach(function (vars, q) { vars.forEach(function (t, v) { var n = norm(t); FLAT.push({ q: q, v: v, n: n, bg: bigrams(n) }); }); });
  // how alike two approved wordings of the same question are
  var SIMV = BANK.map(function (vars) { var n = vars.map(norm); return n.map(function (a) { return n.map(function (b) { return lcsRatio(a, b); }); }); });
  function bestMatch(body) {
    var nb = norm(body); if (nb.length < 6) return null;
    var bg = bigrams(nb), byQ = new Array(Q).fill(0);
    FLAT.forEach(function (f) { var d = dice(bg, f.bg); if (d > byQ[f.q]) byQ[f.q] = d; });
    var top = range(Q).sort(function (a, b) { return byQ[b] - byQ[a]; }).slice(0, 2);
    var best = null, rs = {};
    FLAT.forEach(function (f) {
      if (top.indexOf(f.q) < 0) return;
      var r = lcsRatio(nb, f.n);
      (rs[f.q] = rs[f.q] || [])[f.v] = r;
      if (!best || r > best.r) best = { q: f.q, v: f.v, r: r };
    });
    if (!best || best.r < 0.6) return null;
    // A reworded line still names its question, but not which approved wording was printed. So a line's
    // wording counts only when the line is close to one wording and clearly closer to it than to the nearest
    // other one: by 0.05, or by 40% of the distance between two wordings that are close by design.
    var nv = -1, nr = -1;
    rs[best.q].forEach(function (r, v) { if (v !== best.v && r > nr) { nr = r; nv = v; } });
    best.clear = best.r >= CLEAR_R && best.r - nr >= Math.min(CLEAR_GAP, CLEAR_REL * (1 - SIMV[best.q][best.v][nv]));
    return best;
  }
  function parseLeak(text) {
    var out = [];
    text.split(NL).forEach(function (raw) {
      var ln = raw.trim(); if (!ln) return;
      var m = ln.match(/^[^A-Za-z0-9]*(?:[Qq](?:uestion|n|no)?[ .]*)?([0-9]{1,2})[ ]*[.,):-][ ]*(.+)$/), num = null, body = ln;
      if (m) { num = parseInt(m[1], 10); body = m[2]; }
      var hit = bestMatch(body);
      out.push({ line: ln, num: num, q: hit ? hit.q : null, v: hit ? hit.v : null, r: hit ? hit.r : 0, clear: !!(hit && hit.clear) });
    });
    return out;
  }

  // ------------------------------------------------------------ leaks
  function typo(s) {
    var rate = 0.04, letters = 'abcdefghijklmnopqrstuvwxyz', out = '';
    for (var i = 0; i < s.length; i++) {
      var ch = s[i], r = Math.random();
      if (r < rate / 3) continue;
      if (r < 2 * rate / 3) { out += letters[Math.floor(Math.random() * 26)]; continue; }
      out += ch; if (r < rate) out += ch;
    }
    if (Math.random() < 0.5) out = out.toLowerCase().replace(/[?.]/g, '');
    return out;
  }
  // how a leaker who wants to dodge the trace might reword each question (none of these is an approved wording)
  var REWORD = [
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
  // o.num: 'paper' (numbers as printed) | 'own' (the leaker numbers the lines 1, 2, 3) | 'none'
  function makeLeak(src, k, o) {
    var sources = [src];
    if (o.mix) { var b; do { b = Math.floor(Math.random() * N); } while (b === src); sources.push(b); }
    var qs = shuffle(range(Q), Math.random).slice(0, k);
    var items = qs.map(function (q) { var s = sources[Math.floor(Math.random() * sources.length)]; return { q: q, s: s, slot: POS[s][q], v: VAR[s][q] }; });
    items.sort(function (a, b) { return a.slot - b.slot || a.q - b.q; });
    if (o.shuffle) shuffle(items, Math.random);
    var lines = items.map(function (it, i) {
      var t = o.reword ? REWORD[it.q][Math.floor(Math.random() * 2)] : BANK[it.q][it.v];
      if (o.typos) t = typo(t);
      if (o.num === 'paper') return (it.slot + 1) + '. ' + t;
      if (o.num === 'own') return (i + 1) + '. ' + t;
      return t;
    });
    return { text: lines.join(NL), sources: sources };
  }

  // ------------------------------------------------------------ decoder
  function logFact(n) { var s = 0; for (var i = 2; i <= n; i++) s += Math.log(i); return s; }
  function lse(a, b) { var m = Math.max(a, b); return m + Math.log(Math.exp(a - m) + Math.exp(b - m)); }
  // Numbers that simply run 1, 2, 3 ... may be the paper's or the leaker's own. The decoder weighs both
  // readings (see RHO). Other numbers cannot be the leaker's own count, so they are read as printed.
  function ownNumbering(parsed) {
    var nums = parsed.filter(function (p) { return p.num !== null; }).map(function (p) { return p.num; });
    return nums.length >= 2 && nums.length < Q && nums.every(function (n, i) { return n === i + 1; });
  }
  function decode(parsed) {
    var items = parsed.filter(function (p) { return p.q !== null; });
    var k = items.length;
    if (!k) return { status: 'empty', k: 0, named: [] };
    var own = ownNumbering(parsed);
    var numbered = items.some(function (p) { return p.num !== null; });
    var clearCount = items.filter(function (p) { return p.clear; }).length;
    var lv1 = Math.log(1 - EPS_V), lv0 = Math.log(EPS_V / (V - 1)), lp1 = Math.log(1 - EPS), lp0 = Math.log(EPS / (Q - 1));
    var ll = new Float64Array(N), single = new Float64Array(N), nll = 0, pnll = 0;
    var bare = new Float64Array(N), nllBare = 0;   // wording evidence only, for the leaker's-own-numbers reading
    var states = [], tables = [], qv = new Float64Array(N);
    items.forEach(function (it) {
      var hasPos = numbered && it.num !== null && it.num >= 1 && it.num <= Q, useV = it.clear;
      var st = new Uint8Array(N);
      for (var c = 0; c < N; c++) {
        var s = VAR[c][it.q] === it.v ? 1 : 0;
        if (hasPos && POS[c][it.q] === it.num - 1) s |= 2;
        st[c] = s;
      }
      // reworded lines (useV false) count as their question but carry no wording evidence
      var ell = [0, 1, 2, 3].map(function (s) { return (useV ? ((s & 1) ? lv1 : lv0) : 0) + (hasPos ? ((s & 2) ? lp1 : lp0) : 0); });
      var nItem = (useV ? Math.log(1 / V) : 0) + (hasPos ? Math.log(1 / Q) : 0);
      var ellBare = [0, 1, 2, 3].map(function (s) { return useV ? ((s & 1) ? lv1 : lv0) : 0; }), nBare = useV ? Math.log(1 / V) : 0;
      // the two-source search (stage 2) does not use numbers that may be the leaker's own
      var ellT = own ? ellBare : ell, nT = own ? nBare : nItem;
      var T = new Float64Array(16);
      for (var a = 0; a < 4; a++) for (var b = 0; b < 4; b++) T[a * 4 + b] = lse(ellT[a], ellT[b]) - Math.log(2);
      for (var c2 = 0; c2 < N; c2++) { single[c2] += ell[st[c2]]; bare[c2] += ellBare[st[c2]]; qv[c2] += lse(ellT[st[c2]], nT) - Math.log(2); }
      nll += nItem; nllBare += nBare; pnll += nT; states.push(st); tables.push(T);
    });
    // the order of the lines, for leaks whose numbers are missing or may be the leaker's own
    var ordered = new Float64Array(N), orderNull = 0;
    if ((!numbered || own) && k > 1) {
      var seq = items.map(function (p) { return p.q; });
      var hi = Math.log(1 - EPS_SWAP), lo = Math.log(EPS_SWAP);
      for (var i = 0; i < seq.length; i++) for (var j = i + 1; j < seq.length; j++) {
        if (seq[i] === seq[j]) continue;
        for (var c4 = 0; c4 < N; c4++) ordered[c4] += POS[c4][seq[i]] < POS[c4][seq[j]] ? hi : lo;
      }
      orderNull = -logFact(seq.length);
    }
    if (own) {
      // two readings, for colleges and for the outside-copy null alike: the numbers are the paper's
      // (positions count), or the leaker's own (only the order counts)
      var la = Math.log(1 - RHO), lb = Math.log(RHO);
      for (var c3 = 0; c3 < N; c3++) ll[c3] = lse(la + single[c3], lb + bare[c3] + ordered[c3]);
      nll = lse(la + nll, lb + nllBare + orderNull);
    } else if (!numbered) {
      for (var c6 = 0; c6 < N; c6++) ll[c6] = single[c6] + ordered[c6];
      nll += orderNull;
    } else {
      for (var c7 = 0; c7 < N; c7++) ll[c7] = single[c7];
    }
    var order = range(N).sort(function (a, b) { return ll[b] - ll[a]; });
    var top = order[0], second = order[1];
    // posterior over colleges (uniform prior), for the bars
    var mx = ll[top], z = 0; for (var c5 = 0; c5 < N; c5++) z += Math.exp(ll[c5] - mx);
    var post = order.slice(0, 5).map(function (c) { return { c: c, p: Math.exp(ll[c] - mx) / z }; });

    // two-source scores for every pair of colleges (order evidence not used here, so neither is its null)
    var P = PBUF, best = -Infinity, ba = 0, bb = 0;
    for (var a2 = 0; a2 < N; a2++) for (var b2 = a2; b2 < N; b2++) {
      var s2 = 0;
      for (var t = 0; t < k; t++) s2 += tables[t][states[t][a2] * 4 + states[t][b2]];
      P[a2 * N + b2] = s2;
      if (s2 > best) { best = s2; ba = a2; bb = b2; }
    }
    var gap = ll[top] - ll[second], overNull = ll[top] - nll;
    var res = { status: 'held', k: k, numbered: numbered, own: own, clear: clearCount, order: order, post: post, ll: ll, gap: gap, named: [], stage: 0 };
    if (gap >= TAU && overNull >= TAU + LOG_N && best - P[top * N + top] < TAU) {
      res.status = 'named'; res.named = [top]; res.stage = 1; return res;
    }
    if (best - pnll >= TAU + LOG_PAIRS) {
      [[ba, bb], [bb, ba]].forEach(function (pair) {
        var m = pair[0], partner = pair[1];
        if (res.named.indexOf(m) >= 0) return;
        var w = -Infinity;
        for (var a3 = 0; a3 < N; a3++) { if (a3 === m) continue; for (var b3 = a3; b3 < N; b3++) { if (b3 === m) continue; var v3 = P[a3 * N + b3]; if (v3 > w) w = v3; } }
        if (best - w < TAU) return;
        if (m !== partner && best - qv[partner] < TAU + LOG_N) return;
        res.named.push(m);
      });
      if (res.named.length) { res.status = 'named'; res.stage = 2; res.mixed = ba !== bb; }
    }
    return res;
  }

  // ------------------------------------------------------------ helpers
  function $(id) { return document.getElementById(id); }
  function times(x) {
    if (!isFinite(x) || x >= 1e5) return 'over a lakh';
    return Math.round(x).toLocaleString('en-IN');
  }
  function pct(p) { if (p > 0.999) return '>99.9%'; if (p < 0.001) return '<0.1%'; return (p * 100).toFixed(1) + '%'; }
  function ordinal(n) { var s = ['th', 'st', 'nd', 'rd'], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function svg(tag, attrs, parent) {
    var e = document.createElementNS(SVGNS, tag);
    if (attrs) for (var a in attrs) e.setAttribute(a, attrs[a]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function later(fn) { requestAnimationFrame(function () { requestAnimationFrame(fn); }); }
  function penFilter(root, id) {
    var defs = svg('defs', null, root);
    var f = svg('filter', { id: id, x: '-40%', y: '-40%', width: '180%', height: '180%' }, defs);
    svg('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.8', numOctaves: '2', seed: '4', result: 'noise' }, f);
    svg('feDisplacementMap', { 'in': 'SourceGraphic', in2: 'noise', scale: '2.4', xChannelSelector: 'R', yChannelSelector: 'G' }, f);
    return 'url(#' + id + ')';
  }
  // colleges the evidence cannot yet rule out at ODDS to 1
  function fitMask(ll) {
    var mx = -Infinity, i, m = new Uint8Array(N), n = 0;
    for (i = 0; i < N; i++) if (ll[i] > mx) mx = ll[i];
    for (i = 0; i < N; i++) if (ll[i] >= mx - TAU) { m[i] = 1; n++; }
    return { mask: m, count: n };
  }

  // ------------------------------------------------------------ bubble grid (one bubble per college)
  function makeGrid(root, n, cols, opts) {
    opts = opts || {};
    var cell = 20, r = 6.6, left = opts.marks ? 18 : 0, rows = Math.ceil(n / cols);
    root.setAttribute('viewBox', '0 0 ' + (left + cols * cell) + ' ' + rows * cell);
    var filt = penFilter(root, root.id + '-pen');
    if (opts.marks) for (var y = 0; y < rows; y++) svg('rect', { 'class': 'tm', x: 0, y: y * cell + cell / 2 - 3, width: 10, height: 6 }, root);
    var dots = [];
    for (var i = 0; i < n; i++) {
      var c = svg('circle', { cx: left + (i % cols) * cell + cell / 2, cy: Math.floor(i / cols) * cell + cell / 2, r: r }, root);
      if (opts.title) svg('title', null, c).textContent = opts.title(i);
      dots.push(c);
    }
    var layer = svg('g', { filter: filt }, root);
    return {
      set: function (i, cls) { dots[i].setAttribute('class', cls || ''); },
      all: function (cls) { for (var i = 0; i < n; i++) dots[i].setAttribute('class', cls || ''); },
      clearFills: function () { while (layer.firstChild) layer.removeChild(layer.firstChild); },
      fill: function (i, extra, instant) {
        var d = dots[i];
        var m = svg('circle', { 'class': 'pen' + (extra ? ' ' + extra : ''), cx: d.getAttribute('cx'), cy: d.getAttribute('cy'), r: r + 0.8 }, layer);
        if (instant || REDUCE) m.classList.add('on'); else later(function () { m.classList.add('on'); });
      }
    };
  }

  // ------------------------------------------------------------ college code, bubbled in like an OMR roll number
  function makeCode(root) {
    var colW = 26, top = 32, cell = 17.5, r = 7, texts = [], centers = [], timers = [];
    root.setAttribute('viewBox', '0 0 ' + 3 * colW + ' ' + (top + 10 * cell));
    var filt = penFilter(root, root.id + '-pen');
    for (var d = 0; d < 3; d++) {
      var cx = d * colW + colW / 2, col = [];
      svg('rect', { 'class': 'box', x: d * colW + 2, y: 1, width: colW - 4, height: 25, rx: 1 }, root);
      texts.push(svg('text', { 'class': 'digit', x: cx, y: 19.5, 'text-anchor': 'middle' }, root));
      for (var v = 0; v < 10; v++) {
        var cy = top + v * cell + cell / 2;
        svg('circle', { 'class': 'cb', cx: cx, cy: cy, r: r }, root);
        svg('text', { 'class': 'cbl', x: cx, y: cy + 3, 'text-anchor': 'middle' }, root).textContent = String(v);
        col.push([cx, cy]);
      }
      centers.push(col);
    }
    var layer = svg('g', { filter: filt }, root);
    return {
      clear: function () {
        timers.forEach(clearTimeout); timers = [];
        texts.forEach(function (t) { t.textContent = ''; });
        while (layer.firstChild) layer.removeChild(layer.firstChild);
      },
      show: function (num, animate) {
        String(num).padStart(3, '0').split('').forEach(function (ch, i) {
          function put() {
            texts[i].textContent = ch;
            var at = centers[i][+ch];
            var m = svg('circle', { 'class': 'pen', cx: at[0], cy: at[1], r: r + 0.6 }, layer);
            if (!animate || REDUCE) m.classList.add('on'); else later(function () { m.classList.add('on'); });
          }
          if (animate && !REDUCE) timers.push(setTimeout(put, i * 300)); else put();
        });
      }
    };
  }

  // ------------------------------------------------------------ hero: a leak arrives and 500 colleges shrink to one
  (function hero() {
    var c = 213;
    var grid = makeGrid($('heroGrid'), N, window.innerWidth > 1080 ? 40 : 25, { marks: true, title: code });
    var codeBox = makeCode($('heroCode'));
    var list = $('heroLines'), countEl = $('heroCount'), countLab = $('heroCountLabel');
    var who = $('heroWho'), why = $('heroWhy'), replay = $('replay');
    var slots = slotList(c), lines = [], found = false;

    // the way a hurried leaker retypes: some lines lower-case, a few letters swapped
    function rough(t, s) {
      if (s % 3 === 1) return t.toLowerCase().replace(/[?.]$/, '');
      if (s % 3 === 2) {
        var w = t.split(' '), L = 0;
        for (var i = 1; i < w.length; i++) if (w[i].replace(/[^A-Za-z0-9_]/g, '').length > w[L].replace(/[^A-Za-z0-9_]/g, '').length) L = i;
        var x = w[L], j = Math.floor(x.length / 2);
        while (j < x.length - 1 && x[j] === x[j - 1]) j++;
        if (x.length > 5) w[L] = x.slice(0, j - 1) + x[j] + x[j - 1] + x.slice(j + 1);
        return w.join(' ');
      }
      return t;
    }
    for (var start = 3; start >= 0 && !found; start--) {
      for (var k = 5; k <= Q - start && !found; k++) {
        lines = [];
        for (var s = start; s < start + k; s++) lines.push((s + 1) + '. ' + rough(BANK[slots[s]][VAR[c][slots[s]]], s));
        var res = decode(parseLeak(lines.join(NL)));
        found = res.status === 'named' && res.named.length === 1 && res.named[0] === c;
      }
    }
    var steps = lines.map(function (_, p) { return fitMask(decode(parseLeak(lines.slice(0, p + 1).join(NL))).ll); });
    var items = lines.map(function (l) { var li = el('li', '', l); list.appendChild(li); return li; });
    var timers = [], shown = N, raf = 0;

    function setCount(n, animate) {
      cancelAnimationFrame(raf);
      countLab.textContent = n === 1 ? 'college still fits the leak' : 'colleges still fit the leak';
      if (!animate || REDUCE) { shown = n; countEl.textContent = n; return; }
      var from = shown, t0 = performance.now();
      raf = requestAnimationFrame(function tick(t) {
        var a = Math.min(1, (t - t0) / 520), e = 1 - Math.pow(1 - a, 3);
        shown = Math.round(from + (n - from) * e);
        countEl.textContent = shown;
        if (a < 1) raf = requestAnimationFrame(tick);
      });
    }
    function paint(p) { var m = steps[p].mask; for (var i = 0; i < N; i++) grid.set(i, m[i] ? 'live' : 'out'); }
    function finish(animate) {
      function words() {
        who.textContent = found ? code(c) : 'Shortlist only';
        why.textContent = found
          ? 'Named from ' + lines.length + ' retyped questions. Leak Trace names a college only when it is at least ' + ODDS_TEXT + ' times likelier than every other.'
          : 'The evidence was too thin to name one college, so investigators get a shortlist.';
        replay.hidden = false;
      }
      if (found) { grid.set(c, 'lead'); grid.fill(c, '', !animate); codeBox.show(c + 1, animate); }
      if (animate && !REDUCE) timers.push(setTimeout(words, 1050)); else words();
    }
    function reset() {
      timers.forEach(clearTimeout); timers = [];
      codeBox.clear(); grid.clearFills(); grid.all('');
      items.forEach(function (li) { li.className = ''; });
      setCount(N, false);
      who.textContent = 'Reading the leak';
      why.textContent = 'Each line is checked against the pattern of every college.';
      replay.hidden = true;
    }
    function play() {
      reset();
      if (REDUCE) {
        items.forEach(function (li) { li.className = 'read'; });
        paint(items.length - 1); setCount(steps[steps.length - 1].count, false); finish(false);
        return;
      }
      var t = 450;
      items.forEach(function (li, p) {
        timers.push(setTimeout(function () {
          li.className = 'reading';
          paint(p); setCount(steps[p].count, true);
          timers.push(setTimeout(function () { li.className = 'read'; }, 800));
        }, t));
        t += 900;
      });
      timers.push(setTimeout(function () { finish(true); }, t));
    }
    replay.addEventListener('click', play);
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        if (entries.some(function (e) { return e.isIntersecting; })) { io.disconnect(); play(); }
      }, { threshold: 0.5 });
      io.observe($('heroSheet'));
    } else play();
  })();

  // ------------------------------------------------------------ copy the problem statement
  $('copyBtn').addEventListener('click', function () {
    var btn = this, text = $('statement').textContent, msg = $('copyMsg');
    function done() {
      msg.textContent = 'Copied. Paste it into the entry form.';
      btn.textContent = 'Copied';
      setTimeout(function () { btn.textContent = 'Copy statement'; }, 2400);
    }
    function fallback() {
      var r = document.createRange(); r.selectNodeContents($('statement'));
      var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
      msg.textContent = 'Selected. Press Ctrl+C or Cmd+C to copy.';
    }
    try {
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, fallback);
      else fallback();
    } catch (e) { fallback(); }
  });

  // ------------------------------------------------------------ two papers and their patterns
  (function papers() {
    var pick = [213, 36], box = $('papers'), explain = $('explain'), current = -1;
    var views = pick.map(function (c) {
      var col = el('div', 'paper-col'), art = el('article', 'paper'), head = el('header', 'paper-head');
      head.appendChild(el('p', 'qpcode', 'Q.P. code: SET ' + String(c + 1).padStart(3, '0')));
      head.appendChild(el('p', 'exam', 'B.Tech Degree Examination, November 2026'));
      head.appendChild(el('p', '', 'Third Semester: Data Structures'));
      var tm = el('div', 'tmrow');
      tm.appendChild(el('span', '', 'Time: 3 hours'));
      tm.appendChild(el('span', '', 'Max. marks: 70'));
      head.appendChild(tm);
      head.appendChild(el('p', 'part', 'PART A'));
      head.appendChild(el('p', 'instr', 'Answer all questions. Each question carries 2 marks.'));
      art.appendChild(head);
      var ol = el('ol', 'qs'), rows = {};
      slotList(c).forEach(function (q, s) {
        var li = el('li');
        li.tabIndex = 0;
        li.dataset.q = q;
        li.appendChild(el('span', 'n', (s + 1) + '.'));
        var t = el('span', 't', BANK[q][VAR[c][q]]);
        li.appendChild(t);
        ol.appendChild(li);
        rows[q] = { li: li, t: t };
      });
      art.appendChild(ol);
      art.appendChild(el('p', 'paper-foot', 'Printed for ' + code(c)));
      col.appendChild(art);

      var fig = el('figure', 'pattern'), g = svg('svg', { 'class': 'pg', viewBox: '0 0 216 216', 'aria-hidden': 'true' });
      var colRects = [], rings = [];
      for (var q = 0; q < Q; q++) {
        colRects.push(svg('rect', { 'class': 'col', x: 16 + q * 20 + 1, y: 15, width: 18, height: 200, rx: 9 }, g));
        svg('text', { 'class': 'lab', x: 16 + q * 20 + 10, y: 10, 'text-anchor': 'middle' }, g).textContent = LETTERS[q];
      }
      for (var sl = 0; sl < Q; sl++) svg('text', { 'class': 'lab', x: 6, y: 16 + sl * 20 + 13, 'text-anchor': 'middle' }, g).textContent = String(sl + 1);
      for (var s3 = 0; s3 < Q; s3++) for (var q3 = 0; q3 < Q; q3++) {
        var on = POS[c][q3] === s3, cx = 16 + q3 * 20 + 10, cy = 16 + s3 * 20 + 10;
        svg('circle', { 'class': on ? 'on' : '', cx: cx, cy: cy, r: 6.5 }, g);
        if (on) svg('text', { 'class': 'v', x: cx, y: cy + 3.1, 'text-anchor': 'middle' }, g).textContent = String(VAR[c][q3] + 1);
      }
      for (var q4 = 0; q4 < Q; q4++) rings.push(svg('circle', { 'class': 'ring', cx: 16 + q4 * 20 + 10, cy: 16 + POS[c][q4] * 20 + 10, r: 9.2 }, g));
      fig.appendChild(g);
      var cap = el('figcaption');
      cap.appendChild(el('b', '', code(c) + '’s pattern.'));
      cap.appendChild(document.createTextNode(' No other college has this one.'));
      fig.appendChild(cap);
      col.appendChild(fig);
      box.appendChild(col);
      return { c: c, rows: rows, colRects: colRects, rings: rings };
    });

    function norm1(w) { return w.toLowerCase().replace(/[^a-z0-9+*]/g, ''); }
    // words shared by both wordings (longest common subsequence); the rest get highlighted
    function keepMask(a, b) {
      var n = a.length, m = b.length, L = [], i, j;
      for (i = 0; i <= n; i++) L.push(new Array(m + 1).fill(0));
      for (i = n - 1; i >= 0; i--) for (j = m - 1; j >= 0; j--) L[i][j] = norm1(a[i]) === norm1(b[j]) ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
      var ka = new Array(n).fill(false), kb = new Array(m).fill(false);
      i = 0; j = 0;
      while (i < n && j < m) {
        if (norm1(a[i]) === norm1(b[j])) { ka[i] = kb[j] = true; i++; j++; }
        else if (L[i + 1][j] >= L[i][j + 1]) i++;
        else j++;
      }
      return [ka, kb];
    }
    function paintText(node, words, keep) {
      node.textContent = '';
      words.forEach(function (w, i) {
        if (i) node.appendChild(document.createTextNode(' '));
        if (keep[i]) node.appendChild(document.createTextNode(w)); else node.appendChild(el('mark', '', w));
      });
    }
    function mark(qq) {
      var q = +qq;
      if (q === current) return;
      current = q;
      views.forEach(function (v) {
        for (var key in v.rows) {
          v.rows[key].li.classList.toggle('hl', +key === q);
          v.rows[key].t.textContent = BANK[key][VAR[v.c][key]];
        }
        v.colRects.forEach(function (r, i) { r.classList.toggle('hl', i === q); });
        v.rings.forEach(function (r, i) { r.classList.toggle('hl', i === q); });
      });
      var A = views[0], B = views[1];
      var wa = BANK[q][VAR[A.c][q]].split(' '), wb = BANK[q][VAR[B.c][q]].split(' '), km = keepMask(wa, wb);
      paintText(A.rows[q].t, wa, km[0]);
      paintText(B.rows[q].t, wb, km[1]);
      var pa = POS[A.c][q] + 1, pb = POS[B.c][q] + 1, same = VAR[A.c][q] === VAR[B.c][q];
      explain.textContent = '';
      explain.appendChild(document.createTextNode('Question ' + LETTERS[q] + ', on ' + TOPIC[q] + ', is '));
      explain.appendChild(el('b', '', pa === pb ? 'number ' + pa + ' in both papers' : 'number ' + pa + ' for ' + code(A.c) + ' and number ' + pb + ' for ' + code(B.c)));
      explain.appendChild(document.createTextNode(same
        ? ', with the same wording. The other questions tell these two colleges apart.'
        : ', and each college got a different approved wording.'));
    }
    function pick2(e) { var li = e.target.closest && e.target.closest('li[data-q]'); if (li) mark(li.dataset.q); }
    box.addEventListener('mouseover', pick2);
    box.addEventListener('focusin', pick2);
    box.addEventListener('click', pick2);
    mark(1);
  })();

  // ------------------------------------------------------------ demo: be the leaker
  (function demo() {
    var grid = makeGrid($('demoGrid'), N, 25, { title: code });
    var bgrid = makeGrid($('batchGrid'), 200, 25, {});
    var optTypo = $('optTypo'), optMix = $('optMix'), optReword = $('optReword'), optShuffle = $('optShuffle'), leakText = $('leakText');
    var radios = document.querySelectorAll('input[name=k], input[name=num]');
    var current = null;   // the sources of the last generated leak

    function getK() { var r = document.querySelector('input[name=k]:checked'); return r ? +r.value : 5; }
    function opts() {
      var n = document.querySelector('input[name=num]:checked');
      return { num: n ? n.value : 'paper', typos: optTypo.checked, mix: optMix.checked, reword: optReword.checked, shuffle: optShuffle.checked };
    }
    function newLeak() {
      current = makeLeak(Math.floor(Math.random() * N), getK(), opts());
      current.edited = false;
      leakText.value = current.text;
      $('secretNote').textContent = 'The leaking college stays secret until you trace.';
    }
    leakText.addEventListener('input', function () { if (current) current.edited = true; });

    function setStatus(text, cls) {
      var st = $('status');
      st.className = 'status' + (cls ? ' ' + cls : '');
      st.textContent = '';
      st.appendChild(el('i'));
      st.appendChild(document.createTextNode(text));
    }
    // what the decoder chose not to trust, in words
    function caveat(res) {
      var bits = [], rew = res.k - res.clear;
      if (res.own) bits.push('The numbers simply run 1, 2, 3, so they may be the leaker’s own; only the order of the lines counted.');
      if (rew === 1) bits.push('One reworded line counted as its question, not its wording.');
      else if (rew > 1) bits.push(rew + ' reworded lines counted as their questions, not their wording.');
      return bits.length ? ' ' + bits.join(' ') : '';
    }
    function render(res) {
      var who = $('who'), why = $('why'), top5 = $('top5'), reveal = $('reveal'), readout = $('readout');
      top5.textContent = ''; reveal.textContent = ''; readout.textContent = '';
      grid.clearFills();
      res.parsed.forEach(function (p, idx) {
        var t = 'not recognised';
        if (p.q !== null) {
          t = 'question ' + LETTERS[p.q] + ', ' + (p.clear ? 'wording ' + (p.v + 1) : 'reworded, so its wording is not used');
          t += p.num === null ? ', no number' : (res.own ? ', numbered ' + p.num + ', order only' : ', printed as number ' + p.num);
        }
        readout.appendChild(el('li', '', 'Line ' + (idx + 1) + ': ' + t));
      });
      if (res.status === 'empty') {
        setStatus('No questions recognised');
        who.textContent = 'Nothing to trace';
        why.textContent = 'Paste or type questions from the paper, one per line.';
        grid.all('out');
        return;
      }
      if (res.status === 'named' && res.stage === 2 && res.mixed) {
        setStatus('Mixed copies detected', 'named');
        who.textContent = res.named.map(code).join(' + ');
        why.textContent = 'The leak looks stitched together from more than one college’s paper. Each college named here is at least ' + ODDS_TEXT + ' times likelier to be a source than any explanation without it.' + caveat(res);
      } else if (res.status === 'named' && res.stage === 2) {
        setStatus('Source named', 'named');
        who.textContent = code(res.named[0]);
        why.textContent = 'Named by the second check: every explanation of these ' + res.k + ' questions that leaves this college out is at least ' + ODDS_TEXT + ' times less likely.' + caveat(res);
      } else if (res.status === 'named') {
        setStatus('Source named', 'named');
        who.textContent = code(res.named[0]);
        why.textContent = 'From ' + res.k + ' recognised questions, and under our noise model, this college is ' + times(Math.exp(res.gap)) + ' times likelier than the next one. Leak Trace names a college only above ' + ODDS_TEXT + ' times.' + caveat(res);
      } else {
        setStatus('Held back');
        who.textContent = 'Shortlist only';
        why.textContent = 'From ' + res.k + ' recognised questions, no college is ' + ODDS_TEXT + ' times likelier than the rest, so Leak Trace gives investigators a shortlist instead of a name.' + caveat(res);
      }

      var fit = fitMask(res.ll).mask, short = res.order.slice(0, 5), truth = current ? current.sources : [];
      for (var i = 0; i < N; i++) grid.set(i, fit[i] ? '' : 'out');
      short.forEach(function (s) { grid.set(s, 'short'); });
      truth.forEach(function (s) { grid.set(s, (short.indexOf(s) >= 0 ? 'short ' : '') + 'truth'); });
      res.named.forEach(function (n) { grid.fill(n, truth.length && truth.indexOf(n) < 0 ? 'bad' : ''); });

      var leadSet = res.named.length ? res.named : [res.order[0]];
      res.post.forEach(function (row) {
        var li = el('li', leadSet.indexOf(row.c) >= 0 ? 'lead' : '');
        li.appendChild(el('span', '', code(row.c)));
        var bar = el('span', 'bar'), fillBar = el('i');
        fillBar.style.width = Math.max(1.5, row.p * 100) + '%';
        bar.appendChild(fillBar);
        li.appendChild(bar);
        li.appendChild(el('span', 'pc', pct(row.p)));
        top5.appendChild(li);
      });

      if (current) {
        var p = el('p');
        p.appendChild(document.createTextNode(truth.length > 1 ? 'Actual sources: ' : 'Actual source: '));
        p.appendChild(el('b', '', truth.map(code).join(' and ')));
        p.appendChild(document.createTextNode('. '));
        if (res.named.length) {
          var wrong = res.named.some(function (n) { return truth.indexOf(n) < 0; });
          if (wrong) p.appendChild(el('span', 'bad', 'Wrong accusation.'));
          else p.appendChild(document.createTextNode(res.named.length === truth.length ? (truth.length > 1 ? 'Both named correctly.' : 'Correct.') : 'One of them named correctly.'));
        } else {
          var bestRank = Math.min.apply(null, truth.map(function (s) { return res.order.indexOf(s) + 1; }));
          p.appendChild(document.createTextNode('Not named; ranked ' + ordinal(bestRank) + ' of 500' + (bestRank <= 5 ? ', inside the shortlist.' : '.')));
        }
        if (current.edited) p.appendChild(document.createTextNode(' You edited the leak.'));
        reveal.appendChild(p);
      }
    }
    function trace() {
      var parsed = parseLeak(leakText.value), res = decode(parsed);
      res.parsed = parsed;
      render(res);
    }
    function resetBatch() { bgrid.all(''); $('stats').hidden = true; $('batchMsg').textContent = ''; }

    $('makeBtn').addEventListener('click', function () { newLeak(); trace(); });
    $('traceBtn').addEventListener('click', trace);
    [optTypo, optMix, optReword, optShuffle].concat(Array.prototype.slice.call(radios)).forEach(function (x) {
      x.addEventListener('change', function () { newLeak(); trace(); resetBatch(); });
    });

    $('batchBtn').addEventListener('click', function () {
      var btn = this, msg = $('batchMsg'), total = 200, done = 0, named = 0, top5 = 0, held = 0, wrong = 0;
      var k = getK(), o = opts();
      btn.disabled = true;
      resetBatch();
      (function chunk() {
        var end = Math.min(total, done + 6);
        for (; done < end; done++) {
          var lk = makeLeak(Math.floor(Math.random() * N), k, o), res = decode(parseLeak(lk.text));
          var inTop = !!res.order && lk.sources.some(function (s) { return res.order.indexOf(s) < 5; }), cls;
          if (res.status === 'named') {
            if (res.named.some(function (n) { return lk.sources.indexOf(n) < 0; })) { wrong++; cls = 'b-bad'; } else { named++; cls = 'b-ok'; }
          } else { held++; cls = inTop ? 'b-top' : 'b-held'; }
          if (inTop) top5++;
          bgrid.set(done, cls);
        }
        msg.textContent = 'Tracing ' + done + ' of ' + total;
        if (done < total) { setTimeout(chunk, 0); return; }
        btn.disabled = false;
        msg.textContent = '200 leaks traced';
        $('sNamed').textContent = Math.round(100 * named / total) + '%';
        $('sTop5').textContent = Math.round(100 * top5 / total) + '%';
        $('sHeld').textContent = Math.round(100 * held / total) + '%';
        $('sWrong').textContent = String(wrong);
        $('stats').hidden = false;
      })();
    });

    newLeak();
    trace();
  })();

  // ------------------------------------------------------------ results chart
  (function chart() {
    var root = $('chart');
    var ks = [2, 3, 4, 5, 6, 7, 8, 9, 10];
    var series = [
      { name: 'Numbered + wording variants', lead: true, v: [0, 0, 0, 36.3, 73.9, 91.5, 97.1, 99.2, 99.5] },
      { name: 'MCQ, option order', dash: '', v: [0, 0, 0, 90.4, 88.5, 87.2, 99.2, 98.8, 100] },
      { name: 'No numbers + wording variants', dash: '7 5', v: [0, 0, 0, 0, 0, 1.6, 50.8, 61.9, 83.8] },
      { name: 'Numbered, order only', dash: '2 5', v: [0, 0, 0, 0, 0, 0.1, 7.8, 62.3, 76.1] }
    ];
    var L = 60, R = 700, T = 40, B = 336;
    function X(k) { return L + (k - 2) / 8 * (R - L); }
    function Y(v) { return B - v / 100 * (B - T); }
    svg('rect', { 'class': 'band', x: X(4), y: T, width: X(5) - X(4), height: B - T }, root);
    svg('text', { 'class': 'bandlab', x: X(4) + 6, y: T + 17 }, root).textContent = 'Kannur leak';
    [0, 25, 50, 75, 100].forEach(function (v) {
      svg('line', { 'class': 'gl', x1: L, x2: R, y1: Y(v), y2: Y(v) }, root);
      svg('text', { 'class': 'ax', x: L - 10, y: Y(v) + 4.5, 'text-anchor': 'end' }, root).textContent = v + (v === 100 ? '%' : '');
    });
    ks.forEach(function (k) { svg('text', { 'class': 'ax', x: X(k), y: B + 24, 'text-anchor': 'middle' }, root).textContent = String(k); });
    svg('text', { 'class': 'ax', x: (L + R) / 2, y: B + 52, 'text-anchor': 'middle' }, root).textContent = 'Questions in the leak';
    svg('text', { 'class': 'ax', x: L - 10, y: 20 }, root).textContent = 'Leaks traced to one college with confidence';
    var ends = [];
    series.slice().reverse().forEach(function (s) {
      var d = s.v.map(function (v, i) { return (i ? 'L' : 'M') + X(ks[i]).toFixed(1) + ' ' + Y(v).toFixed(1); }).join(' ');
      var path = svg('path', { 'class': 'line' + (s.lead ? ' lead' : ''), d: d }, root);
      if (s.dash) path.setAttribute('stroke-dasharray', s.dash);
      s.v.forEach(function (v, i) {
        var dot = svg('circle', { 'class': 'dot' + (s.lead ? ' lead' : ''), cx: X(ks[i]), cy: Y(v), r: s.lead ? 4.5 : 2.8 }, root);
        svg('title', null, dot).textContent = s.name + ': ' + ks[i] + ' questions, ' + v + '% traced';
      });
      ends.push({ s: s, y: Y(s.v[s.v.length - 1]) });
    });
    ends.sort(function (a, b) { return a.y - b.y; });
    var lastY = -Infinity;
    ends.forEach(function (e) {
      var y = Math.max(e.y, lastY + 20);
      lastY = y;
      svg('line', { 'class': 'gl', x1: R + 6, x2: R + 16, y1: e.y, y2: y }, root);
      svg('text', { 'class': 'lab' + (e.s.lead ? ' lead' : ''), x: R + 22, y: y + 4.5 }, root).textContent = e.s.name;
    });
    var key = series[0].v[5];
    svg('text', { 'class': 'key', x: X(7) + 12, y: Y(key) + 28 }, root).textContent = Math.round(key) + '% at 7 questions';
  })();
})();
