"""Meter every wall of room 17 over its OWN probe mask.

The mask comes from probe.py: pixels that moved when only that wall's skin
changed colour.  So it is that wall's paint and nothing else -- a sculpture, a
plant, a door casing or the knee wall standing in front of it never moved, so
it is excluded automatically.  No hand-drawn sample box, and every wall is
reported, not the flattering one.

sd and mean|d1| are computed at NATIVE resolution; |d1| only between pairs of
adjacent pixels that are BOTH inside the mask.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PY = os.path.join(ROOT, "backend", ".venv", "Scripts", "python.exe")
OUT = os.path.join(HERE, "probe")
LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

from probe import POSES, POSE                                  # noqa: E402


def shoot(name, tag="wm_"):
    dst = os.path.join(OUT, f"{tag}{name}.png")
    r = subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                        json.dumps(POSES[name]), "--level", "2", "--day",
                        "--no-cutaway", "--out", dst],
                       cwd=os.path.join(ROOT, "tools"),
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-800:] + r.stderr[-800:])
    return np.asarray(Image.open(dst).convert("RGB")).astype(np.float32)


def masked(lum, mask):
    v = lum[mask]
    dh = np.abs(lum[:, 1:] - lum[:, :-1])[mask[:, 1:] & mask[:, :-1]]
    dv = np.abs(lum[1:] - lum[:-1])[mask[1:] & mask[:-1]]
    d1 = 0.5 * (dh.mean() + dv.mean())
    sd = float(v.std())
    return dict(n=int(mask.sum()), mean=float(v.mean()), sd=sd, d1=float(d1),
                ratio=float(d1) / sd if sd > 1e-6 else 0.0)


def main():
    imgs = {p: shoot(p) for p in sorted(set(POSE.values()))}
    print(f"{'wall':<6}{'pose':<10}{'n':>9}{'mean':>8}{'sd':>8}{'|d1|':>8}{'|d1|/sd':>9}")
    for wall in "nwes":
        mp = os.path.join(OUT, f"mask_{wall}.png")
        if not os.path.exists(mp):
            print(f"{wall:<6} no mask")
            continue
        mask = np.asarray(Image.open(mp).convert("L")) > 127
        lum = imgs[POSE[wall]] @ LUM
        s = masked(lum, mask)
        print(f"{wall:<6}{POSE[wall]:<10}{s['n']:>9}{s['mean']:>8.1f}"
              f"{s['sd']:>8.2f}{s['d1']:>8.2f}{s['ratio']:>9.3f}")


if __name__ == "__main__":
    main()
