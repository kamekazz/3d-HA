"""Meter clean object-free patches out of the 1200x1600 hallway photo.

Boxes are (x0, y0, x1, y1) in native pixels.  Every box is also drawn onto
`probe/photo_boxes.png` so the sample regions can be EYEBALLED before their
numbers are trusted -- the ROOM-BRIEF's #1 metering failure is a sample that
quietly swallowed an object.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PHOTO = os.path.join(ROOT, "docs", "photos-jpg", "Second-floor hallway.jpg")
LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

# clean patches, verified against probe/photo_boxes.png
BOXES = {
    "floor near  (bottom strip, both sides)":    (200, 1480, 800, 1590),
    "floor near  (left of runner)":              (300, 1330, 470, 1500),
    "floor mid   (just past the runner end)":    (430, 1320, 780, 1400),
    "floor far   (beyond the runner top)":       (600, 755, 700, 800),
    "wall WEST   (below sculpture)":             (370, 650, 430, 890),
    "wall WEST   (upper, near ceiling)":         (400, 150, 490, 290),
    "wall EAST   (right plane, upper)":          (940, 430, 1160, 620),
    "wall EAST   (right plane, lower)":          (960, 640, 1150, 760),
    "wall NORTH  (far end, right of door)":      (830, 470, 880, 620),
    "ceiling     (between cans)":                (700, 120, 880, 210),
    "ceiling     (near far end)":                (640, 330, 780, 380),
}


def stats(lum):
    dh = np.abs(lum[:, 1:] - lum[:, :-1])
    dv = np.abs(lum[1:] - lum[:-1])
    d1 = 0.5 * (dh.mean() + dv.mean())
    sd = float(lum.std())
    return dict(n=lum.size, mean=float(lum.mean()), sd=sd, d1=float(d1),
                ratio=d1 / sd if sd > 1e-6 else 0.0)


def report(img, boxes, title):
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    print(f"\n{title}   ({a.shape[1]}x{a.shape[0]})")
    print(f"  {'patch':<42}{'n':>8}{'mean':>8}{'sd':>7}{'|d1|':>7}{'|d1|/sd':>9}")
    out = {}
    for k, (x0, y0, x1, y1) in boxes.items():
        s = stats(a[y0:y1, x0:x1] @ LUM)
        out[k] = s
        print(f"  {k:<42}{s['n']:>8}{s['mean']:>8.1f}{s['sd']:>7.2f}"
              f"{s['d1']:>7.2f}{s['ratio']:>9.3f}")
    return out


def main():
    img = Image.open(PHOTO)
    report(img, BOXES, os.path.basename(PHOTO))
    vis = img.convert("RGB").copy()
    d = ImageDraw.Draw(vis)
    for k, b in BOXES.items():
        d.rectangle(b, outline=(255, 0, 0), width=4)
    os.makedirs(os.path.join(HERE, "probe"), exist_ok=True)
    vis.save(os.path.join(HERE, "probe", "photo_boxes.png"))


if __name__ == "__main__":
    main()
