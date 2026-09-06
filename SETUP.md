# Setup — End to End

Your username `SakethSumanBathini` is already wired into every widget. Roughly 20 minutes total.

---

## Step 0 — Fix the two things I couldn't verify

| Placeholder | Where | Action |
|---|---|---|
| `YOUR_LINKEDIN` | Connect section (1 spot) | Replace with your LinkedIn handle |
| Portfolio URL | 2 spots — `https://saketh-suman-bathini.vercel.app` | **I guessed this.** Replace with your real Vercel URL |

Also confirm these two facts, which I wrote from what you told me:

- **"President · Gen AI Club, NIAT"** — appears in `whoami`, the experience timeline, and the leadership table. If the exact title differs (Lead / Founder / Core Member), fix all three.
- **Project repo links** — the Featured Work cards currently have no links, because I don't know your repo names. Once `TriageIQ`, `CallSensei AI`, `SceneSense AI`, `Scam Shield` are public, wrap each card title in a link. A dead link is worse than no link.

---

## Step 1 — Create the profile repo

A repo named **exactly** your username renders on your profile page.

1. https://github.com/new
2. **Name:** `SakethSumanBathini` (case-sensitive)
3. **Public** ✅ — it will not work if private
4. Tick **Add a README file**

GitHub confirms with: *"You found a secret!"*

---

## Step 2 — Add the files

```powershell
git clone https://github.com/SakethSumanBathini/SakethSumanBathini.git
cd SakethSumanBathini
```

Final structure:

```
SakethSumanBathini/
├── README.md
├── assets/
│   ├── name-heatmap.svg          ← your custom SAKETH banner
│   └── emoji/                    ← 7 vendored icons (108 KB)
├── tools/
│   ├── make_name_heatmap.py      ← regenerate the banner
│   └── vendor-elusoc-badges.sh   ← makes ELUSOC badges permanent
└── .github/workflows/
    ├── snake.yml
    ├── profile-cards.yml
    ├── profile-3d.yml
    └── metrics.yml
```

---

## Step 3 — One token, three secret names

**Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new**

Scopes: **`repo`** and **`read:user`**. Copy it — GitHub shows it once.

Add it as a repo secret three times under different names
(**Repo Settings → Secrets and variables → Actions → New repository secret**):

| Secret name | Used by |
|---|---|
| `SUMMARY_GITHUB_TOKEN` | `profile-cards.yml` |
| `METRICS_TOKEN` | `metrics.yml` |
| `PROFILE_3D_TOKEN` | `profile-3d.yml` |

`snake.yml` needs no token.

> Same token value each time. Three names only because each action reads a different variable.

---

## Step 4 — Let Actions write to your repo

**Repo Settings → Actions → General → Workflow permissions → Read and write permissions → Save**

This is the step everyone skips, and then nothing generates.

---

## Step 5 — Push and run

```powershell
git add .
git commit -m "feat: rebuild profile README"
git push
```

Go to **Actions** and run all four manually (**Run workflow**) rather than waiting for the schedule:

1. `Generate Snake Animation` → creates the `output` branch
2. `GitHub Profile Summary Cards` → commits `profile-summary-card-output/`
3. `GitHub Profile 3D Contribution` → commits `profile-3d-contrib/`
4. `GitHub Metrics` → commits `metrics.svg`

Wait 2–3 minutes, then hard-refresh your profile (**Ctrl+Shift+R**).

---

## Step 6 — Make the ELUSOC badges permanent

Your 8 badges currently hotlink from `edulinkup.dev`. If that site blocks hotlinking or goes down, all eight break — and they're some of your best proof.

```bash
bash tools/vendor-elusoc-badges.sh
```

Then find-and-replace in `README.md`:

- Find: `https://www.edulinkup.dev/elusoc/images/ticket/`
- Replace: `./assets/elusoc/`

Commit. Now they're yours permanently. The **Verify on ELUSOC** button still links out, so the proof stays checkable.

---

## What's rate-limit-proof vs what isn't

This matters. The public `github-readme-stats` instance was **paused with a 503 in January 2026**, breaking thousands of profiles at once, and it still hits GitHub's API rate limit regularly. The project's own README now recommends self-hosting.

| Element | Source | Can it break? |
|---|---|---|
| Name heatmap | your repo | **No** |
| 3D calendar | your repo | **No** |
| Summary cards | your repo | **No** |
| Metrics image | your repo | **No** |
| Snake | your repo (`output` branch) | **No** |
| Emoji icons | your repo | **No** |
| Shields.io badges | shields.io | Very unlikely |
| Stats / streak / top-langs | shared Vercel | **Yes** ← |
| Activity graph | shared Vercel | Occasionally |

Everything structural is self-hosted. Only three cards carry risk.

**To remove that too (5 minutes):**

1. Fork https://github.com/anuraghazra/github-readme-stats
2. https://vercel.com/new → import your fork
3. Env var `PAT_1` = your token from Step 3
4. Deploy → you get `your-stats.vercel.app`
5. Replace every `github-readme-stats.vercel.app` in `README.md` with your URL

Now those cards hit *your* rate limit, which you'll never exhaust alone.

---

## Regenerating the name banner

`assets/name-heatmap.svg` is generated, not hand-drawn — 53 columns × 7 rows, exactly like a real contribution year, with SAKETH lit in your brand orange and the rest as recessive grey noise. It animates left-to-right on load, so the name writes itself.

To change the word or colours, edit the top of `tools/make_name_heatmap.py`:

```python
WORD = "SAKETH"                              # any letters in FONT
LETTER = ["#FF5C00", "#FF6E1A", "#FF8A3D", "#FFA05C"]
NOISE  = ["#0e0e13", "#14141b", "#1a1a23", "#20202b"]
```

Then `python tools/make_name_heatmap.py`.

Two design notes, in case you tune it: noise stays **cool grey on purpose** — when I tested warm brown noise, it competed with the orange and the letters stopped reading. And cells default to `opacity: 1` with `animation-fill-mode: both`, so if a renderer ignores CSS the grid still shows instead of going blank.

---

## Troubleshooting

**Broken images on first load** — the Actions haven't run yet. `profile-3d-contrib/`, `profile-summary-card-output/`, `metrics.svg` and the `output` branch don't exist until you run Step 5.

**Workflow fails with 403 / "Permission denied"** — Step 4.

**3D calendar workflow fails** — needs a real PAT, not the built-in token; it reads the GraphQL contributions API. Check `PROFILE_3D_TOKEN`.

**Streak shows 0 days** — honest, not broken. But it's the one widget that can hurt you if someone checks during a quiet week. Delete that single `<img>` if you're not committing daily.

**Everything looks right but doesn't update** — `Ctrl+Shift+R`. GitHub caches README images hard, same as Vite.

---

## One honest note

The 2026 write-ups on profile READMEs converge on a warning: heavy decoration is starting to read as *filler*, because every profile now has the same widgets. Recruiters reportedly spend under two minutes.

You asked for maximalist, and this is maximalist. But the reason it works isn't the animation — it's that **Receipts** and **ELUSOC** sit near the top. "611 PRs merged across 26 repos in 11 weeks," "India Top 10," "Top 850 of 38,000+" are claims almost nobody can make, and all three are independently verifiable — the PRs from your contribution graph, the badges from your public ELUSOC profile.

The visuals stop the scroll. The numbers are what gets remembered. If you ever trim this, cut animation before evidence.
