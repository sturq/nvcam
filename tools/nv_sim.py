#!/usr/bin/env python3
"""
numpy mirror of app/src/main/assets/shaders/nv.frag, so the look can be tuned on a
JPEG without rebuilding the APK.

Usage:
    python tools/nv_sim.py input.jpg output.jpg
"""
import sys

import numpy as np
from PIL import Image

# ---------- shader constants (kept in sync with nv.frag) ----------
BARREL = 0.05
SOFT = 0.0018
GAIN = 1.10
GAMMA = 1.10
BLACK_LIFT = 0.03
HALO_THRESHOLD = 0.75
HALO_RADIUS = 0.02
HALO_STRENGTH = 0.45
GRAIN_AMP = 0.06
VIGNETTE_STRENGTH = 0.45
SHADOW_TINT = np.array([1.10, 0.90, 1.12], dtype=np.float32)
HIGHLIGHT_TINT = np.array([0.94, 1.03, 0.98], dtype=np.float32)
WHITE_ROLLOFF = 0.5

LUMA_W = np.array([0.299, 0.587, 0.114], dtype=np.float32)


def sample(L, u, v):
    """Bilinear clamp-to-edge lookup like texture2D, texel centers at (i + 0.5) / n."""
    h, w = L.shape
    x = np.clip(u * w - 0.5, 0, w - 1)
    y = np.clip(v * h - 0.5, 0, h - 1)
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    fx = x - x0
    fy = y - y0
    top = L[y0, x0] * (1 - fx) + L[y0, x1] * fx
    bot = L[y1, x0] * (1 - fx) + L[y1, x1] * fx
    return top * (1 - fy) + bot * fy


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def process(img: np.ndarray, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h, w = img.shape[:2]
    L = (img.astype(np.float32) / 255.0) @ LUMA_W
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    u, v = xx / w, yy / h
    ex, ey = 1.0 / w, 1.0 / h  # one screen pixel; sim has no rotation
    short = min(w, h)

    sx, sy = (xx - 0.5 * w) / h, (yy - 0.5 * h) / h
    rc2 = 0.25 * (w / h) ** 2 + 0.25
    k = (1 + BARREL * (sx * sx + sy * sy)) / (1 + BARREL * rc2)
    u, v = 0.5 + (u - 0.5) * k, 0.5 + (v - 0.5) * k

    a, b = ex * SOFT * short, ey * SOFT * short
    l = (4 * sample(L, u, v)
         + 2 * (sample(L, u + a, v) + sample(L, u - a, v) + sample(L, u, v + b) + sample(L, u, v - b))
         + sample(L, u + a, v + b) + sample(L, u + a, v - b)
         + sample(L, u - a, v + b) + sample(L, u - a, v - b)) / 16

    hr = HALO_RADIUS * short
    halo = np.zeros_like(l)
    for i in range(8):
        ang = i * 0.785398
        du, dv = ex * np.cos(ang) * hr, ey * np.sin(ang) * hr
        halo += 0.5 * smoothstep(HALO_THRESHOLD, 1.0, sample(L, u + du, v + dv))
        halo += smoothstep(HALO_THRESHOLD, 1.0, sample(L, u + du * 0.5, v + dv * 0.5))
    l = l + halo / 12.0 * HALO_STRENGTH

    l = np.clip(l * GAIN, 0.0, 1.0) ** GAMMA
    # ponytail: rng instead of the shader hash, same 2x2 cells and amplitude, not the same pixels
    cells = rng.random(((h + 1) // 2, (w + 1) // 2), dtype=np.float32)
    grain = np.repeat(np.repeat(cells, 2, 0), 2, 1)[:h, :w]
    l = l + (grain - 0.5) * GRAIN_AMP * (1.0 - 0.5 * l)
    l = np.clip(BLACK_LIFT + (1.0 - BLACK_LIFT) * l, 0.0, 1.0)[..., None]

    t = smoothstep(0.05, 0.35, l)
    col = l * (SHADOW_TINT * (1 - t) + HIGHLIGHT_TINT * t)
    r = smoothstep(0.85, 1.0, l) * WHITE_ROLLOFF
    col = col * (1 - r) + r

    qx, qy = xx / w - 0.5, yy / h - 0.5
    col = col * (1.0 - (qx * qx + qy * qy) * VIGNETTE_STRENGTH)[..., None]
    return (np.clip(col, 0.0, 1.0) * 255).astype(np.uint8)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    out = process(np.asarray(Image.open(src).convert("RGB")), seed=42)
    Image.fromarray(out).save(dst, quality=92)
    print(f"wrote {dst}")
