"""Room 1 -- Movie Room, v3-photo rebuild.  20.4 (x) x 23.5 (z) x 8.0 ft.

ORIENTATION (registered to docs/floor plan/Basement Floor Plan App.png; see the
build report for the derivation and its two independent checks):
  north  z=0     shared with the Arcade Room.  TV wall: ~7.6 ft black TV over a
                 grey slatted media console (plan blob x 2.2-9.9), a black
                 speaker cabinet each side (plan blob x 9.9-12.0), two flush
                 white in-wall speakers, and the white door to the Arcade at
                 x 13.35-16.05 (registered with room 2's opening 103).
  west   x=0     exterior.  Five-panel canvas print, one high egress window,
                 the sectional's west leg, a side table + black lamp, the tall
                 white tower purifier.
  south  z=23.5  exterior.  A second high egress window, the sectional's south
                 leg, then a black cabinet, the bladeless ring fan and a second
                 side table + lamp at its east end.
  east   x=20.4  exterior; the stair (DB stairs row: local x 17.0-20.3,
                 z 3.8-16.2, ascending north) fills it behind a partition at
                 x~16.9 that carries a SECOND flat TV; the two cream swivel
                 barrel chairs stand in front of that partition.

*** The Arcade Room's own south wall body occupies world z 11.40-11.75, i.e.
    this room's local z 0-0.35 ***  (house.js extrudes every wall OUTWARD from
    its footprint line, so on a shared wall each room's wall mass lands inside
    its neighbour).  Everything on the north wall must therefore be authored at
    depth >= NF, or it is buried and invisible -- which is what made round 1
    meter the north wall at a "clipped" 238 with no chair-rail step at all.

Idempotent by piece name.  Run:  python mv2.py
"""
import json
import math
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\bsmt")

from bkit import *            # noqa: F401,F403
from roomkit.glb import uv_quad
import tex as TX

ROOM, W, D, H = 1, 20.4, 23.5, 8.0
BASE = "http://127.0.0.1:5000"

NF = 0.36                       # north wall's true inner face (arcade wall mass)
RAIL = 3.40                     # chair-rail top
DOOR = (13.35, 16.05)           # north wall, local x
WINW = (5.40, 9.00)             # west wall, local z
WINS = (2.40, 6.00)             # south wall, local x
SILL, HEAD = 5.50, 7.35
SWX = (16.74, 17.06)            # stair partition, local x
SWZ = (4.05, 16.28)             # ... and its z run
RUG = (1.90, 15.20, 4.00, 22.40)
RUG_Y = 0.098                   # rug top


# ------------------------------------------------------------------ tiles
T_WALL = TX.grain_tile(96, 246, 2.2, blotch=15.0, cells=13, seed=17)
T_WAIN = TX.grain_tile(96, 246, 2.2, blotch=15.0, cells=13, seed=23)
T_RUG = TX.grain_tile(96, 240, 15.0, blotch=13.0, cells=26, seed=31)
T_PLANK = TX.plank_tile(96, 3, seed=5)
T_FAB = TX.weave_tile(64, 240, 17.0, seed=41, warp=7)
T_GEO = TX.geo_tile(32, seed=21)
T_ART = TX.art_tile()
T_CEIL = TX.grain_tile(80, 249, 2.0, blotch=6.0, cells=8, seed=53)


# --------------------------------------------------------------- palette
# Wall skins are solved by probe (see report); --pv=<hex> paints all four the
# same value so one render gives each wall's response.
PV = None
for a in sys.argv:
    if a.startswith("--pv="):
        PV = a.split("=", 1)[1]

SKIN_UP = {"n": "#6a6c6f", "w": "#a4a6a9", "e": "#d3d5d8", "s": "#fbfdff"}
SKIN_LO = {"n": "#56585b", "w": "#8f9194", "e": "#babcbf", "s": "#dadce0"}
if PV:
    SKIN_UP = {k: PV for k in SKIN_UP}
    SKIN_LO = {k: PV for k in SKIN_LO}

FAB = Material("m2fab", "#767472", roughness=0.95, tex=T_FAB)
FAB_D = Material("m2fabd", "#6b6966", roughness=0.95, tex=T_FAB)
BACKC = Material("m2back", "#7d7b78", roughness=0.95, tex=T_FAB)
SLATE = Material("m2slate", "#6d7c85", roughness=0.95, tex=T_FAB)
BOUCLE = Material("m2bou", "#a59f96", roughness=1.0, tex=T_FAB)
GEO = Material("m2geo", "#868c91", roughness=0.95, tex=T_GEO)
BLKPILL = Material("m2bp", "#252629", roughness=0.90, tex=T_FAB)
THROW = Material("m2throw", "#464a4f", roughness=1.0, tex=T_FAB)
IVORY = Material("m2iv", "#9d9a92", roughness=0.95, tex=T_FAB)
DKWOOD = Material("m2dw", "#2c2825", roughness=0.6)
BLK = Material("m2blk", "#0b0c0e", roughness=0.28)
BEZ = Material("m2bez", "#1e1f22", roughness=0.42)
BOXBLK = Material("m2box", "#141518", roughness=0.55)
GREYWD = Material("m2gw", "#6d6b67", roughness=0.62)
GREYWD2 = Material("m2gw2", "#615f5b", roughness=0.64)
WHTOP = Material("m2wt", "#c9c7c1", roughness=0.45)
SPKR = Material("m2spk", "#d6d3cc", roughness=0.85)
GREEN = Material("m2grn", "#4b6b4a", roughness=0.9)
POT = Material("m2pot", "#1d1e20", roughness=0.6)
ARTM = Material("m2art", "#ffffff", roughness=0.86, tex=T_ART)
LAMPBLK = Material("m2lb", "#141517", roughness=0.5)
LAMPSHD = Material("m2ls", "#191a1d", roughness=0.85)
TBLWOOD = Material("m2tw", "#4c453e", roughness=0.7)
FANW = Material("m2fw", "#e2e0da", roughness=0.5)
STUD = Material("m2stud", "#8e9295", roughness=0.35, metallic=0.45)
RUGM = Material("m2rug", "#8a857e", roughness=1.0, tex=T_RUG)
RUGM2 = Material("m2rug2", "#847f79", roughness=1.0, tex=T_RUG)
CEILM = Material("m2ceil", "#ffffff", roughness=0.95, emissive="#626262",
                 double_sided=False, tex=T_CEIL)


def blit2(m, sub, wall, W_, D_, depth0):
    """kit._blit drops Part.uv and Part.colors, which silently turns a
    tiled-texture panel into flat paint.  This one keeps them."""
    for part, mat in sub._parts:
        v = []
        for (x, y, z) in part.verts:
            if wall == "n":
                v.append((x, y, depth0 + z))
            elif wall == "s":
                v.append((W_ - x, y, D_ - depth0 - z))
            elif wall == "w":
                v.append((depth0 + z, y, D_ - x))
            else:
                v.append((W_ - depth0 - z, y, x))
        m._parts.append((Part(v, part.tris, part.smooth, part.colors, part.uv), mat))


FABRICS = ("m2fab", "m2fabd", "m2back", "m2slate", "m2bou", "m2geo",
           "m2bp", "m2throw", "m2iv")


def fabricate(m, amp=0.060, seed=9):
    """Give every upholstery part a per-vertex colour jitter.

    puff/slab/cylinder carry no UVs, so a tiled texture on them samples one
    texel and renders as flat paint -- which is why round 1's fabrics metered
    |d1| 0.07 against the photo's 1.7-9.7.  COLOR_0 is 4 bytes a vertex and
    multiplies into baseColor, so this costs almost nothing."""
    rnd = TX.R(seed)
    t = 1.15                       # feet per texture repeat
    for part, mat in m._parts:
        if mat.name not in FABRICS:
            continue
        if not part.colors:
            a = amp * (2.6 if mat.name == "m2geo" else 1.0)
            part.colors = [(lambda c: (c, c, c))(1.0 + rnd.f(-a, a))
                           for _ in part.verts]
        if not part.uv:
            # planar projection: puff / slab / cylinder carry no UVs, and a
            # tiled weave needs some.  The tile is noise, so a seam costs
            # nothing and one skewed projection covers every orientation.
            part.uv = [((x + z) / t, (y + 0.42 * (x - z)) / t)
                       for (x, y, z) in part.verts]
    return m


def cush(m, mat, x0, x1, y0, y1, z0, z1, r=0.14, nub=0.0, rnd=None,
         seg=11, rings=5):
    """bkit.cush at a coarser tessellation.  With the fine gradient now coming
    from the tile + vertex colour rather than from mesh cells, seg 14/rings 7
    only bought payload -- this keeps the sectional under the 300 KB cap."""
    m.add(puff(x1 - x0, y1 - y0, z1 - z0, r=r, nub=nub, rnd=rnd,
               anchor="base", seg=seg, rings=rings), mat,
          at=((x0 + x1) / 2, y0, (z0 + z1) / 2))


def cshadow(m, cx, cz, hx, hz, y, out=0.80, strength=0.58, steps=10,
            room=None, tone="#26262a"):
    """Contact shadow whose ramp actually lands OUTSIDE the piece's footprint.

    kit.contact_shadow runs its 12 annuli from s=1.0 down to s=0.10, so with
    rx set near the footprint almost all the darkness is buried UNDER the
    object and only ~3 of 12 layers ever show -- measured 9% darkening at the
    contact edge against ROOM-BRIEF's 34% target.  Here `hx, hz` are the
    piece's own half-extents and the ramp runs from 0.55x that out to
    (h + out), so roughly half the layers overlap at the footprint edge.
    """
    a = round(1.0 - (1.0 - strength) ** (1.0 / steps), 4)
    mat = Material("csh%d" % int(strength * 100), tone, roughness=0.98, opacity=a)
    seg, n = 32, 2.7
    for i in range(steps):
        t = (i / (steps - 1.0)) ** 1.15          # 0 outermost -> 1 innermost
        rx = (hx + out) + (hx * 0.55 - (hx + out)) * t
        rz = (hz + out) + (hz * 0.55 - (hz + out)) * t
        v = [(cx, y + i * 0.0012, cz)]
        for k in range(seg):
            th = 2 * math.pi * k / seg
            ct, st = math.cos(th), math.sin(th)
            px = cx + rx * math.copysign(abs(ct) ** (2.0 / n), ct)
            pz = cz + rz * math.copysign(abs(st) ** (2.0 / n), st)
            if room:
                px = min(max(px, 0.05), room[0] - 0.05)
                pz = min(max(pz, 0.05), room[1] - 0.05)
            v.append((px, y + i * 0.0012, pz))
        m.add(Part(v, [(0, 1 + (k + 1) % seg, 1 + k) for k in range(seg)]), mat)


def api(method, path, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


# ================================================================ openings
def openings():
    with urllib.request.urlopen(f"{BASE}/api/house", timeout=30) as r:
        house = json.loads(r.read().decode())
    room = next(rm for f in house["floors"] for rm in f["rooms"] if rm["id"] == ROOM)
    have = {(o["edge_index"], o["type"]): o for o in room.get("openings", [])}

    # The east-wall 'passage' (id 94) was cut when this room stopped at local
    # x 17 and the stairwell was OUTSIDE the footprint.  The re-trace pulled the
    # east wall out to 20.4, so that hole now punches 6.9 x 7.2 ft straight
    # through the basement's EXTERIOR wall.  Remove it.
    for (edge, typ), o in list(have.items()):
        if edge == 1 and typ == "passage":
            api("DELETE", f"/api/house/opening/{o['id']}")
            print("  opening east passage %d deleted (stale, exterior wall)" % o["id"])
            have.pop((edge, typ))

    want = [
        dict(edge_index=0, type="door", offset=DOOR[0], width=DOOR[1] - DOOR[0],
             height=6.83, elevation=0.0),
        dict(edge_index=3, type="window", offset=D - WINW[1],
             width=WINW[1] - WINW[0], height=HEAD - SILL, elevation=SILL),
        dict(edge_index=2, type="window", offset=W - WINS[1],
             width=WINS[1] - WINS[0], height=HEAD - SILL, elevation=SILL),
    ]
    for spec in want:
        key = (spec["edge_index"], spec["type"])
        if key in have:
            api("PATCH", f"/api/house/opening/{have[key]['id']}", spec)
            print(f"  opening {key} updated")
        else:
            api("POST", f"/api/house/room/{ROOM}/opening", spec)
            print(f"  opening {key} created")


# --------------------------------------------------------- per-wall frames
def frame(wall, depth):
    """pt(a, y) -> room xyz for a point `a` along `wall` at height y."""
    if wall == "n":
        return lambda a, y: (a, y, depth)
    if wall == "s":
        return lambda a, y: (W - a, y, D - depth)
    if wall == "w":
        return lambda a, y: (depth, y, D - a)
    return lambda a, y: (W - depth, y, a)


def band(m, mat, wall, y0, y1, depth, gaps=()):
    """A trim run along `wall`, `depth` proud of that wall's true inner face."""
    total = W if wall in "ns" else D
    d0 = NF if wall == "n" else 0.0
    for a, b in spans(total, gaps):
        if b - a <= 0.02:
            continue
        if wall == "n":
            bx(m, mat, a, b, y0, y1, d0, d0 + depth)
        elif wall == "s":
            bx(m, mat, a, b, y0, y1, D - depth, D)
        elif wall == "w":
            bx(m, mat, 0.0, depth, y0, y1, a, b)
        else:
            bx(m, mat, W - depth, W, y0, y1, a, b)


# =================================================================== skins
def build_skins():
    """Per-wall, NON-emissive albedo skins -- the sanctioned fix for wall-value
    spread (ROOM-BRIEF).  Each covers its wall corner to corner at roughness
    0.95, carries a tiled grain PLUS smooth per-vertex colour jitter (so it is
    not the algebraically-flat paint three earlier rooms shipped), and is cut
    around every real opening.  Named '<Room> Wall Wash <n>' so objects.js
    keeps it unpickable and cutaway.js fades each one with its own wall."""
    out = []
    holes = {"n": [(DOOR[0], DOOR[1], 0.0, 6.83)],
             "w": [(D - WINW[1], D - WINW[0], SILL, HEAD)],
             "s": [(W - WINS[1], W - WINS[0], SILL, HEAD)],
             "e": []}
    for wall in "nswe":
        m = Model()
        rnd = TX.R(1000 + ord(wall))
        total = W if wall in "ns" else D
        up = Material("skinU" + wall, SKIN_UP[wall], roughness=0.95, tex=T_WALL)
        lo = Material("skinL" + wall, SKIN_LO[wall], roughness=0.95, tex=T_WAIN)
        pt = frame(wall, (NF + 0.03) if wall == "n" else 0.03)
        flip = wall in ("n", "e")
        for (mat, ya, yb, t) in ((lo, 0.0, RAIL - 0.14, 1.8),
                                 (up, RAIL - 0.14, H, 2.0)):
            cuts = [(a0, a1) for (a0, a1, hy0, hy1) in holes[wall]
                    if hy1 > ya + 0.01 and hy0 < yb - 0.01]
            for (a0, a1) in spans(total, cuts):
                m.add(TX.grid_panel(pt, a0, a1, ya, yb, t, rnd, amp=0.022,
                                    cell=3.6, flip=flip), mat)
            for (a0, a1, hy0, hy1) in holes[wall]:
                if not (hy1 > ya + 0.01 and hy0 < yb - 0.01):
                    continue
                if hy0 > ya + 0.05:
                    m.add(TX.grid_panel(pt, a0, a1, ya, hy0, t, rnd, amp=0.022,
                                        cell=3.6, flip=flip), mat)
                if hy1 < yb - 0.05:
                    m.add(TX.grid_panel(pt, a0, a1, hy1, yb, t, rnd, amp=0.022,
                                        cell=3.6, flip=flip), mat)
        out.append(save_and_place(f"Movie Wall Wash {wall}", m, ROOM))
    return out


# ================================================================== ceiling
def build_ceiling():
    m = ceiling(W, D, H,
                cans=[(3.2, 3.0), (9.0, 3.0), (14.6, 3.0),
                      (3.2, 8.6), (9.0, 8.6), (14.6, 8.6),
                      (3.2, 14.2), (9.0, 14.2), (14.6, 14.2),
                      (4.6, 19.9), (11.4, 19.9)],
                speakers=[(6.1, 5.8, 0.58), (12.3, 5.8, 0.58),
                          (6.1, 16.4, 0.58), (12.3, 16.4, 0.58)],
                vents=[(9.0, 7.0, 1.05, 0.55), (6.2, 18.6, 1.05, 0.55)],
                crown=False, ceil_mat=CEILM)
    Y = H - 0.01
    m._parts[0] = (uv_quad((0, Y, 0), (W, Y, 0), (W, Y, D), (0, Y, D),
                           (0, 0), (W / 2.0, 0), (W / 2.0, D / 2.0), (0, D / 2.0)),
                   CEILM)
    for y0, y1, dep in ((H - CROWN_H, H - 0.30, 0.055),
                        (H - 0.30, H - 0.145, 0.115),
                        (H - 0.145, H - 0.008, 0.185)):
        mat = TRIM if dep > 0.09 else TRIM_D
        for w in "nswe":
            band(m, mat, w, y0, y1, dep)
    m.add(cylinder(0.30, 0.10, 16), Material("m2sd", "#e9e7e2", roughness=0.6),
          at=(11.9, H - 0.11, 20.6))
    return save_and_place("Movie Ceiling", m, ROOM)


def build_floor():
    """A plank overlay on the slab.  The app's own `wood` floor texture meters
    sd 1.5 / |d1| 1.1 against the photo's 12.0 / 3.9 -- flat plastic at the
    scale a human reads.  One tiled quad fixes that for ~1 KB."""
    m = Model()
    PLK = Material("m2plk", "#52555a", roughness=0.90, tex=T_PLANK)
    y = 0.042
    tu, tv = 7.4, 1.62
    m.add(Part([(0.02, y, D - 0.02), (W - 0.02, y, D - 0.02),
                (W - 0.02, y, 0.02), (0.02, y, 0.02)],
               [(0, 1, 2), (0, 2, 3)],
               uv=[((D - 0.02) / tu, 0.02 / tv), ((D - 0.02) / tu, (W - 0.02) / tv),
                   (0.02 / tu, (W - 0.02) / tv), (0.02 / tu, 0.02 / tv)]), PLK)
    return save_and_place("Movie Floor Planks", m, ROOM)


# ================================================================ trim runs
def build_trim():
    m = Model()
    gaps = {"n": [(DOOR[0] - CASE_W, DOOR[1] + CASE_W)], "s": [], "w": [], "e": []}
    for w in "nswe":
        band(m, TRIM, w, 0.0, BB_H - 0.06, BB_T, gaps[w])
        band(m, TRIM, w, BB_H - 0.06, BB_H, BB_T * 0.72, gaps[w])
        band(m, TRIM, w, RAIL - 0.14, RAIL - 0.035, 0.085, gaps[w])
        band(m, TRIM, w, RAIL - 0.035, RAIL, 0.052, gaps[w])
    sub = Model()
    for a, b in ((DOOR[0] - CASE_W, DOOR[0] + 0.03),
                 (DOOR[1] - 0.03, DOOR[1] + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, 6.83 + CASE_W, 0.0, 0.20)
    bx(sub, TRIM, DOOR[0] - CASE_W, DOOR[1] + CASE_W, 6.83, 6.83 + CASE_W, 0.0, 0.20)
    blit(m, sub, "n", W, D, NF)
    win_trim(m, "w", D - WINW[1], D - WINW[0])
    win_trim(m, "s", W - WINS[1], W - WINS[0])
    return save_and_place("Movie Baseboards", m, ROOM)


def win_trim(m, wall, a0, a1):
    """Casing, stool, apron, muntins -- and a bright pane.

    The app's own glass panel renders these egress windows at luminance 99;
    in every v3 photo they are blown-out white rectangles (the only light
    source in the room).  A small pane at modest emissive is glazing, not the
    banned room-fill wash -- it covers 6.7 sq ft of a 479 sq ft room."""
    sub = Model()
    bx(sub, Material("m2pane", "#eef2f6", roughness=0.6, emissive="#cfd8e0",
                     emissive_strength=1.5),
       a0 + 0.03, a1 - 0.03, SILL + 0.03, HEAD - 0.03, 0.142, 0.156)
    bx(sub, TRIM, a0 - 0.20, a1 + 0.20, SILL - 0.12, SILL, 0.0, 0.26)
    bx(sub, TRIM, a0 + 0.10, a1 - 0.10, SILL - 0.42, SILL - 0.12, 0.0, 0.075)
    for a, b in ((a0 - CASE_W, a0 + 0.02), (a1 - 0.02, a1 + CASE_W)):
        bx(sub, TRIM, a, b, SILL - 0.12, HEAD + CASE_W, 0.0, 0.10)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, HEAD, HEAD + CASE_W, 0.0, 0.10)
    for k in (1, 2):
        c = a0 + (a1 - a0) * k / 3.0
        bx(sub, TRIM, c - 0.035, c + 0.035, SILL, HEAD, 0.160, 0.200)
    blit(m, sub, wall, W, D, 0.0)


# ============================================================== screen wall
def build_screen():
    """Wall-MOUNTED north-wall content only: the TV and the flush speakers.
    (The console and the speaker cabinets are furniture in their own object, so
    cutaway.js cannot tear them in half when this wall fades.)"""
    m = Model()
    sub = Model()
    bx(sub, BEZ, 2.28, 10.02, 3.56, 7.14, 0.02, 0.10)
    bx(sub, BLK, 2.38, 9.92, 3.64, 7.06, 0.10, 0.19)
    for sx in (1.20, 10.42):
        bx(sub, TRIM, sx, sx + 0.80, 4.45, 6.20, 0.02, 0.05)
        bx(sub, SPKR, sx + 0.05, sx + 0.75, 4.50, 6.15, 0.05, 0.08)
    blit(m, sub, "n", W, D, NF)
    return save_and_place("Movie Screen Wall", m, ROOM)


def build_console():
    m = Model()
    cx0, cx1 = 2.20, 9.90
    z0 = NF
    cz1 = z0 + 1.55
    cshadow(m, (cx0 + cx1) / 2, z0 + 0.80, 3.85, 0.80, y=0.058, strength=0.72, room=(W, D))
    bx(m, GREYWD, cx0, cx1, 0.46, 2.22, z0 + 0.12, cz1)
    for i in range(4):
        dw = (cx1 - cx0 - 0.16) / 4
        dx0 = cx0 + 0.08 + i * dw
        bx(m, GREYWD2, dx0, dx0 + dw - 0.05, 0.54, 2.14, cz1, cz1 + 0.030)
        for k in range(5):
            yy = 0.60 + k * 0.31
            bx(m, GREYWD, dx0 + 0.02, dx0 + dw - 0.07, yy, yy + 0.235,
               cz1 + 0.030, cz1 + 0.048)
        bx(m, BLACKMET, dx0 + dw * 0.42, dx0 + dw * 0.58, 2.02, 2.06,
           cz1 + 0.048, cz1 + 0.082)
    bx(m, WHTOP, cx0 - 0.09, cx1 + 0.09, 2.22, 2.35, z0 + 0.06, cz1 + 0.09)
    for px_ in (cx0 + 0.22, cx1 - 0.32):
        bx(m, BLACKMET, px_, px_ + 0.10, 0.0, 0.46, z0 + 0.28, z0 + 0.38)
        bx(m, BLACKMET, px_, px_ + 0.10, 0.0, 0.46, cz1 - 0.22, cz1 - 0.12)
        bx(m, BLACKMET, px_, px_ + 0.10, 0.40, 0.46, z0 + 0.28, cz1 - 0.12)
    for (sx, sw, sh, sd) in ((0.45, 1.60, 1.86, 1.62), (9.98, 2.05, 2.18, 2.02)):
        cshadow(m, sx + sw / 2, z0 + sd / 2, sw / 2, sd / 2, y=0.058,
                out=0.65, strength=0.72, room=(W, D))
        bx(m, BOXBLK, sx, sx + sw, 0.0, sh, z0, z0 + sd)
        bx(m, BEZ, sx + 0.10, sx + sw - 0.10, sh * 0.14, sh * 0.88,
           z0 + sd, z0 + sd + 0.012)
    for px_ in (3.05, 8.35):
        m.add(cylinder(0.22, 0.36, 10, r_top=0.26), POT, at=(px_, 2.35, z0 + 0.62))
        for k in range(7):
            a = 2 * math.pi * k / 7
            m.add(puff(0.30, 0.20, 0.26, r=0.09), GREEN,
                  at=(px_ + 0.22 * math.cos(a), 2.62 + 0.07 * (k % 3),
                      z0 + 0.62 + 0.22 * math.sin(a)))
    bx(m, BEZ, 6.55, 7.45, 2.35, 2.86, z0 + 0.34, z0 + 0.46)
    return save_and_place("Movie Media Console", m, ROOM)


# =========================================================== stair partition
def build_stairwall():
    """The plan shows a partition down the stairwell's room side (local
    x ~16.9, z 4.1-16.3) with a cross wall closing the under-stair space, and
    photo 3 shows a SECOND flat TV mounted on it."""
    m = Model()
    x0, x1 = SWX
    z0, z1 = SWZ
    SKIN = Material("m2sw", SKIN_UP["e"], roughness=0.95, tex=T_WALL)
    SKINL = Material("m2swl", SKIN_LO["e"], roughness=0.95, tex=T_WAIN)
    FLAT = Material("m2swf", SKIN_UP["e"], roughness=0.95)
    FLATL = Material("m2swfl", SKIN_LO["e"], roughness=0.95)
    bx(m, FLATL, x0, x1, 0.0, RAIL - 0.14, z0, z1)
    bx(m, FLAT, x0, x1, RAIL - 0.14, H, z0, z1)
    bx(m, FLATL, x0, W, 0.0, RAIL - 0.14, z0, z0 + 0.32)
    bx(m, FLAT, x0, W, RAIL - 0.14, H, z0, z0 + 0.32)
    rnd = TX.R(4242)
    face = lambda a, y: (x0 - 0.008, y, a)
    m.add(TX.grid_panel(face, z0, z1, 0.0, RAIL - 0.14, 1.8, rnd,
                        amp=0.014, cell=3.2, flip=True), SKINL)
    m.add(TX.grid_panel(face, z0, z1, RAIL - 0.14, H, 2.0, rnd,
                        amp=0.014, cell=3.2, flip=True), SKIN)
    cface = lambda a, y: (a, y, z0 - 0.008)
    m.add(TX.grid_panel(cface, x0, W, 0.0, RAIL - 0.14, 1.8, rnd,
                        amp=0.014, cell=3.2, flip=False), SKINL)
    m.add(TX.grid_panel(cface, x0, W, RAIL - 0.14, H, 2.0, rnd,
                        amp=0.014, cell=3.2, flip=False), SKIN)
    bx(m, TRIM, x0 - BB_T, x0, 0.0, BB_H - 0.06, z0, z1)
    bx(m, TRIM, x0 - BB_T * 0.72, x0, BB_H - 0.06, BB_H, z0, z1)
    bx(m, TRIM, x0 - 0.085, x0, RAIL - 0.14, RAIL - 0.035, z0, z1)
    bx(m, TRIM, x0 - 0.052, x0, RAIL - 0.035, RAIL, z0, z1)
    for y0, y1, dep in ((H - CROWN_H, H - 0.30, 0.055),
                        (H - 0.30, H - 0.145, 0.115),
                        (H - 0.145, H - 0.008, 0.185)):
        bx(m, TRIM if dep > 0.09 else TRIM_D, x0 - dep, x0, y0, y1, z0, z1)
    bx(m, BEZ, x0 - 0.10, x0 - 0.02, 3.82, 6.22, 8.35, 12.55)
    bx(m, BLK, x0 - 0.19, x0 - 0.10, 3.90, 6.14, 8.45, 12.45)
    bx(m, TRIM, x0 - 0.05, x0 - 0.02, 4.40, 5.30, 13.30, 13.62)
    return save_and_place("Movie Stair Wall", m, ROOM)


def build_stairrail():
    """Black newel and cap rail with white balusters at the foot of the flight."""
    m = Model()
    NEWEL = Material("m2newel", "#121214", roughness=0.42)
    x0 = SWX[1]
    zf = SWZ[1]
    nx, nz = x0 + 0.34, zf - 0.24
    m.add(box(0.34, 3.34, 0.34), NEWEL, at=(nx, 0.0, nz))
    m.add(box(0.44, 0.17, 0.44), NEWEL, at=(nx, 3.34, nz))
    m.add(box(0.15, 0.15, 5.60), NEWEL, at=(nx, 3.02, nz - 3.10))
    for i in range(9):
        z = nz - 0.55 - i * 0.58
        m.add(box(0.10, 2.85 - i * 0.02, 0.10), TRIM, at=(nx, 0.10 + i * 0.30, z))
    return save_and_place("Movie Stair Rail", m, ROOM)


# ====================================================================== rug
def build_rug():
    """The photo's very large near-white low-pile rug, plus every contact
    shadow in the room.  Named '... Floor Rug' so objects.js keeps it
    unpickable."""
    m = Model()
    x0, x1, z0, z1 = RUG
    bx(m, RUGM2, x0, x1, 0.046, RUG_Y - 0.014, z0, z1)
    m.add(TX.grid_panel(lambda a, y: (a, RUG_Y, y), x0 + 0.22, x1 - 0.22,
                        z0 + 0.22, z1 - 0.22, 1.25, TX.R(777), amp=0.020,
                        cell=1.4, flip=True), RUGM)
    bx(m, RUGM2, x0, x1, RUG_Y - 0.014, RUG_Y - 0.002, z0, z0 + 0.22)
    bx(m, RUGM2, x0, x1, RUG_Y - 0.014, RUG_Y - 0.002, z1 - 0.22, z1)
    bx(m, RUGM2, x0, x0 + 0.22, RUG_Y - 0.014, RUG_Y - 0.002, z0, z1)
    bx(m, RUGM2, x1 - 0.22, x1, RUG_Y - 0.014, RUG_Y - 0.002, z0, z1)
    Y = RUG_Y + 0.006     # 0.104: clears the rug top and the slab offset
    for (cx, cz, hx, hz) in ((1.97, 15.20, 1.75, 4.65),    # sectional, west leg
                             (5.76, 21.84, 5.54, 1.49),    # sectional, south leg
                             (7.82, 16.05, 1.78, 2.00),    # ottoman
                             (14.35, 13.25, 1.45, 1.45),   # swivel chair
                             (14.45, 8.55, 1.45, 1.45)):
        cshadow(m, cx, cz, hx, hz, y=Y, strength=0.76, room=(W, D))
    return save_and_place("Movie Floor Rug", m, ROOM)


# =============================================================== sectional
def build_sectional():
    m = Model()
    rnd = Rnd(20260822)
    BASE_Y, SEAT_Y, ARM_Y, BACK_Y = 0.46, 1.46, 2.10, 2.78
    ARM_W = 0.42

    def run(x0, x1, z0, z1, facing, seats, arms=(True, True)):
        if facing == "e":
            back_x = x0 + 0.66
            ia = z0 + (ARM_W if arms[0] else 0.0)
            ib = z1 - (ARM_W if arms[1] else 0.0)
            slab(m, FAB_D, x0, x1 - 0.16, 0.05, BASE_Y, z0 + 0.05, z1 - 0.05)
            slab(m, FAB, x0, back_x, BASE_Y, BACK_Y - 0.44, z0, z1, r=0.06)
            slab(m, FAB_D, back_x, x1, BASE_Y, SEAT_Y - 0.26, ia, ib, r=0.06)
            for i in range(seats):
                a = ia + 0.05 + i * (ib - ia) / seats
                b = a + (ib - ia) / seats - 0.18
                slab(m, FAB, back_x + 0.04, x1 - 0.12, SEAT_Y - 0.30, SEAT_Y,
                     a, b, r=0.09)
                cush(m, BACKC, x0 + 0.10, back_x + 0.26, SEAT_Y - 0.10,
                     BACK_Y, a, b, r=0.17, nub=0.012, rnd=rnd)
            for k, on in enumerate(arms):
                if not on:
                    continue
                za, zb = (z0, z0 + ARM_W) if k == 0 else (z1 - ARM_W, z1)
                slab(m, FAB, x0, x1, BASE_Y, ARM_Y, za, zb, r=0.12)
                nailheads(m, STUD, (x1 - 0.01, za + 0.07), (x1 - 0.01, zb - 0.07),
                          ARM_Y - 0.20, 5)
            for cz in (z0 + 0.32, z1 - 0.32):
                for cx in (x0 + 0.34, x1 - 0.30):
                    leg(m, DKWOOD, cx, cz, 0.46, 0.16)
        else:
            back_z = z1 - 0.66
            ia = x0 + (ARM_W if arms[0] else 0.0)
            ib = x1 - (ARM_W if arms[1] else 0.0)
            slab(m, FAB_D, x0 + 0.05, x1 - 0.05, 0.05, BASE_Y, z0 + 0.16, z1)
            slab(m, FAB, x0, x1, BASE_Y, BACK_Y - 0.44, back_z, z1, r=0.06)
            slab(m, FAB_D, ia, ib, BASE_Y, SEAT_Y - 0.26, z0, back_z, r=0.06)
            for i in range(seats):
                a = ia + 0.05 + i * (ib - ia) / seats
                b = a + (ib - ia) / seats - 0.18
                slab(m, FAB, a, b, SEAT_Y - 0.30, SEAT_Y, z0 + 0.12,
                     back_z - 0.04, r=0.09)
                cush(m, BACKC, a, b, SEAT_Y - 0.10, BACK_Y,
                     back_z - 0.26, z1 - 0.10, r=0.17, nub=0.012, rnd=rnd)
            for k, on in enumerate(arms):
                if not on:
                    continue
                xa, xb = (x0, x0 + ARM_W) if k == 0 else (x1 - ARM_W, x1)
                slab(m, FAB, xa, xb, BASE_Y, ARM_Y, z0, z1, r=0.12)
                nailheads(m, STUD, (xa + 0.07, z0 + 0.01), (xb - 0.07, z0 + 0.01),
                          ARM_Y - 0.20, 5)
            for cx in (x0 + 0.32, x1 - 0.32):
                for cz in (z0 + 0.30, z1 - 0.34):
                    leg(m, DKWOOD, cx, cz, 0.46, 0.16)

    run(0.22, 3.72, 10.55, 19.85, "e", 3, arms=(True, False))
    run(0.22, 11.30, 20.35, 23.32, "n", 4, arms=(False, True))

    for cz, mat in ((11.45, GEO), (12.75, SLATE), (14.05, GEO),
                    (15.35, BOUCLE), (16.75, SLATE), (18.15, GEO)):
        cush(m, mat, 0.80, 1.36, 1.52, 2.44, cz - 0.48, cz + 0.48,
             r=0.20, nub=0.02, rnd=rnd)
    for cx, mat in ((2.20, SLATE), (4.40, GEO), (6.70, BOUCLE),
                    (8.90, GEO), (10.40, SLATE)):
        cush(m, mat, cx - 0.48, cx + 0.48, 1.52, 2.44, 22.18, 22.74,
             r=0.20, nub=0.02, rnd=rnd)

    # BLACK BOLSTERS lying flat along the tops of the backs -- the single most
    # conspicuous thing in the v3 photos and absent from every earlier round.
    for cz in (12.10, 14.05, 16.00, 17.95):
        cush(m, BLKPILL, 0.32, 1.14, BACK_Y - 0.06, BACK_Y + 0.62,
             cz - 0.78, cz + 0.78, r=0.24, nub=0.02, rnd=rnd)
    for cx in (2.55, 4.35, 8.30, 10.10):
        cush(m, BLKPILL, cx - 0.78, cx + 0.78, BACK_Y - 0.06, BACK_Y + 0.62,
             22.44, 23.26, r=0.24, nub=0.02, rnd=rnd)
    m.add(sag_plane(2.40, 3.30, 0.05, 9, 11, edge_drop=0.34), THROW,
          at=(1.70, BACK_Y + 0.30, 18.10))
    m.add(sag_plane(2.60, 2.20, 0.05, 9, 8, edge_drop=0.30), THROW,
          at=(6.30, BACK_Y + 0.28, 22.60))
    return save_and_place("Movie Sectional", fabricate(m), ROOM)


# ================================================================== ottoman
def build_ottoman():
    m = Model()
    x0, x1, z0, z1 = 6.05, 9.60, 14.05, 18.05
    slab(m, FAB_D, x0 + 0.06, x1 - 0.06, 0.42, 0.60, z0 + 0.06, z1 - 0.06, r=0.04)
    slab(m, FAB, x0, x1, 0.60, 1.26, z0, z1, r=0.10)
    slab(m, FAB, x0 + 0.05, x1 - 0.05, 1.26, 1.42, z0 + 0.05, z1 - 0.05, r=0.13)
    for cx in (x0 + 0.34, x1 - 0.34):
        for cz in (z0 + 0.34, z1 - 0.34):
            leg(m, DKWOOD, cx, cz, 0.42, 0.19, taper=0.55)
    TRAY = Material("m2tray", "#26272a", roughness=0.55)
    bx(m, TRAY, 7.05, 8.75, 1.42, 1.50, 15.35, 16.75)
    bx(m, TRAY, 7.05, 8.75, 1.42, 1.58, 15.35, 15.42)
    bx(m, TRAY, 7.05, 8.75, 1.42, 1.58, 16.68, 16.75)
    bx(m, Material("m2rem", "#45474a", roughness=0.5), 7.25, 7.45, 1.50, 1.56,
       15.55, 16.45)
    bx(m, Material("m2rem", "#45474a", roughness=0.5), 7.60, 7.80, 1.50, 1.56,
       15.60, 16.40)
    bx(m, Material("m2book", "#8e9ba1", roughness=0.9), 8.05, 8.62, 1.50, 1.62,
       15.60, 16.55)
    return save_and_place("Movie Ottoman", fabricate(m), ROOM)


def shell(m, mat, cx, cz, r, thick, a0, a1, y0, h0, h1, steps=30):
    """One smooth swept upholstered shell -- the wrap-around back of a barrel
    chair.  bkit.barrel() lays 26 separate boxes on the arc and they render as
    a fan of ribs (visible in every earlier round's render); this is a single
    surface: outer wall, inner wall and a rolled top, welded and smooth-shaded."""
    ro, ri = r + thick / 2, r - thick / 2
    vo, vi, vt = [], [], []
    for i in range(steps + 1):
        t = i / steps
        a = a0 + (a1 - a0) * t
        h = h0 + (h1 - h0) * math.sin(math.pi * t) ** 0.6
        ca, sa = math.cos(a), math.sin(a)
        vo += [(cx + ro * ca, y0, cz + ro * sa), (cx + ro * ca, y0 + h - 0.07, cz + ro * sa)]
        vi += [(cx + ri * ca, y0, cz + ri * sa), (cx + ri * ca, y0 + h - 0.07, cz + ri * sa)]
        vt += [(cx + ro * ca, y0 + h - 0.07, cz + ro * sa),
               (cx + (ro + ri) / 2 * ca, y0 + h, cz + (ro + ri) / 2 * sa),
               (cx + ri * ca, y0 + h - 0.07, cz + ri * sa)]
    def strip(v, n, cols):
        t = []
        for i in range(steps):
            for k in range(cols - 1):
                a = i * cols + k; b = a + 1; c = a + cols; d = c + 1
                t += [(a, c, b), (b, c, d)]
        return t
    m.add(Part(vo, strip(vo, steps, 2), smooth=True), mat)
    m.add(Part(vi, [(c, b, a) for (a, b, c) in strip(vi, steps, 2)], smooth=True), mat)
    m.add(Part(vt, strip(vt, steps, 3), smooth=True), mat)
    # end caps
    for i, sgn in ((0, 1), (steps, -1)):
        a = a0 + (a1 - a0) * (i / steps)
        h = h0 + (h1 - h0) * math.sin(math.pi * (i / steps)) ** 0.6
        ca, sa = math.cos(a), math.sin(a)
        p = [(cx + ro * ca, y0, cz + ro * sa), (cx + ri * ca, y0, cz + ri * sa),
             (cx + ri * ca, y0 + h - 0.07, cz + ri * sa),
             (cx + ro * ca, y0 + h - 0.07, cz + ro * sa)]
        tri = [(0, 1, 2), (0, 2, 3)] if sgn > 0 else [(0, 2, 1), (0, 3, 2)]
        m.add(Part(p, tri), mat)


# ============================================================ swivel chairs
def build_chairs():
    m = Model()
    rnd = Rnd(515)

    def chair(cx, cz, rot):
        sub = Model()
        seat_y = 1.46
        sub.add(cylinder(0.72, 0.13, 16), DKWOOD, at=(0, 0.0, 0))
        sub.add(cylinder(0.36, 0.24, 12), DKWOOD, at=(0, 0.13, 0))
        sub.add(puff(2.72, 1.14, 2.72, r=0.38), IVORY, at=(0, 0.30, 0.02))
        slab(sub, IVORY, -0.94, 0.94, seat_y - 0.30, seat_y, -0.70, 1.24, r=0.16)
        shell(sub, IVORY, 0.0, 0.0, 1.20, 0.62, R(163), R(377),
              seat_y - 0.34, 0.64, 1.42, steps=30)
        cush(sub, GEO, -0.60, 0.60, seat_y - 0.02, seat_y + 1.08,
             -0.72, -0.26, r=0.16, nub=0.02, rnd=rnd)
        ca, sa = math.cos(R(rot)), math.sin(R(rot))
        for part, mm in sub._parts:
            v = [(cx + x * ca + z * sa, y, cz - x * sa + z * ca)
                 for (x, y, z) in part.verts]
            m._parts.append((Part(v, part.tris, part.smooth,
                                  part.colors, part.uv), mm))

    chair(14.35, 13.25, 250)
    chair(14.45, 8.55, 292)
    return save_and_place("Movie Swivel Chairs", fabricate(m), ROOM)


# ===================================================================== art
def build_art():
    """Five-panel canvas print on the WEST wall, over the sectional's west leg
    and its corner -- photos 2 and 3 both put it between the west window and
    the SW corner."""
    m = Model()
    z0, z1 = 13.60, 21.10
    y0, y1 = 4.05, 6.55
    n, gap = 5, 0.13
    pw = (z1 - z0 - gap * (n - 1)) / n
    sub = Model()
    for i in range(n):
        a = (D - z1) + i * (pw + gap)
        bx(sub, BEZ, a, a + pw, y0, y1, 0.020, 0.095)
        u0, u1 = i / n, (i + 1) / n
        sub.add(Part([(a, y0, 0.100), (a + pw, y0, 0.100),
                      (a + pw, y1, 0.100), (a, y1, 0.100)],
                     [(0, 1, 2), (0, 2, 3)],
                     uv=[(u0, 1.0), (u1, 1.0), (u1, 0.0), (u0, 0.0)]), ARTM)
    blit2(m, sub, "w", W, D, 0.0)
    return save_and_place("Movie Art Panels", m, ROOM)


# ------------------------------------------------------------- small props
def _lamp(m, tx, tz, base=2.06):
    m.add(cylinder(0.30, 0.07, 14), LAMPBLK, at=(tx, base, tz))
    m.add(cylinder(0.055, 0.62, 8), LAMPBLK, at=(tx, base + 0.07, tz))
    m.add(cylinder(0.42, 0.52, 16, r_top=0.32), LAMPSHD, at=(tx, base + 0.66, tz))
    m.add(cylinder(0.30, 0.02, 14),
          Material("m2bulb", "#fff3dd", roughness=0.3, emissive="#fff0d2",
                   emissive_strength=3.0), at=(tx, base + 1.16, tz))


def _tiered_table(m, tx, tz, w=0.90, d=1.05):
    MET = Material("m2met", "#232427", roughness=0.45, metallic=0.4)
    for y in (0.42, 1.20, 1.94):
        bx(m, TBLWOOD if y > 1.5 else MET, tx - w / 2, tx + w / 2, y, y + 0.10,
           tz - d / 2, tz + d / 2)
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        ax = tx + dx * (w / 2 - 0.06)
        az = tz + dz * (d / 2 - 0.06)
        bx(m, MET, ax - 0.04, ax + 0.04, 0.0, 2.04, az - 0.04, az + 0.04)


def build_side():
    """West wall: tiered side table + black lamp, and the tall tower purifier."""
    m = Model()
    tx, tz = 1.28, 10.35
    cshadow(m, tx, tz, 0.45, 0.53, y=0.058, out=0.55, strength=0.66, room=(W, D))
    _tiered_table(m, tx, tz)
    _lamp(m, tx, tz)
    fx, fz = 0.92, 7.30
    cshadow(m, fx, fz, 0.52, 0.52, y=0.058, out=0.55, strength=0.66, room=(W, D))
    m.add(cylinder(0.52, 0.09, 18), FANW, at=(fx, 0.0, fz))
    m.add(cylinder(0.42, 1.05, 16, r_top=0.40), FANW, at=(fx, 0.09, fz))
    m.add(cylinder(0.40, 0.10, 16), Material("m2fan2", "#a9adb0", roughness=0.4,
                                             metallic=0.35), at=(fx, 1.14, fz))
    m.add(rounded_box(0.62, 2.20, 0.36, r=0.17, seg=4), FANW, at=(fx, 1.24, fz))
    m.add(rounded_box(0.34, 1.72, 0.16, r=0.08, seg=3),
          Material("m2fan3", "#c2c6c8", roughness=0.35), at=(fx, 1.48, fz - 0.02))
    return save_and_place("Movie Side Table", m, ROOM)


def build_corner():
    """South wall, east end: black cabinet, the bladeless ring fan, a small
    cart and a second side table + lamp."""
    m = Model()
    cx0, cx1 = 11.60, 13.45
    cshadow(m, (cx0 + cx1) / 2, 22.55, 0.93, 0.79, y=0.058, out=0.6, strength=0.72, room=(W, D))
    bx(m, BOXBLK, cx0, cx1, 0.0, 2.28, 21.75, 23.32)
    bx(m, BEZ, cx0 + 0.06, cx1 - 0.06, 0.12, 2.16, 21.72, 21.75)
    bx(m, Material("m2cabtop", "#1b1c1f", roughness=0.35),
       cx0 - 0.05, cx1 + 0.05, 2.28, 2.36, 21.70, 23.34)
    fx, fz = 10.55, 22.75
    cshadow(m, fx, fz, 0.44, 0.44, y=0.058, out=0.55, strength=0.66, room=(W, D))
    m.add(cylinder(0.44, 0.07, 16), FANW, at=(fx, 0.0, fz))
    m.add(cylinder(0.21, 1.30, 12, r_top=0.19), FANW, at=(fx, 0.07, fz))
    m.add(torus(0.56, 0.085, 24, 8), FANW, at=(fx, 2.12, fz),
          rot_x=R(90), scale=(0.90, 1.0, 1.32))
    _tiered_table(m, 9.55, 22.72, w=0.80, d=0.90)
    tx, tz = 12.05, 20.55
    cshadow(m, tx, tz, 0.45, 0.53, y=0.104, out=0.55, strength=0.66, room=(W, D))
    _tiered_table(m, tx, tz)
    _lamp(m, tx, tz)
    return save_and_place("Movie Corner Props", m, ROOM)


BUILD = [build_skins, build_ceiling, build_floor, build_trim, build_screen, build_console,
         build_stairwall, build_stairrail, build_rug, build_sectional,
         build_ottoman, build_chairs, build_art, build_side, build_corner]

if __name__ == "__main__":
    print("room 1 Movie Room  (probe=%s)" % (PV or "no"))
    surfaces(ROOM, wall_color="#dcdbd8", floor_color="#5b5d61",
             floor_texture="wood")
    if "--skins-only" in sys.argv:
        out = build_skins()
    else:
        openings()
        out = []
        for fn in BUILD:
            r = fn()
            out += r if isinstance(r, list) else [r]
    print("total %.1f KB" % sum(p["kb"] for p in out))
