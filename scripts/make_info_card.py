#!/usr/bin/env python3
"""
make_info_card.py — Generate a neofetch-style info card SVG.

Creates a terminal-inspired panel with your role, tech stack, and highlights
that fades/slides in line-by-line using CSS keyframes inside the SVG.

Usage:
    python scripts/make_info_card.py

    Set STATIC=1 to emit a frozen frame (no animation):
        STATIC=1 python scripts/make_info_card.py

Output:
    info-card.svg
"""

import os
import pathlib

# ── configuration ──────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC", "0") == "1"

USERNAME = "sxashank"

# ── card content ───────────────────────────────────────────────────
# Each entry: (color_for_label, label, value)
# Use None for a separator line
TITLE_LINE = f"{USERNAME}@github"
TITLE_DASHES = "─" * (len(TITLE_LINE) + 2)

INFO_LINES = [
    # (label_color, label, value)
    ("title", TITLE_LINE, None),
    ("dashes", TITLE_DASHES, None),
    ("#f0883e", "Now", "Pre-Final Year @ IIIT Allahabad"),
    ("#f0883e", "Focus", "AI/ML · SDE · System Design"),
    (None, None, None),  # separator
    ("#58a6ff", "Languages", "Python · C++ · JavaScript · TypeScript"),
    ("#58a6ff", "AI/ML", "PyTorch · TensorFlow · LangChain · RAG"),
    ("#58a6ff", "Backend", "Node.js · Express · FastAPI · Django"),
    ("#58a6ff", "Frontend", "React · Next.js · Tailwind CSS"),
    ("#58a6ff", "DevOps", "Docker · AWS · GitHub Actions · Linux"),
    ("#58a6ff", "Databases", "PostgreSQL · MongoDB · Redis"),
    (None, None, None),  # separator
    ("#3fb950", "Highlights", "Open Source Contributor"),
    ("#3fb950", "", "Full-Stack Project Builder"),
    ("#3fb950", "", "AI/ML Research Enthusiast"),
    ("#3fb950", "", "System Design Evangelist"),
]

# ── styling ────────────────────────────────────────────────────────
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
TEXT_COLOR = "#c9d1d9"
TITLE_COLOR = "#58a6ff"
DASHES_COLOR = "#484f58"
FONT_SIZE = 14
LINE_H = 22
PAD_X = 28
PAD_Y = 28
CARD_W = 480
LABEL_W = 120  # width reserved for label column


def build_svg() -> str:
    """Build the info-card SVG string."""
    # calculate height
    content_lines = len(INFO_LINES)
    card_h = PAD_Y * 2 + content_lines * LINE_H + 12

    parts: list[str] = []

    # ── header ─────────────────────────────────────────────────
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {CARD_W} {card_h}" '
        f'width="{CARD_W}" height="{card_h}">'
    )

    # ── style block with animations ────────────────────────────
    if not STATIC:
        parts.append("<style>")
        parts.append("""
        @keyframes fadeSlideIn {
            0%   { opacity: 0; transform: translateY(8px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        .info-line {
            opacity: 0;
            animation: fadeSlideIn 0.4s ease-out forwards;
        }
        """)
        parts.append("</style>")

    # ── background ─────────────────────────────────────────────
    parts.append(
        f'<rect width="100%" height="100%" fill="{BG_COLOR}" rx="12" '
        f'stroke="{BORDER_COLOR}" stroke-width="1" />'
    )

    # ── terminal dots ──────────────────────────────────────────
    dot_y = 16
    for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        cx = 18 + i * 20
        parts.append(f'<circle cx="{cx}" cy="{dot_y}" r="6" fill="{color}" />')

    # ── info lines ─────────────────────────────────────────────
    start_y = PAD_Y + 24  # below the dots
    for idx, entry in enumerate(INFO_LINES):
        y = start_y + idx * LINE_H
        delay = idx * 0.08

        anim_attr = ""
        anim_class = ""
        if not STATIC:
            anim_class = ' class="info-line"'
            anim_attr = f' style="animation-delay: {delay:.2f}s;"'

        if entry[0] is None:
            # separator — render a dim line
            parts.append(
                f'<g{anim_class}{anim_attr}>'
                f'<text x="{PAD_X}" y="{y}" '
                f'font-family="\'Courier New\', monospace" '
                f'font-size="{FONT_SIZE}" fill="{DASHES_COLOR}">{"─" * 38}</text>'
                f'</g>'
            )
        elif entry[0] == "title":
            # title line
            parts.append(
                f'<g{anim_class}{anim_attr}>'
                f'<text x="{PAD_X}" y="{y}" '
                f'font-family="\'Courier New\', monospace" '
                f'font-size="{FONT_SIZE + 2}" font-weight="bold" '
                f'fill="{TITLE_COLOR}">{entry[1]}</text>'
                f'</g>'
            )
        elif entry[0] == "dashes":
            # dashes below title
            parts.append(
                f'<g{anim_class}{anim_attr}>'
                f'<text x="{PAD_X}" y="{y}" '
                f'font-family="\'Courier New\', monospace" '
                f'font-size="{FONT_SIZE}" fill="{DASHES_COLOR}">{entry[1]}</text>'
                f'</g>'
            )
        else:
            label_color = entry[0]
            label = entry[1]
            value = entry[2]
            parts.append(f'<g{anim_class}{anim_attr}>')
            if label:
                parts.append(
                    f'<text x="{PAD_X}" y="{y}" '
                    f'font-family="\'Courier New\', monospace" '
                    f'font-size="{FONT_SIZE}" fill="{label_color}" '
                    f'font-weight="bold">{_esc(label)}</text>'
                )
                # value after label
                val_x = PAD_X + LABEL_W
                parts.append(
                    f'<text x="{val_x}" y="{y}" '
                    f'font-family="\'Courier New\', monospace" '
                    f'font-size="{FONT_SIZE}" fill="{TEXT_COLOR}">{_esc(value)}</text>'
                )
            else:
                # continuation line (no label, just value indented)
                val_x = PAD_X + LABEL_W
                parts.append(
                    f'<text x="{val_x}" y="{y}" '
                    f'font-family="\'Courier New\', monospace" '
                    f'font-size="{FONT_SIZE}" fill="{TEXT_COLOR}">{_esc(value)}</text>'
                )
            parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


def _esc(text: str | None) -> str:
    if text is None:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def main():
    mode = "static" if STATIC else "animated"
    print(f"[>] Building {mode} info card ...")
    svg = build_svg()
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"[OK] Saved {OUTPUT.name}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
