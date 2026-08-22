"""Build an object-free FLOOR mask for room 17 by probing, then meter over it.

Hand-drawn floor boxes kept swallowing the runner's selvedge and the knee
wall's skirting -- and the runner is another builder's piece, so it moves under
me between rounds and a box that was clean last round is not clean this one.

Same trick probe.py uses for the walls: render the pose twice with ONLY the
room's `floor_color` changed, and keep the pixels that moved.  Those pixels are
the floor -- the slab and the glossy wear layer over it -- and nothing else,
because nothing else in the room reads that column.  The mask is cached, so the
probe runs once and every later measurement is a single render.

    python fprobe.py --remask      # re-probe (2 extra renders), then meter
    python fprobe.py               # meter the current room over the cached mask
"""
import json
import os
import subprocess
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PY = os.path.join(ROOT, "backend", ".venv", "Scripts", "python.exe")
OUT = os.path.join(HERE, "probe")
LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
BASE = "http://127.0.0.1:5000"
BY = 18.0

POSES = {
    "v2_north": {"pos": [12.45, BY + 5.35, 21.60], "target": [13.30, BY + 4.30, 6.90],
                 "fov": 74, "size": [900, 1200]},
    "v2_south": {"pos": [12.45, BY + 5.35, 8.10], "target": [12.60, BY + 4.10, 23.00],
                 "fov": 74, "size": [900, 1200]},
}


def surfaces(**kw):
    req = urllib.request.Request(f"{BASE}/api/house/room/17",
                                 data=json.dumps(kw).encode(), method="PATCH")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


def shoot(pose, tag):
    dst = os.path.join(OUT, f"{tag}{pose}.png")
    r = subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                        json.dumps(POSES[pose]), "--level", "2", "--day",
                        "--no-cutaway", "--out", dst],
                       cwd=os.path.join(ROOT, "tools"),
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-800:] + r.stderr[-800:])
    return np.asarray(Image.open(dst).convert("RGB")).astype(np.float32)


def remask(keep):
    """`keep` is the floor_color to leave the room in when the probe is done."""
    try:
        surfaces(floor_color="#c8c8c8")
        light = {p: shoot(p, "fp_light_") for p in POSES}
        surfaces(floor_color="#3c3c3c")
        dark = {p: shoot(p, "fp_dark_") for p in POSES}
    finally:
        surfaces(floor_color=keep)
    for p in POSES:
        d = np.abs(light[p] @ LUM - dark[p] @ LUM)
        mask = d > 10.0
        # a one-pixel erode drops the antialiased fringe where the floor meets
        # the runner or the skirting -- those pixels are half floor, half not,
        # and they are what inflates a floor's |d1| into looking like grain
        m = mask.copy()
        m[1:] &= mask[:-1]
        m[:-1] &= mask[1:]
        m[:, 1:] &= mask[:, :-1]
        m[:, :-1] &= mask[:, 1:]
        Image.fromarray((m * 255).astype(np.uint8)).save(
            os.path.join(OUT, f"maskfloor_{p}.png"))
        print(f"  {p}: {int(m.sum())} floor px")


def masked(lum, mask):
    v = lum[mask]
    dh = np.abs(lum[:, 1:] - lum[:, :-1])[mask[:, 1:] & mask[:, :-1]]
    dv = np.abs(lum[1:] - lum[:-1])[mask[1:] & mask[:-1]]
    d1 = 0.5 * (dh.mean() + dv.mean())
    return int(mask.sum()), float(v.mean()), float(v.std()), float(d1)


def meter(tag="fm_"):
    print(f"{'pose':<10}{'n':>9}{'mean':>8}{'sd':>8}{'|d1|':>8}{'|d1|/sd':>9}")
    for p in POSES:
        mask = np.asarray(Image.open(
            os.path.join(OUT, f"maskfloor_{p}.png")).convert("L")) > 127
        lum = shoot(p, tag) @ LUM
        n, mu, sd, d1 = masked(lum, mask)
        print(f"{p:<10}{n:>9}{mu:>8.1f}{sd:>8.2f}{d1:>8.2f}"
              f"{(d1 / sd if sd else 0):>9.3f}")


if __name__ == "__main__":
    if "--remask" in sys.argv:
        i = sys.argv.index("--remask")
        keep = sys.argv[i + 1] if len(sys.argv) > i + 1 else "#504f4b"
        remask(keep)
    meter()
