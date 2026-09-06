#!/usr/bin/env python3
"""
LOCAL PREVIEW ONLY.

Creates stand-in SVGs at the exact paths GitHub Actions will later write to,
so `Ctrl+Shift+V` in VS Code shows a complete page instead of broken images.

Every one of these gets overwritten by the real thing the first time the
workflows run. Nothing here needs to be deleted by hand.

    python tools/make_preview_placeholders.py
"""
import os

BG = "#020205"
ACCENT = "#FF5C00"
MUTED = "#8B8B93"
BORDER = "#1F1F23"

# path -> (width, height, title, subtitle)
TARGETS = {
    "profile-3d-contrib/profile-gitblock.svg": (
        880, 400, "3D Contribution Calendar",
        "profile-3d.yml  ·  yoshi389111/github-profile-3d-contrib",
    ),
    "profile-summary-card-output/github_dark/1-repos-per-language.svg": (
        340, 200, "Repos per Language", "profile-cards.yml",
    ),
    "profile-summary-card-output/github_dark/2-most-commit-language.svg": (
        340, 200, "Most Commit Language", "profile-cards.yml",
    ),
    "profile-summary-card-output/github_dark/3-stats.svg": (
        340, 200, "Stats", "profile-cards.yml",
    ),
    "profile-summary-card-output/github_dark/4-productive-time.svg": (
        340, 200, "Productive Time", "profile-cards.yml",
    ),
    "metrics.svg": (
        880, 320, "Full Metrics", "metrics.yml  ·  lowlighter/metrics",
    ),
}

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <rect width="{w}" height="{h}" rx="10" fill="{bg}" stroke="{border}" stroke-width="1"/>
  <rect x="{bx}" y="{by}" width="{bw}" height="3" rx="1.5" fill="{accent}"/>
  <text x="50%" y="{ty}" text-anchor="middle" font-family="system-ui,-apple-system,Segoe UI,sans-serif"
        font-size="{fs}" font-weight="700" fill="{accent}">{title}</text>
  <text x="50%" y="{sy}" text-anchor="middle" font-family="system-ui,-apple-system,Segoe UI,sans-serif"
        font-size="{ss}" fill="{muted}">{sub}</text>
  <text x="50%" y="{ny}" text-anchor="middle" font-family="system-ui,-apple-system,Segoe UI,sans-serif"
        font-size="{ss}" fill="{muted}">placeholder — the real card appears after the workflow runs</text>
</svg>
"""

made = []
for path, (w, h, title, sub) in TARGETS.items():
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)

    big = w > 500
    svg = TEMPLATE.format(
        w=w, h=h, bg=BG, accent=ACCENT, muted=MUTED, border=BORDER,
        bx=w // 2 - 30, by=h // 2 - 52, bw=60,
        ty=h // 2 - 14, sy=h // 2 + 12, ny=h // 2 + 34,
        fs=22 if big else 15,
        ss=12 if big else 10,
        title=title, sub=sub,
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    made.append(path)

print(f"Created {len(made)} preview placeholders:\n")
for p in made:
    print(f"  {p}")
print(
    "\nOpen README.md in VS Code and press Ctrl+Shift+V."
    "\nThe snake stays broken locally — it loads from the 'output' branch,"
    "\nwhich only exists after snake.yml runs on GitHub."
)
