"""
Invariants of the NVCam look. Run: python tools/test_nv_sim.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from nv_sim import process  # noqa: E402


def patch(img, seed=0):
    return process(img, seed=seed).astype(float)[50:70, 70:90].reshape(-1, 3).mean(0)


def flat(v):
    return np.full((120, 160, 3), v, np.uint8)


def dark_with_spot(h=240, w=320, r=6):
    img = np.full((h, w, 3), 8, dtype=np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    img[(xx - w // 2) ** 2 + (yy - h // 2) ** 2 <= r * r] = 255
    return img


def test_mint_highlights():
    r, g, b = patch(flat(210))
    assert g > b > r, f"highlights not mint: {(r, g, b)}"


def test_barely_saturated():
    c = patch(flat(128))
    assert c.max() - c.min() < 16, f"mids too colorful: {c}"


def test_blacks_stay_dark():
    c = patch(flat(0))
    assert c.max() < 22, f"blacks lifted too far: {c}"
    assert c[1] <= c[0] + 2, f"blacks should not turn green: {c}"


def test_halo_around_light():
    out = process(dark_with_spot(), seed=0).astype(float)[..., 1]
    ring = out[116:125, 168:171].mean()  # just outside the r=6 spot, averaged over the grain
    far = out[116:125, 215:225].mean()
    assert ring > far + 10, f"no halo: ring {ring} vs far {far}"


def test_deterministic():
    img = dark_with_spot()
    assert np.array_equal(process(img, seed=3), process(img, seed=3))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
