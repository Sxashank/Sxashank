#!/usr/bin/env python3
"""
fetch_contributions.py — Scrape your public GitHub contribution calendar.

Fetches the HTML fragment from:
    https://github.com/users/<USERNAME>/contributions

Parses each day cell with BeautifulSoup and writes data/contributions.json
with raw day data plus derived stats (current streak, longest streak, best
day, total count, monthly totals).

No GitHub token required — this is a public endpoint.

Usage:
    python scripts/fetch_contributions.py

Output:
    data/contributions.json
"""

import json
import pathlib
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

# ── configuration ──────────────────────────────────────────────────
USERNAME = "Sxashank"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "contributions.json"

URL = f"https://github.com/users/{USERNAME}/contributions"


def fetch_and_parse() -> dict:
    """Fetch contribution HTML and parse into structured data."""
    print(f"[>] Fetching contributions for @{USERNAME} ...")
    resp = requests.get(URL, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (profile-readme-bot)",
        "Accept": "text/html",
    })
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # GitHub renders contribution cells as <td> with data-date and data-level
    days = []
    cells = soup.select("td.ContributionCalendar-day")

    for cell in cells:
        date_str = cell.get("data-date", "")
        level = int(cell.get("data-level", "0"))
        
        # Try to get the count from the tooltip or the cell's text
        count = 0
        # Look for tooltip span inside the cell
        tooltip = cell.find("span", class_="sr-only")
        if tooltip:
            text = tooltip.get_text(strip=True)
            # Parse "X contributions on ..." or "No contributions on ..."
            if text.startswith("No"):
                count = 0
            else:
                try:
                    count = int(text.split()[0].replace(",", ""))
                except (ValueError, IndexError):
                    count = 0
        
        # Also check tool-tip element
        if count == 0 and level > 0:
            tip_id = cell.get("id", "")
            if tip_id:
                tooltip_el = soup.find("tool-tip", attrs={"for": tip_id})
                if tooltip_el:
                    text = tooltip_el.get_text(strip=True)
                    if not text.startswith("No"):
                        try:
                            count = int(text.split()[0].replace(",", ""))
                        except (ValueError, IndexError):
                            # estimate from level
                            count = level * 3

        if count == 0 and level > 0:
            # fallback: estimate from level
            count = max(1, level * 2)

        if date_str:
            days.append({
                "date": date_str,
                "count": count,
                "level": level,
            })

    # sort by date
    days.sort(key=lambda d: d["date"])

    # ── derived stats ──────────────────────────────────────────
    total = sum(d["count"] for d in days)
    best_day = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}

    # streaks
    current_streak = 0
    longest_streak = 0
    streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            streak += 1
            current_streak = max(current_streak, streak)
        else:
            if current_streak == 0:
                # haven't found a contributing day yet at the end
                pass
            else:
                break

    streak = 0
    for d in days:
        if d["count"] > 0:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    # monthly totals
    monthly: dict[str, int] = {}
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + d["count"]

    result = {
        "username": USERNAME,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "total_contributions": total,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "monthly_totals": monthly,
        "days": days,
    }

    return result


def main():
    data = fetch_and_parse()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"[OK] {len(data['days'])} days -> {OUTPUT.name}")
    print(f"  Total: {data['total_contributions']:,}  |  "
          f"Streak: {data['current_streak']}d  |  "
          f"Best: {data['best_day']['count']} on {data['best_day']['date']}")


if __name__ == "__main__":
    main()
