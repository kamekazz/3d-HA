"""Hall2F Wall Wash Skins -- room 17, round V3 wave A.

BUILT FROM NOTHING.  The old object (282) was deleted because a killed agent
left it holding a near-black panel.  Nothing here patches an existing piece.

WHAT THIS IS
------------
One non-emissive albedo skin per wall face of room 17, sitting a hair proud of
whatever surface the camera actually sees there, carrying a BAKED LIGHTING
FIELD as per-vertex colour (glTF COLOR_0, 4 bytes/vertex) plus a shallow
geometric displacement so the normals are not algebraically flat.

WHY EACH WALL NEEDS ITS OWN, AND WHY THE PLANE IS NOT ON THE FOOTPRINT LINE
--------------------------------------------------------------------------
`house.js buildRoom` lands a wall's INNER face on the footprint line and puts
its mass OUTSIDE.  On a party wall the neighbour does the same from their side,
so the surface you actually see from inside room 17 is the NEIGHBOUR'S wall,
its outer face standing one thickness (0.35 ft) inboard of room 17's own line
-- and painted in the NEIGHBOUR'S wall_color.  Room 17's eight walled edges are
faced by six different rooms in five different colours:

    edge  faced by                    their wall_color   face plane (local)
    8  N  room 14 Master Bed          #bdbdba            z = 0.10
    9  E  rooms 16 / 27               #e4e2dd / #e6e4e0  x = 11.55
    7  W  room 13 Guest               #c3c1bd            x = 4.15
    6  aN room 13 Guest               #c3c1bd            z = 11.10
    5  aW room 25                     #e9e7e2            x = 0.35
    4  aS room 15 Rios                #f4f1ec            z = 15.80
    3  jog room 15 Rios               #f4f1ec            x = 4.15
    2  S  room 26 bath                #e9e7e2            z = 16.50

(local = world minus the room anchor 6.70, 6.55.)  So "every wall is the same
white" was never even true here: the hallway was five different paints plus one
directional sun.  Edges 0 and 1 carry full-span passages -- buildRoom skips
those walls outright -- so they get NO skin: edge 0 is the open stairwell cut
and edge 1 is where the knee wall stands.

THE FIELD
---------
Metered off the photographs (450x600, clean object-free patches, native res):

    surface                          mean    sd    |d1|
    runner R wall, upper band       167.0   4.58   0.35
    runner R wall, lower band       144.9   6.41   0.68
    doors2 R wall above the base    170.2   6.32   0.86
    stairs R wall, upper            158.6  12.64   0.46

    vertical ramps, ceiling -> skirting
    stairs  R wall   171 -> 113     (0.66)
    doors2  R wall   185 -> 150     (0.81)
    runner  R wall   166 -> 136     (0.82)
    stairs  ceiling junction: 164 on the wall, dipping to 101.7 IN the seam

So a photographed painted wall is almost all broad gradient (|d1|/sd = 0.04 to
0.14) with a 30-50 level top-to-bottom ramp and a narrow, very dark seam at the
ceiling.  That is what gets baked: ramp, ceiling seam, corner occlusion, a
floor-bounce lift in the last foot, a pool under each ceiling can, and a small
multi-octave mottle.  Nothing is emissive -- emissive wall washes have been
rejected twice in this repo.

    python walls3.py            # build + place the real piece
    python walls3.py probe      # 2-point per-wall fit, THEN re-place the real
                                # piece in the same run (round-2 rule 1)
"""

import json
import math
import os
import subprocess
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from roomkit.glb import Model, Material, Part                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.abspath(os.path.join(HERE, "..", "..", "backend", ".venv",
                                  "Scripts", "python.exe"))
ROOM = 17
NAME = "Hall2F Wall Wash Skins"
BASE = "http://127.0.0.1:5000"

# ---------------------------------------------------------------- geometry
# Every number here is ROOM-LOCAL feet (world minus the anchor 6.70, 6.55).
# `plane` is the coordinate of the VISIBLE face; `n` is the inward normal along
# that axis; a0..a1 is the run, whose ends are the intersections with the
# neighbouring faces so adjacent skins meet in a clean corner.
Y_CEIL = 7.99            # `Hall2F Ceiling` underside (object 156: y 7.918 + the
                         # 0.072 the surface-mount disc hangs below the plane)
Y_BOT = 0.38             # under the 0.45 ft skirting, so no strip of bare wall
INSET = 0.022            # proud of the face; the skirting stands 0.052 proud,
                         # so the skin still sits BEHIND its back
AMP_D = 0.009            # displacement amplitude, ft

WALLS = [
    # key   axis  plane   n     a0      a1    seed
    ("n",   "z",   0.10,  +1,  4.15,  11.55,  11),
    ("e",   "x",  11.55,  -1,  0.10,   6.81,  23),
    ("w",   "x",   4.15,  +1,  0.10,  11.10,  31),
    ("an",  "z",  11.10,  +1,  0.35,   4.15,  43),
    ("aw",  "x",   0.35,  +1, 11.10,  15.80,  57),
    ("as",  "z",  15.80,  -1,  0.35,   4.15,  67),
    ("jog", "x",   4.15,  +1, 15.80,  16.50,  73),
    ("s",   "z",  16.50,  -1,  4.15,   7.61,  83),
]

# doorway holes, as (a_lo, a_hi, y_hi) on each wall's own run coordinate.
# Read live from /api/house so a re-cut opening cannot go stale mid-build.
EDGE_KEY = {8: "n", 6: "an", 5: "aw", 4: "as", 2: "s"}
HOLE_M = 0.125           # margin round the opening; the casing is 0.19 wide,
                         # so it still covers the strip of neighbour wall this
                         # exposes.  Bigger and the casing stops covering it.

# ceiling fixtures, room-local, tracking `ceiling2.py CANS`
CANS = [(5.80, 7.18, 1.15), (7.75, 7.18, 1.00), (6.10, 4.18, 1.00),
        (8.22, 4.10, 1.00), (10.03, 12.74, 0.72), (1.93, 13.46, 0.72)]

# ------------------------------------------------------------- tone field
# All of these are LINEAR multipliers on baseColor (COLOR_0 is decoded through
# sRGB->linear on export, so the values below are converted on the way out).
RAMP_BOT = 0.500         # linear multiplier at the skirting
RAMP_GAM = 0.78          # shape of the climb to the ceiling
BOUNCE = 0.055           # floor-bounce lift, last ~1 ft
BOUNCE_H = 0.80
# The photo's ceiling junction is not a hairline: on the p_stairs right wall the
# wall meters 164 two inches down and 101.7 IN the seam -- a 0.62 ratio.  That
# needs a deep, narrow multiplier AND rows fine enough to hold it, which is what
# FINE_TOP is for.
SEAM_DK = 0.72           # ceiling-junction seam
SEAM_H = 0.125
CORNER_DK = 0.175        # reentrant vertical corner
CORNER_W = 0.64
POOL = 0.20              # brightening under a ceiling can
MOTTLE = 0.026


def _rnd(i):
    """Deterministic 0..1 hash -- no numpy dependency inside the builder."""
    x = math.sin(i * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


def field(w, a, y):
    """Linear albedo multiplier at run-coordinate `a`, height `y`, on wall `w`."""
    key, axis, plane, n, a0, a1, seed = w
    t = max(0.0, min(1.0, (y - Y_BOT) / (Y_CEIL - Y_BOT)))
    g = RAMP_BOT + (1.0 - RAMP_BOT) * (t ** RAMP_GAM)
    g += BOUNCE * math.exp(-((y - Y_BOT) / BOUNCE_H) ** 1.5)

    for (cx, cz, k) in CANS:
        if axis == "x":
            perp, along = n * (cx - plane), cz
        else:
            perp, along = n * (cz - plane), cx
        if perp < 0.25:
            continue                      # the can is behind this wall
        g += (POOL * k * math.exp(-((a - along) / 2.05) ** 2)
              * math.exp(-(max(0.0, Y_CEIL - y) / 2.70) ** 2)
              / (1.0 + (perp / 2.30) ** 2))

    de = min(a - a0, a1 - a)              # into a vertical corner
    g *= 1.0 - CORNER_DK * math.exp(-(max(0.0, de) / CORNER_W) ** 1.25)
    # the ceiling seam: a narrow, hard-bottomed dark line, the way the photo's is
    g *= 1.0 - SEAM_DK * math.exp(-(max(0.0, Y_CEIL - y) / SEAM_H) ** 1.15)

    ph = seed * 0.7371
    g *= (1.0 + MOTTLE * math.sin(a / 1.63 + ph) * math.sin(y / 1.17 + ph * 2.1)
          + 0.011 * math.sin(a / 0.61 + ph * 3.3) * math.sin(y / 0.74 + ph)
          + 0.006 * math.sin(a / 0.27 + ph * 5.1)
          + 0.005 * math.sin(y / 0.23 + ph * 7.7))
    return g


def disp(w, a, y):
    """Shallow drywall undulation -- ~0.1 in, which is what a taped-and-floated
    wall actually has.  Its whole job is to stop the normal being constant."""
    ph = w[6] * 1.113
    return AMP_D * (0.55 * math.sin(a / 1.35 + ph) * math.sin(y / 1.05 + ph * 1.7)
                    + 0.28 * math.sin(a / 0.62 + ph * 2.9) * math.sin(y / 0.55 + ph)
                    + 0.17 * math.sin(a / 0.29 + ph * 4.3)
                    + 0.13 * math.sin(y / 0.33 + ph * 6.1))


# The paint is not neutral.  Measured on clean wall fields, the photographs run
# B above R by 5-6 levels (runner 159.9/160.4/166.2, stairs 150.5/150.4/155.2,
# doors2 169.1/170.1/173.8) -- a cool grey.  A neutral skin rendered 167/167/169.
# So every fitted grey is tinted on the way into its material; the fit itself
# stays in luma, which this leaves alone to within 1%.
TINT = (0.972, 0.992, 1.030)


def tint(hexs):
    v = int(hexs[1:3], 16)
    return "#%02x%02x%02x" % tuple(min(255, round(v * t)) for t in TINT)


def _lin_to_srgb(v):
    v = max(0.0, min(1.0, v))
    return 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055


# ------------------------------------------------------------------ builder
def live_holes():
    with urllib.request.urlopen(BASE + "/api/house", timeout=30) as fh:
        house = json.load(fh)
    room = None
    for f in house["floors"]:
        for r in f["rooms"]:
            if r["id"] == ROOM:
                room = r
    if room is None:
        raise SystemExit("room 17 not found")
    holes = {k: [] for k in EDGE_KEY.values()}
    # each edge's run coordinate frame, as (start, direction) in local x or z
    frame = {8: (3.86, +1), 6: (0.0, +1), 5: (16.15, -1),
             4: (3.86, -1), 2: (7.61, -1)}
    for o in room["openings"]:
        key = EDGE_KEY.get(o["edge_index"])
        if not key:
            continue
        s, d = frame[o["edge_index"]]
        p0 = s + d * o["offset"]
        p1 = s + d * (o["offset"] + o["width"])
        holes[key].append((min(p0, p1) - HOLE_M, max(p0, p1) + HOLE_M,
                           o["elevation"] + o["height"] + HOLE_M))
    return holes


# Refinement lines.  A refinement ROW costs one vertex per column and vice
# versa, so these are kept to the two features that actually need sub-cell
# resolution: the ceiling seam (0.115 ft deep) and the corner occlusion.
FINE_TOP = (0.025, 0.06, 0.11, 0.18, 0.30)
FINE_BOT = (0.06, 0.18)
FINE_END = (0.06, 0.16, 0.34)


def _grid(lo, hi, cell, extra):
    """Uniform grid plus refinement lines, deduped and clamped.

    A uniform 0.24 ft grid smears the two features that carry this piece: the
    ceiling seam (the photo's is ~0.15 ft deep) and the corner occlusion (~0.6
    ft).  Refining only where they live costs a handful of rows per wall
    instead of quadrupling the whole sheet.
    """
    n = max(2, int(round((hi - lo) / cell)))
    vals = [lo + (hi - lo) * i / n for i in range(n + 1)]
    vals += [v for v in extra if lo + 1e-4 < v < hi - 1e-4]
    vals.sort()
    out = [vals[0]]
    for v in vals[1:]:
        if v - out[-1] > 0.012:
            out.append(v)
    out[-1] = hi
    return out


def build(colors, cell=0.29, flat=False, holes=None):
    """`flat=True` drops the baked field (used only by the two-point probe)."""
    holes = holes if holes is not None else live_holes()
    m = Model()
    mats = {}
    for w in WALLS:
        key, axis, plane, n, a0, a1, seed = w
        col = tint(colors[key])
        if col not in mats:
            mats[col] = Material("h17w3" + col.lstrip("#"), col,
                                 roughness=0.95, metallic=0.0)
        hs = holes.get(key, [])
        ys = _grid(Y_BOT, Y_CEIL, cell,
                   [Y_CEIL - d for d in FINE_TOP] + [Y_BOT + d for d in FINE_BOT]
                   + [yt for (_, _, yt) in hs])
        aa = _grid(a0, a1, cell,
                   [a0 + d for d in FINE_END] + [a1 - d for d in FINE_END]
                   + [e for (h0, h1, _) in hs for e in (h0, h1)])
        na, ny = len(aa) - 1, len(ys) - 1

        def blocked(a, y):
            return any(h0 <= a <= h1 and y <= yt for (h0, h1, yt) in hs)

        # keep only the vertices a surviving quad actually touches
        live = set()
        quads = []
        for j in range(ny):
            yc = (ys[j] + ys[j + 1]) / 2.0
            for i in range(na):
                ac = (aa[i] + aa[i + 1]) / 2.0
                if blocked(ac, yc):
                    continue
                p = j * (na + 1) + i
                quads.append((p, p + 1, p + na + 1, p + na + 2))
                live.update((p, p + 1, p + na + 1, p + na + 2))

        remap, verts, raw = {}, [], []
        for j in range(ny + 1):
            y = ys[j]
            for i in range(na + 1):
                p = j * (na + 1) + i
                if p not in live:
                    continue
                a = aa[i]
                d = plane + n * (INSET + (0.0 if flat else disp(w, a, y)))
                remap[p] = len(verts)
                verts.append((d, y, a) if axis == "x" else (a, y, d))
                raw.append(1.0 if flat else field(w, a, y))
        # Normalise each wall's field so its BRIGHTEST point is 1.0.  Anything
        # over 1.0 would clip on export (COLOR_0 is 0..1) and clipping flattens
        # exactly the pools the field exists to draw.  The wall's LEVEL is then
        # carried by its base albedo, which is fitted from a real render.
        k = 1.0 / max(raw)
        cols = [(lambda s: (s, s, s))(_lin_to_srgb(v * k)) for v in raw]

        tris = []
        for (p, q, r, t) in quads:
            p, q, r, t = remap[p], remap[q], remap[r], remap[t]
            # wound so the face looks along +n
            if (axis == "x" and n > 0) or (axis == "z" and n < 0):
                tris += [(p, r, q), (q, r, t)]
            else:
                tris += [(p, q, r), (q, t, r)]
        m.add(Part(verts, tris, smooth=True, colors=cols), mats[col])
    return m


def save_and_place(m, name=NAME, fname="hall2f_wall_wash_skins"):
    from roomkit.place import place
    path = os.path.join(HERE, "glb", fname + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    print(f"  {name}  size={tuple(round(hi[i]-lo[i], 2) for i in range(3))}"
          f"  {kb:.1f} KB  {res['action']}")
    return kb


# --------------------------------------------------------------- the paints
# Base albedos, fitted per wall from the two-point render probe below (see
# `python walls3.py probe`).  Every one of them is plain non-emissive paint.
SKINS = {"n": "#e6e6e6", "e": "#e6e6e6", "w": "#e6e6e6", "an": "#e6e6e6",
         "aw": "#e6e6e6", "as": "#e6e6e6", "jog": "#e6e6e6", "s": "#e6e6e6"}

try:
    with open(os.path.join(HERE, "walls3_fit.json")) as fh:
        SKINS.update(json.load(fh))
except OSError:
    pass


def shoot(tag, poses):
    env = dict(os.environ, TAG=tag)
    subprocess.run([PY, "v3.py"] + list(poses), cwd=HERE, env=env, check=False)


def main():
    args = sys.argv[1:]
    if args and args[0] == "probe":
        poses = args[1:] or ["p_runner", "p_stairs", "p_doors2"]
        try:
            # the probe runs the REAL field at two grey albedos, so even if this
            # is killed mid-run what is left placed is a coherent (if wrongly
            # toned) hallway, never a test card.
            for tag, grey in (("wpA_", "#808080"), ("wpB_", "#ffffff")):
                save_and_place(build({k: grey for k in SKINS}))
                shoot(tag, poses)
        finally:
            # RULE 1: never finish a step with a probe piece placed.
            save_and_place(build(SKINS))
        return
    save_and_place(build(SKINS))


if __name__ == "__main__":
    main()
