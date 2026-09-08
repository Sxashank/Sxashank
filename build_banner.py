import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from importlib import util
import math
import random
import scipy.optimize
import cv2
import os

USERNAME = "Sxashank"
ROLE = "Pre-Final Year @ IIIT Allahabad"
ORIGIN = "Prayagraj, India"
STATUS = "ONLINE"
TOOLCHAIN = "Python . Git . GitHub . VS Code"
LANGUAGES = "Python . JavaScript . C++ . SQL"
FOCUS = "AI/ML . Full Stack . DSA"
OS_NAME = "Windows / Arch Linux"
SHELL = "PowerShell"

W_SVG = 1180
H_SVG = 610

# Palettes
PALETTE = {
    "dark": {"bg": "#0A101F", "portrait": "#A78BFA", "chrome": "#22D3EE", "accent": "#10B981"},
    "light": {"bg": "#F8FAFC", "portrait": "#7C3AED", "chrome": "#0891B2", "accent": "#10B981"}
}

def floyd_steinberg_dither(img_gray):
    # simple floyd steinberg
    arr = np.array(img_gray, dtype=float)
    h, w = arr.shape
    for y in range(h):
        for x in range(w):
            old = arr[y, x]
            new = 255 if old > 128 else 0
            arr[y, x] = new
            err = old - new
            if x + 1 < w: arr[y, x + 1] += err * 7 / 16
            if y + 1 < h:
                if x > 0: arr[y + 1, x - 1] += err * 3 / 16
                arr[y + 1, x] += err * 5 / 16
                if x + 1 < w: arr[y + 1, x + 1] += err * 1 / 16
    return arr > 128

def generate_logo_points(text, num_points):
    # Render text to an image and get points
    img = Image.new("L", (200, 200), 0)
    import cv2
    arr = np.zeros((200, 200), dtype=np.uint8)
    cv2.putText(arr, text, (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 3, 255, 5, cv2.LINE_AA)
    y_coords, x_coords = np.where(arr > 128)
    if len(y_coords) == 0:
        return np.random.rand(num_points, 2) * 200
    pts = np.column_stack((x_coords, y_coords))
    indices = np.random.choice(len(pts), num_points, replace=True)
    return pts[indices]

def build_svg(theme):
    pal = PALETTE[theme]
    
    # Process image
    src = Image.open("source-photo.png").convert("RGBA")
    # Crop to a nice head-and-shoulders ratio before shrinking
    w, h = src.size
    # let's try a 300x340 aspect ratio crop from the center
    target_aspect = 300 / 340
    current_aspect = w / h
    if current_aspect > target_aspect:
        # crop width
        new_w = int(h * target_aspect)
        left = (w - new_w) // 2
        src = src.crop((left, 0, left + new_w, h))
    else:
        # crop height
        new_h = int(w / target_aspect)
        top = (h - new_h) // 2
        src = src.crop((0, top, w, top + new_h))

    # create white bg for dark mode segmentation / light mode
    bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(bg, src).convert("L")
    
    # Contrast & Crop & Resize
    comp = comp.resize((150, 170), Image.LANCZOS) # using 150x170 to keep file size reasonable for now
    from PIL import ImageOps
    comp = ImageOps.autocontrast(comp, cutoff=1)
    
    enhancer = ImageEnhance.Contrast(comp)
    comp = enhancer.enhance(1.3)
    comp = comp.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    
    dithered = floyd_steinberg_dither(comp)
    
    # For dark mode, dots should draw the subject (white parts of dither against dark bg)
    # For light mode, dots should draw the shadow (black parts of dither against light bg)
    if theme == "dark":
        y_idx, x_idx = np.where(~dithered) # In source-prepped, background is white, so ~dithered (black) is the subject
    else:
        y_idx, x_idx = np.where(~dithered)

    pts = np.column_stack((x_idx, y_idx))
    # scale points to fit visual map panel
    # We resized to 150x170. We want it to fill 300x340 space. Scale by 2.
    pts = pts * 2
    pts[:, 0] = pts[:, 0] + 90
    pts[:, 1] = pts[:, 1] + 130
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_SVG} {H_SVG}" width="{W_SVG}" height="{H_SVG}">')
    svg.append(f'<rect width="100%" height="100%" fill="{pal["bg"]}" rx="12"/>')
    
    # Layout shapes
    svg.append(f'<rect x="40" y="40" width="400" height="530" fill="{pal["bg"]}" stroke="{pal["chrome"]}" stroke-width="2" rx="8"/>')
    svg.append(f'<text x="50" y="30" fill="{pal["chrome"]}" font-family="monospace">VISUAL.MAP</text>')
    
    svg.append(f'<rect x="480" y="40" width="660" height="530" fill="none" stroke="{pal["chrome"]}" stroke-width="2" rx="8"/>')
    svg.append(f'<text x="490" y="30" fill="{pal["chrome"]}" font-family="monospace">SYSTEM.INFO</text>')
    
    # Text info
    y_text = 80
    def add_row(label, val):
        nonlocal y_text
        svg.append(f'<text x="500" y="{y_text}" fill="{pal["chrome"]}" font-family="monospace" font-size="16">{label}</text>')
        # add dotted leader
        dots = "." * max(1, 40 - len(label) - len(val))
        svg.append(f'<text x="{520 + len(label)*10}" y="{y_text}" fill="{pal["chrome"]}" opacity="0.3" font-family="monospace" font-size="16">{dots}</text>')
        svg.append(f'<text x="1100" y="{y_text}" fill="{pal["chrome"]}" font-family="monospace" font-size="16" text-anchor="end">{val}</text>')
        y_text += 42
        
    add_row("Subject", USERNAME)
    add_row("Role", ROLE)
    add_row("Origin", ORIGIN)
    add_row("Status", STATUS)
    add_row("Toolchain", TOOLCHAIN)
    add_row("Languages", LANGUAGES)
    add_row("Focus", FOCUS)
    add_row("OS", OS_NAME)
    add_row("Shell", SHELL)
    
    # Draw paths
    paths = []
    # Removed the downsampling!
    for x, y in pts:
        paths.append(f"M{x},{y}h2v2h-2Z")
        
    svg.append(f'<path d="{"".join(paths)}" fill="{pal["portrait"]}" shape-rendering="crispEdges"/>')
    svg.append('</svg>')
    
    with open(f"{theme}.svg", "w") as f:
        f.write("\n".join(svg))
        
build_svg("dark")
build_svg("light")
print("Done")
