#!/usr/bin/env python3
"""
Fills assets/card-terminal.svg with live numbers from the GitHub API.

Every value on the card carries an id ("repo_data", "loc_data", ...). This
script rewrites the text inside those ids and re-pads the matching "*_dots"
leader runs so the columns stay aligned as numbers change width.

Design notes
------------
* Contribution counts come from contributionsCollection, one query per year
  of the account's life. The commit-search API is deliberately avoided: it
  counts every fork's copy of a commit and wildly overstates the total.
* Lines of code walks each owned, non-fork repository's default branch and
  sums additions/deletions for commits authored by the user. Results are
  cached per repo against the head commit oid in tools/loc_cache.json, so
  repeat runs only re-walk what actually changed.
* Any single section failing degrades to "n/a" rather than failing the run.
  A card with one missing row beats a workflow that goes red.

Usage:
    GITHUB_TOKEN=ghp_xxx USERNAME=SakethSumanBathini python tools/update_stats_card.py
"""
import json
import os
import re
import sys
import time
import datetime
import urllib.error
import urllib.request

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("STATS_TOKEN")
USER = os.environ.get("USERNAME") or "SakethSumanBathini"
# (path, dot_target) — each card lays its leader dots out to a different
# width, so re-padding must use the same target the generator used.
# (path, dot_target, loc_target, skip_realign)
#
# skip_realign lists ids whose row holds MORE than one value — the grid card
# packs "Repos … { Contributions … } | Stars …" onto one line. Re-padding
# those from a single value's width blows the row far past the canvas, so
# their dot runs are left exactly as the generator wrote them.
CARDS = [
    ("assets/card-terminal.svg", 70, 46, set()),
    ("profile-grid.svg", 56, 42,
     {"repo_data", "star_data", "contrib_data",
      "pr_data", "issue_data", "follower_data"}),
]
CACHE = "tools/loc_cache.json"

if not TOKEN:
    sys.exit("GITHUB_TOKEN is not set — cannot query the GitHub API.")

GQL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"bearer {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": f"{USER}-profile-card",
}


def gql(query, variables=None, retries=3):
    """POST a GraphQL query, retrying on transient failures."""
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(GQL, data=body, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=45) as r:
                payload = json.loads(r.read())
            if "errors" in payload:
                raise RuntimeError(payload["errors"])
            return payload["data"]
        except Exception as e:                     # noqa: BLE001
            if attempt == retries - 1:
                raise
            wait = 3 * (attempt + 1)
            print(f"    retry {attempt+1}/{retries-1} after {wait}s ({e})")
            time.sleep(wait)
    return None


# ── profile basics ───────────────────────────────────────────────────────
def fetch_profile():
    data = gql("""
      query($login:String!) {
        user(login:$login) {
          createdAt
          followers { totalCount }
          repositories(ownerAffiliations:OWNER, first:1) { totalCount }
          pullRequests { totalCount }
          issues { totalCount }
          starred: repositories(ownerAffiliations:OWNER, first:100,
                                orderBy:{field:STARGAZERS, direction:DESC}) {
            nodes { stargazerCount }
          }
        }
      }""", {"login": USER})
    u = data["user"]
    return {
        "created": u["createdAt"],
        "followers": u["followers"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in u["starred"]["nodes"]),
    }


def fetch_contributions(created_iso):
    """Sum contributionsCollection year by year — the number GitHub shows."""
    start = datetime.datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    total = 0
    y = start.year
    while y <= now.year:
        a = max(start, datetime.datetime(y, 1, 1, tzinfo=datetime.timezone.utc))
        b = min(now, datetime.datetime(y, 12, 31, 23, 59, 59,
                                       tzinfo=datetime.timezone.utc))
        d = gql("""
          query($login:String!,$from:DateTime!,$to:DateTime!) {
            user(login:$login) {
              contributionsCollection(from:$from,to:$to) {
                contributionCalendar { totalContributions }
              }
            }
          }""", {"login": USER,
                 "from": a.isoformat().replace("+00:00", "Z"),
                 "to": b.isoformat().replace("+00:00", "Z")})
        total += d["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
        y += 1
    return total


# ── lines of code ────────────────────────────────────────────────────────
def fetch_loc():
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE))
        except Exception:                          # noqa: BLE001
            cache = {}

    repos, cursor = [], None
    while True:
        d = gql("""
          query($login:String!,$cursor:String) {
            user(login:$login) {
              repositories(ownerAffiliations:OWNER, isFork:false,
                           first:100, after:$cursor) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  nameWithOwner
                  defaultBranchRef { target { ... on Commit { oid } } }
                }
              }
            }
          }""", {"login": USER, "cursor": cursor})
        r = d["user"]["repositories"]
        repos += [n for n in r["nodes"] if n["defaultBranchRef"]]
        if not r["pageInfo"]["hasNextPage"]:
            break
        cursor = r["pageInfo"]["endCursor"]

    add = dele = 0
    for repo in repos:
        name = repo["nameWithOwner"]
        head = repo["defaultBranchRef"]["target"]["oid"]
        if cache.get(name, {}).get("oid") == head:
            add += cache[name]["add"]
            dele += cache[name]["del"]
            continue

        owner, rname = name.split("/")
        r_add = r_del = 0
        cur = None
        while True:
            d = gql("""
              query($owner:String!,$name:String!,$cursor:String) {
                repository(owner:$owner,name:$name) {
                  defaultBranchRef { target { ... on Commit {
                    history(first:100, after:$cursor) {
                      pageInfo { hasNextPage endCursor }
                      nodes { additions deletions author { user { login } } }
                    }
                  }}}
                }
              }""", {"owner": owner, "name": rname, "cursor": cur})
            ref = d["repository"]["defaultBranchRef"]
            if not ref:
                break
            h = ref["target"]["history"]
            for c in h["nodes"]:
                who = (c.get("author") or {}).get("user") or {}
                if who.get("login") == USER:
                    r_add += c["additions"]
                    r_del += c["deletions"]
            if not h["pageInfo"]["hasNextPage"]:
                break
            cur = h["pageInfo"]["endCursor"]

        cache[name] = {"oid": head, "add": r_add, "del": r_del}
        add += r_add
        dele += r_del
        print(f"    walked {name}: +{r_add} -{r_del}")

    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(cache, open(CACHE, "w"), indent=1, sort_keys=True)
    return add, dele, add - dele


# ── formatting ───────────────────────────────────────────────────────────
def human_age(created_iso):
    start = datetime.datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    years = now.year - start.year
    months = now.month - start.month
    days = now.day - start.day
    if days < 0:
        months -= 1
        days += 30
    if months < 0:
        years -= 1
        months += 12
    def p(n, w):
        return f"{n} {w}" + ("" if n == 1 else "s")
    return f"{p(years,'year')}, {p(months,'month')}, {p(days,'day')}"


def put(svg, vid, value):
    """Replace the text inside <tspan id="vid">…</tspan>."""
    pat = re.compile(rf'(<tspan[^>]*id="{vid}"[^>]*>)(.*?)(</tspan>)', re.S)
    if not pat.search(svg):
        print(f"    WARN: id '{vid}' not found in card")
        return svg
    return pat.sub(lambda m: m.group(1) + str(value) + m.group(3), svg, count=1)


def realign(svg, vid, target=70):
    """Re-pad the leader dots so the value column stays flush."""
    dots_id = vid.replace("_data", "_dots")
    m_val = re.search(rf'<tspan[^>]*id="{vid}"[^>]*>(.*?)</tspan>', svg, re.S)
    m_lbl = re.search(
        rf'<tspan class="key">([^<]*)</tspan><tspan class="cc" id="{dots_id}">',
        svg)
    if not (m_val and m_lbl):
        return svg
    n = max(2, target - len(m_lbl.group(1)) - len(m_val.group(1)))

    def repl(m):
        # Cards differ: the terminal card writes " .... ", the grid card
        # writes ": .... ". Preserve whichever separator this card uses.
        lead = ": " if m.group(2).lstrip().startswith(":") else " "
        return m.group(1) + lead + "." * n + " " + m.group(3)

    return re.sub(rf'(<tspan class="cc" id="{dots_id}">)([^<]*)(</tspan>)',
                  repl, svg, count=1)


def main():
    print(f"Updating stats for {USER}")

    print("  profile…")
    p = fetch_profile()

    print("  contributions…")
    try:
        contrib = f"{fetch_contributions(p['created']):,}"
    except Exception as e:                         # noqa: BLE001
        print(f"    contributions failed ({e}) — leaving n/a")
        contrib = "n/a"

    print("  lines of code…")
    try:
        a, dl, net = fetch_loc()
        loc = (f"{net:,}", f"{a:,}", f"{dl:,}")
    except Exception as e:                         # noqa: BLE001
        print(f"    LOC failed ({e}) — leaving n/a")
        loc = ("n/a", "n/a", "n/a")

    values = {
        "age_data":      human_age(p["created"]),
        "repo_data":     f'{p["repos"]:,}',
        "star_data":     f'{p["stars"]:,}',
        "follower_data": f'{p["followers"]:,}',
        "pr_data":       f'{p["prs"]:,}',
        "issue_data":    f'{p["issues"]:,}',
        "contrib_data":  contrib,
        "loc_data":      loc[0],
        "loc_add":       loc[1],
        "loc_del":       loc[2],
    }

    for card, target, loc_target, skip in CARDS:
        if not os.path.exists(card):
            print(f"  skip {card} (not present)")
            continue
        svg = open(card, encoding="utf-8").read()
        for vid, val in values.items():
            svg = put(svg, vid, val)
        for vid in values:
            if vid.endswith("_data") and vid not in skip:
                svg = realign(svg, vid,
                              loc_target if vid == "loc_data" else target)
        open(card, "w", encoding="utf-8").write(svg)
        print(f"  updated {card}")

    print("\nDone:")
    print(f"  repos {p['repos']}  stars {p['stars']}  followers {p['followers']}")
    print(f"  PRs {p['prs']}  issues {p['issues']}  contributions {contrib}")
    return


def _unused(p, svg):
    svg = put(svg, "age_data", human_age(p["created"]))
    svg = put(svg, "repo_data", f'{p["repos"]:,}')
    svg = put(svg, "star_data", f'{p["stars"]:,}')
    svg = put(svg, "follower_data", f'{p["followers"]:,}')
    svg = put(svg, "pr_data", f'{p["prs"]:,}')
    svg = put(svg, "issue_data", f'{p["issues"]:,}')

    print("  contributions…")
    try:
        svg = put(svg, "contrib_data", f"{fetch_contributions(p['created']):,}")
    except Exception as e:                         # noqa: BLE001
        print(f"    contributions failed ({e}) — leaving n/a")
        svg = put(svg, "contrib_data", "n/a")

    print("  lines of code…")
    try:
        a, dl, net = fetch_loc()
        svg = put(svg, "loc_data", f"{net:,}")
        svg = put(svg, "loc_add", f"{a:,}")
        svg = put(svg, "loc_del", f"{dl:,}")
    except Exception as e:                         # noqa: BLE001
        print(f"    LOC failed ({e}) — leaving n/a")
        for k in ("loc_data", "loc_add", "loc_del"):
            svg = put(svg, k, "n/a")

    for vid in ("age_data", "repo_data", "star_data", "follower_data",
                "pr_data", "issue_data", "contrib_data", "loc_data"):
        svg = realign(svg, vid)

    open(CARD, "w", encoding="utf-8").write(svg)
    print("\nDone:")
    print(f"  repos {p['repos']}  stars {p['stars']}  followers {p['followers']}")
    print(f"  PRs {p['prs']}  issues {p['issues']}")


if __name__ == "__main__":
    main()
