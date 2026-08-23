"""Meter the photographs' floor: value vs wall, spread, fine gradient, plank pitch."""
import sys, os, numpy as np
from PIL import Image

PH = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"

def L(a):
    return 0.2126*a[...,0] + 0.7152*a[...,1] + 0.0722*a[...,2]

def stats(im, box, name):
    x0,y0,x1,y1 = box
    a = np.asarray(im.crop(box), dtype=np.float64)
    l = L(a)
    d1 = np.abs(np.diff(l, axis=1)).mean()
    d1v = np.abs(np.diff(l, axis=0)).mean()
    rgb = a.reshape(-1,3).mean(0)
    print(f"  {name:22s} {x1-x0:3d}x{y1-y0:3d}  mean {l.mean():6.1f}  sd {l.std():5.2f}"
          f"  |d1|h {d1:5.2f} |d1|v {d1v:5.2f}  ratio {d1/max(l.std(),1e-6):5.3f}"
          f"  rgb {rgb[0]:5.1f},{rgb[1]:5.1f},{rgb[2]:5.1f}")
    return l.mean(), l.std(), d1

def scan(im, y, x0, x1, name):
    a = np.asarray(im.crop((x0, y-2, x1, y+3)), dtype=np.float64)
    l = L(a).mean(0)
    print(f"  scanline {name} y={y}: " + " ".join(f"{v:.0f}" for v in l))

if __name__ == "__main__":
    for fn, boxes in [
        ("hallway_with_white_runner_rug.jpg", [
            ("floor near-left",  (20, 480, 130, 580)),
            ("floor mid-left",   (60, 380, 150, 450)),
            ("floor right-far",  (280, 330, 340, 380)),
            ("floor near-right", (330, 480, 420, 570)),
            ("wall right",       (350, 180, 430, 300)),
            ("wall left",        (30, 150, 90, 260)),
            ("ceiling",          (150, 20, 260, 60)),
        ]),
        ("hallway_looking_towards_stairs.jpg", [
            ("floor near-left",  (30, 480, 150, 580)),
            ("floor mid",        (120, 400, 180, 460)),
            ("floor far",        (200, 320, 250, 350)),
            ("wall right",       (350, 200, 430, 320)),
            ("wall left-far",    (150, 180, 200, 260)),
            ("ceiling",          (200, 30, 300, 70)),
        ]),
        ("two_closed_white_doors_2.jpg", [
            ("floor near",       (150, 470, 280, 570)),
            ("floor mid",        (120, 400, 250, 460)),
            ("floor far",        (150, 350, 260, 390)),
            ("wall right",       (380, 200, 440, 320)),
            ("door leaf",        (120, 120, 200, 220)),
        ]),
        ("two_closed_white_doors_1.jpg", [
            ("floor near",       (120, 470, 300, 580)),
            ("floor mid",        (150, 380, 300, 450)),
            ("wall",             (380, 150, 440, 300)),
        ]),
    ]:
        im = Image.open(os.path.join(PH, fn)).convert("RGB")
        print(fn)
        for n, b in boxes:
            stats(im, b, n)
        print()
