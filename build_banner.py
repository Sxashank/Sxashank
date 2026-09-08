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
from PIL import ImageOps
import sys

def process_portrait(src_path, theme, pal):
    from rembg import remove
    print("Removing background for a clean portrait...")
    src = Image.open(src_path).convert("RGBA")
    
    # 1. Remove background completely to remove static noise
    subject_only = remove(src)

    w, h = subject_only.size
    target_aspect = 300 / 340
    current_aspect = w / h
    
    if current_aspect > target_aspect:
        new_w = int(h * target_aspect)
        left = (w - new_w) // 2
        subject_only = subject_only.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_aspect)
        top = (h - new_h) // 2
        subject_only = subject_only.crop((0, top, w, top + new_h))

    # Resize to higher resolution for clearer image (250x283)
    subject_only = subject_only.resize((250, 283), Image.LANCZOS)
    
    # Isolate the alpha channel so we ONLY draw where the person actually is
    alpha = np.array(subject_only.split()[-1])
    
    # Composite onto white to get correct shading levels
    white_bg = Image.new("RGBA", subject_only.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(white_bg, subject_only).convert("L")
    
    comp = ImageOps.autocontrast(comp, cutoff=1)
    comp = ImageEnhance.Contrast(comp).enhance(1.3)
    comp = comp.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    
    dithered = floyd_steinberg_dither(comp)
    
    svg_paths = []
    # y = rows, x = cols
    arr = dithered
    for y in range(arr.shape[0]):
        for x in range(arr.shape[1]):
            # Only draw a dot if it is inside the alpha mask (the person)
            if alpha[y, x] > 128: 
                # Dark mode: draw the light parts (white dots)
                # Light mode: draw the dark parts (black dots)
                draw_dot = not arr[y, x] if theme == "light" else arr[y, x]
                if draw_dot:
                    # scale points to fit the 300x340 visual map box
                    sx = (x * 1.2) + 60
                    sy = (y * 1.2) + 100
                    # using smaller dots (1.5x1) for higher detail
                    svg_paths.append(f"M{sx:.1f},{sy:.1f}h1v1h-1Z")
    
    return "".join(svg_paths)

def build_svg(theme):
    pal = PALETTE[theme]
    
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
    
    # Map dots
    paths = process_portrait("source-photo.png", theme, pal)
    svg.append(f'<path d="{paths}" fill="{pal["portrait"]}" shape-rendering="crispEdges"/>')
    svg.append('</svg>')
    
    with open(f"{theme}.svg", "w") as f:
        f.write("\n".join(svg))
    
    with open(f"{theme}.svg", "w") as f:
        f.write("\n".join(svg))
        
build_svg("dark")
build_svg("light")
print("Done")
