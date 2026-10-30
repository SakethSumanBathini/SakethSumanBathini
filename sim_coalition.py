"""
Leak Trace — coalition-aware decoder (stage 2) and collusion test.

Stage 1 is the single-college rule from sim_decode.py: accuse college c only if
it beats the runner-up by tau and an outside-copy null by tau + ln N. Added here:
a stage-1 accusation is kept only if the leak looks single-source, i.e. no pair
of colleges explains the non-order evidence e^tau times better than c alone
(CHECK_SINGLE_SOURCE). Otherwise the leak is treated as mixed and goes to stage 2.

Stage 2 runs only when stage 1 abstains. It asks "which colleges' copies could
this leak have been assembled from?" using a two-source mixture model: each
leaked item comes from copy A or copy B with probability 1/2 (A = B allowed,
which is the single-source case). The pair log-likelihood for every pair of
colleges is computed at once as  sum_items  X_i T_i X_i^T  (one-hot item states
times a small mixture table), so all 125,250 pairs cost a few milliseconds.
A college m is named as a source only if
  (1) the best pair P* contains m,
  (2) P* beats the best pair WITHOUT m by tau,
  (3) P* beats the outside-copy null by tau + ln(N + N(N-1)/2)  (union bound), and
  (4) when P* = (m, partner) with partner != m, P* also beats "partner's copy mixed
      with an unknown outside copy" by tau + ln N, so that a few items that happen
      to match some innocent college cannot get it named (union bound over N).
So stage 2 can name 0, 1 or 2 colleges, and names a college only when every
explanation that leaves it out is at least e^tau = ODDS times less likely (10,000 by default;
set LEAKTRACE_ODDS to change it).

Scenarios tested (same codebook, same noise):
  single  : the leak comes from one college's copy
  mix2    : two colleges' copies mixed, each item taken from A or B at random
  outside : a copy that is not in the codebook at all (e.g. a fabricated paper)
"""
import json, math, os, sys, itertools
import numpy as np

rng = np.random.default_rng(41)
N = 500
EPS, EPS_V, EPS_SWAP = 0.02, 0.05, 0.03
V = 4
ODDS = float(os.environ.get("LEAKTRACE_ODDS", "10000"))   # name a college only at these odds (9.2 nats)
TAU = math.log(ODDS)
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
varc = rng.integers(0, V, (N, 20))


# ------------------------------------------------------------------ leaks ----
def copy_of(c):
    if c == "outside":
        return dict(pA=rng.permutation(10), lb=rng.integers(0, 2, 5), sb=rng.integers(0, 2, 10),
                    vr=rng.integers(0, V, 20), op=rng.integers(0, len(OPTP), 20))
    return dict(pA=posA[c], lb=lab[c], sb=sub[c], vr=varc[c], op=opt[c])


def make_leak(sources, k, mode):
    """Return (items, orderA). Each item is a list of evidence tuples that share
    one latent source copy. orderA is the retyped order of Part A items (unnumbered)."""
    copies = [copy_of(s) for s in sources]
    items, a_seen = [], []
    if mode == "mcq":
        for q in rng.choice(20, k, replace=False):
            cp = copies[rng.integers(len(copies))]
            o = cp["op"][q] if rng.random() > EPS else rng.integers(0, len(OPTP))
            items.append([("opt", int(q), int(o))])
        return items, None
    for it in rng.choice(20, k, replace=False):
        cp = copies[rng.integers(len(copies))]
        mis = rng.random() < EPS
        v = cp["vr"][it] if rng.random() > EPS_V else rng.integers(0, V)
        ev = [("var", int(it), int(v))]
        if it < 10:
            q = it if not mis else int(rng.integers(0, 10))
            if mode == "numbered":
                ev.append(("posA", int(q), int(cp["pA"][it])))
            else:
                a_seen.append((int(q), int(cp["pA"][it])))
        else:
            bq = it - 10; u = bq // 2; m = bq % 2
            s = cp["sb"][bq] if rng.random() > EPS_SWAP else 1 - cp["sb"][bq]
            ev.append(("sub", int(bq), int(s)))
            if mode == "numbered":
                l = (cp["lb"][u] ^ m) if not mis else int(rng.integers(0, 2))
                ev.append(("lab", int(bq), int(l)))
        items.append(ev)
    order = None
    if mode == "unnumbered" and len(a_seen) > 1:
        a_seen.sort(key=lambda x: x[1]); order = [q for q, _ in a_seen]
        for i in range(len(order) - 1):
            if rng.random() < EPS_SWAP: order[i], order[i + 1] = order[i + 1], order[i]
    return items, order


# ---------------------------------------------------------------- scoring ----
def element(e):
    """-> (match vector over colleges, log p if match, log p if not, log p under null)"""
    t = e[0]
    if t == "posA":
        _, q, p = e; return posA[:, q] == p, math.log(1 - EPS), math.log(EPS / 9), math.log(1 / 10)
    if t == "lab":
        _, bq, l = e; u, m = bq // 2, bq % 2
        return (lab[:, u] ^ m) == l, math.log(1 - EPS), math.log(EPS), math.log(0.5)
    if t == "sub":
        _, bq, s = e; return sub[:, bq] == s, math.log(1 - EPS_SWAP), math.log(EPS_SWAP), math.log(0.5)
    if t == "var":
        _, it, v = e; return varc[:, it] == v, math.log(1 - EPS_V), math.log(EPS_V / (V - 1)), math.log(1 / V)
    if t == "opt":
        _, q, o = e; return opt[:, q] == o, math.log(1 - EPS), math.log(EPS / 23), math.log(1 / 24)
    raise ValueError(t)


def single_scores(items, order):
    ll = np.zeros(N); nll = 0.0
    for ev in items:
        for e in ev:
            m, hi, lo, nl = element(e); ll += np.where(m, hi, lo); nll += nl
    if order:
        for i in range(len(order)):
            for j in range(i + 1, len(order)):
                ll += np.where(posA[:, order[i]] < posA[:, order[j]], math.log(1 - EPS_SWAP), math.log(EPS_SWAP))
        nll += -math.log(math.factorial(len(order)))
    return ll, nll


def pair_scores(items):
    """N x N matrix of two-source mixture log-likelihoods (order evidence not used),
    plus Q[y] = log-likelihood of "college y's copy mixed with an unknown outside copy"."""
    P = np.zeros((N, N)); Q = np.zeros(N); nll = 0.0
    for ev in items:
        els = [element(e) for e in ev]
        J = len(els); S = 1 << J
        state = np.zeros(N, dtype=np.int64); item_null = 0.0
        for j, (m, _, _, nl) in enumerate(els):
            state |= (m.astype(np.int64) << j); item_null += nl
        nll += item_null
        ell = np.array([sum(els[j][1] if (s >> j) & 1 else els[j][2] for j in range(J)) for s in range(S)])
        T = np.logaddexp.outer(ell, ell) - math.log(2)
        X = np.eye(S)[state]                       # N x S one-hot
        P += X @ T @ X.T
        Q += np.logaddexp(ell[state], item_null) - math.log(2)
    return P, Q, nll


def decide_single(ll, nll):
    o = np.argsort(ll)[::-1]
    if ll[o[0]] - ll[o[1]] >= TAU and ll[o[0]] - nll >= TAU + math.log(N):
        return int(o[0])
    return None


LOG_H = math.log(N + N * (N - 1) / 2)


TRIU = np.triu(np.ones((N, N), bool))


def decide_members(P, Q, nll):
    U = np.where(TRIU, P, -np.inf)
    a, b = (int(x) for x in np.unravel_index(np.argmax(U), U.shape))
    best = P[a, b]
    if best - nll < TAU + LOG_H:
        return set()
    named = set()
    for m, partner in ((a, b), (b, a)):
        if m in named:
            continue
        W = U.copy(); W[m, :] = -np.inf; W[:, m] = -np.inf
        if best - W.max() < TAU:
            continue                 # some explanation without m is nearly as good
        if m != partner and best - Q[partner] < TAU + math.log(N):
            continue                 # m's share could be an unknown outside copy (union bound over N)
        named.add(m)
    return named


CHECK_SINGLE_SOURCE = True


def trace(items, order):
    ll, nll = single_scores(items, order)
    d = decide_single(ll, nll)
    P, Q, pnll = pair_scores(items)
    if d is not None:
        # Accept a stage-1 accusation only if the leak looks single-source: no pair of
        # colleges explains the non-order evidence e^tau times better than d alone.
        # (Under mixing the single-source model is wrong, and the order channel can
        # then favour an innocent college whose order happens to fit the merged leak.)
        if not CHECK_SINGLE_SOURCE or np.max(P) - P[d, d] < TAU:
            return {d}, 1, ll
    return decide_members(P, Q, pnll), 2, ll


# ------------------------------------------------------------------ runs -----
TRIALS_BY_SCENARIO = {"mix2": 3000, "single": 1000, "outside": 1000}


def run(mode, k, scenario):
    TRIALS = TRIALS_BY_SCENARIO[scenario]
    named_any_true = named_both = innocent = abstain = stage2_hits = 0
    one5 = 0; innocent_stage = []
    for _ in range(TRIALS):
        if scenario == "outside":
            src = ["outside"]
        elif scenario == "single":
            src = [int(rng.integers(0, N))]
        else:
            src = [int(x) for x in rng.choice(N, 2, replace=False)]
        items, order = make_leak(src, k, mode)
        named, stage, ll = trace(items, order)
        truth = set(s for s in src if s != "outside")
        if not named:
            abstain += 1
        elif named - truth:
            innocent += 1; innocent_stage.append(stage)
        else:
            named_any_true += 1
            named_both += (len(truth) == 2 and named == truth)
            stage2_hits += (stage == 2)
        top5 = set(np.argsort(ll)[::-1][:5].tolist())
        one5 += bool(truth & top5)
    r = dict(mode=mode, k=k, scenario=scenario, named_only_true_sources=named_any_true / TRIALS,
             named_both_colluders=named_both / TRIALS, named_an_innocent=innocent / TRIALS,
             abstain=abstain / TRIALS, correct_via_stage2=stage2_hits / TRIALS,
             a_true_source_in_single_top5=one5 / TRIALS, innocent_naming_stages=innocent_stage)
    print(f"{scenario:7s} {mode:10s} k={k:2d} true-only={r['named_only_true_sources']*100:5.1f}% "
          f"both={r['named_both_colluders']*100:5.1f}% innocent={r['named_an_innocent']*100:4.2f}% "
          f"abstain={r['abstain']*100:5.1f}% via-stage2={r['correct_via_stage2']*100:5.1f}% "
          f"top5={r['a_true_source_in_single_top5']*100:5.1f}% innocent-stages={innocent_stage}", flush=True)
    return r


if __name__ == "__main__":
    # optional second argument: comma-separated scenarios to run (default: all three)
    scenarios = sys.argv[2].split(",") if len(sys.argv) > 2 else ["mix2", "single", "outside"]
    results = []
    for scenario in scenarios:
        for mode in ("numbered", "unnumbered", "mcq"):
            for k in (4, 6, 8, 10, 12):
                results.append(run(mode, k, scenario))
    meta = dict(n_colleges=N, trials=TRIALS_BY_SCENARIO, wording_variants=V, eps_item=EPS, eps_variant=EPS_V,
                eps_swap=EPS_SWAP, tau_nats=round(TAU, 2), stage2_null_threshold_nats=round(TAU + LOG_H, 2),
                single_source_check=CHECK_SINGLE_SOURCE,
                mix2="each leaked item copied from college A or B at random")
    name = "coalition_results.json" if len(scenarios) == 3 else f"coalition_results_{'_'.join(scenarios)}.json"
    json.dump(dict(meta=meta, results=results), open(f"{OUT}/{name}", "w"), indent=1)
