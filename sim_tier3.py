"""
Leak Trace — Tier 3: marks a leaker cannot cheaply remove, because changing them makes the leaked answers wrong.

Tiers 1 and 2 (question order, approved wordings, option order) survive retyping, but a
leaker who rewords every question AND shuffles them can erase them. Tier 3 uses content
the leak cannot do without:

1. Answer keys. Each college's MCQ options are arranged so that its answer key (the letter
   of the right option for each printed question) is a codeword of a quaternary linear
   code, shifted by the setter's master key:  key_c = master + C_c  over GF(4).
   Any two colleges' keys differ in at least d of n answers, and every college's key
   differs from the master key (never issued) in at least d answers, so a leaked key
   that matches the master points upstream, to the setter or the press.
2. Numeric values. Each numerical question has A approved parameter sets of equal
   difficulty (e.g. two numbers with four approved values each, A = 16); college c gets
   set p[c][q]. Rewording or shuffling cannot remove the numbers: they decide the answer.
3. The guarantee. For a copy from outside the system, the chance that ANY college clears
   the bar against an outside copy (T * N) is at most 1/T, and stays at most 1/T while
   lines arrive one at a time (Markov / Ville). We check this empirically.

Usage: python3 sim_tier3.py [out_dir]
"""
import itertools, json, math, os, sys, time
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "results"
rng = np.random.default_rng(31)
N = 500
ODDS = float(os.environ.get("LEAKTRACE_ODDS", "10000"))
TAU = math.log(ODDS)
LOG = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


# ---------------------------------------------------------------- GF(4) linear code
# elements 0, 1, w, w^2 coded as 0, 1, 2, 3; addition is XOR; w^2 = w + 1
MUL = np.array([[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 3, 1], [0, 3, 1, 2]], dtype=np.uint8)


def codewords(G):
    k, n = G.shape
    msgs = np.array(list(itertools.product(range(4), repeat=k)), dtype=np.uint8)
    cw = np.zeros((len(msgs), n), dtype=np.uint8)
    for i in range(k):
        cw ^= MUL[msgs[:, i][:, None], G[i][None, :]]
    return cw


def profile(G):
    w = (codewords(G) != 0).sum(1)[1:]
    d = int(w.min())
    return d, int((w == d).sum())


def search_code(n, k, iters, seed):
    r = np.random.default_rng(seed)
    P = r.integers(0, 4, (k, n - k), dtype=np.uint8)
    G = np.hstack([np.eye(k, dtype=np.uint8), P])
    best = profile(G)
    for _ in range(iters):
        i, j = r.integers(k), r.integers(n - k)
        old = P[i, j]
        P[i, j] = r.integers(0, 4)
        G[:, k:] = P
        cand = profile(G)
        if (cand[0], -cand[1]) >= (best[0], -best[1]):
            best = cand
        else:
            P[i, j] = old
    G[:, k:] = P
    return G, best


def answer_key_code(n=20, k=5):
    t0 = time.time()
    best_G, best = None, (0, 0)
    for seed in range(6):
        G, prof = search_code(n, k, 6000, 100 + seed)
        if (prof[0], -prof[1]) > (best[0], -best[1]):
            best_G, best = G.copy(), prof
    cw = codewords(best_G)
    say(f"quaternary [{n},{k}] code: minimum distance {best[0]} ({best[1]} codewords of that weight), search {time.time() - t0:.1f}s")
    # Fairness: relabel the four letters separately at each of the 20 positions (a bijection per position keeps
    # every pairwise distance), searching for labels under which as many keys as possible use each letter 3-7 times
    # and put 8-12 right answers in the middle positions B and C (test-takers favour the middle; Attali & Bar-Hillel
    # 2003). The master key is the image of the zero codeword.
    nz = cw[1:]
    perms = np.array(list(itertools.permutations(range(4))), dtype=np.uint8)
    def labelled(P):
        return perms[P][np.arange(n)[None, :], nz]
    def fit(P):
        kk = labelled(P)
        cnt = np.stack([(kk == a).sum(1) for a in range(4)], 1)
        md = cnt[:, 1] + cnt[:, 2]
        ok1 = (cnt.min(1) >= 3) & (cnt.max(1) <= 7) & (md >= 8) & (md <= 12)
        ok2 = ok1 & (cnt.min(1) >= 4) & (cnt.max(1) <= 6) & (md >= 9) & (md <= 11)
        return int(ok1.sum()), int(ok2.sum())
    lr = np.random.default_rng(11)
    best_P, best_fit = None, (-1, -1)
    for _ in range(12):
        P = lr.integers(0, 24, n)
        cur = fit(P)
        for _ in range(4000):
            j = lr.integers(n); old = P[j]; P[j] = lr.integers(24)
            f = fit(P)
            if f >= cur:
                cur = f
            else:
                P[j] = old
        if cur > best_fit:
            best_fit, best_P = cur, P.copy()
    global KEY_LABELS
    KEY_LABELS = perms[best_P].tolist()               # KEY_LABELS[j][symbol] = letter index at position j
    keys = labelled(best_P)
    master = perms[best_P][np.arange(n), 0].astype(np.uint8)
    counts = np.stack([(keys == a).sum(1) for a in range(4)], 1)
    md = counts[:, 1] + counts[:, 2]
    in_range = (counts.min(1) >= 3) & (counts.max(1) <= 7) & (md >= 8) & (md <= 12)
    tight = (counts.max(1) - counts.min(1)) + np.abs(md - n // 2)
    order = np.lexsort((np.arange(len(keys)), tight, ~in_range))[:N]
    order = np.sort(order)                            # colleges in message order
    chosen = keys[order]
    cc = counts[order]; mm = md[order]
    pair_min = min(int((chosen[i] != chosen[j]).sum()) for i in range(N) for j in range(i + 1, N))
    say(f"answer keys for {N} colleges: each letter appears {int(cc.min())}-{int(cc.max())} times in 20, "
        f"{int(mm.min())}-{int(mm.max())} right answers in the middle positions B and C; "
        f"closest two keys differ in {pair_min} answers; every key differs from the master in >= {int((chosen != master).sum(1).min())}")
    global KEY_MESSAGES
    KEY_MESSAGES = [int(i) + 1 for i in order]        # message numbers 1..1023 (0 is the master)
    return chosen, master, best[0], best_G


# ---------------------------------------------------------------- answer-key decoder
# mix_ll accepts several error rates and averages over them (a mixture is still a proper likelihood, so the
# outside-copy guarantee holds unchanged). One rate decoded best in our tests: a mixture pays up to ln(#rates) nats.
DELTAS = (0.2,)   # one wrong answer in five; a single rate decoded best in our tests
KEY_MESSAGES = []
KEY_LABELS = []


def mix_ll(r, k, alphabet, rates):
    """log of the average over error rates of P(leak | candidate); r = matches per candidate out of k."""
    terms = [r * math.log(1 - e) + (k - r) * math.log(e / (alphabet - 1)) for e in rates]
    return np.logaddexp.reduce(np.stack(terms), 0) - math.log(len(rates))


def key_decode(cands, idx, letters, n_colleges):
    """cands: candidate keys (colleges + master as the last row). Returns (named index or None, ll, nll)."""
    r = (cands[:, idx] == letters[None, :]).sum(1)
    k = len(idx)
    ll = mix_ll(r, k, 4, DELTAS)
    nll = k * math.log(1 / 4)
    o = np.argsort(ll)[::-1]
    named = None
    if ll[o[0]] - ll[o[1]] >= TAU and ll[o[0]] - nll >= TAU + math.log(n_colleges + 1):
        named = int(o[0])
    return named, ll, nll


def shortlist_rank(ll, src):
    """colleges at least as likely as the true source, ties counted against us"""
    return int((ll >= ll[src] - 1e-9).sum())


def key_leak(key, k, delta_true, n):
    idx = np.sort(rng.choice(n, k, replace=False))
    letters = key[idx].copy()
    wrong = rng.random(k) < delta_true
    letters[wrong] = (letters[wrong] + rng.integers(1, 4, wrong.sum())) % 4   # a different letter
    return idx, letters.astype(np.uint8)


def run_keys(keys, master, label, n=20, trials=3000):
    cands = np.vstack([keys, master[None, :]])
    rows = []
    for delta in (0.0, 0.1, 0.2, 0.3):
        for k in range(4, n + 1, 2):
            named = wrong = top5 = 0
            for _ in range(trials):
                src = int(rng.integers(N))
                idx, letters = key_leak(cands[src], k, delta, n)
                d, ll, _ = key_decode(cands, idx, letters, N)
                if d is None:
                    pass
                elif d == src:
                    named += 1
                else:
                    wrong += 1
                top5 += shortlist_rank(ll, src) <= 5
            rows.append(dict(code=label, delta=delta, k=k, named=named / trials, wrong=wrong, top5=top5 / trials, trials=trials))
        say(f"  {label:7s} solver errors {int(delta * 100):2d}%: named " +
            " ".join(f"k={r['k']}:{r['named'] * 100:.0f}%" for r in rows if r['delta'] == delta and r['code'] == label) +
            f" | wrong {sum(r['wrong'] for r in rows if r['delta'] == delta and r['code'] == label)}")
    # leaks of the master key (the setter's or printer's copy): should point upstream, never at a college
    up = wrong_up = 0
    for _ in range(trials):
        idx, letters = key_leak(master, 16, 0.1, n)
        d, _, _ = key_decode(cands, idx, letters, N)
        up += d == N
        wrong_up += d is not None and d != N
    say(f"  {label:7s} master-key leaks (16 answers, 10% errors): traced upstream {up / trials * 100:.1f}%, pinned on a college {wrong_up}")
    return rows, dict(code=label, upstream=up / trials, pinned_on_college=wrong_up, trials=trials)


# ---------------------------------------------------------------- numeric-value channel
def greedy_code(A, n, n_words, max_agree, seed):
    r = np.random.default_rng(seed)
    code = np.empty((0, n), dtype=np.int16)
    tries = 0
    while len(code) < n_words:
        c = r.integers(0, A, n).astype(np.int16)
        tries += 1
        if not len(code) or (code == c[None, :]).sum(1).max() <= max_agree:
            code = np.vstack([code, c])
        if tries > 3_000_000:
            raise RuntimeError("code search failed")
    return code


EPS_NUM = (0.05,)


def run_numeric(trials=3000, n=8, eps_true=0.03):
    rows = []
    for A, agree in ((4, 5), (16, 2), (64, 1)):
        code = greedy_code(A, n, N, agree, 7 + A)
        ln0 = math.log(1 / A)
        line = []
        for k in range(2, n + 1):
            named = wrong = top5 = 0
            for _ in range(trials):
                src = int(rng.integers(N))
                qs = rng.choice(n, k, replace=False)            # reworded and shuffled: only the numbers survive
                sym = code[src, qs].copy()
                bad = rng.random(k) < eps_true
                sym[bad] = (sym[bad] + rng.integers(1, A, bad.sum())) % A
                M = code[:, qs] == sym[None, :]
                r_ = M.sum(1)
                ll = mix_ll(r_, k, A, EPS_NUM)
                nll = k * ln0
                o = np.argsort(ll)[::-1]
                if ll[o[0]] - ll[o[1]] >= TAU and ll[o[0]] - nll >= TAU + math.log(N):
                    named += int(o[0]) == src
                    wrong += int(o[0]) != src
                top5 += shortlist_rank(ll, src) <= 5
            rows.append(dict(A=A, k=k, named=named / trials, wrong=wrong, top5=top5 / trials, trials=trials, max_agree=agree))
            line.append(f"k={k}:{named / trials * 100:.0f}%")
        say(f"  numeric values, {A:2d} approved sets per question (any two colleges share <= {agree} of {n}): named " + " ".join(line) +
            f" | wrong {sum(r['wrong'] for r in rows if r['A'] == A)}")
    return rows


# ---------------------------------------------------------------- the guarantee, checked
def perm_code(n_slots, n_words, max_agree, seed):
    r = np.random.default_rng(seed)
    code = []
    while len(code) < n_words:
        c = r.permutation(n_slots)
        if not code or (np.array(code) == c).sum(1).max() <= max_agree:
            code.append(c)
    return np.array(code)


def bound_check(copies=200_000, batch=500):
    """Outside copies, read one line at a time. For each T, how often does ANY college's
    likelihood ratio against the outside-copy model reach T * N, at the end (fixed k) or at
    any line along the way (anytime)? The guarantee says at most 1/T in both cases."""
    Ts = [10.0, 100.0, 1000.0, 10000.0]
    out = {}
    # (a) Part A: numbered lines, positions + approved wordings (the decoder's model, V = 4, Q = 10)
    Q, V, EPS, EPS_V = 10, 4, 0.02, 0.05
    POS = perm_code(Q, N, 4, 2026)
    VAR = np.random.default_rng(99).integers(0, V, (N, Q))
    ph, pm = math.log((1 - EPS) * Q), math.log(EPS / (Q - 1) * Q)
    vh, vm = math.log((1 - EPS_V) * V), math.log(EPS_V / (V - 1) * V)
    for kind in ("model", "realistic"):
        hits_any = {T: 0 for T in Ts}
        hits_end = {T: 0 for T in Ts}
        done = 0
        while done < copies:
            b = min(batch, copies - done)
            order = np.argsort(rng.random((b, Q)), 1)                    # which question each line is
            if kind == "model":
                pos = rng.integers(0, Q, (b, Q))                          # independent uniform (the null model)
            else:
                pos = np.argsort(rng.random((b, Q)), 1)                   # a real paper: a random permutation
            var = rng.integers(0, V, (b, Q))
            # per line, per college: log-likelihood ratio against the outside-copy model
            qline = order                                                 # b x Q (question id on line t)
            p_line = np.take_along_axis(pos, qline, 1)
            v_line = np.take_along_axis(var, qline, 1)
            POSq = POS[:, qline]                                          # N x b x Q
            VARq = VAR[:, qline]
            lr = np.where(POSq == p_line[None], ph, pm) + np.where(VARq == v_line[None], vh, vm)
            cum = np.cumsum(lr, 2)                                        # N x b x Q
            best_t = cum.max(0)                                           # b x Q: best college after t lines
            for T in Ts:
                bar = math.log(T * N)
                hits_any[T] += int((best_t >= bar).any(1).sum())
                hits_end[T] += int((best_t[:, 6] >= bar).sum())         # a fixed 7-line leak
            done += b
        out[f"partA_{kind}"] = dict(copies=copies, lines=Q,
                                    anytime={str(int(T)): hits_any[T] / copies for T in Ts},
                                    fixed_7_lines={str(int(T)): hits_end[T] / copies for T in Ts})
        say(f"  Part A outside copies ({kind}), {copies:,}: " + ", ".join(
            f"T={int(T):,}: any line {hits_any[T] / copies:.2e}, 7 lines {hits_end[T] / copies:.2e} (bound {1 / T:.0e})" for T in Ts))
    return out


def bound_check_keys(keys, master, copies=400_000, batch=250):
    Ts = [10.0, 100.0, 1000.0, 10000.0]
    cands = np.vstack([keys, master[None, :]])
    n = cands.shape[1]
    hits_any = {T: 0 for T in Ts}
    hits_end = {T: 0 for T in Ts}
    done = 0
    while done < copies:
        b = min(batch, copies - done)
        letters = rng.integers(0, 4, (b, n))
        match = (cands[:, None, :] == letters[None]).astype(np.int16)  # (N+1) x b x n
        r = np.cumsum(match, 2)                                          # matches after t answers
        t = np.arange(1, n + 1)[None, None, :]
        lr = mix_ll(r, t, 4, DELTAS) - t * math.log(1 / 4)               # mixture likelihood ratio after t answers
        best_t = lr.max(0)
        for T in Ts:
            bar = math.log(T * (N + 1))
            hits_any[T] += int((best_t >= bar).any(1).sum())
            hits_end[T] += int((best_t[:, -1] >= bar).sum())
        done += b
    say(f"  answer-key outside copies, {copies:,}: " + ", ".join(
        f"T={int(T):,}: any answer {hits_any[T] / copies:.2e}, full key {hits_end[T] / copies:.2e} (bound {1 / T:.0e})" for T in Ts))
    return dict(copies=copies, answers=n, anytime={str(int(T)): hits_any[T] / copies for T in Ts},
                full_key={str(int(T)): hits_end[T] / copies for T in Ts})


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    say(f"Leak Trace tier 3 — {N} colleges, naming bar {ODDS:,.0f}:1")
    keys, master, dmin, G = answer_key_code()
    rand_keys = rng.integers(0, 4, (N, 20)).astype(np.uint8)
    rmin = min(int((rand_keys[i] != rand_keys[j]).sum()) for i in range(N) for j in range(i + 1, N))
    say(f"random keys for comparison: closest two differ in {rmin} answers")
    say("answer-key leaks (decoder assumes up to one wrong answer in five):")
    rows_code, up_code = run_keys(keys, master, "code")
    rows_rand, up_rand = run_keys(rand_keys, master, "random")
    say("numeric values, reworded and shuffled (only the numbers survive):")
    rows_num = run_numeric()
    say("the guarantee, checked on outside copies:")
    bc = bound_check()
    bk = bound_check_keys(keys, master)
    res = dict(meta=dict(n_colleges=N, odds=ODDS, tau_nats=round(TAU, 3), answer_key_code=f"quaternary linear [20,5,{dmin}] shifted by a balanced master key",
                         answer_key_min_distance=dmin, random_key_min_distance=rmin, delta_mixture=list(DELTAS),
                         numeric=dict(questions=8, eps_true=0.03, eps_mixture=list(EPS_NUM)), seconds=round(time.time() - t0, 1)),
               generator_matrix=G.tolist(), key_labels=KEY_LABELS, master_key="".join("ABCD"[x] for x in master), key_messages=KEY_MESSAGES,
               answer_keys=rows_code + rows_rand, master_leaks=[up_code, up_rand], numeric=rows_num,
               bound_partA=bc, bound_keys=bk)
    json.dump(res, open(f"{OUT}/tier3_results.json", "w"), indent=1)
    np.save(f"{OUT}/answer_keys_500.npy", keys)
    open(f"{OUT}/run_tier3.log", "w").write("\n".join(LOG) + "\n")
    say(f"done in {time.time() - t0:.0f}s")
