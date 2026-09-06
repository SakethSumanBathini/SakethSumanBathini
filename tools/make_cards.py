#!/usr/bin/env python3
"""
Builds the three SVG cards for the profile README:

    assets/card-identity.svg   760 x 200   identity / contact strip
    assets/card-terminal.svg  1180 x 530   neofetch-style stats terminal
    assets/card-footer.svg     760 x  80   rotating quote footer

All three are pure vector, written from scratch in the #FF5C00 / #020205
brand. No third-party photographs, no borrowed identity data. The stats in
the terminal card are placeholders until tools/update_stats_card.py fills
them with live numbers from the GitHub API.

Card layout is inspired by the neofetch-style profile card popularised by
Andrew6rant/Andrew6rant; the geometry, palette and copy here are original.

    python tools/make_cards.py
"""
import os
from xml.sax.saxutils import escape

# ── identity ─────────────────────────────────────────────────────────────
NAME      = "SAKETH SUMAN BATHINI"
HANDLE    = "@SakethSumanBathini"
TAGLINE   = "Data Analyst -> AI Engineer | I turn messy data into decisions"
EMAIL     = "sakethsumanbathini@gmail.com"
LINKEDIN  = "linkedin.com/in/saketh-suman-bathini-5922532ba"
PORTFOLIO = "sakethsuman.xyz"
STATUS    = "Building RAG pipelines that actually ship"

# ── palette ──────────────────────────────────────────────────────────────
ACCENT  = "#FF5C00"
ACCENT2 = "#FF8A3D"
BG      = "#0a0a0f"
DEEP    = "#020205"
TEXT    = "#E6E6E6"
MUTED   = "#8B8B93"
DOTS    = "#4a4a55"
ADD     = "#39d353"
DEL     = "#f85149"

MONO = ("ui-monospace,'SFMono-Regular',Menlo,Consolas,"
        "'DejaVu Sans Mono','Liberation Mono','Courier New',monospace")
DISP = "'Courier New',Courier,monospace"

os.makedirs("assets", exist_ok=True)


def shared_defs(accent, w, h, scan_id="scan", glow_id="glow"):
    """Glow filter + scanline pattern, reused by identity and footer."""
    return f'''  <defs>
    <filter id="{glow_id}" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="b1"/>
      <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b2"/>
      <feMerge>
        <feMergeNode in="b2"/><feMergeNode in="b1"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <pattern id="{scan_id}" patternUnits="userSpaceOnUse" width="{w}" height="4">
      <rect width="{w}" height="1" fill="white"/>
    </pattern>'''


# ═════════════════════════════════════════════════════════════════════════
# CARD 1 — IDENTITY
# ═════════════════════════════════════════════════════════════════════════
def build_identity():
    W, H = 760, 200
    marquee = "* DATA * AI * OPEN SOURCE " * 4

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(NAME)} identity card">
  <!--
    CARD 1 - IDENTITY
    Brand: {ACCENT} on {DEEP}. Avatar is a generated monogram, not a photo.
    To use your own picture instead: python tools/embed_avatar.py <file>
  -->
  <style>
    .marquee {{ font-family: {DISP}; font-weight: bold; letter-spacing: 4px; }}
    .display {{ font-family: {DISP}; font-weight: bold; letter-spacing: 2px; }}
    .body    {{ font-family: {MONO}; }}
  </style>
{shared_defs(ACCENT, W, H)}
    <clipPath id="mClip"><rect x="6" y="3" width="748" height="20"/></clipPath>
    <clipPath id="avatarClip"><rect x="24" y="34" width="140" height="140" rx="6"/></clipPath>
    <linearGradient id="mono" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{ACCENT}"/>
      <stop offset="100%" stop-color="#7a2a00"/>
    </linearGradient>
  </defs>

  <!-- frame -->
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="6" fill="{BG}"/>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="6" fill="none" stroke="{ACCENT}" stroke-width="1.5" filter="url(#glow)" opacity="0.5"/>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="6" fill="none" stroke="{ACCENT}" stroke-width="1.5"/>
  <rect x="5" y="5" width="{W-10}" height="{H-10}" rx="4" fill="none" stroke="{ACCENT}" stroke-width="0.5" opacity="0.2"/>

  <!-- marquee -->
  <rect x="2" y="2" width="{W-4}" height="22" rx="5" fill="{ACCENT}" opacity="0.06"/>
  <line x1="6" y1="25" x2="{W-6}" y2="25" stroke="{ACCENT}" stroke-width="0.5" opacity="0.25"/>
  <g clip-path="url(#mClip)">
    <g>
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-{W} 0" dur="14s" repeatCount="indefinite"/>
      <text x="0" y="18" class="marquee" fill="{ACCENT}" font-size="12" opacity="0.8">{escape(marquee)}</text>
      <text x="{W}" y="18" class="marquee" fill="{ACCENT}" font-size="12" opacity="0.8">{escape(marquee)}</text>
    </g>
  </g>

  <!-- avatar: generated monogram -->
  <rect x="22" y="32" width="144" height="144" rx="6" fill="none" stroke="{ACCENT}" stroke-width="1" opacity="0.4"/>
  <g clip-path="url(#avatarClip)">
    <rect x="24" y="34" width="140" height="140" fill="{DEEP}"/>
    <rect x="24" y="34" width="140" height="140" fill="url(#mono)" opacity="0.16"/>
    <!-- orbital echo of the terminal card -->
    <g transform="translate(94,104)" fill="none" stroke="{ACCENT}" stroke-width="1.2" opacity="0.55">
      <ellipse rx="52" ry="18"/>
      <ellipse rx="52" ry="18" transform="rotate(60)"/>
      <ellipse rx="52" ry="18" transform="rotate(120)"/>
    </g>
    <circle cx="94" cy="104" r="7" fill="{ACCENT}">
      <animate attributeName="r" values="6;8.5;6" dur="3s" repeatCount="indefinite"/>
    </circle>
    <text x="94" y="150" text-anchor="middle" class="display" fill="{ACCENT2}" font-size="26" opacity="0.9">SSB</text>
  </g>

  <!-- content -->
  <text x="186" y="56" class="display" fill="{ACCENT}" font-size="25">{escape(NAME)}</text>
  <text x="186" y="76" class="body" fill="{MUTED}" font-size="13">{escape(HANDLE)}</text>
  <text x="186" y="99" class="body" fill="{TEXT}" font-size="12">{escape(TAGLINE)}</text>

  <text x="186" y="128" class="body" fill="{ACCENT}" font-size="12" opacity="0.75">EMAIL</text>
  <text x="278" y="128" class="body" fill="{TEXT}" font-size="12">{escape(EMAIL)}</text>
  <text x="186" y="148" class="body" fill="{ACCENT}" font-size="12" opacity="0.75">PORTFOLIO</text>
  <text x="278" y="148" class="body" fill="{TEXT}" font-size="12">{escape(PORTFOLIO)}</text>
  <text x="186" y="168" class="body" fill="{ACCENT}" font-size="12" opacity="0.75">STATUS</text>
  <text x="278" y="168" class="body" fill="{TEXT}" font-size="12">{escape(STATUS)}<animate attributeName="opacity" values="1;0.35;1" dur="2.4s" repeatCount="indefinite"/></text>

  <rect x="2" y="2" width="{W-4}" height="{H-4}" rx="5" fill="url(#scan)" opacity="0.035"/>
</svg>
'''
    open("assets/card-identity.svg", "w", encoding="utf-8").write(svg)
    return "assets/card-identity.svg", W, H


# ═════════════════════════════════════════════════════════════════════════
# CARD 3 — FOOTER
# ═════════════════════════════════════════════════════════════════════════
QUOTES = [
    "611 pull requests. 26 repositories. 11 weeks.",
    "Ship the dashboard someone opens twice.",
    "The merge log is the resume.",
]


def build_footer():
    W, H = 760, 80
    marquee = "> SYSTEM ONLINE " * 6
    dur = 12  # 3 quotes x 4s

    clips, texts = [], []
    for i in range(3):
        s = i / 3.0                       # slot start as fraction of loop
        kt = [0, s + 0.005, s + 0.075, s + 0.275, s + 0.315, 1]
        kt = [round(min(max(v, 0), 1), 4) for v in kt]
        vals = "0;0;700;700;0;0"
        clips.append(f'''    <clipPath id="qClip{i+1}">
      <rect x="30" y="40" height="20" width="0">
        <animate attributeName="width" values="{vals}" keyTimes="{';'.join(str(v) for v in kt)}" dur="{dur}s" repeatCount="indefinite"/>
      </rect>
    </clipPath>''')
        texts.append(f'''  <g clip-path="url(#qClip{i+1})">
    <text x="30" y="54" class="body" font-size="13">
      <tspan fill="{ACCENT}" opacity="0.7">&gt;&gt; </tspan><tspan fill="{TEXT}">{escape(QUOTES[i])}</tspan><tspan class="cursor" fill="{ACCENT}">&#x258E;</tspan>
    </text>
  </g>''')

    # three contribution-cell squares instead of hearts
    cells = []
    for i, (fill, delay) in enumerate(((ACCENT, "0s"), (ACCENT2, "0.4s"), ("#5c2a0a", "0.8s"))):
        x = 668 + i * 26
        cells.append(f'''  <g transform="translate({x},42)">
    <rect x="-7" y="-7" width="14" height="14" rx="3" fill="{fill}">
      <animate attributeName="opacity" values="1;0.25;1" dur="2.4s" begin="{delay}" repeatCount="indefinite"/>
    </rect>
  </g>''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Footer">
  <!--
    CARD 3 - FOOTER
    Three quotes share one {dur}s loop ({dur//3}s each). Each types in via a
    clipPath whose width is keyframed, holds, then wipes before the next.
    Change a quote's text freely - the keyTimes below do not need editing
    as long as the rect stays wider than the longest line (~700px).
  -->
  <style>
    .marquee {{ font-family: {DISP}; font-weight: bold; letter-spacing: 4px; }}
    .body    {{ font-family: {MONO}; }}
    @keyframes blink {{ 0%,49.9%{{opacity:1}} 50%,100%{{opacity:0}} }}
    .cursor {{ animation: blink 1s step-end infinite; }}
  </style>
{shared_defs(ACCENT, W, H)}
    <clipPath id="mClip"><rect x="6" y="3" width="748" height="18"/></clipPath>
{chr(10).join(clips)}
  </defs>

  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="6" fill="{BG}"/>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="6" fill="none" stroke="{ACCENT}" stroke-width="1.5" filter="url(#glow)" opacity="0.5"/>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="6" fill="none" stroke="{ACCENT}" stroke-width="1.5"/>
  <rect x="5" y="5" width="{W-10}" height="{H-10}" rx="4" fill="none" stroke="{ACCENT}" stroke-width="0.5" opacity="0.2"/>

  <rect x="2" y="2" width="{W-4}" height="20" rx="5" fill="{ACCENT}" opacity="0.06"/>
  <line x1="6" y1="23" x2="{W-6}" y2="23" stroke="{ACCENT}" stroke-width="0.5" opacity="0.25"/>
  <g clip-path="url(#mClip)">
    <g>
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-{W} 0" dur="{dur}s" repeatCount="indefinite"/>
      <text x="0" y="16" class="marquee" fill="{ACCENT}" font-size="13" opacity="0.8">{escape(marquee)}</text>
      <text x="{W}" y="16" class="marquee" fill="{ACCENT}" font-size="13" opacity="0.8">{escape(marquee)}</text>
    </g>
  </g>

{chr(10).join(texts)}

{chr(10).join(cells)}

  <rect x="2" y="2" width="{W-4}" height="{H-4}" rx="5" fill="url(#scan)" opacity="0.035"/>
</svg>
'''
    open("assets/card-footer.svg", "w", encoding="utf-8").write(svg)
    return "assets/card-footer.svg", W, H


# ═════════════════════════════════════════════════════════════════════════
# CARD 2 — TERMINAL
# ═════════════════════════════════════════════════════════════════════════
# (label, value, id or None). Values marked with an id are overwritten by
# tools/update_stats_card.py with live numbers from the GitHub API.
ROWS_LEFT = [
    ("Subject",      "Saketh Suman Bathini",                       None),
    ("Role",         "Data Analyst -> AI Engineer",                None),
    ("Account.Age",  "--",                                         "age_data"),
    ("Status",       "Building | Learning | Shipping",             None),
    ("Toolchain",    "VS Code, Git, Vite, Antigravity",            None),
    (None, None, None),
    ("Core.Lang",    "Python, SQL, JavaScript, TypeScript",        None),
    ("Core.AI",      "LangChain, Groq, n8n, Hugging Face",         None),
    ("Core.Data",    "Power BI, Tableau, Pandas, NumPy",           None),
    ("Core.Web",     "React, Node.js, Vite, Tailwind",             None),
    ("Core.Store",   "PostgreSQL, MongoDB, Supabase, SQLite",      None),
]

CONTACT = [
    ("Grid.Mail",      EMAIL,                            None),
    ("Grid.Portfolio", PORTFOLIO,                        None),
    ("Grid.LinkedIn",  "saketh-suman-bathini-5922532ba", None),
    ("Grid.GitHub",    "SakethSumanBathini",             None),
]


def dot_run(label_len, value_len, target=70):
    """Leader dots so the value column lines up regardless of text length."""
    return "." * max(2, target - label_len - value_len)


def build_terminal():
    W, H = 1180, 600
    art = open("tools/ascii_art.txt", encoding="utf-8").read().split("\n")

    # ASCII block: 9px line step, scaled 0.88 -> centre it vertically
    # Monospace advance ratios vary by font (~0.50-0.62 of font-size), and
    # textLength is unreliable across renderers. Instead the scale below is
    # chosen so 80 columns land between ~276px and ~342px wide in the worst
    # and best case -- comfortably clear of the text column at x=440.
    step = 10
    n = len(art)
    span = (n - 1) * step
    y0 = round((H - span) / 2 - 20)
    art_tspans = "\n".join(
        f'<tspan x="0" y="{y0 + i*step}">{escape(line)}</tspan>'
        for i, line in enumerate(art)
    )

    X = 440          # right column origin
    y = 34
    out = []

    def rule(title, colour):
        nonlocal y
        dashes = "-" * 54
        out.append(f'<tspan x="{X}" y="{y}" fill="{colour}">- {escape(title)} -{dashes}</tspan>')
        y += 22

    def row(label, value, vid=None, extra=""):
        nonlocal y
        dots = dot_run(len(label), len(value))
        vid_attr = f' id="{vid}"' if vid else ""
        did_attr = f' id="{vid.replace("_data","_dots")}"' if vid else ""
        out.append(
            f'<tspan x="{X}" y="{y}" class="cc">. </tspan>'
            f'<tspan class="key">{escape(label)}</tspan>'
            f'<tspan class="cc"{did_attr}> {dots} </tspan>'
            f'<tspan class="value"{vid_attr}>{escape(value)}</tspan>{extra}'
        )
        y += 20

    def blank():
        nonlocal y
        out.append(f'<tspan x="{X}" y="{y}" class="cc">.</tspan>')
        y += 20

    out.append(f'<tspan x="{X}" y="{y}" fill="{ACCENT}" font-size="17">SakethSumanBathini@neural-grid</tspan>')
    y += 24
    out.append(f'<tspan x="{X}" y="{y}" fill="{DOTS}">{"-"*70}</tspan>')
    y += 20

    for label, value, vid in ROWS_LEFT:
        if label is None:
            blank()
        else:
            row(label, value, vid)

    y += 6
    rule("Contact", ACCENT2)
    for label, value, vid in CONTACT:
        row(label, value, vid)

    y += 6
    rule("GitHub Stats", ACCENT2)

    for label, vid in (("Repositories", "repo"), ("Contributions", "contrib"),
                       ("Pull Requests", "pr"), ("Issues", "issue"),
                       ("Stars Earned", "star"), ("Followers", "follower")):
        dots = dot_run(len(label), 2)
        out.append(
            f'<tspan x="{X}" y="{y}" class="cc">. </tspan>'
            f'<tspan class="key">{label}</tspan>'
            f'<tspan class="cc" id="{vid}_dots"> {dots} </tspan>'
            f'<tspan class="value" id="{vid}_data">--</tspan>'
        )
        y += 20

    # The LOC row carries "( NNN++, NNN-- )" after the value, which the
    # normal target does not account for. Use a narrower run so it fits.
    dots = dot_run(len("Lines of Code"), 2, target=46)
    out.append(
        f'<tspan x="{X}" y="{y}" class="cc">. </tspan>'
        f'<tspan class="key">Lines of Code</tspan>'
        f'<tspan class="cc" id="loc_dots"> {dots} </tspan>'
        f'<tspan class="value" id="loc_data">--</tspan>'
        f'<tspan class="cc">  ( </tspan>'
        f'<tspan class="addColor" id="loc_add">--</tspan><tspan class="addColor">++</tspan>'
        f'<tspan class="cc">, </tspan>'
        f'<tspan class="delColor" id="loc_del">--</tspan><tspan class="delColor">--</tspan>'
        f'<tspan class="cc"> )</tspan>'
    )
    y += 20

    body = "\n".join(out)

    svg = f'''<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{MONO}" font-size="15px" role="img" aria-label="Terminal profile card">
  <!--
    CARD 2 - TERMINAL
    Layout inspired by the neofetch-style profile card popularised by
    Andrew6rant/Andrew6rant. Geometry, ASCII art, palette and copy here are
    original to this repository.

    Every value carrying an id ("*_data") is rewritten in place by
    tools/update_stats_card.py using live GitHub API numbers, so nothing on
    this card is hand-typed or stale. The matching "*_dots" runs are
    re-padded at the same time so the columns stay aligned.
  -->
<style>
.key      {{ fill: {ACCENT2}; }}
.value    {{ fill: {TEXT}; }}
.cc       {{ fill: {DOTS}; }}
.ascii    {{ fill: {ACCENT}; }}
.addColor {{ fill: {ADD}; }}
.delColor {{ fill: {DEL}; }}
text, tspan {{ white-space: pre; }}
</style>
<rect width="{W}" height="{H}" fill="{DEEP}" rx="15" stroke="{ACCENT}" stroke-opacity="0.25" stroke-width="2"/>
<g transform="translate(30,20) scale(0.46,1)">
<text x="0" y="0" class="ascii" font-size="15px" opacity="0.9" xml:space="preserve">
{art_tspans}
</text>
</g>
<text x="{X}" y="0" fill="{TEXT}">
{body}
</text>
</svg>
'''
    open("assets/card-terminal.svg", "w", encoding="utf-8").write(svg)
    return "assets/card-terminal.svg", W, H


if __name__ == "__main__":
    for path, w, h in (build_identity(), build_terminal(), build_footer()):
        size = os.path.getsize(path)
        print(f"  wrote {path:32} {w}x{h}  {size:,} bytes")
