# Leak Trace

**Tracing a leaked exam paper to the college that printed it.** Entry for the Seva First Innovation Challenge 2026 (South Zone, Theme 4: Shikshit & Kaushal Bharat, Track A), by a team from Sreyas Institute of Engineering and Technology, Hyderabad.

| | |
|---|---|
| Live demo | [`index.html`](https://raw.githack.com/SakethSumanBathini/SakethSumanBathini/leak-trace-site/index.html): the decoder runs in your browser against 500 simulated colleges |
| Research paper | [`leak-trace-paper.pdf`](https://raw.githack.com/SakethSumanBathini/SakethSumanBathini/leak-trace-site/leak-trace-paper.pdf) (15 pages; LaTeX source and chart script in `paper/`) |
| Concept document | [`leak-trace-concept.pdf`](https://raw.githack.com/SakethSumanBathini/SakethSumanBathini/leak-trace-site/leak-trace-concept.pdf) (10 pages) |
| Demo video | [`leak-trace-demo.mp4`](https://raw.githack.com/SakethSumanBathini/SakethSumanBathini/leak-trace-site/leak-trace-demo.mp4) (2 min 5 s, with voice-over and music; subtitles in [`leak-trace-demo.srt`](leak-trace-demo.srt); the video's sources are in `media/`) |
| Page sources | `site/` (`index.html` at the root is the same page with fonts, styles and script inlined) |

Everything below documents the code and results in this branch.

---

# Leak Trace — starter kit

Prototype code for tracing a leaked exam paper to the college that printed it. Each college gets a fair, content-identical paper whose question order, either/or labels, sub-part order, MCQ option order and (optionally) meaning-neutral wording variants carry a college codeword. A decoder recovers the source college from a leaked photo or a few retyped questions. It names a college only when the evidence is 10,000 times likelier for that college than for any other and for a copy from outside the codebook; otherwise it returns a ranked shortlist.

Built and run on 17–18 Oct 2026 as a feasibility spike, extended on 30 Oct 2026. Everything here uses **synthetic** papers and synthetic photo damage; the campus leak lab is the next step.

**Live demo:** https://raw.githack.com/SakethSumanBathini/SakethSumanBathini/leak-trace-site/index.html · **Research paper:** `leak-trace-paper.pdf` · **Concept document:** `leak-trace-concept.pdf`

## What changed on 30 Oct

1. **A third layer of marks, which a leaker cannot cheaply remove: changing them makes the leaked answers wrong** (`sim_tier3.py`).
   - *Answer keys.* Each college's MCQ options are arranged so that its answer key is a codeword of a quaternary linear [20, 5, 12] code (found by local search), with the four letters relabelled per position so every key is balanced: each letter 3–7 times out of 20 and 8–12 right answers in the middle positions B and C. Any two colleges' keys differ in at least 12 of 20 answers (a random codebook: 6), and every key differs from the setter's master key (the zero codeword, never issued) in at least 12, so a leaked master key points upstream. A paper's MCQs carry either this key code or the Reed–Solomon option-order code below, not both; a product code that carries both is future work.
   - *Numeric values.* Each numerical question gets one of A faculty-approved value sets per college (A = 4, 16 or 64), from a code with a maximum-agreement filter. Rewording and shuffling cannot remove the numbers.
2. **The guarantee, proven and checked.** Under the outside-copy model, the chance that any college's likelihood ratio reaches T × N is at most 1/T (Markov plus a union bound), and stays at most 1/T while the leak is read line by line (Ville's inequality; the average of the colleges' likelihood ratios is a test martingale). With the two-college stage the full decoder's bound is 2/T (union bound). The bound covers copies from outside the system only; wrong names for real leaks are measured, not bounded. `sim_tier3.py` checks it on 800,000 simulated outside copies (200,000 from the model, 200,000 realistic papers, 400,000 answer keys).
3. **The live page** gained an answer-key demo, a line-by-line evidence meter and the guarantee chart. Its decoder for short questions is unchanged: `node adversarial/equiv.js adversarial/app_30oct.js` replays 1,920 leaks through both versions and gets identical decisions.

## What changed on 18 Oct

We attacked our own decoder (`adversarial/`). As it stood on 17 Oct, the browser demo's decoder named an innocent college 8 times in 148,000 simulated leaks. None came from an honest copy; all came from deliberate tricks (lines renumbered 1, 2, 3, reworded or shuffled) or from copies made outside the 500 colleges. Four changes followed:

1. **Numbers that simply run 1, 2, 3 …** may be the leaker's own count rather than the paper's. The decoder now weighs both readings, for every college and for the outside-copy test alike, with a prior of 1 in 10 that the leaker typed them (`RHO`; the leak lab will measure it). Other numbers are read as printed. Photos of the printed page are unaffected: their numbers are ours.
2. **Wording counts only when a line clearly matches one approved wording**: similarity at least 0.8 and ahead of the next-closest wording of the same question by 0.05, or by 40% of the distance between two wordings that are close by design. A reworded line still identifies its question, so its position or order still counts.
3. **The bar to name a college went from 1,000 to 10,000 to 1**, in every script (the Python scripts read `LEAKTRACE_ODDS`; `adversarial/sweep.js` takes the odds as its fourth argument). The guards above removed the trick-specific failures, but a leak that carries no real code (an outside copy, or one scrambled on purpose) still matches some college by chance about as often as the bar allows: with the guards at 1,000 to 1, 4 innocent colleges were named in the same 148,000 leaks. The cost is one more line for single-copy leaks (named from 5 numbered or 7 un-numbered lines instead of 4 and 6) and two more for numbered two-copy mixes (10 instead of 8). Results at the old bar are kept in `results/archive_odds1000/`.
4. **Bug fix in the browser decoder's second stage**: its outside-copy test for un-numbered leaks included the null model for line order, although the two-source scores do not use order. The Python reference (`sim_coalition.py`) was already right.

`custody.py` (key splitting, signed fingerprint, audit log) was also added.

## Files

| File | What it does |
|---|---|
| `sim_decode.py` | Monte Carlo simulation of the codebook and decoder: 500 colleges, numbered / un-numbered / MCQ leaks of 2–10 questions, noise, false-accusation control |
| `e2e_ocr.py` | End-to-end test: renders a college's Part A page, damages it like a phone photo forwarded on WhatsApp, runs Tesseract OCR, fuzzy-matches questions, decodes |
| `sim_coalition.py` | Collusion test: two colleges' copies mixed into one leak. Adds a second decoding stage that can name one or both sources, and re-checks single-source and outside-copy leaks with both stages on. Optional second argument runs some scenarios only, e.g. `python3 sim_coalition.py results mix2` |
| `sim_tier3.py` | Third layer: answer-key tracing with a quaternary [20, 5, 12] code and balanced keys, numeric value sets (A = 4, 16, 64) after rewording and shuffling, master-key leaks, and the outside-copy guarantee checked on 800,000 copies read line by line |
| `sim_rs_mcq.py` | Reed–Solomon codebook for the MCQ option-order channel, compared with the random codebook under single-source, two- and three-copy mixes and outside copies |
| `custody.py` | Key custody and tamper evidence: Shamir 2-of-3 key splitting, codewords derived from the key, Merkle-root fingerprint of every college's PDF signed by two officials, hash-chained event log. `python3 custody.py` runs 12 self-checks |
| `adversarial/sweep.js` | Adversarial breakdown sweep. Loads the decoder straight from a copy of the demo page's `app.js` and runs it on 148,000 simulated leaks: typing damage, renumbering, shuffling, rewording, mixed copies, outside copies. Every wrong accusation is saved with its text and evidence |
| `adversarial/app_after.js` | The live demo page's code (decoder as of 18 Oct). `app_before.js` is the 17 Oct version |
| `adversarial/summarise.js` | Builds the tables below from sweep output |
| `adversarial/equiv.js` | Replays leaks through two versions of the page decoder and counts identical decisions (`app_30oct.js` is the 30 Oct page) |
| `adversarial/near_matches.js` | Upper bound on how often a random outside copy of k numbered lines could be pinned on some college at a given bar |
| `adversarial/runs/` | Sweep outputs (JSON and logs): `after_odds10000` (shipped decoder), `after_odds1000` (shipped decoder at the old bar), `before_odds1000` (17 Oct decoder), `after_noise_odds10000` (typing damage at 5–8 lines) |
| `results/*.json` | Outputs of the Python scripts at 10,000 to 1 (`sim_coalition.py` was run per scenario and merged with `results/merge_coalition.py`); `results/archive_odds1000/` holds the 17 Oct runs at 1,000 to 1 |
| `results/sample_leak_photo.jpg` | One of the synthetic leaked photos |

## Run it

```bash
sudo apt install tesseract-ocr          # Windows: install from the UB Mannheim build
pip install -r requirements.txt
python3 custody.py                      # ~1 s, prints 12 PASS lines
python3 sim_decode.py results           # ~40 s
python3 e2e_ocr.py results              # ~1 min
python3 sim_coalition.py results        # ~30-45 min; or run `mix2` and `single,outside` as two processes, then python3 results/merge_coalition.py
python3 sim_rs_mcq.py results           # ~10-20 min
python3 sim_tier3.py results            # ~4 min: answer keys, numeric values, guarantee check
node adversarial/sweep.js adversarial/app_after.js 2000 adversarial/runs/after.json    # ~12 min, Node 18+
node adversarial/summarise.js adversarial/runs/after.json adversarial/runs/before_odds1000.json
```

`e2e_ocr.py` expects the Liberation Serif font at `/usr/share/fonts/truetype/liberation/`; change `FONT` at the top of the file on other systems. Set `LEAKTRACE_ODDS=1000` to rerun the Python scripts at the old bar, or pass `1000` as the sweep's fourth argument.

## Headline results (synthetic, 10,000 to 1)

- **No wrong accusations** for honest single-source leaks in any configuration (0 of 135,000 in `sim_decode.py`), and no outside copy named there either (0 of 135,000; 13 at the old bar).
- Whole paper, numbered, with wording variants: 4 questions put the real source in the top 5 in 99.9% of leaks; 7 questions name it 92% of the time (5: 36%, 6: 74%, 8: 97%). MCQs: 5 questions name it 90% of the time.
- Photos with 5–6 questions visible: 100% named and correct (n = 30); 4 visible: never named, but the source is in the top 5 every time (n = 26); 3 visible: top 5 in 96%.
- Retyped without question numbers: only nameable with the wording-variant channel (top 5 in 78% of 3–6 question leaks in `e2e_ocr.py`'s retype test; whole-paper simulation: 2% named at 7 questions, 51% at 8, 84% at 10). Line order alone never names a college but puts the source in the top 5 in 77–94% of 8–10 question leaks.
- **Two colleges' copies mixed** (each leaked item taken at random from one of two copies; 3,000 leaks per cell, `sim_coalition.py`): with 12 numbered questions the two-stage decoder names only real sources 87% of the time (both of them 18%), with 10 questions 59%; with 4–8 it mostly abstains, but a real source is in the top 5 for 88–100%. MCQ mixes: 83% at 10 questions, 97% at 12. Un-numbered retyped mixes abstain (2% named at most). No innocent college was named in 45,000 mixed leaks. At the old bar there was one, and a separate 20,000-leak scan found another: the two colleges' random wording variants happened to spell a third college's code ("framing"). The single-source check cannot catch that, because the framed college alone explains the leak as well as any pair; the fix is codebook design (below). With both stages and the check on, no single-source leak was pinned on an innocent college (0 of 15,000) and no college was named for any of 15,000 outside copies.
- **Reed–Solomon codebook for MCQs** (`sim_rs_mcq.py`): option orders as symbols of GF(23), f(x) = m0 + m1·x, so any two colleges share at most one question's option order. In the same two-stage decoder it matches the random codebook (single source: 89–90% named at 6 questions; two-copy mixes: 81–83% named at 10 questions, under 10% at 8; no innocent college named for either code in 52,000 leaks), and it turns "no framing seen" into a guarantee for two colluders once 5 or more MCQs leak without misreads (the minimum-distance condition d > n(1 − 1/c²) of traceability codes).

- **Answer keys** (`sim_tier3.py`, 3,000 leaks per cell): a leaked key with no wrong answers is named from 14 answers every time; with one wrong answer in ten, 20-answer keys are named 87% of the time (source in the top 5 for 95.4% of keys from just 8 answers); with one in five, 41%. Master-key leaks (16 answers, one error in ten) are traced upstream 52% of the time and never pinned on a college.
- **Numeric values, reworded and shuffled** (only the numbers survive, 3% misread): 16 approved sets per question name the source from 6 questions in 83% of leaks and 8 in 98%; 64 sets from 4 questions in 89%; 4 sets never name but keep the source in the top 5 for at least 98% of 6-question leaks. No innocent college was named in 171,000 third-layer leaks.
- **The guarantee, checked:** of outside copies read one line at a time, the share for which some college ever reached 10,000 × 500 was 5.5 × 10⁻⁵ for realistic short-question papers (11 of 200,000) and 3.5 × 10⁻⁵ for answer keys (14 of 400,000), inside the proven 10⁻⁴. At a 100-to-1 bar, realistic papers crossed 1.13% of the time against the model's 1%, because a real paper's positions are a permutation rather than independent draws.

## Adversarial sweep (`adversarial/`)

The decoder that runs in the browser demo, 2,000 simulated leaks per setting, 74 settings, typing damage at 4% of characters unless stated. "Named from" is the smallest leak named in at least 95% of cases.

Before = the 17 Oct decoder at 1,000 to 1 (`app_before.js`); after = the shipped decoder at 10,000 to 1 (`app_after.js`). The other columns are for the shipped decoder. The same decoder at 1,000 to 1 (`runs/after_odds1000.json`) names the source from 4 numbered or 6 un-numbered lines, but named 4 innocent colleges: 1 for a shuffled leak and 3 for outside copies.

| What the leaker did | Named from (≥ 95% of leaks) | Real source in top 5, 6 lines | Innocent college named (before → after) |
|---|---|---:|---:|
| Kept the printed numbers | 5 lines | 100% | 0 → 0 of 12,000 |
| Left the numbers out | 7 lines | 100% | 0 → 0 of 12,000 |
| Renumbered the lines 1, 2, 3 | 7 lines | 100% | 3 → 0 of 12,000 |
| Copied the first questions, real numbers 1, 2, 3 | 6 lines | 100% | 0 → 0 of 8,000 |
| Reworded every question, kept the numbers | holds back (61% named at 10 lines) | 99.8% | 1 → 0 of 12,000 |
| Reworded every question, no numbers | holds back | 56.3% | 0 → 0 of 12,000 |
| Shuffled the lines, no numbers | holds back | 31.4% | 1 → 0 of 12,000 |
| Mixed two colleges’ copies, kept the numbers | 10 lines | >99.9% | 0 → 0 of 6,000 |
| Mixed two colleges’ copies, no numbers | holds back (3% named at 10 lines) | 88.8% (10 lines) | 0 → 0 of 2,000 |
| Sent a copy from outside the 500 colleges | – | – | 3 → 1 of 32,000 |

All 74 settings: 8 → 1 innocent college named in 148,000 leaks.

| Named the source, by typing damage (share of characters) | 0% | 5% | 10% | 15% | 20% | 30% | 40% |
|---|---:|---:|---:|---:|---:|---:|---:|
| Numbered, 5 lines | 99.6% | 99.5% | 99.3% | 99.2% | 95.8% | 33.8% | 0.4% |
| Numbered, 6 lines | 100% | 100% | 100% | >99.9% | 99.9% | 95.3% | 29.3% |
| Un-numbered, 7 lines | 99.8% | 99.5% | 99.7% | 99.7% | 93.2% | 17.4% | 0% |
| Un-numbered, 8 lines | >99.9% | 100% | 99.9% | 100% | 99.8% | 58.9% | 0.6% |

No innocent college was named in these 56,000 leaks, and the real source was in the top 5 every time. The main sweep also ran 6-line un-numbered leaks at every damage level: never named at the strict bar (it needs 7 lines), real source in the top 5 in at least 99.9%. Damage means characters deleted, replaced or doubled at that rate; half the lines are also lower-cased with ? and . removed.

The one innocent college named at 10,000 to 1 came from an outside copy of 6 numbered lines whose positions all matched that college's paper and whose wordings matched on 5 of 6. Nothing in the leak distinguishes it from a real leak from that college. For numbered copies from outside the codebook, the chance that some college's evidence clears the bar peaks at 6 lines, at most about 1 in 20,000 copies; at 4 lines it is now zero, against about 1 in 2,600 at the old bar (`node adversarial/near_matches.js adversarial/app_after.js 6 1000000`, one million random copies per length; an upper bound, since it skips the runner-up test). Every length stays under the 1-in-10,000 design bound.

## Key custody and tamper evidence (`custody.py`)

The codebook is only as trustworthy as the people who hold it. `custody.py` covers that side:

1. **No single key-holder.** The master key is split into 3 shares with Shamir's secret sharing over the prime field 2^521 − 1; any 2 rebuild it, 1 alone reveals nothing. Give one each to, say, the Controller of Examinations, the Registrar and an outside observer.
2. **No stored college-to-pattern table.** Every college's codeword is derived from the key (HMAC-SHA256 as the random generator), so the table exists only while two share-holders are present. The structure that bounds look-alikes is kept: descriptive papers use a permutation code (any two colleges share at most 4 question positions), MCQs the Reed–Solomon code over GF(23) (any two colleges share at most 1 question's option order).
3. **A fingerprint that leaves the building.** All per-college PDFs are hashed into one Merkle root (RFC 6962 leaf and node prefixes), signed by two officials with Ed25519 and sent to every principal before the exam. Each college can later prove which file it received, and nobody can swap a paper afterwards without the published root exposing it.
4. **An internal event log**, hash-chained, for audit. On its own a local log proves little (whoever runs the machine can rebuild it), which is why the root in step 3 is published.

The 12 self-checks (all pass): any 2 of 3 shares rebuild the key and 1 does not; both share pairs derive the same codebook (about 0.6 s for 500 colleges) and another key derives a different one; descriptive codes share at most 4 positions and MCQ codes at most 1 option order; the witness token carries two valid signatures; a college's inclusion proof passes, a swapped paper fails and a forged root is rejected; the log chain is intact and editing any entry breaks it.

Nothing here is zero-knowledge, and shares must never be stored together or in the log.

## How the decision rule works

**Stage 1 (one source).** For every college the decoder computes the log-likelihood of the leaked evidence (positions, labels, sub-part order, variants, option order) under a small noise model. It accuses college *c* only if *c* beats the runner-up by τ = ln 10,000 nats **and** beats an "outside copy" null model by τ + ln N. The second test is a union-bound correction: with 500 colleges, a weak match to *some* college is likely by chance, so the bar rises with N; it caps the chance that an outside copy names anyone at 1 in 10,000. In `sim_coalition.py` and the demo, a stage-1 accusation is also kept only if no *pair* of colleges explains the non-order evidence e^τ times better (the leak must look single-source).

**Stage 2 (two sources, `sim_coalition.py` and the demo).** If stage 1 abstains, a two-source mixture model scores all N(N+1)/2 college pairs at once: for each leaked item, colleges fall into a few match states, and the pair log-likelihood is Σ X T Xᵀ over items (one-hot states × a small mixture table). A college is named only if it is in the best pair, the best pair beats every pair without it by τ, the best pair beats the outside-copy null by τ + ln(number of pairs), and its share of the evidence could not come from an unknown outside copy (τ + ln N). Stage 2 can name one source, both or none.

Otherwise the decoder abstains and returns a ranked shortlist for investigators.

**Text-level guards (demo decoder, 18 Oct).** Numbers that run 1, 2, 3 are weighed both as printed and as the leaker's own; a line's wording counts only when it clearly matches one approved wording (see "What changed").

## Known limits (say these out loud)

- Synthetic page and damage; no page curl, shadows, handwriting or repeated re-compression.
- English only; Tesseract ships Kannada, Malayalam, Tamil and Telugu models, untested here.
- Wording variants were hand-written; real ones need setter approval, a fairness check and a minimum distance from each other, so that a typo cannot turn one into another (two of ours differ only by swapping "BFS" and "DFS").
- A leaker who knows the scheme can launder the code. In the sweep, shuffling the lines or rewording them without numbers stopped the decoder naming anyone; rewording with the numbers kept, or mixing numbered copies, only delayed it (61% and 99.8% named at 10 lines). It never named an innocent college for any of these, but laundering does stop the trace. Use several channels and treat tracing as a deterrent plus investigative lead, never as automatic punishment.
- A copy from outside the codebook can match a college by chance (at most about 1 in 20,000, above). Give the setter's master copy and the press proof codewords of their own, so that leaks from them are traced too, and confirm every naming with the custody log.
- The descriptive codebook is greedy-random (wording variants, sub-part order, labels drawn at random), which is what allows the rare framing in `sim_coalition.py`. MCQs can move to the Reed–Solomon code in `sim_rs_mcq.py` now; descriptive papers need bigger per-question alphabets first, e.g. one 16-state symbol per either/or pair (wording variant × sub-part order × label), then a structured code over them.
- Two-copy mixes are named reliably only from about 10 numbered lines (demo decoder) to 12 (`sim_coalition.py`); with fewer the decoder mostly returns a shortlist. Un-numbered mixes are almost never named (2% at most, even at 12).

## Next steps

1. **Generator:** per-college PDFs with WeasyPrint or Typst (both handle Indic shaping), plus per-college answer keys for MCQs; codewords from `custody.py` (MCQ option orders from the GF(23) code, descriptive variants from a distance-constrained code).
2. **Leak lab:** give each classmate group a different "college" copy of a mock paper; collect 300+ real leaks (phone photos, WhatsApp forwards, crops, screenshots, retyped fragments); report top-1 accuracy, false-accusation rate and accuracy against number of leaked questions. Also measure how often people renumber, reword or reorder when they retype, which sets `RHO` and shows which attacks matter.
3. **Indic:** test Tesseract `tel`/`kan`/`mal`/`tam` or PaddleOCR on a bilingual paper.
4. **Service:** FastAPI endpoint — upload photo or paste text → ranked colleges with likelihood and evidence trail.

## Dependencies and licences (checked 17 Oct 2026)

Tesseract (Apache-2.0), OpenCV (Apache-2.0), RapidFuzz (MIT), Pillow (MIT-CMU), NumPy (BSD-3), pytesseract (Apache-2.0), cryptography (Apache-2.0 or BSD-3), Node.js for the sweep (MIT); for the next steps WeasyPrint (BSD-3), Typst (Apache-2.0), FastAPI (MIT), galois (MIT), PaddleOCR (Apache-2.0). Avoid PyMuPDF (AGPL-3.0) in a hosted service.
