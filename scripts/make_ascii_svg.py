#!/usr/bin/env python3
"""
make_ascii_svg.py — Convert the prepped portrait into a self-typing
monochrome ASCII SVG with SMIL animation.

The prepped image is downsampled to a character grid (~100 cols × ~53 rows).
Each pixel's brightness picks a glyph from a density ramp. The SVG animates
each row with a clip-path wipe left→right, staggered top→bottom, so the
portrait appears to "type" itself in. Plays once, then freezes.

Usage:
    python scripts/make_ascii_svg.py

Output:
    sxashank-ascii.svg
"""

import os
import pathlib
import numpy as np
from PIL import Image

# ── configuration ──────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
INPUT = ROOT / "source-prepped.png"
OUTPUT = ROOT / "sxashank-ascii.svg"

# ASCII density ramp: bright (sparse) → dark (dense)
RAMP = " .`:-=+*cs#%@"

# grid dimensions
COLS = 90
ROWS = 55

# SVG character rendering
CHAR_W = 7.2       # monospace character width in px
CHAR_H = 12.5      # line height in px
FONT_SIZE = 11      # font-size in px
FILL_COLOR = "#c9d1d9"   # light gray (GitHub dark-theme friendly)
BG_COLOR = "#0d1117"     # dark background

# animation timing
ROW_DURATION = 0.12    # seconds for each row to wipe in
ROW_STAGGER = 0.04     # stagger between rows
CURSOR_WIDTH = 8       # px width of the typing cursor block

# env: STATIC=1 to emit a frozen (no-animation) version
STATIC = os.environ.get("STATIC", "0") == "1"


def image_to_ascii_grid(img_path: pathlib.Path) -> list[str]:
    """Load the prepped image and convert to a list of ASCII strings."""
    img = Image.open(img_path).convert("L")
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    pixels = np.array(img)

    lines = []
    for row in pixels:
        chars = []
        for val in row:
            idx = int(val / 256 * len(RAMP))
            idx = min(idx, len(RAMP) - 1)
            chars.append(RAMP[idx])
        lines.append("".join(chars))
    return lines


def escape_xml(text: str) -> str:
    """Escape characters that break SVG/XML."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
    )


def build_svg(lines: list[str]) -> str:
    """Build the full SVG string with SMIL row-wipe animation."""
    pad_x, pad_y = 16, 16
    svg_w = COLS * CHAR_W + pad_x * 2
    svg_h = ROWS * CHAR_H + pad_y * 2

    parts: list[str] = []

    # ── SVG header ─────────────────────────────────────────────
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w:.1f} {svg_h:.1f}" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}" '
        f'font-family="\'Courier New\', Courier, monospace" '
        f'font-size="{FONT_SIZE}" '
        f'fill="{FILL_COLOR}">'
    )

    # ── background ─────────────────────────────────────────────
    parts.append(
        f'<rect width="100%" height="100%" fill="{BG_COLOR}" rx="12" />'
    )

    # ── defs: clip paths for each row ──────────────────────────
    if not STATIC:
        parts.append("<defs>")
        for i in range(len(lines)):
            row_y = pad_y + i * CHAR_H - 2
            clip_id = f"clip-r{i}"
            row_w = COLS * CHAR_W + CURSOR_WIDTH
            parts.append(
                f'<clipPath id="{clip_id}">'
                f'<rect x="{pad_x}" y="{row_y}" width="{row_w:.1f}" height="{CHAR_H + 4}" >'
                f'<animate attributeName="width" from="0" to="{row_w:.1f}" '
                f'dur="{ROW_DURATION}s" begin="{i * ROW_STAGGER:.3f}s" '
                f'fill="freeze" />'
                f'</rect>'
                f'</clipPath>'
            )
        parts.append("</defs>")

    # ── text rows ──────────────────────────────────────────────
    for i, line in enumerate(lines):
        y = pad_y + i * CHAR_H + FONT_SIZE  # baseline
        text_el = (
            f'<text x="{pad_x}" y="{y:.1f}" '
            f'xml:space="preserve">{escape_xml(line)}</text>'
        )

        if STATIC:
            parts.append(text_el)
        else:
            # wrap in group with clip-path
            parts.append(
                f'<g clip-path="url(#clip-r{i})">'
                f'{text_el}'
            )
            # cursor block that rides the wipe edge
            cursor_x_start = pad_x
            cursor_x_end = pad_x + COLS * CHAR_W
            cursor_y = pad_y + i * CHAR_H
            parts.append(
                f'<rect x="{cursor_x_start}" y="{cursor_y}" '
                f'width="{CURSOR_WIDTH}" height="{CHAR_H}" '
                f'fill="{FILL_COLOR}" opacity="0.85" rx="1">'
                f'<animate attributeName="x" '
                f'from="{cursor_x_start}" to="{cursor_x_end:.1f}" '
                f'dur="{ROW_DURATION}s" begin="{i * ROW_STAGGER:.3f}s" '
                f'fill="freeze" />'
                f'<animate attributeName="opacity" '
                f'from="0.85" to="0" '
                f'dur="0.01s" begin="{(i * ROW_STAGGER + ROW_DURATION):.3f}s" '
                f'fill="freeze" />'
                f'</rect>'
            )
            parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not INPUT.exists():
        print(f"[X] Prepped image not found: {INPUT}")
        print("  Run  python scripts/prep_photo.py  first.")
        return

    print(f"[>] Converting {INPUT.name} to ASCII grid ({COLS}x{ROWS}) ...")
    lines = image_to_ascii_grid(INPUT)

    mode = "static" if STATIC else "animated"
    print(f"[>] Building {mode} SVG ...")
    svg = build_svg(lines)

    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"[OK] Saved {OUTPUT.name}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
