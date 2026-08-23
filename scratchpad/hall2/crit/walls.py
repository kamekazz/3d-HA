"""Hall2F Wall Wash Skins -- round 2, re-fitted to the CURRENT 10-vertex L.

WHAT THIS PIECE IS.  Room 17's eight real walls, each given its own
non-emissive albedo skin standing ~0.03 ft in front of whatever surface the
camera actually sees there (which is usually the NEIGHBOUR room's wall mass,
not room 17's own -- see FACE below, measured by crit/eprobe.py).  Per-wall
albedo is what closes the renderer's wall-to-wall value spread; the vertex
colour field on top of it is what the round-1 critics were actually asking for.

WHY IT HAD TO BE REBUILT.  The skins in the DB were authored for the old 8.1 x
16.7 rectangle.  crit/eprobe.py fired rays at all ten polygon edges: edges
3/4/5/6 (the whole west alcove) and the first 2 ft of edge 7 came back as raw
`wall`, i.e. unskinned, and edge 8 was wearing a #7e7e7e skin fitted to a wall
that no longer faces the same way.

THE FIELD, and where each number comes from.  Every figure below was metered
off the six photographs at native 450x600 by crit/cprof.py / crit/phm.py:

  * VERTICAL RAMP.  runner right wall, x415-448: 172 at the ceiling line to 136
    at the skirting (ratio 0.79).  doors2 right wall: 184 -> 161 (0.875).
    stairs right wall: 160 -> 109 (0.68).  So a real wall in this house loses
    12-32% top to bottom; RAMP_BOT 0.82 sits in that band.  The photos' curves
    are close to linear with a slight flattening in the last foot, which is the
    floor bounce -- BOUNCE puts that back.
  * CEILING JUNCTION.  A 0.13 ft occlusion band under the lid.  The photos
    cannot resolve it (2 in at 450 px is ~2 px, JPEG-smeared), so it is kept
    thin and shallow; its job is the critics' "the joint nearly vanishes at the
    far end", and the value break it makes with the (brighter) ceiling is what
    keeps the joint legible for the whole run.
  * CORNER OCCLUSION.  doors2, rows 200-300, sweeping x into the reentrant
    corner at x=335: 212 212 211 207 202 -- a ~5 level dip over the last few
    px.  So corner AO in these photographs is REAL but SMALL: CORNER_DK 0.055
    over 0.55 ft.  The two CONVEX corners (v4, v7) get the opposite -- the same
    sweep shows the receding wall 10 levels BRIGHTER just past the arris than
    it is ten feet later -- so they carry a small lift, not a dip.
  * CAN POOLS.  Fixture positions are the ceiling piece's own CANS list.  The
    pool is a gaussian along the wall run times a gaussian in height-below-lid,
    divided down by how far the can stands off the wall plane.
  * SKIRTING SHADOW.  A thin dark line in the first 0.10 ft above the
    baseboard cap: the caulk/shadow reveal where trim stands proud of paint.
  * TEXTURE.  Clean photo wall patches meter sd 3.0-10.2 with mean|d1| 0.32-1.58
    (|d1|/sd 0.05-0.16) at 450x600.  Painted drywall is therefore ALMOST ALL
    broad gradient and a little fine grain -- so the field carries two octaves
    of broad mottle plus a per-cell hash at the grid pitch, and the sheet is
    physically displaced +-0.009 ft so the shading itself breaks up.

NOTHING HERE IS EMISSIVE.  Emissive wall washes have been rejected twice in
this repo (they glow at night and read as light, not paint).  This is albedo.
"""

import hashlib
import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import Model, Material, Part                  # noqa: E402
from roomkit.place import place                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "http://127.0.0.1:5000"
ROOM = 17
H = 8.0

# ----------------------------------------------------------------- footprint
POLY = [(11.92, 6.81), (7.61, 6.81), (7.61, 16.89), (3.86, 16.89), (3.86, 16.15),
        (0.0, 16.15), (0.0, 10.77), (3.86, 10.77), (3.86, 0.0), (11.92, 0.0)]

# Edges that are actually walls (0 and 1 are full-span passages: no wall).
# `face` = how far the FIRST solid surface stands in from the polygon line,
# measured by crit/eprobe.py (neighbouring rooms extrude their wall mass 0.35 ft
# past their own footprint, and several of them are traced inside room 17's
# line).  Edge 2's own face is hidden behind the bath door assembly in every
# probe ray, so it takes the arithmetic value: room 26's north wall runs
# world z 23.05..23.40 and room 17's line is 23.44, i.e. 0.39.
FACE = {2: 0.39, 3: 0.35, 4: 0.35, 5: 0.35, 6: 0.33, 7: 0.29, 8: 0.10, 9: 0.37}

# Reentrant (inside) corners of the L, by polygon vertex; the wall darkens into
# these.  v4 and v7 are CONVEX arrises -- the wall turns away and catches light.
# v0 and v2 are free ends (edges 0/1 carry no wall), so neither applies.
REENTRANT = {3, 5, 6, 8, 9}
CONVEX = {4, 7}

# ------------------------------------------------------------------ fixtures
# Copied from the ceiling piece (scratchpad/hall2/ceiling.py CANS) so the wash
# lands under the cans that are actually in the room.
CANS = [(5.80, 7.18), (7.75, 7.18), (6.10, 4.18), (8.22, 4.10),
        (10.03, 12.74), (1.93, 13.46)]

# --------------------------------------------------------------- the field
Y0 = 0.44           # under the 0.52 ft baseboard cap, so the joint never gaps
Y1 = 7.955          # the ceiling plane sits at 7.99
CELL = 0.28
INSET = 0.028       # the skin stands this far in front of the surface behind it
DISP = 0.009        # relief amplitude (max), keeps it clear of trim at 0.05

RAMP_BOT = 0.820    # albedo at the skirting relative to the top of the ramp
RAMP_GAM = 0.86
BOUNCE = 0.055      # floor-bounce lift in the last foot
BOUNCE_H = 0.95
CEIL_DK, CEIL_H = 0.075, 0.13
SKIRT_DK, SKIRT_H = 0.060, 0.115
CORNER_DK, CORNER_R = 0.055, 0.55
CONVEX_UP, CONVEX_R = 0.035, 0.45
POOL_AMP = 0.105
MOTTLE = (0.021, 0.013)
GRAIN = 0.0135      # per-cell hash, the finest tone the vertex field can carry


def _hash(i, j, k):
    h = hashlib.md5(("%d,%d,%d" % (i, j, k)).encode()).digest()
    return (h[0] + h[1] * 256) / 65535.0 * 2.0 - 1.0


def _geom(edge):
    a = POLY[edge]
    b = POLY[(edge + 1) % len(POLY)]
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz)
    u = (dx / L, dz / L)
    n = (-u[1], u[0])                       # inward normal (house.js convention)
    return a, u, n, L


# ------------------------------------------------------------------ openings
def live_openings():
    """Read room 17's cuts from the app rather than hard-coding them: a
    parallel builder re-cutting a jamb went stale inside one build last round."""
    with urllib.request.urlopen(BASE + "/api/house", timeout=30) as r:
        house = json.load(r)
    for f in house["floors"]:
        for room in f["rooms"]:
            if room["id"] == ROOM:
                out = {}
                for o in room.get("openings", []):
                    out.setdefault(o["edge_index"], []).append(
                        (o["offset"], o["offset"] + o["width"],
                         o["elevation"] + o["height"]))
                for k in out:
                    out[k].sort()
                return out
    raise SystemExit("no room 17")


# --------------------------------------------------------------------- tone
def tone(edge, a, y, L, seed):
    """Multiplicative albedo at along-distance `a`, height `y`, on `edge`."""
    A, u, n, _ = _geom(edge)
    x = A[0] + u[0] * a
    z = A[1] + u[1] * a

    # 1. vertical ramp + floor bounce
    t = (y - Y0) / (Y1 - Y0)
    g = RAMP_BOT + (1.0 - RAMP_BOT) * (t ** RAMP_GAM)
    g *= 1.0 + BOUNCE * math.exp(-(max(0.0, y - Y0) / BOUNCE_H) ** 1.6)

    # 2. can pools -- brightest high on the wall, under the fixture, and dying
    #    off with how far the can stands off this wall's plane
    pool = 0.0
    for (fx, fz) in CANS:
        along = (fx - A[0]) * u[0] + (fz - A[1]) * u[1]
        perp = (fx - A[0]) * n[0] + (fz - A[1]) * n[1]
        if perp < -0.5 or not (-3.0 <= along <= L + 3.0):
            continue
        pool += (POOL_AMP
                 * math.exp(-((a - along) / 1.95) ** 2)
                 * math.exp(-((H - y) / 2.45) ** 2)
                 / (1.0 + (max(perp, 0.0) / 1.65) ** 2))
    g *= 1.0 + pool

    # 3. junctions: the lid, the skirting cap, and every corner of the L
    g *= 1.0 - CEIL_DK * math.exp(-(max(0.0, Y1 - y) / CEIL_H) ** 1.25)
    g *= 1.0 - SKIRT_DK * math.exp(-(max(0.0, y - Y0) / SKIRT_H) ** 1.25)
    v0, v1 = edge, (edge + 1) % len(POLY)
    d0 = max(0.0, a)
    d1 = max(0.0, L - a)
    if v0 in REENTRANT:
        g *= 1.0 - CORNER_DK * math.exp(-(d0 / CORNER_R) ** 1.35)
    if v1 in REENTRANT:
        g *= 1.0 - CORNER_DK * math.exp(-(d1 / CORNER_R) ** 1.35)
    if v0 in CONVEX:
        g *= 1.0 + CONVEX_UP * math.exp(-(d0 / CONVEX_R) ** 1.5)
    if v1 in CONVEX:
        g *= 1.0 + CONVEX_UP * math.exp(-(d1 / CONVEX_R) ** 1.5)

    # 4. surface: two octaves of broad mottle, then a per-cell hash so the
    #    field is not algebraically smooth at the scale a human looks at it
    g *= (1.0 + MOTTLE[0] * math.sin(x / 1.63 + z / 2.11 + seed)
          * math.sin(y / 1.19 + 0.4 + seed)
          + MOTTLE[1] * math.sin(x / 0.61 - z / 0.77 + 2.7 + seed)
          * math.sin(y / 0.53 + 1.1))
    g *= 1.0 + GRAIN * _hash(edge, int(round(a / CELL)), int(round(y / CELL)))
    return g


def relief(x, z, y, seed):
    return DISP * (0.52 * math.sin(x / 0.47 + z / 0.61 + seed)
                   * math.sin(y / 0.39 + seed * 1.7)
                   + 0.30 * math.sin(x / 0.19 - z / 0.23 + 1.9)
                   * math.sin(y / 0.17 + 2.4)
                   + 0.18 * math.sin(y / 1.31 + x / 1.07 + 0.6))


# --------------------------------------------------------------------- build
def panel(m, edge, a0, a1, y0, y1, mat, seed, norm):
    A, u, n, L = _geom(edge)
    na = max(2, int(round((a1 - a0) / CELL)))
    ny = max(2, int(round((y1 - y0) / CELL)))
    d0 = FACE[edge] + INSET
    verts, cols = [], []
    for j in range(ny + 1):
        y = y0 + (y1 - y0) * j / ny
        for i in range(na + 1):
            a = a0 + (a1 - a0) * i / na
            x = A[0] + u[0] * a
            z = A[1] + u[1] * a
            d = d0 + relief(x, z, y, seed)
            verts.append((x + n[0] * d, y, z + n[1] * d))
            s = tone(edge, a, y, L, seed) * norm
            s = max(0.06, min(1.0, s))
            cols.append((s, s, s))
    tris = []
    w = na + 1
    for j in range(ny):
        for i in range(na):
            p = j * w + i
            tris += [(p, p + 1, p + w + 1), (p, p + w + 1, p + w)]
    m.add(Part(verts, tris, smooth=True, colors=cols), mat)


def wall_bands(edge, cuts):
    """Split one edge into the rectangles that are NOT a doorway."""
    _, _, _, L = _geom(edge)
    out = []
    a = 0.0
    for (c0, c1, ctop) in cuts:
        c0 = max(0.0, min(L, c0))
        c1 = max(0.0, min(L, c1))
        if c0 - a > 0.02:
            out.append((a, c0, Y0, Y1))
        if Y1 - ctop > 0.05 and c1 - c0 > 0.02:
            out.append((c0, c1, max(Y0, ctop), Y1))       # the header
        a = max(a, c1)
    if L - a > 0.02:
        out.append((a, L, Y0, Y1))
    return out


def _norm_factor(edge, cuts):
    """Scale so the field's BRIGHTEST point on this wall is 1.0.  Normalising
    to the mean instead needs clipping wherever a pool runs past white, and
    clipping flattens exactly the part of the wall the falloff exists for."""
    _, _, _, L = _geom(edge)
    hi = 0.0
    for (a0, a1, y0, y1) in wall_bands(edge, cuts):
        for i in range(25):
            for j in range(25):
                hi = max(hi, tone(edge, a0 + (a1 - a0) * i / 24.0,
                                  y0 + (y1 - y0) * j / 24.0, L, SEED[edge]))
    return 1.0 / hi


SEED = {2: 1.7, 3: 4.2, 4: 0.9, 5: 2.6, 6: 5.1, 7: 3.3, 8: 6.0, 9: 1.1}


def piece(colors, cuts=None):
    cuts = live_openings() if cuts is None else cuts
    m = Model()
    for edge in sorted(FACE):
        c = colors[edge]
        mat = Material("h17w2_%d_%s" % (edge, c.lstrip("#")), c,
                       roughness=0.95, metallic=0.0, double_sided=False)
        ec = cuts.get(edge, [])
        k = _norm_factor(edge, ec)
        for (a0, a1, y0, y1) in wall_bands(edge, ec):
            panel(m, edge, a0, a1, y0, y1, mat, SEED[edge], k)
    return m


# ------------------------------------------------------------------- place
NAME = "Hall2F Wall Wash Skins"


def save_and_place(m, name=NAME, fname="hall2f_wall_wash_skins"):
    path = os.path.join(HERE, "glb", fname + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    print("  %-26s size=%s  %.1f KB  %s"
          % (name, tuple(round(hi[i] - lo[i], 2) for i in range(3)), kb,
             res["action"]))
    return kb


# Fitted from two-point render probes -- see crit/wprobe.py.  Placeholder
# values until the first fit runs.
SKINS = {2: "#c8c8c8", 3: "#c8c8c8", 4: "#c8c8c8", 5: "#c8c8c8",
         6: "#c8c8c8", 7: "#c8c8c8", 8: "#c8c8c8", 9: "#c8c8c8"}

_fitted = os.path.join(HERE, "skins.json")
if os.path.exists(_fitted):
    SKINS = {int(k): v for k, v in json.load(open(_fitted)).items()}


if __name__ == "__main__":
    if len(sys.argv) > 1:                      # walls.py <hex>  -> flat probe
        SKINS = {e: sys.argv[1] for e in FACE}
    save_and_place(piece(SKINS))
