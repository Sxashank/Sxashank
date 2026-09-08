#!/usr/bin/env python3
"""
prep_photo.py — Prepare a portrait for ASCII conversion.

Steps:
  1. Remove background with rembg (isolates the subject).
  2. Boost local contrast with CLAHE (brings out highlights/shadows).
  3. Composite onto pure white (background maps to spaces in ASCII).

Usage:
    python scripts/prep_photo.py [source-photo.png]

Output:
    source-prepped.png  (grayscale, white-bg, contrast-enhanced)
"""

import sys
import pathlib
import numpy as np
from PIL import Image
from rembg import remove
import cv2

# ── paths ──────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "source-photo.png"
OUTPUT = ROOT / "source-prepped.png"


def main():
    src_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    if not src_path.exists():
        print(f"✗ Source image not found: {src_path}")
        sys.exit(1)

    print(f"[>] Loading {src_path.name} ...")
    img = Image.open(src_path).convert("RGBA")

    # 1. remove background
    print("[>] Removing background ...")
    img_nobg = remove(img)

    # 2. composite onto white
    white = Image.new("RGBA", img_nobg.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white, img_nobg)
    gray = composited.convert("L")  # to grayscale

    # 3. CLAHE contrast boost
    print("[>] Boosting contrast (CLAHE) ...")
    arr = np.array(gray)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    arr = clahe.apply(arr)

    # save
    result = Image.fromarray(arr)
    result.save(OUTPUT)
    print(f"[OK] Saved {OUTPUT.name}  ({result.size[0]}x{result.size[1]})")


if __name__ == "__main__":
    main()
