"""
Leak Trace — Reed-Solomon codebook for the MCQ option-order channel (framing test).

Why: with a random codebook, two colleges that pool their copies can, by rare
chance, produce a leak that matches a THIRD college's copy on every leaked item
("framing"). Fingerprinting theory has the fix: a code with minimum distance
d > n(1 - 1/c^2) is c-traceable -- the codeword closest to any mix of c
colluders' copies is always one of the colluders (Chor-Fiat-Naor; Staddon,
Stinson & Wei 2001).

Construction: each MCQ question shows its 4 options in one of 24 orders; we use
23 of them as the symbols of GF(23). College c gets the polynomial
f_c(x) = m0 + m1*x over GF(23) (529 possible colleges) and question i shows
option order f_c(i). Two different colleges agree on at most ONE question.
For k leaked questions (no noise) with two colluders, one colluder supplied
>= k/2 of them, while any innocent matches at most 2 (one per colluder), so for
k >= 5 the closest college is always a colluder, and an innocent can never be
framed. Three colluders: guaranteed for k >= 10.

This script compares that code with the random codebook used in sim_decode.py,
under the same noise model and the same two-stage decoder (stage 1 single
source + single-source check; stage 2 two-source mixture; see sim_coalition.py).
"""
import json, math, os, sys
import numpy as np

rng = np.random.default_rng(23)
N, Q = 500, 20
EPS = 0.02                       # an option order is mis-read (any of 24 orders)
ODDS = float(os.environ.get("LEAKTRACE_ODDS", "10000"))   # name a college only at these odds (9.2 nats)
TAU = math.log(ODDS)
TRIALS = 2000
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
LOG_HIT, LOG_MISS, LOG_NULL = math.log(1 - EPS), math.log(EPS / 23), math.log(1 / 24)
LOG_PAIRS = math.log(N + N * (N - 1) / 2)


def random_code():
    return rng.integers(0, 24, (N, Q))


def rs_code(p=23):
    msgs = rng.choice(p * p, N, replace=False)
    m0, m1 = msgs // p, msgs % p
    x = np.arange(Q)
    return (m0[:, None] + m1[:, None] * x[None, :]) % p


def leak(code, sources, k):
    qs = rng.choice(Q, k, replace=False)
    obs = []
    for q in qs:
        s = sources[rng.integers(len(sources))]
        sym = code[s, q] if s is not None else rng.integers(0, 24)
        if rng.random() < EPS:
            sym = rng.integers(0, 24)
        obs.append((int(q), int(sym)))
    return obs


IU0, IU1 = np.triu_indices(N)          # all pairs a <= b (a == b is the single-source case)


def decode(code, obs):
    qs = np.array([q for q, _ in obs]); syms = np.array([s for _, s in obs])
    M = (code[:, qs] == syms[None, :]).astype(float)          # N x k match matrix
    k = len(obs); r = M.sum(1)
    ll = r * LOG_HIT + (k - r) * LOG_MISS; nll = k * LOG_NULL
    # two-source mixture scores for every pair, from match counts
    A11 = M @ M.T
    t = lambda x, y: np.logaddexp(x, y) - math.log(2)
    T00, T01, T11 = t(LOG_MISS, LOG_MISS), t(LOG_MISS, LOG_HIT), t(LOG_HIT, LOG_HIT)
    P = (T00 * (k - r[:, None] - r[None, :] + A11) + T01 * (r[None, :] - A11)
         + T01 * (r[:, None] - A11) + T11 * A11)
    Pv = P[IU0, IU1]
    Qv = r * t(LOG_HIT, LOG_NULL) + (k - r) * t(LOG_MISS, LOG_NULL)
    # stage 1 + single-source check
    o = np.argsort(ll)[::-1]
    if ll[o[0]] - ll[o[1]] >= TAU and ll[o[0]] - nll >= TAU + math.log(N):
        d = int(o[0])
        if Pv.max() - P[d, d] < TAU:
            return {d}, ll, r
    # stage 2: name m only if every pair without m is e^tau times less likely
    j = int(np.argmax(Pv)); a, b = int(IU0[j]), int(IU1[j]); best = Pv[j]
    named = set()
    if best - nll >= TAU + LOG_PAIRS:
        for m, partner in ((a, b), (b, a)):
            if m in named:
                continue
            without = Pv[(IU0 != m) & (IU1 != m)].max()
            if best - without < TAU:
                continue
            if m != partner and best - Qv[partner] < TAU + math.log(N):
                continue
            named.add(m)
    return named, ll, r


def run(code_name, code, scenario, k):
    named_true = innocent = abstain = closest_is_source = 0
    for _ in range(TRIALS):
        if scenario == "outside":
            src = [None]
        else:
            n_src = {"single": 1, "mix2": 2, "mix3": 3}[scenario]
            src = [int(x) for x in rng.choice(N, n_src, replace=False)]
        obs = leak(code, src, k)
        named, ll, r = decode(code, obs)
        truth = set(s for s in src if s is not None)
        if not named: abstain += 1
        elif named - truth: innocent += 1
        else: named_true += 1
        if truth:
            top = np.flatnonzero(r == r.max())
            closest_is_source += (len(top) == 1 and int(top[0]) in truth)
    res = dict(code=code_name, scenario=scenario, k=k, named_only_true=named_true / TRIALS,
               named_innocent=innocent / TRIALS, abstain=abstain / TRIALS,
               closest_college_is_a_source=closest_is_source / TRIALS)
    print(f"{code_name:6s} {scenario:7s} k={k:2d} true={res['named_only_true']*100:5.1f}% "
          f"innocent={res['named_innocent']*100:5.2f}% abstain={res['abstain']*100:5.1f}% "
          f"closest-is-source={res['closest_college_is_a_source']*100:5.1f}%", flush=True)
    return res


codes = {"random": random_code(), "rs23": rs_code()}
agree = {name: int(max((c[i] == c[j]).sum() for i in range(0, N, 7) for j in range(i + 1, N, 5)))
         for name, c in codes.items()}
print("max pairwise agreement (sampled pairs):", agree, flush=True)
results = []
plan = [("single", (4, 6)), ("mix2", (4, 5, 6, 8, 10)), ("mix3", (6, 8, 10, 12)), ("outside", (6, 10))]
for scenario, ks in plan:
    for name, code in codes.items():
        for k in ks:
            results.append(run(name, code, scenario, k))
json.dump(dict(meta=dict(n_colleges=N, questions=Q, eps=EPS, tau_nats=round(TAU, 2), trials=TRIALS,
                         rs="GF(23), f(x)=m0+m1*x, x=0..19, symbols = 23 of the 24 option orders"),
               results=results), open(f"{OUT}/rs_mcq_results.json", "w"), indent=1)
