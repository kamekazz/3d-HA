"""Room 17 (2F Hallway) -- ROUND 3: FLOOR, WALLS, CEILING.

Answering the four blind round-2 verdicts, whose #1 complaint was that no
surface in the room has any texture, so everything reads as flat tinted
plastic.  Scope is exactly four things:

    Hall2F Floor Planks      -> a glossy WEAR LAYER over the app's own tiled
                                wood slab, instead of an opaque plank deck
    Hall2F Wall Wash Skins   -> the same displaced skins, now carrying a BAKED
                                LIGHT FALLOFF as vertex colour (non-emissive)
    Hall2F Ceiling           -> tone from banded emissive pools, not one flat
                                emissive plane that meters sd 0.00
    room 17 wall_color / floor_color

Nothing else is touched: Doors, Baseboards, Floor Runner, Knee Wall, Plants,
Wall Art, Wall Fittings, every stair piece, every opening and the footprint all
belong to other builders working concurrently.

    python r3.py            # all four
    python r3.py floor      # one piece

------------------------------------------------------------------ the levers
`roomkit.glb` has no image-texture API, so "texture" for a GLB piece means
geometry plus per-vertex tone.  Round 3 adds `Part(colors=...)` to the exporter
(glTF COLOR_0), which is the only way to put a SMOOTH gradient on a surface
inside the payload budget: 4 bytes per already-shared vertex, against the ~24
bytes per DUPLICATED vertex that splitting the same field into per-cell
material buckets costs.  The wall skins carry ~4000 vertices; as material
buckets a 2-D tone field on them would have cost ~250 KB, as vertex colour it
costs 16.

The other lever the round-2 floor never used is `roughness`.  The floor was
0.90, which cannot catch a highlight at all; scene.js builds a PMREM
RoomEnvironment IBL, so a low-roughness surface picks up a real, view-dependent
specular sheen -- brightest at grazing angles, i.e. running away down the hall,
which is exactly the cue a critic said carries the hall's length.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "circ"))

from ckit import *                                            # noqa: F401,F403
from roomkit.glb import Part                                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOM, W, D, H = 17, 8.1, 16.7, 8.0
KX, KZ = 3.95, 7.7                      # the stairwell notch: x>=KX, z>=KZ

# where each wall's VISIBLE face is -- house.js extrudes walls OUTWARD, so on a
# party wall the NEIGHBOUR's 0.35 ft slab is the surface the camera sees inside
# room 17.  Copied verbatim from build.py, which measured it off /api/house.
FACE = {"n": 0.05, "e": 0.35, "s": 0.25}
W_STEP = 10.70                          # west wall: room 13's slab ends here


def save_and_place(name, m, room=ROOM, fname=None):
    path = os.path.join(HERE, "glb",
                        (fname or name.replace(" ", "_").lower()) + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    from roomkit.place import place
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    print(f"  {name:26s} size={tuple(round(hi[i]-lo[i],2) for i in range(3))}"
          f"  {kb:7.1f} KB  {res['action']}")
    return kb


# ===================================================================== FLOOR
#
# WHY THE PLANK DECK IS GONE.  Round 2's floor was an opaque GLB deck: 7 plank
# columns, one flat tone each out of an 8-swatch palette, roughness 0.90, with
# a 0.024 ft gap round every board that showed the dark slab through it.  All
# four critics read it as flat plastic and one read the butt-lines as UV seams.
#
# Measured against `docs/photos-jpg/Second-floor hallway.jpg` (1200x1600, clean
# object-free patches, native resolution):
#
#     surface                     mean     sd   mean|d1|   |d1|/sd
#     photo, foreground floor    105.3  14.36     4.47      0.378
#     photo, left of the runner  116.2  11.04     5.70      0.516
#     round-2 render, same spot  ~151   (mostly the plank-gap seams)  0.05
#
# |d1| = 4.5-5.7 is grain at a 1-2 px scale on screen.  Vertex colour cannot
# reach it: at 75 px/ft in the foreground it needs tone every ~0.02 ft, i.e.
# ~170k vertices over this floor, ~9 MB.  An IMAGE MAP can, and the app already
# has one -- room 17 is already set to `floor_texture: 'wood'`, 4 planks per
# 2.2 ft tile (0.55 ft boards, which is the photo's board width), and the deck
# was simply covering it up.
#
# So the slab does the grain and this piece becomes the WEAR LAYER a real vinyl
# plank floor actually has: a thin, low-roughness, semi-transparent sheet over
# the slab.  You see the tiled grain through it; it adds the broad specular
# sheen (Fresnel makes that strongest at grazing angles, so it runs away down
# the hall the way the photo's does) and carries per-plank tone variation and
# soft joint shading as vertex colour.  Cost: ~20 KB against the deck's 15.8,
# and it does not have to fight the texture -- its tone bands are pitched at
# 0.55 ft so they land exactly on the texture's own boards.
FLOOR_Y = 0.020                         # over the slab (y 0.01), under the
                                        # runner (0.056) and every contact decal
PLANK = 0.55                            # = textures.js wood size 2.2 / 4 boards
NSEG = 6                                # grain lanes across one board
RIDGE = 0.0105                          # embossed grain relief, ft
GLOSS = Material("h17gloss", "#8e8b85", roughness=0.20, metallic=0.0,
                 opacity=0.40, double_sided=False)
# the bullnose along the two cut edges over the stairwell is the one part of
# the old deck worth keeping -- without it the slab ends in a raw sawn line
EDGEBD = Material("h17edge", "#4f4e4a", roughness=0.45)


def piece_floor():
    """The glossy wear layer, laid board by board over the textured slab.

    Each board is a strip NSEG lanes wide.  A lane is a GRAIN STREAK: it holds
    its own tone for the whole length of the board and drifts slowly along it,
    which is what wood grain looks like and what a flat-tone deck cannot do.
    The lanes are also embossed a millimetre, so at roughness 0.20 the specular
    sheen breaks up along them instead of sitting on the floor as one sheet.

    Board ends are placed at random and are two rows 0.06 ft apart carrying a
    darker tone, so a butt joint is a soft graded line, not the hard black gap
    a critic read as a UV seam.
    """
    m = Model()
    rn = Rnd(4407)
    for (ax0, ax1, zmax) in ((0.00, KX, D), (KX, W, KZ)):
        ncol = int(round((ax1 - ax0) / PLANK))
        pw = (ax1 - ax0) / ncol
        for c in range(ncol):
            x0 = ax0 + c * pw
            board = 0.968 + 0.028 * rn.f(-1.0, 1.0)
            # ALTERNATING lane tones, not just random ones.  The photo's floor
            # meters |d1|/sd 0.38-0.52 near the camera and this piece was
            # sitting at 0.13: the shortfall is not how MUCH tone there is (sd
            # already matched) but how FINE it is, so neighbouring lanes are
            # pushed apart deliberately, which puts every step at the 0.09 ft
            # lane pitch instead of at the 0.56 ft board pitch.
            lane = [0.972 + (0.058 if i % 2 else -0.058) * rn.f(0.45, 1.0)
                    for i in range(NSEG + 1)]
            lane[0] = lane[NSEG] = 0.912          # the board's own long edges
            ph = rn.f(0.0, 6.283)

            # rows: a regular ladder plus a doubled pair at every board end
            rows = [zmax * k / max(4, int(round(zmax / 0.85)))
                    for k in range(max(4, int(round(zmax / 0.85))) + 1)]
            joints = []
            z = rn.f(1.2, 4.0)
            while z < zmax - 1.0:
                joints += [z - 0.03, z + 0.03]
                z += rn.f(3.0, 6.4)
            rows = sorted(set(rows + joints))

            verts, cols, tris = [], [], []
            for v in rows:
                near_joint = any(abs(v - jz) < 0.05 for jz in joints)
                # broad sheen: the photo's floor runs ~105 in the foreground
                # and 116-135 at mid-distance, where the cans are.  A critic
                # named that gradient as most of what tells you the hall is long
                sheen = 0.055 * math.exp(-((v - 8.4) / 6.4) ** 2)
                drift = 0.024 * math.sin(v / 1.31 + ph)
                for i in range(NSEG + 1):
                    x = x0 + pw * i / NSEG
                    s = board * lane[i] * (1.0 + drift + sheen
                                           + 0.020 * math.sin(v / 0.41 + i * 2.3 + ph))
                    if near_joint:
                        s *= 0.86
                    y = FLOOR_Y + RIDGE * math.sin(math.pi * i / NSEG * 2.0 + ph)
                    verts.append((x, y, v))
                    cols.append((s, s * 0.995, s * 0.99))
            n = NSEG + 1
            for j in range(len(rows) - 1):
                for i in range(NSEG):
                    a = j * n + i
                    tris += [(a, a + n, a + 1), (a + 1, a + n, a + n + 1)]
            m.add(Part(verts, tris, smooth=True, colors=cols), GLOSS)
    # bullnose on the two edges that face the void
    bx(m, EDGEBD, KX, W, -0.075, 0.022, KZ - 0.08, KZ + 0.02)
    bx(m, EDGEBD, KX - 0.08, KX + 0.02, -0.075, 0.022, KZ - 0.08, D)
    return m


# ===================================================================== WALLS
#
# Same construction as round 2 -- a shallow displaced, smooth-shaded grid over
# each wall's VISIBLE face, one plain non-emissive colour per wall -- with the
# one thing round 2 had no way to add: a BAKED LIGHT FALLOFF, as vertex colour.
#
# Metered off the photo, the east wall runs 176 at the ceiling line down to 118
# at the skirting -- a 58-level ramp -- and the whole plane meters sd 16.51 with
# mean|d1| 0.47 (ratio 0.028: a painted wall has almost no FINE texture, it is
# nearly all broad gradient).  Round 2's skins metered sd 3.45-8.16, which is
# the 2-4x flatness the brief calls out; the gap is entirely in the gradient,
# so that is what this bakes:
#
#   * a vertical ramp, bright at the ceiling and falling to the skirting;
#   * a pool under every ceiling can and the drum, strongest on the wall the
#     fixture is nearest and dying off with its distance from that wall;
#   * corner darkening at both ends of each run and along the floor line, so
#     the wall/wall and wall/floor junctions are gradients, not steps;
#   * a little low-frequency mottle so the field is not algebraically smooth.
#
# NON-EMISSIVE, deliberately: emissive wall washes have been rejected twice in
# this repo and read as glowing panels.  This is albedo -- exactly what paint
# under a light does.
# Base albedos, re-fitted from a real render after the falloff went in.  Each
# wall's response was measured by probe.py as value = k * albedo**g, with
# g = 0.727 (n) / 1.586 (s) / 1.025 (w) / 1.483 (e), and these invert that onto
# the round-2 targets (n 165, s 165, e 158, w 175) taken off the photo.  The
# SOUTH wall cannot reach 165: it is already at pure white and lands at ~153,
# which is still inside the photo's own 139-176 wall spread, so it is left there
# rather than compensated with emissive.
SKINS = {"n": "#7e7e7e", "s": "#ffffff", "e": "#eaeaea", "w": "#d0d0d0"}

CELL = 0.30
AMP = (0.012, 0.013, 0.008, 0.004, 0.003)
LAM = (1.02, 0.48, 0.235, 0.137, 0.113)
INSET = 0.072
BOT = BB_H - 0.02
TOP = H - 0.05

# ceiling fixtures, room-local (x, z) -- must track build.py's CANS/DRUM
FIXTURES = [(2.05, 4.55), (5.85, 4.40), (6.15, 9.60), (1.95, 14.35),
            (1.95, 10.80)]

# Shape of the vertical ramp.  The response measured by probe.py is roughly
# value ~ albedo**0.73, so a rendered ratio r needs an albedo ratio r**(1/0.73);
# the photo's east wall runs 176 at the ceiling to 118 at the skirting, i.e.
# 0.67 rendered -> 0.58 albedo.  A first pass ran the whole field over
# 0.40-1.00 and metered sd 25-31 against the photo's 16.5-20.6 -- overshooting
# is not closer (ROOM-BRIEF), so the field is pulled back to ~0.63-1.00 total.
RAMP_BOT, RAMP_TOP = 0.745, 1.055
POOL_AMP = 0.075                        # brightening under a ceiling fixture
CORNER_DK, FLOOR_DK = 0.080, 0.060      # junction gradients


def _tone_field(wall, a, y, a0, a1, c0, c1):
    """Multiplicative albedo field on one wall, before renormalisation.

    `a0..a1` is the span being built; `c0..c1` are the run's REAL ends.  The
    west wall is built as two spans because room 13's slab steps out of it at
    z 10.70, and taking the corner shading off the span ends instead of the
    wall ends painted a dark band down the middle of it.
    """
    t = (y - BOT) / (TOP - BOT)
    g = RAMP_BOT + (RAMP_TOP - RAMP_BOT) * (t ** 0.80)

    # pools under the ceiling fixtures.  `a` is the coordinate along the wall
    # run; each fixture projects onto it, and how much of its pool lands on
    # this wall falls off with how far the fixture is from the wall plane.
    for (fx, fz) in FIXTURES:
        if wall == "n":
            along, perp = fx, fz
        elif wall == "s":
            along, perp = KX - fx, D - fz
        elif wall == "w":
            along, perp = D - fz, fx
        else:
            along, perp = fz, W - fx
        if not (a0 - 2.6 <= along <= a1 + 2.6):
            continue
        g += (POOL_AMP * math.exp(-((a - along) / 1.75) ** 2)
              * math.exp(-((H - y) / 2.30) ** 2)
              / (1.0 + (perp / 1.9) ** 2))

    # corner + floor-line darkening: a junction in the photo is a gradient
    de = min(a - c0, c1 - a)
    g *= 1.0 - CORNER_DK * math.exp(-(de / 0.55) ** 1.4)
    g *= 1.0 - FLOOR_DK * math.exp(-((y - BOT) / 0.75) ** 1.4)

    # broad mottle -- paint under a raking light is never algebraically flat
    g *= 1.0 + 0.022 * math.sin(a / 1.7 + 1.3) * math.sin(y / 1.1 + 0.4) \
        + 0.014 * math.sin(a / 0.63 + 2.7)
    return g


def _skinmat(c):
    return Material("h17s3" + c.lstrip("#"), c, roughness=0.95, metallic=0.0)


def skin_wall(m, wall, a0, a1, color, holes=(), seed=11, face=0.0, ends=None):
    c0, c1 = ends or (a0, a1)
    na = max(2, int(round((a1 - a0) / CELL)))
    ny = max(2, int(round((TOP - BOT) / CELL)))
    rn = Rnd(seed)
    ph = [rn.f(0, 6.283) for _ in range(8)]

    def disp(a, y):
        return (AMP[0] * math.sin(a / LAM[0] + ph[0]) * math.sin(y / (LAM[0] * .85) + ph[1])
                + AMP[1] * math.sin(a / LAM[1] + ph[2]) * math.sin(y / (LAM[1] * 1.3) + ph[3])
                + AMP[2] * math.sin(a / LAM[2] + ph[4]) * math.sin(y / (LAM[2] * .82) + ph[5])
                + AMP[3] * math.sin(a / LAM[3] + ph[6] + y * 2.1)
                + AMP[4] * math.sin(y / LAM[4] + ph[7] + a * 1.7))

    def hidden(a, y):
        for (ha0, ha1, hy0, hy1) in holes:
            if ha0 <= a <= ha1 and hy0 <= y <= hy1:
                return True
        return False

    verts, cols, raw = [], [], []
    for j in range(ny + 1):
        y = BOT + (TOP - BOT) * j / ny
        for i in range(na + 1):
            a = a0 + (a1 - a0) * i / na
            d = face + INSET + disp(a, y)
            if wall == "n":
                verts.append((a, y, d))
            elif wall == "s":
                verts.append((a, y, D - d))
            elif wall == "w":
                verts.append((d, y, a))
            else:
                verts.append((W - d, y, a))
            raw.append(_tone_field(wall, a, y, a0, a1, c0, c1))
    # Normalise so the BRIGHTEST point of the field is 1.0.  Normalising to
    # mean 1.0 instead needs clipping wherever the pools push past white, and
    # clipping flattens exactly the part of the wall the falloff is for.  The
    # mean each wall then lands at is whatever this scaling gives, so the base
    # albedos below are re-fitted from a real render, not assumed.
    k = 1.0 / max(raw)
    for g in raw:
        s = g * k
        cols.append((s, s, s))

    tris = []
    for j in range(ny):
        yA = BOT + (TOP - BOT) * (j + 0.5) / ny
        for i in range(na):
            aA = a0 + (a1 - a0) * (i + 0.5) / na
            if hidden(aA, yA):
                continue
            p = j * (na + 1) + i
            q, r_, s_ = p + 1, p + na + 1, p + na + 2
            if wall in ("n", "e"):          # faces +z / -x, i.e. into the room
                tris += [(p, q, r_), (q, s_, r_)]
            else:
                tris += [(p, r_, q), (q, r_, s_)]
    m.add(Part(verts, tris, smooth=True, colors=cols), _skinmat(color))


EDGE_WALL = {0: ("n", False), 1: ("e", False), 4: ("s", True), 5: ("w", True)}


def live_holes(margin=0.36):
    """Read room 17's openings from the app -- hard-coding them went stale
    inside one build the last time a parallel builder re-cut the west wall."""
    holes = {"n": [], "e": [], "s": [], "w": []}
    for o in room_row(ROOM).get("openings", []):
        ew = EDGE_WALL.get(o["edge_index"])
        if not ew:
            continue
        wall, rev = ew
        total = {"n": W, "e": KZ, "s": KX, "w": D}[wall]
        a0, a1 = o["offset"], o["offset"] + o["width"]
        if rev:
            a0, a1 = total - a1, total - a0
        holes[wall].append((a0 - margin, a1 + margin, 0.0,
                            o["elevation"] + o["height"] + margin))
    return holes


def piece_skins(colors=None):
    colors = colors or SKINS
    m = Model()
    hl = live_holes()
    skin_wall(m, "n", 0.02, W - 0.02, colors["n"], hl["n"], 11, FACE["n"])
    skin_wall(m, "e", 0.02, KZ - 0.02, colors["e"], hl["e"], 23, FACE["e"])
    skin_wall(m, "s", 0.02, KX - 0.02, colors["s"], hl["s"], 37, FACE["s"])
    # the west wall steps: room 13's slab juts 0.35 ft in as far as z=10.70.
    # The step falls INSIDE the guest doorway's hole, so no seam shows -- but
    # both spans must shade their corners against the WHOLE run's ends.
    ends = (0.02, D - 0.02)
    skin_wall(m, "w", 0.02, W_STEP, colors["w"], hl["w"], 53, 0.35, ends)
    skin_wall(m, "w", W_STEP, D - 0.02, colors["w"], hl["w"], 59, 0.0, ends)
    return m


# =================================================================== CEILING
#
# The round-2 ceiling metered sd 0.00 -- algebraically perfect paint -- because
# it is a single EMISSIVE plane, and emissive is normal-independent, so no
# amount of relief can shade it.  Nor can vertex colour: COLOR_0 multiplies
# baseColor, not emissiveFactor.
#
# The first fix tried was a stack of emissive levels -- one material per tone
# band, cells bucketed into them.  At six levels it rendered as a literal
# contour map (flat terraces, staircase edges, worse than the flat plane), and
# at twenty the terraces were still legible, because the eye locks onto a
# straight boundary long after it stops seeing the step across it.  Banding is
# the wrong tool for a smooth wash.
#
# What actually works came out of a four-point probe of the ceiling plane
# (`probe/ct_*.png`):
#
#     emissive   albedo    renders
#     none       #ffffff      96.1     <- so it is NOT unlit; there is IBL here
#     none       #808080      25.9
#     #5c5c5c    #ffffff     148.4
#     #5c5c5c    #333333     102.1
#
# A downward face in this scene collects plenty; the reason the ceiling had to
# be emissive was only that albedo alone tops out at 96 against the photo's
# 148.  Keep the emissive as the FLOOR of the value, and the albedo -- the one
# thing COLOR_0 multiplies -- then swings the ceiling over a ~46 level range on
# top of it.  So the whole ceiling is ONE material with a smooth per-vertex
# field: no bands, no terraces, and ~1/50th of the banded version's weight.
CEILM = Material("h17ceil3", "#ffffff", roughness=0.95, emissive="#5c5c5c",
                 double_sided=False)
CEIL_DIM = 0.80                         # vertex colour in the dimmest corner
DRUMBODY = Material("h17drum", "#f6f5f3", roughness=0.45)
CANS = [(2.05, 4.55), (5.85, 4.40), (6.15, 9.60), (1.95, 14.35)]
DRUM = (1.95, 10.80, 0.46)


def _ceil_lit(x, z):
    """Vertex colour on the ceiling: 1.0 under a fixture, CEIL_DIM in a corner."""
    lit = 0.0
    for (fx, fz) in FIXTURES:
        lit = max(lit, math.exp(-(((x - fx) ** 2 + (z - fz) ** 2) / (2 * 2.35 ** 2))))
    # the corners of a hallway ceiling never get a fixture's full cone
    edge = min(x, W - x, z, D - z)
    lit *= 0.55 + 0.45 * min(1.0, edge / 1.5)
    lit += 0.05 * math.sin(x / 1.4 + 0.7) * math.sin(z / 2.1 + 1.9)
    return CEIL_DIM + (1.0 - CEIL_DIM) * max(0.0, min(1.0, lit))


def piece_ceiling():
    """The ceiling DOES continue over the stairwell in every photo (the lid is
    8 ft above THIS slab and the void is below it), so it covers the full rect;
    only the FLOOR has the L cut out of it."""
    m = Model()
    Y = H - 0.01
    step = 0.62
    nx, nz = int(round(W / step)), int(round(D / step))
    verts, cols, tris = [], [], []
    for j in range(nz + 1):
        z = D * j / nz
        for i in range(nx + 1):
            x = W * i / nx
            verts.append((x, Y, z))
            s = _ceil_lit(x, z)
            cols.append((s, s, s))
    for j in range(nz):
        for i in range(nx):
            p = j * (nx + 1) + i
            q, r_, s_ = p + 1, p + nx + 1, p + nx + 2
            # wound to face DOWN, into the room (invisible from the plan pose)
            tris += [(p, q, s_), (p, s_, r_)]
    m.add(Part(verts, tris, smooth=True, colors=cols), CEILM)

    for (cx, cz) in CANS:
        ring_down(m, CEIL_FLAT, cx, cz, Y - 0.022, 0.255, 0.345)
        ring_down(m, CAN_CONE, cx, cz, Y - 0.070, 0.215, 0.258)
        disc_down(m, LENS, cx, cz, Y - 0.092, 0.222)
    cx, cz, r = DRUM
    m.add(cylinder(r * 0.74, 0.155, 20), DRUMBODY, at=(cx, Y - 0.155, cz))
    ring_down(m, CEIL_FLAT, cx, cz, Y - 0.012, r * 0.70, r * 1.02)
    ring_down(m, CEIL_FLAT, cx, cz, Y - 0.158, r * 0.60, r * 0.76)
    disc_down(m, LENS, cx, cz, Y - 0.168, r * 0.62)
    return m


# ====================================================================== main
PIECES = {
    "floor":   ("Hall2F Floor Planks", piece_floor),
    "skins":   ("Hall2F Wall Wash Skins", piece_skins),
    "ceiling": ("Hall2F Ceiling", piece_ceiling),
}

WALL_COLOR = "#cfd1d2"
FLOOR_COLOR = "#504f4b"


def main(only=None):
    tot = 0.0
    if only in (None, "surf"):
        surfaces(ROOM, wall_color=WALL_COLOR, floor_color=FLOOR_COLOR,
                 floor_texture="wood")
    for k, (name, fn) in PIECES.items():
        if only in (None, k):
            tot += save_and_place(name, fn())
    if tot:
        print(f"  -- {tot:.1f} KB written")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
