#!/usr/bin/env python3
"""
render_heatmap_svg.py — Render data/contributions.json as an animated
contribution heatmap SVG.

The classic 53-week × 7-day calendar of rounded, colored boxes with a
GitHub-ish green ramp. Revealed once with a diagonal line-after-line
slide-down (CSS keyframes, plays once, then freezes).

Usage:
    python scripts/render_heatmap_svg.py

Output:
    contrib-heatmap.svg
"""

import json
import pathlib

# ── configuration ──────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "contrib-heatmap.svg"

# GitHub-ish green ramp: level 0 → level 4+
PALETTE = [
    "#161b22",   # 0 — none
    "#0e4429",   # 1
    "#006d32",   # 2
    "#26a641",   # 3
    "#39d353",   # 4
    "#69f0a0",   # 5 — neon top
]

BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
TEXT_COLOR = "#8b949e"
TITLE_COLOR = "#c9d1d9"

BOX_SIZE = 12       # side length of each day box
BOX_GAP = 3         # gap between boxes
BOX_RADIUS = 2      # border-radius
WEEKS = 53
DAYS_PER_WEEK = 7

PAD_X = 48          # left pad (for day labels)
PAD_Y = 42          # top pad (for month labels)
PAD_BOTTOM = 60     # bottom pad (for legend + stats)
PAD_RIGHT = 20

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]


def build_svg(data: dict) -> str:
    days = data["days"]
    total = data["total_contributions"]

    # ── build the week/day grid ────────────────────────────────
    # GitHub calendar: columns are weeks, rows are days (0=Sun..6=Sat)
    # We need to organize the flat list into a 53×7 grid
    grid: list[list[dict | None]] = [[None] * DAYS_PER_WEEK for _ in range(WEEKS)]

    if days:
        from datetime import datetime, timedelta

        # Find the last date and work backwards 53 weeks
        last_date = datetime.strptime(days[-1]["date"], "%Y-%m-%d")
        # Find the start of the calendar (Sunday of the week 52 weeks before last)
        start_date = last_date - timedelta(weeks=52)
        # Adjust to the nearest Sunday
        start_date = start_date - timedelta(days=start_date.weekday() + 1)
        if start_date.weekday() != 6:  # if not Sunday
            start_date = start_date - timedelta(days=(start_date.weekday() + 1) % 7)

        # Create a date lookup
        date_lookup = {d["date"]: d for d in days}

        for week_idx in range(WEEKS):
            for day_idx in range(DAYS_PER_WEEK):
                current_date = start_date + timedelta(weeks=week_idx, days=day_idx)
                date_str = current_date.strftime("%Y-%m-%d")
                if date_str in date_lookup:
                    grid[week_idx][day_idx] = date_lookup[date_str]
                else:
                    grid[week_idx][day_idx] = {"date": date_str, "count": 0, "level": 0}

    # ── SVG dimensions ─────────────────────────────────────────
    grid_w = WEEKS * (BOX_SIZE + BOX_GAP)
    grid_h = DAYS_PER_WEEK * (BOX_SIZE + BOX_GAP)
    svg_w = PAD_X + grid_w + PAD_RIGHT
    svg_h = PAD_Y + grid_h + PAD_BOTTOM

    parts: list[str] = []

    # ── header ─────────────────────────────────────────────────
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w} {svg_h}" '
        f'width="{svg_w}" height="{svg_h}">'
    )

    # ── styles with CSS keyframes ──────────────────────────────
    parts.append("<style>")
    parts.append(f"""
    .bg {{ fill: {BG_COLOR}; }}
    .day-box {{ rx: {BOX_RADIUS}; ry: {BOX_RADIUS}; }}
    .label {{ fill: {TEXT_COLOR}; font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 11px; }}
    .stats {{ fill: {TEXT_COLOR}; font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 12px; }}
    .title-text {{ fill: {TITLE_COLOR}; font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 13px; font-weight: 600; }}

    @keyframes slideIn {{
        0%   {{ opacity: 0; transform: translateY(-8px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}
    .week-col {{
        opacity: 0;
        animation: slideIn 0.3s ease-out forwards;
    }}
    """)
    # per-column animation delays (diagonal reveal)
    for w in range(WEEKS):
        delay = w * 0.03
        parts.append(f"    .week-{w} {{ animation-delay: {delay:.2f}s; }}")
    parts.append("</style>")

    # ── background ─────────────────────────────────────────────
    parts.append(
        f'<rect class="bg" width="100%" height="100%" rx="12" '
        f'stroke="{BORDER_COLOR}" stroke-width="1" />'
    )

    # ── month labels ───────────────────────────────────────────
    if days:
        shown_months: set[str] = set()
        for w in range(WEEKS):
            cell = grid[w][0]
            if cell:
                month = int(cell["date"][5:7])
                month_key = cell["date"][:7]
                if month_key not in shown_months:
                    shown_months.add(month_key)
                    x = PAD_X + w * (BOX_SIZE + BOX_GAP)
                    parts.append(
                        f'<text class="label" x="{x}" y="{PAD_Y - 8}">'
                        f'{MONTH_NAMES[month - 1]}</text>'
                    )

    # ── day labels (Mon, Wed, Fri) ─────────────────────────────
    for d, label in enumerate(DAY_LABELS):
        if label:
            y = PAD_Y + d * (BOX_SIZE + BOX_GAP) + BOX_SIZE - 1
            parts.append(
                f'<text class="label" x="{PAD_X - 32}" y="{y}" '
                f'text-anchor="start">{label}</text>'
            )

    # ── contribution boxes ─────────────────────────────────────
    for w in range(WEEKS):
        x_base = PAD_X + w * (BOX_SIZE + BOX_GAP)
        parts.append(f'<g class="week-col week-{w}">')
        for d in range(DAYS_PER_WEEK):
            cell = grid[w][d]
            if cell is None:
                continue
            level = min(cell.get("level", 0), len(PALETTE) - 1)
            color = PALETTE[level]
            x = x_base
            y = PAD_Y + d * (BOX_SIZE + BOX_GAP)
            count = cell.get("count", 0)
            date = cell.get("date", "")
            parts.append(
                f'<rect class="day-box" x="{x}" y="{y}" '
                f'width="{BOX_SIZE}" height="{BOX_SIZE}" fill="{color}">'
                f'<title>{count} contributions on {date}</title>'
                f'</rect>'
            )
        parts.append("</g>")

    # ── legend (Less → More) ───────────────────────────────────
    legend_y = PAD_Y + grid_h + 20
    legend_x = svg_w - PAD_RIGHT - 160

    parts.append(f'<text class="label" x="{legend_x}" y="{legend_y + 10}">Less</text>')
    for i, color in enumerate(PALETTE):
        bx = legend_x + 36 + i * (BOX_SIZE + 3)
        parts.append(
            f'<rect class="day-box" x="{bx}" y="{legend_y}" '
            f'width="{BOX_SIZE}" height="{BOX_SIZE}" fill="{color}" />'
        )
    more_x = legend_x + 36 + len(PALETTE) * (BOX_SIZE + 3) + 4
    parts.append(f'<text class="label" x="{more_x}" y="{legend_y + 10}">More</text>')

    # ── stats footer ───────────────────────────────────────────
    stats_y = legend_y + 2
    streak_text = f"Current streak: {data.get('current_streak', 0)}d"
    total_text = f"{total:,} contributions in the last year"

    parts.append(
        f'<text class="stats" x="{PAD_X}" y="{stats_y + 10}">'
        f'{total_text}</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not INPUT.exists():
        print(f"[X] Contribution data not found: {INPUT}")
        print("  Run  python scripts/fetch_contributions.py  first.")
        return

    data = json.loads(INPUT.read_text(encoding="utf-8"))
    print(f"[>] Rendering heatmap for @{data.get('username', '?')} "
          f"({data.get('total_contributions', 0):,} contributions) ...")

    svg = build_svg(data)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"[OK] Saved {OUTPUT.name}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
