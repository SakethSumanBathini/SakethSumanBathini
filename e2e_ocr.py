"""
Leak Trace — end-to-end spike (spike 2 of 2).

Pipeline under test:
  per-college paper (order + wording-variant codeword)
  -> render page -> simulate a partial phone photo forwarded on WhatsApp
     (crop to 3-6 questions, rotation, perspective, blur, noise, downscale, JPEG)
  -> Tesseract OCR -> parse "N. question" lines -> fuzzy-match to canonical bank
  -> likelihood decoder over 500 colleges -> confident attribution / shortlist / abstain.
Also tests retyped leaks with typos (no image) with and without question numbers.
"""
import io, json, math, os, re, sys, random
import numpy as np, cv2, pytesseract
from PIL import Image, ImageDraw, ImageFont
from rapidfuzz import fuzz, process

rng = np.random.default_rng(7); random.seed(7)
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
N = 500
EPS, EPS_V = 0.02, 0.05
FONT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"

BANK = [
 ["Define an abstract data type and give one example.", "What is an abstract data type? Give one example.",
  "Give one example of an abstract data type after defining it.", "Define the term abstract data type, with one example."],
 ["Compare a stack and a queue.", "Compare a queue and a stack.",
  "Bring out the differences between a stack and a queue.", "How does a stack differ from a queue?"],
 ["State the time complexity of binary search.", "What is the time complexity of binary search?",
  "Give the time complexity of binary search.", "Write down the time complexity of a binary search."],
 ["What is a circular linked list?", "Define a circular linked list.",
  "Explain what a circular linked list is.", "What do you mean by a circular linked list?"],
 ["Convert the infix expression A + B * C to postfix.", "Convert A + B * C from infix to postfix form.",
  "Write the postfix form of the infix expression A + B * C.", "Give the postfix equivalent of A + B * C."],
 ["List any two applications of a priority queue.", "Give two applications of a priority queue.",
  "Mention any two uses of a priority queue.", "Write two applications of priority queues."],
 ["Define the height of a binary tree.", "What is meant by the height of a binary tree?",
  "State what the height of a binary tree is.", "What is the height of a binary tree?"],
 ["What is hashing? Name one collision resolution technique.", "Define hashing and name one collision resolution technique.",
  "Name one collision resolution technique and define hashing.", "Explain hashing briefly and name one collision resolution method."],
 ["Differentiate between BFS and DFS.", "Differentiate between DFS and BFS.",
  "Compare breadth-first search with depth-first search.", "How does BFS differ from DFS?"],
 ["What is a minimum spanning tree?", "Define a minimum spanning tree.",
  "Explain the term minimum spanning tree.", "What do you understand by a minimum spanning tree?"],
]
FLAT = [(q, v, BANK[q][v].lower()) for q in range(10) for v in range(4)]
CHOICES = [t for _, _, t in FLAT]

def perm_code(n_slots, n_words, max_agree):
    code = []
    while len(code) < n_words:
        c = rng.permutation(n_slots)
        if not code or (np.array(code) == c).sum(1).max() <= max_agree:
            code.append(c)
    return np.array(code)
POS = perm_code(10, N, 4)               # POS[c, q] = printed slot of canonical question q
VAR = rng.integers(0, 4, (N, 10))       # VAR[c, q] = wording variant used by college c

def render(c):
    W, H = 1654, 1400
    img = Image.new("L", (W, H), 255); d = ImageDraw.Draw(img)
    f_h = ImageFont.truetype(FONT, 40); f = ImageFont.truetype(FONT, 38)
    d.text((120, 60), "B.Tech III Semester Examination - Data Structures", font=f_h, fill=0)
    d.text((120, 120), "PART A - Answer ALL questions (10 x 2 = 20 marks)", font=f, fill=0)
    order = np.argsort(POS[c])          # canonical question printed at each slot
    y, boxes = 210, []
    for slot, q in enumerate(order):
        line = f"{slot + 1}. {BANK[q][VAR[c, q]]}"
        d.text((120, y), line, font=f, fill=0); boxes.append((y - 10, y + 60)); y += 112
    return img, boxes

def phone_photo(img, boxes, k):
    start = int(rng.integers(0, 10 - k + 1))
    top, bot = boxes[start][0] - 20, boxes[start + k - 1][1] + 20
    a = np.array(img)[max(top, 0):bot, :]
    a = cv2.copyMakeBorder(a, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=235)
    h, w = a.shape
    ang = rng.uniform(-4, 4)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
    a = cv2.warpAffine(a, M, (w, h), borderValue=235)
    j = 0.03 * w
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[rng.uniform(0, j), rng.uniform(0, j)], [w - rng.uniform(0, j), rng.uniform(0, j)],
                      [w - rng.uniform(0, j), h - rng.uniform(0, j)], [rng.uniform(0, j), h - rng.uniform(0, j)]])
    a = cv2.warpPerspective(a, cv2.getPerspectiveTransform(src, dst), (w, h), borderValue=235)
    a = cv2.GaussianBlur(a, (0, 0), rng.uniform(0.6, 1.4))
    a = np.clip(a.astype(float) * rng.uniform(0.75, 1.0) + rng.normal(0, 8, a.shape), 0, 255).astype(np.uint8)
    scale = 900 / w
    a = cv2.resize(a, (900, int(h * scale)), interpolation=cv2.INTER_AREA)
    ok, enc = cv2.imencode(".jpg", a, [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(35, 56))])
    return cv2.imdecode(enc, cv2.IMREAD_GRAYSCALE), start

def ocr_items(gray):
    up = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    txt = pytesseract.image_to_string(up, config="--psm 6")
    items = []
    for ln in txt.splitlines():
        m = re.match(r"^\W*(\d{1,2})\s*[.,)]\s*(.+)$", ln.strip())
        if m:
            items.append((int(m.group(1)), m.group(2).strip()))
        elif items and ln.strip():
            items[-1] = (items[-1][0], items[-1][1] + " " + ln.strip())
    return items, txt

def match(text):
    best = process.extractOne(text.lower(), CHOICES, scorer=fuzz.ratio)
    if best is None or best[1] < 60: return None
    q, v, _ = FLAT[best[2]]; return q, v

def score(ev):
    ll = np.zeros(N); nll = 0.0
    for kind, q, val in ev:
        if kind == "pos":
            ll += np.where(POS[:, q] == val, math.log(1 - EPS), math.log(EPS / 9)); nll += math.log(1 / 10)
        elif kind == "var":
            ll += np.where(VAR[:, q] == val, math.log(1 - EPS_V), math.log(EPS_V / 3)); nll += math.log(1 / 4)
    return ll, nll

ODDS = float(os.environ.get("LEAKTRACE_ODDS", "10000"))   # name a college only at these odds (9.2 nats)

def decide(ll, nll, src, tau=math.log(ODDS)):
    o = np.argsort(ll)[::-1]
    short = int((ll >= ll[src] - 1e-9).sum())
    conf = None
    if ll[o[0]] - ll[o[1]] >= tau and ll[o[0]] - nll >= tau + math.log(N): conf = int(o[0])
    return conf, short

def typo(s, rate=0.04):
    out = []
    for ch in s:
        r = random.random()
        if r < rate / 3: continue                       # deletion
        if r < 2 * rate / 3: out.append(random.choice("abcdefghijklmnopqrstuvwxyz")); continue
        out.append(ch)
        if r < rate: out.append(ch)                     # duplication
    s = "".join(out)
    return s.lower().replace("?", "").replace(".", "") if random.random() < 0.5 else s

# ---------------------------------------------------------------- photo test --
photo = []
sample_saved = False
for t in range(80):
    c = int(rng.integers(0, N)); k = int(rng.integers(3, 7))
    img, boxes = render(c)
    gray, start = phone_photo(img, boxes, k)
    if not sample_saved:
        cv2.imwrite(f"{OUT}/sample_leak_photo.jpg", gray); sample_saved = True
    items, _ = ocr_items(gray)
    ev, correct_items = [], 0
    truth = {int(np.argsort(POS[c])[s]): s for s in range(start, start + k)}
    for num, text in items:
        m = match(text)
        if m is None: continue
        q, v = m
        ev += [("pos", q, num - 1), ("var", q, v)]
        if q in truth and truth[q] == num - 1 and VAR[c, q] == v: correct_items += 1
    ll, nll = score(ev)
    conf, short = decide(ll, nll, c)
    photo.append(dict(k=k, visible=k, recovered_items=correct_items, confident=conf, correct=(conf == c),
                      wrong=(conf is not None and conf != c), shortlist=short))

def summarize(rows, label):
    n = len(rows)
    s = dict(label=label, n=n,
             item_recovery=round(sum(r["recovered_items"] for r in rows) / max(1, sum(r["visible"] for r in rows)), 3),
             confident_correct=round(sum(r["correct"] for r in rows) / n, 3),
             wrong_accusation=round(sum(r["wrong"] for r in rows) / n, 3),
             shortlist_le5=round(sum(r["shortlist"] <= 5 for r in rows) / n, 3),
             median_shortlist=float(np.median([r["shortlist"] for r in rows])))
    print(s); return s

summ = [summarize(photo, "photo, 3-6 questions visible (all)")]
for k in (3, 4, 5, 6):
    sub = [r for r in photo if r["k"] == k]
    if sub: summ.append(summarize(sub, f"photo, {k} questions visible"))

# ---------------------------------------------------------------- retype test -
for numbered in (True, False):
    rows = []
    for t in range(400):
        c = int(rng.integers(0, N)); k = int(rng.integers(3, 7))
        qs = list(rng.choice(10, k, replace=False)); qs.sort(key=lambda q: POS[c, q])
        ev, rec = [], 0
        for q in qs:
            m = match(typo(BANK[q][VAR[c, q]]))
            if m is None: continue
            mq, mv = m
            ev.append(("var", mq, mv))
            if numbered: ev.append(("pos", mq, int(POS[c, q])))
            rec += (mq == q and mv == VAR[c, q])
        ll, nll = score(ev); conf, short = decide(ll, nll, c)
        rows.append(dict(k=k, visible=k, recovered_items=rec, confident=conf, correct=(conf == c),
                         wrong=(conf is not None and conf != c), shortlist=short))
    summ.append(summarize(rows, f"retyped with typos, {'numbered' if numbered else 'no numbers'}, 3-6 questions"))

json.dump(summ, open(f"{OUT}/e2e_results.json", "w"), indent=1)
