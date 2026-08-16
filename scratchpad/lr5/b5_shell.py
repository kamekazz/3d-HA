"""Round 5 shell -- PER-WALL ALBEDO SKINS.

Round 4 aimed one `wall_color` at the four-wall AVERAGE and shipped a spread of
114.4 (N 219.0 / W 170.3 / E 133.6 / S 104.6) against photo f's four clean wall
patches at 157.1 / 159.6 / 176.7 / 147.6 -- a spread of 29.  ROOM-BRIEF says
that residual spread is the renderer's one-sun-no-bounce limit only while the
room has ONE albedo, and that per-wall non-emissive skins close it: office
85.5 -> 22.9, garage 91.5 -> 12.3, laundry 89.6 -> 18.2.  This is that lever.

The skins are plain painted surfaces: no emissive (the rejected "wall wash"
glowed at night and read as light), corner to corner (the rejected one showed
hard rectangular edges), roughness 0.95 to match the room wall's, and gapped
exactly at the real openings so no skin crosses a hole.

Usage:
    python b5_shell.py probe <hexA> <hexB>   # two-point fit, prints the solve
    python b5_shell.py <hexN> <hexW> <hexE> <hexS>
    python b5_shell.py                        # ship the solved set
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

from kit5 import *

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY = sys.executable

WALL = "#c0bfbb"          # the room wall itself; the skins are what is seen
FLOOR = "#4c4e53"

# skin runs from the top of the 5.6 in skirting to under the crown
Y0, Y1 = 0.50, 8.40

# (edge, [(y0, y1, [(t0, t1), ...]) ...]) -- gaps are the REAL openings, given
# in each edge's own offset parameter, padded 0.10 ft so no skin laps a jamb.
BANDS = {
    S: [(Y0, 3.45, [(2.39, 6.59)]),
        (3.45, 7.00, [(2.39, 6.59), (11.39, 20.09)]),
        (7.00, 7.50, [(11.39, 20.09)]),
        (7.50, Y1, [])],
    W: [(Y0, 2.35, []), (2.35, 6.90, [(1.96, 5.16)]), (6.90, Y1, [])],
    N: [(Y0, 6.90, [(7.03, 14.08)]), (6.90, Y1, [])],
    E: [(Y0, 2.35, []), (2.35, 6.90, [(0.94, 4.12)]), (6.90, Y1, [])],
}
EDGE_OF = {"n": N, "w": W, "e": E, "s": S}

# clean bare-wall boxes, each checked against an m5 _boxes.png overlay
BOX = {"look_n": (690, 125, 1080, 200),
       "look_w": (390, 195, 700, 330),
       "look_e": (700, 200, 1000, 480),
       "look_s": (340, 150, 430, 500)}

POSES = json.loads(subprocess.check_output(
    [PY, "-m", "roomkit.rooms", "5", "--poses-only"], cwd=TOOLS))


def build(colors):
    m = Model()
    for w, edge in EDGE_OF.items():
        for (y0, y1, gaps) in BANDS[edge]:
            wall_skin(m, edge, colors[w], y0, y1, gaps)
    return m


def ship(colors):
    req("PATCH", "/api/house/room/5",
        {"wall_color": WALL, "floor_color": FLOOR,
         "wall_texture": "plaster", "floor_texture": "wood"})
    m = build(colors)
    put_in_place("Living Wall Wash", m, save5(m, "skins5"))
    print("  skins " + " ".join("%s=%s" % kv for kv in sorted(colors.items())))


def meter(tag):
    out = {}
    for name, b in BOX.items():
        png = os.path.join(OUT, "sk_%s_%s.png" % (tag, name))
        subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                        json.dumps(POSES[name]), "--level", "1", "--day",
                        "--out", png], cwd=TOOLS, check=True,
                       stdout=subprocess.DEVNULL)
        a = np.asarray(Image.open(png).convert("RGB")).astype(np.float32)
        p = a[b[1]:b[3], b[0]:b[2]] @ np.array([0.2126, 0.7152, 0.0722],
                                               dtype=np.float32)
        out[name[-1]] = float(p.mean())
    print("  %-8s N=%.1f W=%.1f E=%.1f S=%.1f  spread=%.1f" %
          (tag, out["n"], out["w"], out["e"], out["s"],
           max(out.values()) - min(out.values())))
    return out


def val(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


TARGET = {"n": 160.0, "w": 160.0, "e": 168.0, "s": 156.0}   # photo f's own walls

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "probe":
        c1, c2 = a[1], a[2]
        ship({w: c1 for w in "nwes"})
        v1 = meter("p1")
        ship({w: c2 for w in "nwes"})
        v2 = meter("p2")
        x1, x2 = val(c1), val(c2)
        sol = {}
        for w in "nwes":
            slope = (v2[w] - v1[w]) / (x2 - x1)
            want = x1 + (TARGET[w] - v1[w]) / slope
            want = max(8.0, min(252.0, want))
            k = int(round(want))
            sol[w] = "#%02x%02x%02x" % (k, k, k)
            print("    %s slope=%.3f  ->  %.1f  %s" % (w, slope, want, sol[w]))
        print("  SOLVED", json.dumps(sol))
    elif len(a) == 4:
        ship(dict(zip("nwes", a)))
        meter("t")
    else:
        ship(json.load(open(os.path.join(OUT, "skins5.json"))))
