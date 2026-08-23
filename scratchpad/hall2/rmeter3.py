"""Meter a render's floor against the matching photograph, at PHOTO scale.

Renders are 900x1200; the photographs are 450x600.  |d1| is scale-dependent, so
every render is BOX-downsampled 2x before it is metered -- measuring the native
render against a 450x600 photo inflates nothing but flatters the photo.
"""
import os, sys
import numpy as np
from PIL import Image

SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
PH = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"

def L(a):
    return 0.2126*a[...,0] + 0.7152*a[...,1] + 0.0722*a[...,2]

def load(p, half):
    im = Image.open(p).convert("RGB")
    if half:
        im = im.resize((im.width//2, im.height//2), Image.BOX)
    return im

def stats(im, box, name):
    a = np.asarray(im.crop(box), dtype=np.float64)
    l = L(a)
    print(f"    {name:18s} mean {l.mean():6.1f}  sd {l.std():5.2f}"
          f"  |d1|h {np.abs(np.diff(l,axis=1)).mean():5.2f}"
          f"  |d1|v {np.abs(np.diff(l,axis=0)).mean():5.2f}"
          f"  rgb {a[...,0].mean():5.1f},{a[...,1].mean():5.1f},{a[...,2].mean():5.1f}")
    return l.mean()

# (pose, photo, [(label, render box, photo box)])  -- boxes at 450x600
SETS = {
    "p_stairs": ("hallway_looking_towards_stairs.jpg", [
        ("floor L strip",  (149, 445, 176, 535), (25, 470, 140, 575)),
        ("floor R strip",  (263, 420, 300, 472), (255, 420, 300, 480)),
        ("floor far",      (200, 398, 262, 424), (200, 305, 250, 332)),
        ("wall right",     (352, 220, 420, 330), (350, 200, 430, 320)),
    ]),
    "p_runner": ("hallway_with_white_runner_rug.jpg", [
        ("floor L strip",  (157, 445, 180, 555), (20, 480, 130, 580)),
        ("floor R strip",  (288, 435, 318, 515), (330, 480, 420, 570)),
        ("floor far",      (205, 400, 255, 420), (200, 300, 260, 330)),
        ("wall right",     (330, 200, 370, 320), (350, 180, 430, 300)),
    ]),
    "p_doors2": ("two_closed_white_doors_2.jpg", [
        ("floor near",     (215, 520, 350, 595), (150, 470, 280, 570)),
        ("floor mid",      (225, 492, 330, 518), (120, 400, 250, 460)),
        ("wall right",     (428, 150, 448, 330), (380, 200, 440, 320)),
    ]),
}

if __name__ == "__main__":
    tag = sys.argv[1]
    for pose, (photo, boxes) in SETS.items():
        p = os.path.join(SH, f"{tag}{pose}.png")
        if not os.path.exists(p):
            continue
        r = load(p, True)
        q = load(os.path.join(PH, photo), False)
        print(f"{pose}   render={tag}{pose}.png")
        for name, rb, pb in boxes:
            stats(r, rb, "R " + name)
            stats(q, pb, "P " + name)
        print()
