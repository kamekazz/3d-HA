"""Two-point probe of every wall's response, then solve the four skin albedos.

ROOM-BRIEF: "Fit each from a probe, never by eye."  The round-1 fit recorded in
rooms/7.json is void -- its "bare north wall = 233" was really the Pantry /
Laundry / printer-room walls protruding 0.35 ft into this room, not room 7's
own north face (see gk.NF).  So all four walls are re-fitted here against the
FURRED geometry, with the room still empty enough to meter clean fields.

    python probe_walls.py render A     # all skins at grey A
    python probe_walls.py render B     # all skins at grey B
    python probe_walls.py fit          # meter both, solve, print the albedos
"""
import json
import os
import subprocess
import sys

import g8_surface as S
import gk as G
from m import stats
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PY = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\.venv\Scripts\python.exe"
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"

GREYS = {"A": "#808080", "B": "#dcdcdc"}
POSES = {
    "n": {"pos": [29.1, 13.6, 26.0], "target": [29.1, 12.6, 13.0]},
    "s": {"pos": [29.1, 13.6, 21.0], "target": [29.1, 12.6, 34.7]},
    "e": {"pos": [26.0, 13.6, 23.85], "target": [39.3, 12.6, 23.85]},
    "w": {"pos": [32.0, 13.6, 23.85], "target": [18.9, 12.6, 23.85]},
}
SIZE = [900, 700]
FOV = 62

# clean wall fields, chosen off the pass-A renders (see boxes_*.png)
BOXES = {
    # clean wall fields in the FURNISHED room, picked off vsheet.png by hand.
    # roomkit.meter's centre patch lands on furniture in a furnished room and
    # the empty-room boxes above stopped being wall the moment the banner, the
    # cabinets and the pegboard went in -- that is exactly the mis-metering
    # ROOM-BRIEF describes, so these are re-picked and shown in boxesV_*.png.
    "n": [(330, 158, 800, 205), (806, 215, 856, 470)],
    "s": [(5, 230, 52, 520)],
    "w": [(10, 190, 175, 330), (660, 230, 870, 500)],
    "e": [(150, 420, 330, 540)],
}


def apply(hexcolor):
    orig = S.skin_hex
    S.skin_hex = lambda w, boost=1.0: hexcolor
    G.save_and_place("Garage Wall Wash", S.skins())
    S.skin_hex = orig


def render(tag):
    apply(GREYS[tag])
    for w, p in POSES.items():
        pose = dict(p, fov=FOV, size=SIZE)
        out = os.path.join(HERE, "probe_%s_%s.png" % (tag, w))
        subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(pose),
                        "--level", "1", "--day", "--no-cutaway", "--out", out],
                       cwd=TOOLS, check=True, capture_output=True)
        print("  ", out)


def s2l(u):
    u = u / 255.0
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4


def l2s(v):
    v = max(0.0, min(1.0, v))
    u = v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return int(round(u * 255))


def field(tag, w):
    im = Image.open(os.path.join(HERE, "probe_%s_%s.png" % (tag, w)))
    vals, n = [], 0
    for b in BOXES[w]:
        st = stats(im, b)
        vals.append((st["mean"], st["sd"], st["d1"], st["n"]))
        n += st["n"]
    mean = sum(v[0] * v[3] for v in vals) / n
    return mean, vals


def boxes_overlay(tag):
    for w in POSES:
        p = os.path.join(HERE, "probe_%s_%s.png" % (tag, w))
        im = Image.open(p).convert("RGB")
        dr = ImageDraw.Draw(im)
        for b in BOXES[w]:
            dr.rectangle(b, outline=(255, 0, 255), width=3)
        im.save(os.path.join(HERE, "boxes%s_%s.png" % (tag, w)))


TARGET_SRGB = 173.0            # photo clean walls: north 166.9, east 178.1


def fit():
    la, lb = s2l(int(GREYS["A"][1:3], 16)), s2l(int(GREYS["B"][1:3], 16))
    out = {}
    for w in "nswe":
        ma, va = field("A", w)
        mb, vb = field("B", w)
        ya, yb = s2l(ma), s2l(mb)
        k = (yb - ya) / (lb - la)
        c = ya - k * la
        want = s2l(TARGET_SRGB)
        alb = (want - c) / k if k > 1e-6 else 1.0
        alb = max(0.0, min(1.0, alb))
        hx = "#%02x%02x%02x" % ((l2s(alb),) * 3)
        out[w] = hx
        print("  %s  A %6.1f  B %6.1f   k %6.3f  c %+7.4f  -> albedo %s "
              "(predicted %s%s)"
              % (w, ma, mb, k, c, hx,
                 l2s(k * s2l(int(hx[1:3], 16)) + c),
                 "  CLAMPED" if alb in (0.0, 1.0) else ""))
        for tag, vs in (("A", va), ("B", vb)):
            for (mn, sd, d1, n) in vs:
                print("        %s mean %6.1f sd %5.2f d1 %5.2f n %d"
                      % (tag, mn, sd, d1, n))
    print(json.dumps(out))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "render":
        render(sys.argv[2])
    elif sys.argv[1] == "boxes":
        boxes_overlay(sys.argv[2])
    else:
        fit()


def verify(tag="V"):
    """Render the four look poses AS BUILT -- no skin override."""
    for w, p in POSES.items():
        pose = dict(p, fov=FOV, size=SIZE)
        out = os.path.join(HERE, "probe_%s_%s.png" % (tag, w))
        subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(pose),
                        "--level", "1", "--day", "--no-cutaway", "--out", out],
                       cwd=TOOLS, check=True, capture_output=True)
        print("  ", out)


def report(tag="V"):
    print("  wall  mean    sd    |d1|  |d1|/sd     n")
    ms = {}
    for w in "nswe":
        mean, vs = field(tag, w)
        n = sum(v[3] for v in vs)
        sd = sum(v[1] * v[3] for v in vs) / n
        d1 = sum(v[2] * v[3] for v in vs) / n
        ms[w] = mean
        print("   %s   %6.1f %6.2f %6.2f  %6.3f  %6d"
              % (w, mean, sd, d1, d1 / sd if sd else 0, n))
    print("  spread %.1f  (max %s %.1f, min %s %.1f)"
          % (max(ms.values()) - min(ms.values()),
             max(ms, key=ms.get), max(ms.values()),
             min(ms, key=ms.get), min(ms.values())))
