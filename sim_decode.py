"""
Leak Trace — decoding simulation v2.

Each college's paper is content-identical but carries a codeword spread over
channels that survive retyping to different degrees:
  posA : printed position of each Part A question (needs question numbers in the leak)
  lab  : (a)/(b) label of each either/or pair in Part B (needs numbering)
  sub  : order of the two sub-parts (i)/(ii) of each Part B question (survives retyping)
  var  : one of V meaning-neutral surface variants per question, e.g. notation or
         phrasing ("Compare A and B" / "Compare B and A", "5,000" / "5000") (survives retyping)
  opt  : MCQ option order (survives retyping when options are copied)

Decision rule controls false accusation: accuse college c only if its likelihood beats
(1) the runner-up by tau and (2) an "outside copy" null model by tau + ln(N)
(a union-bound correction for testing N colleges at once).
"""
import json, math, os, sys, itertools
import numpy as np

rng = np.random.default_rng(17)
N = 500
TRIALS = 3000
EPS = 0.02      # an item is mis-matched to the wrong canonical question
EPS_V = 0.05    # a surface variant is mis-read (typos, OCR)
EPS_SWAP = 0.03 # leaker re-orders a neighbouring pair when retyping
OUT = sys.argv[1] if len(sys.argv) > 1 else "."

def perm_code(n_slots, n_words, max_agree):
    code = []
    while len(code) < n_words:
        c = rng.permutation(n_slots)
        if not code or (np.array(code) == c).sum(1).max() <= max_agree:
            code.append(c)
    return np.array(code)

posA = perm_code(10, N, 4)
lab = rng.integers(0, 2, (N, 5))
sub = rng.integers(0, 2, (N, 10))
OPTP = np.array(list(itertools.permutations(range(4))))
opt = rng.integers(0, len(OPTP), (N, 20))

def make_var(V):
    return rng.integers(0, V, (N, 20)) if V > 1 else np.zeros((N, 20), int)

def leak(src, k, mode, V, varc, outside=False):
    if outside:
        pA = rng.permutation(10); lb = rng.integers(0, 2, 5); sb = rng.integers(0, 2, 10)
        vr = rng.integers(0, max(V, 1), 20); op = rng.integers(0, len(OPTP), 20)
    else:
        pA, lb, sb, vr, op = posA[src], lab[src], sub[src], varc[src], opt[src]
    ev = []
    if mode == "mcq":
        for q in rng.choice(20, k, replace=False):
            o = op[q] if rng.random() > EPS else rng.integers(0, len(OPTP))
            ev.append(("opt", int(q), int(o)))
        return ev
    items = rng.choice(20, k, replace=False)
    a_seen = []
    for it in items:
        mis = rng.random() < EPS
        v = vr[it] if rng.random() > EPS_V else rng.integers(0, max(V, 1))
        if V > 1:
            ev.append(("var", int(it), int(v)))
        if it < 10:
            q = it if not mis else rng.integers(0, 10)
            if mode == "numbered":
                ev.append(("posA", int(q), int(pA[it])))
            else:
                a_seen.append((int(q), int(pA[it])))
        else:
            bq = it - 10; u = bq // 2; m = bq % 2
            s = sb[bq] if rng.random() > EPS_SWAP else 1 - sb[bq]
            ev.append(("sub", int(bq), int(s)))
            if mode == "numbered":
                l = (lb[u] ^ m) if not mis else rng.integers(0, 2)
                ev.append(("lab", int(bq), int(l)))
    if mode == "unnumbered" and len(a_seen) > 1:
        a_seen.sort(key=lambda x: x[1]); seq = [q for q, _ in a_seen]
        for i in range(len(seq) - 1):
            if rng.random() < EPS_SWAP: seq[i], seq[i + 1] = seq[i + 1], seq[i]
        ev.append(("orderA", tuple(seq)))
    return ev

def score(ev, V, varc):
    ll = np.zeros(N); nll = 0.0
    for e in ev:
        t = e[0]
        if t == "posA":
            _, q, p = e
            ll += np.where(posA[:, q] == p, math.log(1 - EPS), math.log(EPS / 9)); nll += math.log(1 / 10)
        elif t == "lab":
            _, bq, l = e; u, m = bq // 2, bq % 2
            ll += np.where((lab[:, u] ^ m) == l, math.log(1 - EPS), math.log(EPS)); nll += math.log(0.5)
        elif t == "sub":
            _, bq, s = e
            ll += np.where(sub[:, bq] == s, math.log(1 - EPS_SWAP), math.log(EPS_SWAP)); nll += math.log(0.5)
        elif t == "var":
            _, it, v = e
            ll += np.where(varc[:, it] == v, math.log(1 - EPS_V), math.log(EPS_V / (V - 1))); nll += math.log(1 / V)
        elif t == "opt":
            _, q, o = e
            ll += np.where(opt[:, q] == o, math.log(1 - EPS), math.log(EPS / 23)); nll += math.log(1 / 24)
        elif t == "orderA":
            seq = e[1]
            for i in range(len(seq)):
                for j in range(i + 1, len(seq)):
                    ll += np.where(posA[:, seq[i]] < posA[:, seq[j]], math.log(1 - EPS_SWAP), math.log(EPS_SWAP))
            nll += -math.log(math.factorial(len(seq)))
    return ll, nll

def decide(ll, nll, tau):
    o = np.argsort(ll)[::-1]
    if ll[o[0]] - ll[o[1]] >= tau and ll[o[0]] - nll >= tau + math.log(N):
        return int(o[0])
    return None

def run(mode, k, V, tau):
    varc = make_var(V)
    c = w = a = fa = top5 = 0
    sl_sizes = []
    for _ in range(TRIALS):
        src = int(rng.integers(0, N))
        ll, nll = score(leak(src, k, mode, V, varc), V, varc)
        shortlist = int((ll >= ll[src] - 1e-9).sum())   # colleges at least as likely as the true source (ties count against us)
        top5 += shortlist <= 5
        sl_sizes.append(shortlist)
        d = decide(ll, nll, tau)
        if d is None: a += 1
        elif d == src: c += 1
        else: w += 1
        if decide(*score(leak(0, k, mode, V, varc, outside=True), V, varc), tau) is not None:
            fa += 1
    return dict(mode=mode, k=k, V=V, tau=tau, correct=c / TRIALS, wrong=w / TRIALS,
                abstain=a / TRIALS, false_accusation_outside_copy=fa / TRIALS, source_in_top5=top5 / TRIALS, median_shortlist=float(np.median(sl_sizes)))

ODDS = float(os.environ.get("LEAKTRACE_ODDS", "10000"))   # name a college only at these odds (9.2 nats)
TAU = math.log(ODDS)
configs = [("numbered", 1), ("numbered", 4), ("unnumbered", 1), ("unnumbered", 4), ("mcq", 1)]
results = []
for mode, V in configs:
    for k in range(2, 11):
        r = run(mode, k, V, TAU); results.append(r)
        print(f"{mode:10s} V={V} k={k:2d} correct={r['correct']*100:5.1f}% wrong={r['wrong']*100:4.2f}% "
              f"abstain={r['abstain']*100:5.1f}% false-acc={r['false_accusation_outside_copy']*100:4.2f}% top5={r['source_in_top5']*100:5.1f}% median-shortlist={r['median_shortlist']:.0f}")
meta = dict(n_colleges=N, trials=TRIALS, eps_item=EPS, eps_variant=EPS_V, eps_swap=EPS_SWAP,
            tau_nats=round(TAU, 2), union_bound_correction="tau + ln(N) vs outside-copy null")
json.dump(dict(meta=meta, results=results), open(f"{OUT}/sim_results.json", "w"), indent=1)
print(json.dumps(meta))
