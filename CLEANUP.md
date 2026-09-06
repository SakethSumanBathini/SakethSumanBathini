# Cleanup + Brand Upgrade

Your pull brought in **402 files**. Your README uses **6 of them**. This fixes that
and recolours the 3D calendar to your brand at the same time.

Run everything below from `D:\github-profile`.

---

## Step 1 — Drop the ~390 unused files

```powershell
# Every summary-card theme except the one the README uses
Get-ChildItem profile-summary-card-output -Directory |
  Where-Object { $_.Name -ne 'github_dark' } |
  Remove-Item -Recurse -Force

Remove-Item profile-summary-card-output\README.md -Force -ErrorAction SilentlyContinue

# 3D calendar variants you don't display
Remove-Item profile-3d-contrib\*.svg -Force
```

---

## Step 2 — Add the new files

Copy into the repo root:

- `profile-3d-settings.json`

Replace:

- `.github\workflows\profile-cards.yml`
- `.github\workflows\profile-3d.yml`
- `README.md`

---

## Step 3 — Commit and re-run

```powershell
git add -A
git commit -m "chore: single-theme cards, brand-coloured 3D calendar, drop ~390 unused files"
git push
```

Then Actions → run **GitHub Profile 3D Contribution**, wait for green, then
**GitHub Profile Summary Cards**.

---

## What changed and why

**`THEME: github_dark`** — the action's `THEME` input defaults to empty, which
means *generate every theme*. That's what produced folders from `2077` to
`zenburn`: ~60 themes × 6 files. You display five cards from one theme.

**`ANIMATION: rise` + `DURATION: 1.2`** — the action can bake a CSS animation
directly into the SVGs. Free motion, no extra requests. Other options if `rise`
isn't to taste: `fade`, `draw`, `stagger`, `load`, `sequence`, `tint`, `rgb`.

**`EXCLUDE: html,css,scss`** — matches the `hide=` already on your stats card, so
markup doesn't crowd out real languages in the breakdown.

**`SETTING_JSON: profile-3d-settings.json`** — without it the action emits ten
variants in GitHub green. With it you get one file, `profile-brand.svg`, in
`#FF5C00` on `#020205`, with `growingAnimation` on so the towers rise on load.

The contribution ramp steps through five stops:

```
#14141b → #5c2a0a → #a34410 → #e0530f → #FF8A3D
```

Empty days sit at near-black; your heaviest days glow at the top of the range.
Same logic as the name banner — the busiest cells are the brightest.

---

## Tuning the 3D calendar

Everything lives in `profile-3d-settings.json`.

| Key | Does |
|---|---|
| `contribColors` | Five-stop ramp, lightest → heaviest day |
| `strongColor` | Headline numbers |
| `weakColor` | Labels and secondary text |
| `radarColor` | The contribution-type radar chart |
| `growingAnimation` | `false` for a static render |
| `fileName` | Output name — change it and update the README path too |

Also supported: `"type": "season"` for four seasonal palettes across the year,
and `"type": "rainbow"`. If you switch types the required colour keys change —
`season` wants `contribColors1` through `contribColors4` instead of
`contribColors`.

---

## Optional — a .gitignore guard

The workflows will keep writing only what you've configured now, but if you ever
clear `THEME` the flood comes back. Nothing to add here; just know that `THEME`
is the switch.
