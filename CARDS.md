# The Three Cards

Three SVG cards, all generated from code in `tools/`, all living in your repo.
Nothing here is hotlinked, so nothing here can 402 on you.

| Card | File | Size | Updates |
|---|---|---|---|
| Identity | `assets/card-identity.svg` | 760 x 200 | Manual — edit `tools/make_cards.py` |
| Terminal stats | `assets/card-terminal.svg` | 1180 x 600 | **Daily, automatic** |
| Footer | `assets/card-footer.svg` | 760 x 80 | Manual |

---

## What I changed from the versions you sent, and why

**The "Neural-grid" card was Siddhu's, half-renamed.** Your name and handle had
been swapped in, but it still carried `siddhu3116@gmail.com`, `siddhu.info`,
`linkedin: siddhu-singh`, the role "Blockchain & Full Stack Dev", and stats of
37 repos / 85 commits / 13 followers / 156,151 lines. Pushing it would have put
another person's email on your profile and stated numbers about you that
aren't yours — and yours are better. Everything on the new card is either
your real information or fetched live from the GitHub API.

**The pkbros identity card embedded a photograph.** That `<image>` tag held a
base64 JPEG of Prateek Sharma's face. Your card uses a generated monogram
instead — an orbital mark echoing your portfolio, with "SSB" beneath it.

**The ASCII art is drawn, not traced.** `tools/make_ascii_art.py` renders a
four-layer neural network with weighted edges, then converts it to an 80x46
character grid. It's original geometry, so there's no question of whose
likeness it is.

---

## Setup — one token, one workflow

The terminal card needs API access to count your stats.

1. Reuse the PAT you already made (scopes `repo` + `read:user`)
2. Repo **Settings → Secrets and variables → Actions → New repository secret**
3. Name it **`STATS_CARD_TOKEN`**, paste the same token
4. Actions tab → **Terminal Stats Card** → **Run workflow**

First run takes a few minutes: it walks every repo's commit history to compute
lines of code. After that it's fast, because results are cached per repo
against the head commit oid in `tools/loc_cache.json` — only repos that
actually changed get re-walked.

---

## How the numbers are counted

**Contributions** come from `contributionsCollection`, queried one year at a
time and summed. The commit-search API is deliberately not used: it counts
every fork's copy of a commit, which is how people end up claiming absurd
totals.

**Lines of code** walks each owned, non-fork repository's default branch and
sums additions and deletions for commits authored by you. The card shows net
lines with the gross figures beside it in green and red.

**Account age** is derived from your GitHub `createdAt`, not a birthday. It's a
real, checkable number.

Any section that fails degrades to `n/a` rather than failing the workflow. A
card with one missing row beats a run that goes red.

---

## Editing the cards

Everything is in `tools/make_cards.py` at the top:

```python
NAME      = "SAKETH SUMAN BATHINI"
TAGLINE   = "Data Analyst -> AI Engineer | I turn messy data into decisions"
STATUS    = "Building RAG pipelines that actually ship"
QUOTES    = [...]          # footer rotation, 3 lines
ROWS_LEFT = [...]          # terminal card's identity rows
```

Then:

```powershell
python tools\make_ascii_art.py     # only if changing the art
python tools\make_cards.py
```

**Important:** regenerating the terminal card resets its stats to `--`. Re-run
the **Terminal Stats Card** workflow afterwards to refill them.

### Swapping in your own photo

If you'd rather have a real picture than the monogram, the card needs it
base64-embedded — GitHub strips external image references inside SVG, so a URL
won't work. Ask and I'll write `tools/embed_avatar.py` for it.

---

## A note on placement

The terminal card repeats some of what the `whoami` block already says —
role, toolchain, contact. You asked me not to remove anything, so both are
there. If you'd rather not say it twice, the cleanest cut is dropping the
`whoami` YAML block, since the terminal card covers the same ground and adds
live stats on top. Your call, and easy to do later.

---

# profile-grid.svg — the card you uploaded

## What that ASCII art actually was

You described it as "just triangle shit." It wasn't. Rendered with a working
monospace font it is a **photographic portrait** — a person in a suit and tie,
face clearly legible. It only looked abstract because the file's font stack was
broken (see below), which collapsed the character grid into noise.

The uploaded card also carried `siddhu3116@gmail.com`, `siddhu.info` and
`linkedin: siddhu-singh`, so that portrait is almost certainly Siddhu Singh.
It is not on your profile.

**Your card ships with generated neural-network art instead**, on the identical
120 x 55 grid. To swap in your own face:

```powershell
python tools\photo_to_ascii.py "C:\path\to\your-photo.jpg" --preview
python tools\make_profile_grid.py
```

That converts your photo to the same grid and charset, updates the checksum
guard, and rebuilds the card. Head-and-shoulders shot, plain background,
portrait crop works best.

## Two bugs in the uploaded file, both fixed

**`fontsize="15px"` is not a valid SVG attribute.** No size was set, so browsers
fell back to 16px. At 16px the 120-character art measures ~484px and collides
with the data column at x=520 — visible as art bleeding through "Contact" and
"GitHub Stats". With a correct `font-size="15px"` it measures ~453px.

**The font stack led with `ConsolasFallback`**, an `@font-face` whose only
source is `local('Consolas')`. On macOS and Linux, where Consolas is not
installed, that face fails and the renderer can drop to a proportional font —
which collapses the art's spaces and destroys the grid. That is precisely why
it looked like triangles to you. The chain now starts with `ui-monospace` and
ends with real fallbacks on every platform.

## Content changes

| Field | Was (Siddhu's) | Now |
|---|---|---|
| Role | Blockchain & Full Stack Dev | Data Analyst -> AI Engineer |
| Age | 20 years, 7 months, 6 days | Live, from your GitHub `createdAt` |
| ToolChain | VS Code, Git, Foundry, Hardhat | VS Code, Git, Vite, Antigravity |
| Neural.Core | Solidity, Rust, TS, JS, Python | Python, SQL, JavaScript, TypeScript |
| Neural.AI | LangChain, OpenAI, LLMs | LangChain, Groq, n8n, Hugging Face |
| Neural.Stack | EVM, Smart Contracts, AggLayer | Replaced with Neural.Data (Power BI, Tableau, Pandas, NumPy) |
| Grid.Mail | siddhu3116@gmail.com | sakethsumanbathini@gmail.com |
| Grid.Portfolio | siddhu.info | sakethsuman.xyz |
| Grid.LinkedIn | siddhu-singh | saketh-suman-bathini-5922532ba |
| All stats | Hardcoded | Live from the GitHub API |

## Palette

The card keeps the teal it arrived with, because you said not to change the
design. Your profile is orange everywhere else, so it will stand out. One line
in `tools/make_profile_grid.py` switches it:

```python
PALETTE = "brand"     # was "original"
```

Then `python tools\make_profile_grid.py`.

## Live updates

`tools/update_stats_card.py` now fills **both** cards in one pass, and the
**Terminal Stats Card** workflow stages both. Same `STATS_CARD_TOKEN` secret.
