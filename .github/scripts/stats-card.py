"""Custom GitHub stats card generator — Apple-inspired minimal design.

Queries GitHub API for real user stats and renders a clean SVG card.
Designed to run as a GitHub Actions workflow on schedule.
"""

import json
import os
import sys
import textwrap
from datetime import datetime, timezone

def api(path):
    """Call GitHub REST API."""
    import urllib.request
    token = os.environ["GH_TOKEN"]
    url = f"https://api.github.com/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "hermes-stats-card/1.0",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def fetch_stats(username):
    """Gather real stats from GitHub API."""
    user = api(f"users/{username}")

    # Count repos
    repos = []
    page = 1
    while True:
        batch = api(f"users/{username}/repos?per_page=100&page={page}&sort=pushed")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    public_repos = len([r for r in repos if not r["fork"]])
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)

    # Language breakdown
    langs = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            langs[lang] = langs.get(lang, 0) + 1
    top_langs = sorted(langs.items(), key=lambda x: -x[1])[:5]

    # Recent events (last 90 days)
    events = api(f"users/{username}/events/public?per_page=100")
    now = datetime.now(timezone.utc)
    recent = 0
    for e in events:
        dt = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00"))
        if (now - dt).days <= 90:
            recent += 1

    # PR count
    prs_found = 0
    for e in events:
        if e["type"] == "PullRequestEvent" and e["payload"].get("action") == "opened":
            prs_found += 1

    return {
        "username": username,
        "name": user.get("name") or username,
        "followers": user.get("followers", 0),
        "public_repos": public_repos,
        "total_stars": total_stars,
        "recent_activity": recent,
        "prs": prs_found,
        "top_langs": top_langs,
        "year": now.year,
    }

def format_num(n):
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)

def generate_svg(stats):
    name = stats["name"]
    username = stats["username"]
    year = stats["year"]

    # Card dimensions
    W, H = 620, 180
    accent = "#0AFF9D"
    bg = "#0D1117"
    border = "#21262D"
    text_primary = "#E6EDF3"
    text_secondary = "#8B949E"
    lang_colors = ["#58A6FF", "#3FB950", "#D29922", "#F78166", "#A371F7"]

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="glow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
    <filter id="blur">
      <feGaussianBlur stdDeviation="1.5"/>
    </filter>
  </defs>

  <!-- Card background -->
  <rect width="{W}" height="{H}" rx="12" fill="{bg}" stroke="{border}" stroke-width="1"/>
  <rect width="{W}" height="{H}" rx="12" fill="url(#glow)"/>

  <!-- Accent line top -->
  <rect x="0" y="0" width="{W}" height="3" rx="12" fill="{accent}" opacity="0.5"/>

  <!-- Name -->
  <text x="24" y="38" font-family="SF Mono,Menlo,Monaco,Consolas,monospace" font-size="13" fill="{text_secondary}">
    $ whoami
  </text>
  <text x="24" y="60" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,sans-serif" font-size="20" font-weight="600" fill="{text_primary}">
    {name}
  </text>

  <!-- Stats row -->
  <g transform="translate(24, 82)">
    <!-- Public repos -->
    <text x="0" y="0" font-family="SF Mono,Menlo,monospace" font-size="22" font-weight="700" fill="{accent}">{stats['public_repos']}</text>
    <text x="0" y="18" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="10" fill="{text_secondary}">REPOS</text>

    <!-- Stars -->
    <text x="80" y="0" font-family="SF Mono,Menlo,monospace" font-size="22" font-weight="700" fill="{text_primary}">{format_num(stats['total_stars'])}</text>
    <text x="80" y="18" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="10" fill="{text_secondary}">STARS</text>

    <!-- Recent activity -->
    <text x="160" y="0" font-family="SF Mono,Menlo,monospace" font-size="22" font-weight="700" fill="{text_primary}">{stats['recent_activity']}</text>
    <text x="160" y="18" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="10" fill="{text_secondary}">EVENTS (90d)</text>

    <!-- PRs -->
    <text x="260" y="0" font-family="SF Mono,Menlo,monospace" font-size="22" font-weight="700" fill="{text_primary}">{stats['prs']}</text>
    <text x="260" y="18" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="10" fill="{text_secondary}">PRs (90d)</text>

    <!-- Followers -->
    <text x="340" y="0" font-family="SF Mono,Menlo,monospace" font-size="22" font-weight="700" fill="{text_primary}">{format_num(stats['followers'])}</text>
    <text x="340" y="18" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="10" fill="{text_secondary}">FOLLOWERS</text>
  </g>

  <!-- Language bar -->
  <g transform="translate(24, 138)">'''

    total_lang = sum(c for _, c in stats["top_langs"])
    if total_lang == 0:
        total_lang = 1

    x_offset = 0
    bar_width = 280
    for i, (lang, count) in enumerate(stats["top_langs"]):
        w = max(int(bar_width * count / total_lang), 30)
        color = lang_colors[i % len(lang_colors)]
        svg += f'\n    <rect x="{x_offset}" y="0" width="{w}" height="8" rx="4" fill="{color}" opacity="0.8"/>'
        x_offset += w + 4

    # Legend
    svg += f'\n    <text x="0" y="24" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="10" fill="{text_secondary}">'
    svg += " · ".join(f'{lang}' for lang, _ in stats["top_langs"])
    svg += '</text>'

    svg += f'''
  </g>

  <!-- Footer -->
  <text x="{W - 24}" y="{H - 16}" font-family="SF Mono,Menlo,monospace" font-size="9" fill="{text_secondary}" text-anchor="end">
    github.com/{username} · refreshed {datetime.now(timezone.utc).strftime("%b %d, %Y")}
  </text>
</svg>'''

    return svg


def main():
    username = os.environ.get("GH_USERNAME", "MainEmis")
    stats = fetch_stats(username)
    svg = generate_svg(stats)

    os.makedirs("dist", exist_ok=True)
    output_path = "dist/stats-card.svg"
    with open(output_path, "w") as f:
        f.write(svg)

    # Also write a dark variant (same for now, since we're dark by default)
    with open("dist/stats-card.svg", "w") as f:
        f.write(svg)

    print(f"Generated {output_path} ({len(svg)} bytes)")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
