"""Honest metering helper for room 17.

Reports, for every named patch: n, mean luminance, sd, mean|d1| (mean abs
difference between horizontally adjacent pixels, averaged with the vertical
one), and the ratio |d1|/sd.  ALWAYS at native resolution -- no resizing.

    python m.py photo            # the 1200x1600 reference patches
    python m.py <png> <patchset> # a render
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.float32)


def stats(a, box):
    x0, y0, x1, y1 = box
    p = a[y0:y1, x0:x1]
    lum = p @ LUM
    dh = np.abs(np.diff(lum, axis=1)).mean() if lum.shape[1] > 1 else 0.0
    dv = np.abs(np.diff(lum, axis=0)).mean() if lum.shape[0] > 1 else 0.0
    d1 = 0.5 * (dh + dv)
    sd = float(lum.std())
    return dict(n=lum.size, mean=round(float(lum.mean()), 1), sd=round(sd, 2),
                d1=round(float(d1), 2), ratio=round(float(d1) / sd, 3) if sd > 1e-6 else 0.0,
                rgb=[round(float(p[..., i].mean()), 1) for i in range(3)])


def report(path, patches, title=""):
    a = load(path)
    print(f"\n== {title or os.path.basename(path)}  ({a.shape[1]}x{a.shape[0]}) ==")
    print(f"{'patch':<22}{'n':>7}{'mean':>8}{'sd':>8}{'|d1|':>8}{'|d1|/sd':>9}   rgb")
    for name, box in patches.items():
        s = stats(a, box)
        print(f"{name:<22}{s['n']:>7}{s['mean']:>8.1f}{s['sd']:>8.2f}"
              f"{s['d1']:>8.2f}{s['ratio']:>9.3f}   {s['rgb']}")
    return a


# ---------------------------------------------------------------- the photo
PHOTO = os.path.join(ROOT, "docs", "photos-jpg", "Second-floor hallway.jpg")

PHOTO_PATCHES = {
    # x0, y0, x1, y1   (1200 x 1600)
    "runner near":      (455, 1080, 745, 1290),
    "runner mid":       (487,  900, 700, 1050),
    "runner far":       (520,  810, 655,  880),
    "wall WEST hi":     (352,  330,  432,  560),
    "wall WEST lo":     (356,  660,  440,  940),
    "wall EAST":        (940,  480, 1150,  900),
    "wall NORTH":       (560,  520,  620,  740),
    "ceiling":          (700,  120,  900,  250),
    "floor planks":     (250, 1180,  420, 1420),
    "kneewall face":    (900, 1000, 1080, 1250),
}


def crops(a, patches, outdir, scale=3):
    os.makedirs(outdir, exist_ok=True)
    for name, (x0, y0, x1, y1) in patches.items():
        im = Image.fromarray(a[y0:y1, x0:x1].astype(np.uint8))
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        im.save(os.path.join(outdir, name.replace(" ", "_") + ".png"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "photo":
        a = report(PHOTO, PHOTO_PATCHES, "PHOTO Second-floor hallway.jpg")
        if "--crops" in sys.argv:
            crops(a, PHOTO_PATCHES, os.path.join(HERE, "crops"))
    else:
        import json
        path = sys.argv[1]
        patches = json.loads(sys.argv[2])
        report(path, {k: tuple(v) for k, v in patches.items()})
