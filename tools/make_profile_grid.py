#!/usr/bin/env python3
"""
Rebuilds profile-grid.svg from the uploaded card.

The ASCII art comes from tools/grid_art.txt — 55 lines
of 120 characters, checksum verified on every run. Only the data column is
rewritten, with Saketh's real information replacing the values the source
file carried.

Two bugs from the source are fixed because both break rendering:

  1. The root carried  fontsize="15px"  which is not a valid SVG attribute,
     so no size was set and browsers fell back to 16px. At 16px the 120-char
     art measures ~484px and collides with the data column at x=520. With a
     correct font-size="15px" it measures ~453px and clears it.

  2. The font stack led with 'ConsolasFallback', an @font-face whose only
     source is local('Consolas'). On macOS and Linux, where Consolas is not
     installed, that face fails and the renderer can drop to a proportional
     font — which collapses the art's spaces and destroys the grid.

    python tools/make_profile_grid.py
"""
import hashlib
import os
from xml.sax.saxutils import escape

# ── palette ──────────────────────────────────────────────────────────────
# "original" keeps the teal the uploaded card shipped with.
# "brand"    matches the #FF5C00 used everywhere else on the profile.
PALETTE = "original"

THEMES = {
    "original": dict(art="#00f0ff", key="#5EEAD4", value="#E5E7EB",
                     cc="#5f6b7a", rule="#e11d48", add="#39ff14",
                     dele="#ef4444", bg="#0d1117", stroke="#1F1F23"),
    "brand":    dict(art="#FF5C00", key="#FF8A3D", value="#E6E6E6",
                     cc="#4a4a55", rule="#FF5C00", add="#39d353",
                     dele="#f85149", bg="#020205", stroke="#FF5C00"),
}
C = THEMES[PALETTE]

MONO = ("ui-monospace,'SFMono-Regular',Menlo,Consolas,"
        "'DejaVu Sans Mono','Liberation Mono','Courier New',monospace")

ART_SHA = "ca56178addfbc83c97be92853731de68"   # guards against edits

# ── content ──────────────────────────────────────────────────────────────
HEADER = "SAKETHSUMANBATHINI@Neural-grid"

# (label, value, live-id or None). Ids are filled by update_stats_card.py.
IDENTITY = [
    ("Subject",   "Saketh Suman Bathini",                   None),
    ("Role",      "Data Analyst -> AI Engineer",            None),
    ("Age",       "--",                                     "age_data"),
    ("Status",    "Building - Learning - Shipping",         None),
    ("ToolChain", "VS Code, Git, Vite, Antigravity",        None),
]

NEURAL = [
    ("Neural.Core",     "Python, SQL, JavaScript, TypeScript"),
    ("Neural.AI",       "LangChain, Groq, n8n, Hugging Face"),
    ("Neural.Data",     "Power BI, Tableau, Pandas, NumPy"),
    ("Neural.Frontend", "HTML/CSS, React, Vite, Tailwind"),
    ("Neural.Backend",  "Node.js, PostgreSQL, MongoDB, Supabase"),
]

CONTACT = [
    ("Grid.Mail",      "sakethsumanbathini@gmail.com"),
    ("Grid.Portfolio", "sakethsuman.xyz"),
    ("Grid.LinkedIn",  "saketh-suman-bathini-5922532ba"),
    ("Grid.Github",    "SakethSumanBathini"),
]

W, H = 1180, 530
X = 505                 # source used 520; art ends ~448 so this keeps
                        # 57px clearance and 120px right margin
DOT_TARGET = 56


def load_art():
    lines = open("tools/grid_art.txt", encoding="utf-8").read().split("\n")
    sha = hashlib.sha256("\n".join(lines).encode()).hexdigest()[:32]
    if sha != ART_SHA:
        raise SystemExit(
            f"ASCII art checksum changed ({sha} != {ART_SHA}).\n"
            "tools/grid_art.txt must stay exactly as uploaded."
        )
    assert len(lines) == 55 and all(len(l) == 120 for l in lines)
    return lines


def dots(label, value, target=DOT_TARGET):
    return "." * max(2, target - len(label) - len(value))


def build():
    art = load_art()

    # art block: identical geometry to the source file
    art_tspans = "\n".join(
        f'<tspan x="-10" y="{-30 + i * 9}">{escape(l)}</tspan>'
        for i, l in enumerate(art)
    )

    rows, y = [], 24

    def row(label, value, vid=None):
        nonlocal y
        did = label.replace(".", "_").lower() + "_dots"
        vid_a = f' id="{vid}"' if vid else ""
        rows.append(
            f'<tspan x="{X}" y="{y}" class="cc">. </tspan>'
            f'<tspan class="key">{escape(label)}</tspan>'
            f'<tspan class="cc" id="{did}">: {dots(label, value)} </tspan>'
            f'<tspan class="value"{vid_a}>{escape(value)}</tspan>'
        )
        y += 20

    def rule(title):
        nonlocal y
        rows.append(
            f'<tspan x="{X}" y="{y}" class="rule">- {escape(title)} </tspan>'
            f'<tspan class="cc">{"-" * 46}</tspan>'
        )
        y += 22

    def gap():
        nonlocal y
        rows.append(f'<tspan x="{X}" y="{y}" class="cc">.</tspan>')
        y += 16

    rows.append(f'<tspan x="{X}" y="{y}" class="key">{escape(HEADER)} </tspan>'
                f'<tspan class="cc">{"-" * 30}</tspan>')
    y += 22

    for label, value, vid in IDENTITY:
        row(label, value, vid)
    gap()
    for label, value in NEURAL:
        row(label, value)
    gap()
    rule("Contact")
    for label, value in CONTACT:
        row(label, value)
    gap()
    rule("GitHub Stats")

    # stats block — every number carries an id for the live updater
    rows.append(
        f'<tspan x="{X}" y="{y}" class="cc">. </tspan>'
        f'<tspan class="key">Repos</tspan><tspan class="cc" id="repo_dots">: .. </tspan>'
        f'<tspan class="value" id="repo_data">--</tspan>'
        f'<tspan class="cc"> {{ </tspan><tspan class="key">Contributions</tspan>'
        f'<tspan class="cc">: </tspan><tspan class="value" id="contrib_data">--</tspan>'
        f'<tspan class="cc"> }} | </tspan>'
        f'<tspan class="key">Stars</tspan><tspan class="cc" id="star_dots">: ... </tspan>'
        f'<tspan class="value" id="star_data">--</tspan>'
    )
    y += 20
    rows.append(
        f'<tspan x="{X}" y="{y}" class="cc">. </tspan>'
        f'<tspan class="key">Pull Requests</tspan><tspan class="cc" id="pr_dots">: .. </tspan>'
        f'<tspan class="value" id="pr_data">--</tspan>'
        f'<tspan class="cc"> | </tspan>'
        f'<tspan class="key">Issues</tspan><tspan class="cc" id="issue_dots">: .. </tspan>'
        f'<tspan class="value" id="issue_data">--</tspan>'
        f'<tspan class="cc"> | </tspan>'
        f'<tspan class="key">Followers</tspan><tspan class="cc" id="follower_dots">: .. </tspan>'
        f'<tspan class="value" id="follower_data">--</tspan>'
    )
    y += 20
    rows.append(
        f'<tspan x="{X}" y="{y}" class="cc">. </tspan>'
        f'<tspan class="key">Lines of Code on GitHub</tspan>'
        f'<tspan class="cc" id="loc_dots">: {dots("Lines of Code on GitHub", "--", 42)} </tspan>'
        f'<tspan class="value" id="loc_data">--</tspan>'
        f'<tspan class="cc"> ( </tspan>'
        f'<tspan class="addColor" id="loc_add">--</tspan><tspan class="addColor">++</tspan>'
        f'<tspan class="cc">, </tspan>'
        f'<tspan class="delColor" id="loc_del">--</tspan><tspan class="delColor">--</tspan>'
        f'<tspan class="cc"> )</tspan>'
    )

    body = "\n".join(rows)

    svg = f'''<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{MONO}" font-size="15px" role="img" aria-label="{escape(HEADER)}">
<!--
  profile-grid.svg

  ASCII art: preserved byte for byte from the uploaded card
  (tools/grid_art.txt, 55 lines x 120 chars, sha256 {ART_SHA}).
  make_profile_grid.py refuses to run if that file changes.

  Data column: rebuilt with real information. Values carrying an id are
  filled by tools/update_stats_card.py from the live GitHub API.

  Regenerate with:  python tools/make_profile_grid.py
-->
<style>
.ascii    {{ fill: {C['art']}; }}
.key      {{ fill: {C['key']}; }}
.value    {{ fill: {C['value']}; }}
.cc       {{ fill: {C['cc']}; }}
.rule     {{ fill: {C['rule']}; }}
.addColor {{ fill: {C['add']}; }}
.delColor {{ fill: {C['dele']}; }}
text, tspan {{ white-space: pre; }}
</style>
<rect width="{W}" height="{H}" fill="{C['bg']}" rx="15" stroke="{C['stroke']}" stroke-opacity="0.35" stroke-width="2"/>
<g transform="translate(22,20) scale(0.42,0.88)">
<text x="0" y="0" class="ascii" font-size="15px" xml:space="preserve">
{art_tspans}
</text>
</g>
<text x="{X}" y="0" class="value" font-size="15px" xml:space="preserve">
{body}
</text>
</svg>
'''
    open("profile-grid.svg", "w", encoding="utf-8").write(svg)
    print(f"  wrote profile-grid.svg   {W}x{H}   palette={PALETTE}")
    print(f"  art preserved: 55 lines x 120 chars, sha256 {ART_SHA}")
    print(f"  data rows: {len(rows)}   last baseline y={y}  (canvas {H})")


if __name__ == "__main__":
    build()
