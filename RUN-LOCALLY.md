# Run It Locally in VS Code

Read this before you preview, or the broken images will look like my fault.

---

## Step 1 — Download and unzip

Download **`github-profile.zip`** — take the whole thing. It's 110 KB, and grabbing files individually means rebuilding the folder structure by hand, which is exactly where this breaks.

Unzip it somewhere sensible:

```
D:\GITHUB-PROFILE\
```

**Do not** unzip it inside your portfolio project. This is a separate repo.

---

## Step 2 — Open the folder in VS Code

```powershell
cd D:\GITHUB-PROFILE
code .
```

Or: **File → Open Folder**. Open the *folder*, not the README file — relative paths like `./assets/name-heatmap.svg` only resolve when the folder is the workspace root.

---

## Step 3 — Install the GitHub preview extension

VS Code's stock markdown preview doesn't look like GitHub. One extension fixes that:

**Extensions panel (Ctrl+Shift+X)** → search **`bierner.github-markdown-preview`** → Install.

It's an extension pack — GitHub CSS, `:emoji:`, task lists, footnotes. Worth the 10 seconds.

---

## Step 4 — Generate the preview placeholders

Seven images in the README are produced by GitHub Actions and **do not exist yet**. Without this step your preview looks half-broken.

```powershell
python tools\make_preview_placeholders.py
```

This writes labelled stand-ins at the exact six paths the workflows will later use. They get overwritten automatically the first time each workflow runs — nothing to clean up.

---

## Step 5 — Preview

Open `README.md`, then **Ctrl+Shift+V**.

Side-by-side instead: **Ctrl+K** then **V**.

---

## What you'll actually see

| Element | Locally | Why |
|---|---|---|
| **SAKETH name banner** | ✅ Animated | Local file — this is the real thing |
| Section emoji | ✅ | Vendored into `assets/emoji/` |
| Shields.io badges | ✅ | Live from shields.io |
| Typing animation | ✅ | Live from demolab |
| Skillicons row | ✅ | Live from skillicons.dev |
| ELUSOC badges ×8 | ✅ | Live from edulinkup.dev |
| Stats / streak / languages | ✅ | Live — assuming your handle is right |
| Activity graph | ✅ | Live |
| Footer wave | ✅ | Live from capsule-render |
| 3D calendar | 🟠 Placeholder | Real one after `profile-3d.yml` runs |
| Summary cards ×4 | 🟠 Placeholder | After `profile-cards.yml` |
| Metrics image | 🟠 Placeholder | After `metrics.yml` |
| **Snake** | ❌ Broken | Loads from the `output` branch, which only exists on GitHub |

The snake is the one thing you genuinely cannot preview locally. That's unavoidable — the URL points at a branch that doesn't exist yet.

---

## The real end-to-end test

Local preview confirms **layout, wording, and your own assets**. It cannot confirm the Actions pipeline. For that you have to push — and pushing is safe, because a profile repo with a broken widget for five minutes costs you nothing.

Recommended sequence:

1. Preview locally, fix wording and the placeholders in `SETUP.md` Step 0
2. Create the `SakethSumanBathini` repo and push
3. Add the three secrets, flip **Read and write permissions**
4. Run all four workflows manually
5. Reload your profile — everything orange should now be real

Full detail in **`SETUP.md`**.

---

## Fast checks while you're in there

**Is the name banner right?** Open `assets/name-heatmap.svg` directly in VS Code — it previews as an image, animation and all. Regenerate with `python tools\make_name_heatmap.py`.

**Did I get your handle right?** Load this in a browser:

```
https://github-readme-stats.vercel.app/api?username=SakethSumanBathini
```

Real numbers = correct. "Could not fetch user" = wrong handle, and you'll need to find-and-replace it in 18 places.

**Images not loading in preview at all?** Click the shield icon in the preview's top-right → **Allow insecure content**. VS Code's webview blocks mixed content by default.

**Tables rendering as raw text?** You opened the file outside the workspace folder. Reopen with **File → Open Folder**.
