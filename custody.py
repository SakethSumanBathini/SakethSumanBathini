"""Key custody and tamper-evident fingerprints for Leak Trace.

What this module does
---------------------
1. Splits one secret master key into 3 shares; any 2 rebuild it (Shamir's secret
   sharing over the prime field 2^521 - 1). Give one share each to, say, the
   Controller of Exams, the Registrar and an outside observer. No single person
   can decode a leak, and no single person can quietly rebuild the codebook.
2. Derives every college's codeword from the key (HMAC-SHA256 as a random
   generator), so the college -> pattern table is never stored. The codes keep
   their structure, which is what bounds how alike two colleges can look:
     * descriptive papers: permutation code, any two colleges share at most 4
       question positions
     * MCQ option orders: Reed-Solomon code over GF(23), f(x) = m0 + m1*x at
       secret points, so any two colleges share at most 1 question's option order
3. Fingerprints all per-college PDFs as one Merkle root, signed by two
   officials (Ed25519). Send the signed root to every principal before the
   exam. Each college can prove which file it received, and nobody can swap a
   paper afterwards without the published root exposing it.
4. Keeps a hash-chained event log for internal audit. On its own a local log
   proves little (whoever runs the machine can rebuild it), which is why the
   root leaves the building in step 3.

Run `python3 custody.py` for a self-checking demo. Needs `cryptography`.
"""
import hashlib
import hmac
import itertools
import json
import secrets
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

PRIME = 2 ** 521 - 1          # Mersenne prime, larger than any 256-bit key


# ----------------------------------------------------------------------------- Shamir 2-of-3
def split_key(key: bytes, n: int = 3, t: int = 2) -> list:
    """Split `key` into n shares; any t of them rebuild it. Shares look like '2-9f3a...'."""
    secret = int.from_bytes(key, "big")
    coeffs = [secret] + [secrets.randbelow(PRIME) for _ in range(t - 1)]
    shares = []
    for x in range(1, n + 1):
        y = 0
        for c in reversed(coeffs):
            y = (y * x + c) % PRIME
        shares.append(f"{x}-{y:x}")
    return shares


def combine_shares(shares: list, length: int = 32) -> bytes:
    """Rebuild the key from t shares (Lagrange interpolation at x = 0)."""
    pts = [(int(s.split("-")[0]), int(s.split("-")[1], 16)) for s in shares]
    if len({x for x, _ in pts}) != len(pts):
        raise ValueError("duplicate shares")
    secret = 0
    for i, (xi, yi) in enumerate(pts):
        num, den = 1, 1
        for j, (xj, _) in enumerate(pts):
            if i != j:
                num = num * (-xj) % PRIME
                den = den * (xi - xj) % PRIME
        secret = (secret + yi * num * pow(den, PRIME - 2, PRIME)) % PRIME
    if secret >= 1 << (8 * length):
        raise ValueError("these shares do not rebuild a valid key")
    return secret.to_bytes(length, "big")


def key_fingerprint(key: bytes) -> str:
    """Public check value: confirms a rebuilt key is the right one, reveals nothing about it."""
    return hashlib.sha256(b"leaktrace-key-check" + key).hexdigest()[:16]


# ----------------------------------------------------------------------------- keyed random generator
class KeyedRNG:
    """Deterministic generator: HMAC-SHA256(key, label || counter). Same key and label, same stream."""

    def __init__(self, key: bytes, label: str):
        self.key, self.label, self.ctr, self.buf = key, label.encode(), 0, b""

    def _bytes(self, n: int) -> bytes:
        while len(self.buf) < n:
            self.ctr += 1
            self.buf += hmac.new(self.key, self.label + self.ctr.to_bytes(8, "big"), hashlib.sha256).digest()
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def randbelow(self, n: int) -> int:
        limit = (1 << 64) - ((1 << 64) % n)          # rejection sampling, no modulo bias
        while True:
            v = int.from_bytes(self._bytes(8), "big")
            if v < limit:
                return v % n

    def shuffle(self, items: list) -> list:
        for i in range(len(items) - 1, 0, -1):
            j = self.randbelow(i + 1)
            items[i], items[j] = items[j], items[i]
        return items


# ----------------------------------------------------------------------------- codebook from the key
def derive_codebook(key: bytes, exam_id: str, colleges: list, n_desc: int = 10, n_variants: int = 4,
                    max_agree: int = 4, n_mcq: int = 20) -> dict:
    """College -> codeword, rebuilt on demand from the key. Nothing here is ever written to disk."""
    if n_mcq > 23:
        raise ValueError("the GF(23) Reed-Solomon code supports at most 23 MCQs per paper")
    rng = KeyedRNG(key, f"{exam_id}|codebook|v1")
    n = len(colleges)

    # descriptive part: distance-constrained permutation code (greedy, key-driven)
    perms = []
    while len(perms) < n:
        p = rng.shuffle(list(range(n_desc)))
        if all(sum(a == b for a, b in zip(p, c)) <= max_agree for c in perms):
            perms.append(p)
    variants = [[rng.randbelow(n_variants) for _ in range(n_desc)] for _ in range(n)]

    # MCQ part: Reed-Solomon over GF(23) at secret evaluation points
    points = rng.shuffle(list(range(23)))[:n_mcq]
    messages = rng.shuffle([(m0, m1) for m0 in range(23) for m1 in range(23)])[:n]
    orders = ["".join(o) for o in itertools.permutations("ABCD")]          # 24 option orders
    symbol_to_order = rng.shuffle(list(range(24)))[:23]
    mcq = [[orders[symbol_to_order[(m0 + m1 * x) % 23]] for x in points] for (m0, m1) in messages]

    # secret assignment of codewords to colleges
    order = rng.shuffle(list(range(n)))
    book = {}
    for slot, college in zip(order, colleges):
        book[college] = {"positions": perms[slot], "variants": variants[slot], "mcq_orders": mcq[slot]}
    return book


# ----------------------------------------------------------------------------- Merkle fingerprint
def _h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def leaf_hash(college: str, pdf_bytes: bytes) -> bytes:
    return _h(b"\x00" + college.encode() + b"\x00" + _h(pdf_bytes))     # 0x00 = leaf (RFC 6962 style)


def merkle_tree(leaves: list):
    """Return (root, proofs) where proofs[i] lists (sibling_hash, sibling_is_right) up to the root."""
    level, idx = list(leaves), list(range(len(leaves)))
    proofs = [[] for _ in leaves]
    pos = {i: i for i in idx}
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        nxt = [_h(b"\x01" + level[i] + level[i + 1]) for i in range(0, len(level), 2)]   # 0x01 = node
        for leaf_i, p in pos.items():
            sib = p ^ 1
            proofs[leaf_i].append((level[sib].hex(), sib > p))
            pos[leaf_i] = p // 2
        level = nxt
    return level[0], proofs


def verify_inclusion(college: str, pdf_bytes: bytes, proof: list, root_hex: str) -> bool:
    node = leaf_hash(college, pdf_bytes)
    for sib_hex, sib_right in proof:
        sib = bytes.fromhex(sib_hex)
        node = _h(b"\x01" + (node + sib if sib_right else sib + node))
    return node.hex() == root_hex


# ----------------------------------------------------------------------------- signed witness token
def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def make_witness(exam_id: str, root: bytes, n_papers: int, key_check: str, officials: dict) -> dict:
    """officials: {name: Ed25519PrivateKey}. Returns the token every principal receives."""
    body = {"exam_id": exam_id, "merkle_root": root.hex(), "papers": n_papers,
            "key_check": key_check, "issued_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    sigs = []
    for name, sk in officials.items():
        pk = sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        sigs.append({"official": name, "public_key": pk.hex(), "signature": sk.sign(canonical(body)).hex()})
    return {"body": body, "signatures": sigs}


def verify_witness(token: dict, trusted_keys: dict, needed: int = 2) -> bool:
    """trusted_keys: {official: public key hex}, published separately (e.g. on the university notice board)."""
    good = set()
    for s in token["signatures"]:
        if trusted_keys.get(s["official"]) != s["public_key"]:
            continue
        try:
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(s["public_key"])).verify(
                bytes.fromhex(s["signature"]), canonical(token["body"]))
            good.add(s["official"])
        except InvalidSignature:
            pass
    return len(good) >= needed


# ----------------------------------------------------------------------------- hash-chained event log
class EventLog:
    def __init__(self):
        self.entries = []

    def add(self, event: str, data: dict):
        prev = self.entries[-1]["hash"] if self.entries else "0" * 64
        entry = {"seq": len(self.entries), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "event": event, "data": data, "prev": prev}
        entry["hash"] = hashlib.sha256(canonical(entry)).hexdigest()
        self.entries.append(entry)

    def intact(self) -> bool:
        prev = "0" * 64
        for e in self.entries:
            body = {k: v for k, v in e.items() if k != "hash"}
            if e["prev"] != prev or hashlib.sha256(canonical(body)).hexdigest() != e["hash"]:
                return False
            prev = e["hash"]
        return True


# ----------------------------------------------------------------------------- demo
def _demo():
    exam_id = "DS-SEM3-NOV2026"
    colleges = [f"C{i:03d}" for i in range(1, 501)]
    log = EventLog()
    ok = lambda b: "PASS" if b else "FAIL"

    # 1. key and shares
    key = secrets.token_bytes(32)
    check = key_fingerprint(key)
    shares = split_key(key)
    log.add("key_split", {"exam_id": exam_id, "shares": 3, "needed": 2, "key_check": check})
    rebuilt_13 = combine_shares([shares[0], shares[2]])
    rebuilt_23 = combine_shares([shares[1], shares[2]])
    print(f"[{ok(rebuilt_13 == key and rebuilt_23 == key)}] any 2 of 3 shares rebuild the key")
    try:
        one = combine_shares([shares[0]])
        single = key_fingerprint(one) == check
    except ValueError:
        single = False
    print(f"[{ok(not single)}] a single share does not rebuild it")

    # 2. codebook rebuilt on demand, identical each time, never stored
    t0 = time.time()
    book = derive_codebook(rebuilt_13, exam_id, colleges)
    again = derive_codebook(rebuilt_23, exam_id, colleges)
    print(f"[{ok(book == again)}] same codebook from either pair of shares ({time.time() - t0:.1f}s for two builds)")
    other_key = derive_codebook(secrets.token_bytes(32), exam_id, colleges)
    print(f"[{ok(book != other_key)}] a different key gives a completely different codebook")
    worst_pos = max(sum(a == b for a, b in zip(book[x]["positions"], book[y]["positions"]))
                    for x, y in itertools.combinations(colleges[:200], 2))
    worst_mcq = max(sum(a == b for a, b in zip(book[x]["mcq_orders"], book[y]["mcq_orders"]))
                    for x, y in itertools.combinations(colleges[:200], 2))
    print(f"[{ok(worst_pos <= 4)}] descriptive: any two colleges share at most {worst_pos} positions (bound 4)")
    print(f"[{ok(worst_mcq <= 1)}] MCQ: any two colleges share at most {worst_mcq} option order (bound 1)")
    log.add("codebook_derived", {"exam_id": exam_id, "colleges": len(colleges)})

    # 3. per-college PDFs (stand-ins here), Merkle root, two signatures
    pdfs = {c: canonical({"exam": exam_id, "college": c, "paper": book[c]}) for c in colleges}
    leaves = [leaf_hash(c, pdfs[c]) for c in colleges]
    root, proofs = merkle_tree(leaves)
    officials = {"controller_of_exams": Ed25519PrivateKey.generate(),
                 "registrar": Ed25519PrivateKey.generate(),
                 "outside_observer": Ed25519PrivateKey.generate()}
    trusted = {n: k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
               for n, k in officials.items()}
    token = make_witness(exam_id, root, len(colleges), check,
                         {n: officials[n] for n in ("controller_of_exams", "registrar")})
    log.add("witness_issued", {"merkle_root": root.hex(), "signed_by": [s["official"] for s in token["signatures"]]})
    print(f"[{ok(verify_witness(token, trusted))}] witness token carries two valid official signatures")

    # 4. what a principal can check
    i = colleges.index("C214")
    print(f"[{ok(verify_inclusion('C214', pdfs['C214'], proofs[i], token['body']['merkle_root']))}] College 214 proves its PDF is the one fingerprinted")
    swapped = pdfs["C214"].replace(b'"positions":[', b'"positions":[9,')
    print(f"[{ok(not verify_inclusion('C214', swapped, proofs[i], token['body']['merkle_root']))}] a paper swapped after the fact fails the check")
    forged = json.loads(json.dumps(token))
    forged["body"]["merkle_root"] = "00" * 32
    print(f"[{ok(not verify_witness(forged, trusted))}] a re-issued root without the officials' keys is rejected")

    # 5. internal log
    print(f"[{ok(log.intact())}] event log hash chain intact ({len(log.entries)} entries)")
    log.entries[1]["data"]["colleges"] = 499
    print(f"[{ok(not log.intact())}] editing any log entry breaks the chain")
    print()
    print("Witness token sent to principals (truncated):")
    print(json.dumps({"body": token["body"], "signatures": [{"official": s["official"], "signature": s["signature"][:24] + "..."}
                                                              for s in token["signatures"]]}, indent=1))


if __name__ == "__main__":
    _demo()
