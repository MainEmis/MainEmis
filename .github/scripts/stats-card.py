"""neofetch-style status card — Apple-inspired system info block.

Generates a clean SVG card styled like `neofetch` output.
Rotates through subtle variants via GitHub Actions schedule.
No API dependency — pure aesthetic.
"""

import os
from datetime import datetime, timezone


STATUS_LINES = [
    "building something that breaks before it ships",
    "reverse-engineering undocumented protocols",
    "tuning inference pipelines at 2 AM",
    "writing Bash one-liners that shouldn't exist",
    "hunting race conditions in distributed systems",
    "making ESP32 do things it wasn't designed for",
    "profiling Python until it hurts",
    "auditing auth chains, finding the gap",
]

def pick_status():
    """Select a status line, trying not to repeat."""
    # Use the day of year to cycle deterministically
    return STATUS_LINES[datetime.now(timezone.utc).timetuple().tm_yday % len(STATUS_LINES)]


def generate_svg():
    W, H = 600, 220
    accent = "#0AFF9D"
    dim = "#484F58"
    bg = "#0D1117"
    border = "#21262D"
    text = "#E6EDF3"
    secondary = "#8B949E"
    now = datetime.now(timezone.utc)

    status = pick_status()

    # Build the neofetch-style ASCII art (left column)
    ascii_art = [
        "      :---:       ",
        "    :-------:     ",
        "  :----------:   ",
        ":--------=-----: ",
        ":------=++*=---: ",
        ":-----=+***+==-: ",
        ":----=+****+=--: ",
        ":---=+*****+---: ",
        ":--=+******=---: ",
        ":--+******=----: ",
        " :+******=----:  ",
        "  :+***+=----:   ",
        "   :=+=-----:    ",
        "    :------:     ",
        "      :---:       ",
    ]

    # Info lines (right column)
    info = [
        ("",        f"emilio@github"),
        ("",        "───────────────"),
        ("OS",       "macOS Sequoia · Arch Linux"),
        ("Shell",    "zsh · bash"),
        ("Editor",   "terminal-first, dark mode"),
        ("Focus",    "Backend · Security · Signal Processing"),
        ("Lang",     "Python · Node.js · C · Bash"),
        ("Location", "Mexico"),
        ("",        "───────────────"),
        ("",        status),
    ]

    # Generate SVG
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <!-- Card -->
  <rect width="{W}" height="{H}" rx="10" fill="{bg}" stroke="{border}" stroke-width="1"/>
  <rect width="{W}" height="{H}" rx="10" fill="url(#fade)"/>

  <!-- Accent dot -->
  <circle cx="16" cy="16" r="4" fill="{accent}" opacity="0.7"/>
  <circle cx="16" cy="16" r="7" fill="{accent}" opacity="0.15"/>

  <!-- Title -->
  <text x="30" y="20" font-family="SF Mono,Menlo,monospace" font-size="11" fill="{secondary}">
    $ neofetch --stdout
  </text>'''

    # ASCII art (left side)
    art_x = 20
    art_y = 45
    for i, line in enumerate(ascii_art):
        y = art_y + i * 11
        svg += f'\n    <text x="{art_x}" y="{y}" font-family="SF Mono,Menlo,monospace" font-size="10" fill="{accent}" opacity="0.7">{line}</text>'

    # Info lines (right side)
    info_x = 200
    info_y = 45
    for i, (label, value) in enumerate(info):
        y = info_y + i * 12.5
        if label:
            svg += f'\n    <text x="{info_x}" y="{y}" font-family="SF Mono,Menlo,monospace" font-size="10" fill="{dim}">{label}</text>'
            svg += f'\n    <text x="{info_x + 100}" y="{y}" font-family="SF Mono,Menlo,monospace" font-size="10" fill="{text}">{value}</text>'
        else:
            status_prefixes = ("building", "reverse", "tuning", "writing", "hunting", "making", "profiling", "auditing")
            is_status = value.startswith(status_prefixes)
            fill_color = text if is_status else dim
            svg += f'\n    <text x="{info_x}" y="{y}" font-family="SF Mono,Menlo,monospace" font-size="10" fill="{fill_color}">{value}</text>'

    # Bottom accent bar
    svg += f'''
  <rect x="0" y="{H-1}" width="{W}" height="1" fill="{border}"/>
  <rect x="0" y="{H-1}" width="80" height="1" fill="{accent}" opacity="0.5"/>

  <!-- Timestamp -->
  <text x="{W-20}" y="{H-16}" font-family="SF Mono,Menlo,monospace" font-size="9" fill="{dim}" text-anchor="end">
    refreshed {now.strftime("%b %d, %Y · %H:%M UTC")}
  </text>
</svg>'''

    return svg


def main():
    svg = generate_svg()
    os.makedirs("dist", exist_ok=True)
    with open("dist/stats-card.svg", "w") as f:
        f.write(svg)
    print(f"Generated stats-card.svg ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
