"""Room 17 (2F Hallway) -- SURFACES + SOFT GOODS rebuild (v2).

Scope, and ONLY this scope:
    Hall2F Floor Runner      chunky cream knit runner  (was a striped ladder)
    Hall2F Ceiling           recessed cans + one surface-mount drum
    Hall2F Wall Art          the welded stick sculpture, WEST wall
    Hall2F Plants            two snake plants
    Hall2F Wall Wash Skins   per-wall NON-emissive albedo skins, now with relief
    Hall2F Wall Fittings     switch plate, outlet + purple night light, return grille
    room 17 wall_color

NOT touched: any opening, Baseboards, Floor Planks, Knee Wall, floor_color,
the footprint, any other room.

The footprint is an L:
    [[0,0],[8.1,0],[8.1,7.7],[3.95,7.7],[3.95,16.7],[0,16.7]]
so the EAST wall exists only over z 0..7.7 and the SOUTH wall only over
x 0..3.95.  Every edge-to-edge run below is clipped to that.

    python build.py            # everything
    python build.py runner     # one piece
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "circ"))

from ckit import *                                            # noqa: F401,F403
from ckit import save_and_place as _sap, blit
from roomkit.glb import Part

HERE = os.path.dirname(os.path.abspath(__file__))
ROOM, W, D, H = 17, 8.1, 16.7, 8.0

# the L: the stairwell notch is x >= KX, z >= KZ
KX, KZ = 3.95, 7.7

# openings (local, from BRIEF.md) -- read only, used to punch the skins
MBED = (4.05, 6.95)          # north wall, local x
GUEST = (7.95, 10.68)        # west wall, local z
WDOOR = (11.90, 14.60)       # west wall, local z
BATH = (0.90, 3.70)          # south wall, local x
PASS_TOP = 7.00
LEAF_TOP = 6.78

# ---------------------------------------------------------------------------
# WHERE EACH WALL'S VISIBLE FACE ACTUALLY IS.
#
# house.js extrudes every wall OUTWARD from its own room's footprint line, so on
# a party wall the NEIGHBOUR's 0.35 ft slab lands INSIDE room 17 and is what the
# camera sees.  Measured off /api/house (level 2 rects):
#     room 13 Guest    x -1.90..10.50  z  6.50..17.30 -> its east slab fills
#                      room 17 local x 0.00..0.35 over local z -0.10..10.70
#     room 14 Master   z -12.38.. 6.30                -> local z -0.30.. 0.05
#     room 16 M.Bath   x 18.60..33.40 z -0.30..12.40  -> local x  7.75.. 8.10
#     room 26 bath     z 23.40..32.10                 -> local z 16.45..16.80
# Anything authored against the footprint line therefore renders INSIDE the
# neighbour's slab and vanishes.  That is why round 1's sculpture was invisible
# and why the previous round's skins metered as if they were not there: on three
# of the four walls they were not.  Every wall-mounted piece below is offset by
# the value here instead.
FACE = {"n": 0.05, "e": 0.35, "s": 0.25}
W_STEP = 10.70               # west wall: room 13's slab ends here


def wface(z):
    """The visible west-wall face at local z."""
    return 0.35 if z < W_STEP else 0.0


def save_and_place(name, m, room=ROOM, fname=None):
    """ckit.save_and_place, but writing into scratchpad/hall2/glb."""
    path = os.path.join(HERE, "glb",
                        (fname or name.replace(" ", "_").lower()) + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    from roomkit.place import place
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=1.0)
    size = tuple(round(hi[i] - lo[i], 3) for i in range(3))
    kb = os.path.getsize(path) / 1024.0
    print(f"  {name:26s} size={size}  pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f})"
          f"  {kb:7.1f} KB  {res['action']}")
    return kb


# ====================================================================== 1
# THE RUNNER.  The old piece was full-width cylinders on a white slab, 0.26 ft
# apart -- lit from above they read as a piano keyboard.  The photo
# ('Second-floor hallway.jpg', crops/runner_near.png) is a chunky garter-stitch
# wool runner: ropes running ACROSS the width at ~1.85 in pitch, each rope
# beaded along its length, no gaps between ropes and no dark line anywhere, and
# a fat plaited rope round the whole perimeter.
#
# Built as ONE smooth-shaded height field so adjacent ropes SHARE vertices --
# there is no gap for a shadow to fall into, which is the entire failure of the
# old piece.  A height field is also the cheapest way to buy fine-scale
# gradient: 5880 shared verts for 11310 triangles.
RUG_X0, RUG_X1 = 0.72, 3.22          # 2.50 ft wide, centred in the 3.95 strip
RUG_Z0, RUG_Z1 = 3.60, 13.60         # 10.0 ft long
RUG_Y = 0.056                        # over Floor Planks (0.014) and the shadow

# WHY THIS IS NOT A GRID.  Three rounds of this piece failed the same way, each
# time from REGULARITY, not from the wrong tone:
#   r1  full-width cylinders over a slab      -> a piano keyboard
#   r2  light/dark pair across straight ropes -> painted grey stripes
#   r3  a basketweave on a straight lattice   -> a white floor GRATE from the
#       dollhouse pose, which is the pose this app actually presents
# The photo ('hallway_with_white_runner_rug.jpg') is a soft mass of one tone:
# fat woolly loops, rounded, irregular, NO straight line anywhere and no
# continuous rib crossing the full width.  So the surface is now a quasi-
# periodic sum of five waves running in five different directions -- their
# periods are mutually irrational, so nothing ever lines up into a rib -- and
# the three tones are picked from the resulting HEIGHT, which makes them blobs
# that follow the wool rather than cells that follow the mesh.  Contrast is
# deliberately low (18 levels top to bottom, against r3's 40).
#
# Tone values solved from the measured response on this surface (albedo 186 ->
# 220, albedo 159 -> 195), targeting 190 / 181 / 172 -- an 18-level total
# range, against r3's 40 -- so the piece means ~181, the photo's own value.
WOOL = Material("h17wool2", "#9d9990", roughness=0.97, metallic=0.0)
WOOL_M = Material("h17woolm", "#928f8a", roughness=0.97, metallic=0.0)
WOOL_D = Material("h17woold", "#858280", roughness=0.97, metallic=0.0)

# (weight, period ft, direction) -- periods share no common factor, so the
# pattern never repeats inside the rug.  The two near-transverse waves carry
# most of the weight, which keeps the knit's row DIRECTION readable without
# ever producing an actual straight row.
WAVES = (
    (1.00, 0.181, (0.11, 1.00)),
    (0.82, 0.223, (-0.17, 1.00)),
    (0.55, 0.267, (1.00, 0.21)),
    (0.38, 0.331, (0.74, 0.67)),
    (0.30, 0.409, (-0.63, 0.78)),
)


def piece_runner():
    m = Model()
    cx, cz = (RUG_X0 + RUG_X1) / 2, (RUG_Z0 + RUG_Z1) / 2
    contact_shadow(m, cx, cz, (RUG_X1 - RUG_X0) / 2 + 0.62,
                   (RUG_Z1 - RUG_Z0) / 2 + 0.62, y=0.050, strength=0.30,
                   room=(W, D))

    nx, nz = 18, 136                 # 0.1389 x 0.0735 ft cells
    lw, ld = RUG_X1 - RUG_X0, RUG_Z1 - RUG_Z0
    A_ROW = 0.062                    # loop height, crest to trough
    T0 = 0.030
    BW = 0.17                        # the selvedge, deliberately narrow now:
    A_BORD = 0.050                   # a wide plain frame read as a grille bezel

    rn = Rnd(9317)
    wv = []
    for (wgt, per, (dx, dz)) in WAVES:
        n = math.hypot(dx, dz)
        wv.append((wgt, 2 * math.pi / per, dx / n, dz / n, rn.f(0, 6.283)))
    wsum = sum(w[0] for w in wv)

    def wool(u, v):
        """0..1 quasi-periodic woolly field -- five waves, five directions."""
        t = 0.0
        for (wgt, k, dx, dz, ph) in wv:
            t += wgt * (0.5 + 0.5 * math.cos(k * (u * dx + v * dz) + ph))
        return t / wsum

    def height(u, v):
        d = min(u, lw - u, v, ld - v)
        h = T0 + A_ROW * wool(u, v)
        if d < BW:                                  # rolled selvedge
            s = max(0.0, min(1.0, d / BW))
            h += A_BORD * max(0.0, math.sin(math.pi * s)) ** 0.7
        return h * min(1.0, d / 0.050) ** 0.85

    verts = []
    for j in range(nz + 1):
        v = ld * j / nz
        for i in range(nx + 1):
            u = lw * i / nx
            verts.append((RUG_X0 + u, RUG_Y + height(u, v), RUG_Z0 + v))

    # Tone follows the WOOL, not the mesh: three bands of the same field that
    # makes the bumps, so a light patch is a raised loop and a darker one is the
    # dip beside it.  Blobby, so the tone edges are not cell edges.
    def tone(u, v):
        t = wool(u, v)
        return 0 if t > 0.615 else (1 if t > 0.335 else 2)

    buckets = [[], [], []]
    for j in range(nz):
        v = ld * (j + 0.5) / nz
        for i in range(nx):
            u = lw * (i + 0.5) / nx
            a = j * (nx + 1) + i
            b, c, e = a + 1, a + nx + 1, a + nx + 2
            # alternate the split diagonal, or every cell shares one and the
            # whole field picks up a directional grain (the Living Room lesson)
            if (i + j) % 2:
                buckets[tone(u, v)] += [(a, c, b), (b, c, e)]
            else:
                buckets[tone(u, v)] += [(a, e, b), (a, c, e)]

    # each tone gets its OWN compacted vertex list -- Part.verts is copied
    # wholesale by glb._weld, so handing all three parts the full grid would
    # triple the file for nothing.
    for tris, mat in zip(buckets, (WOOL, WOOL_M, WOOL_D)):
        remap, vs, out = {}, [], []
        for tri in tris:
            t = []
            for k in tri:
                if k not in remap:
                    remap[k] = len(vs)
                    vs.append(verts[k])
                t.append(remap[k])
            out.append(tuple(t))
        m.add(Part(vs, out, smooth=True), mat)
    return m


# ====================================================================== 2
# CEILING.  Photo evidence (crops/ceil_big.png, crops/ceil_hallway_look.png,
# crops/ceil_hallway_with.png): FOUR fixtures are visible -- three flat
# recessed cans and, nearest the camera in the walking strip, ONE surface-mount
# mini drum with a visible white cylindrical body.  No crown anywhere; the
# ceiling/wall junction is a plain drywall corner.  No ceiling register.
CANS = [(2.05, 4.55), (5.85, 4.40), (6.15, 9.60), (1.95, 14.35)]
DRUM = (1.95, 10.80, 0.46)

DRUMBODY = Material("h17drum", "#f6f5f3", roughness=0.45)


# kit.CEIL carries emissive #b0b0b0, which put this ceiling at 207.7 against
# the photo's 144-148 -- brighter than every wall, where the photo has it the
# DARKEST large surface in the room.  Same construction, solved emissive.
CEILM = Material("h17ceil", "#ffffff", roughness=0.95, emissive="#5c5c5c",
                 double_sided=False)


def piece_ceiling():
    # The ceiling DOES continue over the stairwell in every photo (the lid is
    # 8 ft above THIS slab, the void is below it), so it is built over the full
    # rect; only the FLOOR has the L cut out of it.
    m = ceiling(W, D, H, crown=False, cans=CANS, ceil_mat=CEILM)
    cx, cz, r = DRUM
    Y = H - 0.01
    # the underside of a surface-mount fixture faces straight DOWN and this
    # renderer gives a downward non-emissive face almost nothing -- round 1
    # shipped it as a charcoal donut.  Both down-facing rings use the same
    # lightly-emissive stock kit.py uses for the ceiling plane itself.
    m.add(cylinder(r * 0.74, 0.155, 20), DRUMBODY, at=(cx, Y - 0.155, cz))
    ring_down(m, CEIL_FLAT, cx, cz, Y - 0.012, r * 0.70, r * 1.02)
    ring_down(m, CEIL_FLAT, cx, cz, Y - 0.158, r * 0.60, r * 0.76)
    disc_down(m, LENS, cx, cz, Y - 0.168, r * 0.62)
    return m


# ====================================================================== 3
# WALL ART -- the welded stick sculpture, WEST wall.
# Metered off 'Second-floor hallway.jpg' against the single-gang switch plate
# below it (0.375 ft tall = 45 px): the panel is 2.8 ft tall, its top 1.85 ft
# below the ceiling, and roughly square in wall space.  crops/sculpt_v2.png
# shows what it is made of: ~130 THIN straight rods in two rough directions,
# several depth layers, brushed nickel with warm brass and a few dark bronze.
ART_Z0, ART_Z1 = 3.00, 5.60
ART_Y0, ART_Y1 = 3.35, 6.17

NICKEL = Material("h17nik", "#aeb1b5", roughness=0.42, metallic=0.28)
NICKEL2 = Material("h17nik2", "#94979b", roughness=0.45, metallic=0.28)
BRASS = Material("h17brs", "#9d8b71", roughness=0.44, metallic=0.30)
BRONZE = Material("h17brz", "#77706a", roughness=0.48, metallic=0.28)


def piece_wall_art():
    m = Model()
    rn = Rnd(4451)
    zc, yc = (ART_Z0 + ART_Z1) / 2, (ART_Y0 + ART_Y1) / 2
    hz, hy = (ART_Z1 - ART_Z0) / 2, (ART_Y1 - ART_Y0) / 2
    mats = [NICKEL, NICKEL2, BRASS, NICKEL, NICKEL2, BRONZE, NICKEL, BRASS]
    t = 0.019                                   # rod thickness (~1/4 in)

    def seg(lo=-1.04, hi=1.04, span=(0.22, 1.55)):
        """Two ends inside the panel, |length| in `span` (normalised units)."""
        for _ in range(24):
            a, b = rn.f(lo, hi), rn.f(lo, hi)
            if span[0] <= abs(b - a) <= span[1]:
                return (min(a, b), max(a, b))
        return (-0.4, 0.4)

    for k in range(132):
        mat = mats[int(rn.f(0, 7.99))]
        # room 13's slab fills local x 0..0.35, and the skin sits on its face,
        # so the sculpture starts at 0.47 -- round 1 put it at 0.03 and it was
        # rendered INSIDE the guest room's wall, i.e. completely invisible.
        x = 0.470 + rn.f(0.0, 0.115)            # which depth layer
        if k % 2:                               # a near-vertical rod
            y0n, y1n = seg()
            L = (y1n - y0n) * hy
            z = zc + rn.f(-1.0, 1.0) ** 1.0 * hz
            m.add(box(t, L, t), mat, at=(x, yc + y0n * hy, z),
                  rot_x=R(rn.f(-3.5, 3.5)))
        else:                                   # a near-horizontal rod
            z0n, z1n = seg()
            L = (z1n - z0n) * hz
            y = yc + rn.f(-1.0, 1.0) * hy
            m.add(box(t, t, L), mat,
                  at=(x, y, zc + (z0n + z1n) / 2 * hz), rot_x=R(rn.f(-4, 4)))
    return m


# ====================================================================== 4
# PLANTS.  crops/plants_v2.png: two SANSEVIERIA -- tall flat sword blades,
# near-upright, dark green with a pale yellow-green margin.  The west one is a
# white tapered pot on a dark WOOD four-leg stand; the east one a pale teal pot
# on a black metal stand.
POTW = Material("h17potw", "#f2f0eb", roughness=0.50)
POTT = Material("h17pott", "#93bfba", roughness=0.48)
SOIL = Material("h17soil", "#40382f", roughness=0.95)
WOODST = Material("h17wdst", "#2f2a26", roughness=0.62)
LEAFA = Material("h17lfa", "#4c6238", roughness=0.86)
LEAFB = Material("h17lfb", "#39502c", roughness=0.86)
LEAFC = Material("h17lfc", "#5d7442", roughness=0.86)
EDGE = Material("h17lfe", "#a3ad63", roughness=0.86)


def blade(m, cx, cy, cz, ang, h, w, lean, seed):
    """A sansevieria blade: flat, tall, arching, with a pale margin.

    Built as ONE smooth strip per blade so it reads as a soft sword leaf, not
    as the spiky agave the old triangle-fan version gave.
    """
    n = 5
    dx, dz = math.cos(ang), math.sin(ang)
    px, pz = -dz, dx
    body = (LEAFA, LEAFB, LEAFC)[seed % 3]

    def rib(s, frac):
        yy = cy + h * s
        r = lean * (s ** 1.9)
        # a sansevieria blade is a narrow sword: widest a third of the way up,
        # tapering to a point, NOT the broad agave fan round 1 drew
        ww = w * (0.42 + 0.95 * math.sin(math.pi * min(1.0, s * 0.93)) ** 0.42)
        ww *= frac
        bxx, bzz = cx + dx * r, cz + dz * r
        return ((bxx - px * ww / 2, yy, bzz - pz * ww / 2),
                (bxx + px * ww / 2, yy, bzz + pz * ww / 2))

    prev = None
    for i in range(n + 1):
        cur = rib(i / n, 1.0)
        if prev:
            m.add(Part([prev[0], prev[1], cur[1], cur[0]],
                       [(0, 1, 2), (0, 2, 3)], smooth=True), body)
        prev = cur
    # one pale margin, on the side the light comes from -- a second ribbon on
    # the shaded edge cost 19 KB across the two plants and was never visible
    prev = None
    for i in range(n + 1):
        a, b = rib(i / n, 1.0)
        cur = (b, (b[0] - px * 0.12 * w, b[1], b[2] - pz * 0.12 * w))
        if prev:
            m.add(Part([prev[0], prev[1], cur[1], cur[0]],
                       [(0, 1, 2), (0, 2, 3)], smooth=True), EDGE)
        prev = cur


def snake_plant(m, cx, cz, pot_mat, seed, stand, pot_r=0.42, pot_h=0.80,
                nblade=17, bh=(1.9, 3.0)):
    contact_shadow(m, cx, cz, 0.80, 0.80, y=0.050, strength=0.44, room=(W, D))
    if stand == "wood":
        sh = 1.05
        for (ox, oz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            m.add(box(0.075, sh, 0.075), WOODST,
                  at=(cx + ox * 0.36, 0.0, cz + oz * 0.36))
        for y in (0.30, sh - 0.055):
            m.add(box(0.80, 0.055, 0.055), WOODST, at=(cx, y, cz - 0.36))
            m.add(box(0.80, 0.055, 0.055), WOODST, at=(cx, y, cz + 0.36))
            m.add(box(0.055, 0.055, 0.80), WOODST, at=(cx - 0.36, y, cz))
            m.add(box(0.055, 0.055, 0.80), WOODST, at=(cx + 0.36, y, cz))
    else:
        sh = 1.22
        plant_stand(m, cx, cz, 0.46, sh, BLACKMET)
    m.add(cylinder(pot_r, pot_h, 18, r_top=pot_r * 0.88), pot_mat,
          at=(cx, sh, cz))
    m.add(cylinder(pot_r * 0.86, 0.05, 14), SOIL, at=(cx, sh + pot_h - 0.05, cz))
    rn = Rnd(seed)
    y0 = sh + pot_h - 0.06
    for i in range(nblade):
        a = 2 * math.pi * i / nblade + rn.f(-0.25, 0.25)
        rr = rn.f(0.03, 0.16)
        blade(m, cx + rr * math.cos(a), y0, cz + rr * math.sin(a), a,
              rn.f(*bh), rn.f(0.115, 0.185), rn.f(0.10, 0.40), seed + i * 7)


def piece_plants():
    m = Model()
    # west side, just south of the master-bedroom doorway (photo: white pot on
    # a dark wood stand, standing in the corner by the cased opening)
    snake_plant(m, 0.95, 1.75, POTW, 771, "wood", pot_r=0.40, pot_h=0.84,
                nblade=18, bh=(1.85, 2.85))
    # east side, against the east wall north of the stairwell (teal pot)
    snake_plant(m, 7.20, 1.55, POTT, 913, "wire", pot_r=0.37, pot_h=0.72,
                nblade=14, bh=(1.50, 2.35))
    return m


# ====================================================================== 5
# SMALL WALL FITTINGS -- west wall.  A single-gang switch plate under the
# sculpture, a duplex outlet with the purple night light plugged into it, and
# the small high return-air grille near the north end.
PLATE = Material("h17plate", "#f4f3f0", roughness=0.42)
PLATED = Material("h17plated", "#c9c7c2", roughness=0.55)
GRILLD = Material("h17grild", "#3a3c3d", roughness=0.70)
NLGLOW = Material("h17nl", "#8a6cff", roughness=0.35, emissive="#7d5cff",
                  emissive_strength=3.2)


def piece_fittings():
    m = Model()
    # every plate sits on the VISIBLE west face, which is room 13's slab at
    # x=0.35 up to z=10.70 and room 17's own wall line beyond it
    def plate(z, y, w, h):
        x0 = wface(z) + 0.115
        bx(m, PLATE, x0, x0 + 0.032, y - h / 2, y + h / 2,
           z - w / 2, z + w / 2)
        return x0 + 0.032

    # switch, single gang, 4 ft up, south of the sculpture
    x1 = plate(6.55, 3.95, 0.229, 0.375)
    bx(m, PLATED, x1, x1 + 0.020, 3.86, 4.09, 6.50, 6.60)
    # a second bank at the south end was dropped: the west wall's only solid
    # run is now z 0..7.95, the rest is the three doorways.
    # duplex outlet + the purple night light
    NZ, NY = 2.95, 1.18
    x1 = plate(NZ, NY, 0.229, 0.375)
    bx(m, PLATE, x1, x1 + 0.075, NY - 0.16, NY + 0.10, NZ - 0.085, NZ + 0.085)
    m.add(cylinder(0.052, 0.030, 12), NLGLOW, at=(x1 + 0.085, NY + 0.055, NZ),
          rot_z=R(90))
    # small high return-air grille, west wall near the north end
    gz, gy, gw, gh = 2.15, 6.70, 0.42, 0.62
    gx = plate(gz, gy, gw, gh)
    for k in range(4):
        y = gy - gh / 2 + 0.085 + k * 0.135
        bx(m, GRILLD, gx - 0.012, gx + 0.004, y, y + 0.062,
           gz - gw / 2 + 0.045, gz + gw / 2 - 0.045)
    return m


# ====================================================================== 6
# WALL SKINS.  Non-emissive per-wall albedo, ROOM-BRIEF option 2.  The last
# round shipped them as flat boxes and they metered sd 0.00 / mean|d1| 0.00
# against the photo's 14-17 / 0.33-0.69.  They are now shallow displaced
# grids: the large-wavelength component buys the sd (a real wall's sd is a
# LIGHTING gradient, not grain), the short one buys the fine-scale |d1|.
# Still one plain colour per wall, still zero emissive.
# Solved by probe.py, NOT by eye: each wall is rendered twice (skin #c8c8c8,
# then #3c3c3c), the pixels that MOVED are taken as that wall's mask, and the
# wall is then metered over that mask alone -- so a sculpture, a plant or a door
# casing standing in front of it can never be counted as wall.
#
# probe.py's log-linear inverse over-darkened every wall: the real response is
# convex (it saturates near white), so a power law fitted to the two extremes
# is concave and misses the middle badly -- it asked for 165 on the north wall
# and got 187.8.  These four are interpolated between MEASURED points instead:
#   wall   alb 200   alb 60    third measured point      target
#   n        228.5     95.2    128 -> 187.8              165
#   s        129.8     19.2    233 -> 154.5              165
#   e        156.0     26.2    199 -> 155.2              158
#   w        191.3     55.7    183 -> 178.8              175
SKINS = {"n": "#6f6f6f", "s": "#f7f7f7", "e": "#cacaca", "w": "#b2b2b2"}

CELL = 0.26
# Displacement amplitudes (ft) and their wavelength scales.  INSET must exceed
# sum(AMP) or the skin sinks behind the room wall and punches holes in itself.
# Shading responds to SLOPE (A/lambda), not to amplitude, so round 1's very
# long wavelengths bought protrusion and no texture: sd 0.47-4.15 measured.
# Round 2 ran INSET at sum(AMP)+0.009 and the north wall broke into a
# camouflage blob pattern -- 2.7 mm of clearance is inside the depth buffer's
# noise at 15 ft.  Minimum clearance is now 32 mm.
AMP = (0.012, 0.013, 0.008, 0.004, 0.003)
LAM = (1.02, 0.48, 0.235, 0.137, 0.113)   # shortened 0.78x: slope, not amplitude, is what shades
INSET = 0.072


def _skinmat(c):
    return Material("h17sk" + c.lstrip("#"), c, roughness=0.95, metallic=0.0)


def skin_wall(m, wall, a0, a1, y0, y1, color, holes=(), inset=INSET, seed=11,
              face=0.0):
    """A displaced, smooth-shaded skin over one wall face, a0..a1 along it."""
    na = max(2, int(round((a1 - a0) / CELL)))
    ny = max(2, int(round((y1 - y0) / CELL)))
    rn = Rnd(seed)
    ph = [rn.f(0, 6.283) for _ in range(8)]

    def disp(a, y):
        # a real painted wall's sd comes from a LIGHTING gradient across broad
        # soft undulations, not from grain, so the long wavelengths carry most
        # of the amplitude and the short ones only buy the fine-scale |d1|.
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

    verts, tris = [], []
    for j in range(ny + 1):
        y = y0 + (y1 - y0) * j / ny
        for i in range(na + 1):
            a = a0 + (a1 - a0) * i / na
            d = face + inset + disp(a, y)
            if wall == "n":
                verts.append((a, y, d))
            elif wall == "s":
                verts.append((a, y, D - d))
            elif wall == "w":
                verts.append((d, y, a))
            else:
                verts.append((W - d, y, a))
    for j in range(ny):
        yA = y0 + (y1 - y0) * (j + 0.5) / ny
        for i in range(na):
            aA = a0 + (a1 - a0) * (i + 0.5) / na
            if hidden(aA, yA):
                continue
            p = j * (na + 1) + i
            q, r_, s = p + 1, p + na + 1, p + na + 2
            if wall in ("n", "e"):          # face +z / -x, i.e. into the room
                tris += [(p, q, r_), (q, s, r_)]
            else:                           # 's' faces -z, 'w' faces +x
                tris += [(p, r_, q), (q, r_, s)]
    m.add(Part(verts, tris, smooth=True), _skinmat(color))


# Edge -> (wall letter, does the edge run backwards along that wall's axis).
# Edges 2 and 3 are the stairwell head and the knee-wall line: both cut away,
# so no wall and no skin.
EDGE_WALL = {0: ("n", False), 1: ("e", False), 4: ("s", True), 5: ("w", True)}


def live_holes(margin=0.36):
    """Read room 17's openings from the app and turn them into skin holes.

    Hard-coding them went stale inside one build: a parallel builder re-cut the
    west wall (opening 126 moved and 135 appeared) while this was running, and
    a hard-coded hole list paints straight over a doorway.
    """
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
    top, bot = H - 0.05, BB_H - 0.02
    hl = live_holes()
    # NORTH wall, full 0..W (master-bedroom passage punched out)
    skin_wall(m, "n", 0.02, W - 0.02, bot, top, colors["n"], hl["n"],
              seed=11, face=FACE["n"])
    # EAST wall exists ONLY over z 0..KZ (the stairwell is cut out beyond)
    skin_wall(m, "e", 0.02, KZ - 0.02, bot, top, colors["e"], hl["e"], seed=23,
              face=FACE["e"])
    # SOUTH wall exists ONLY over x 0..KX
    skin_wall(m, "s", 0.02, KX - 0.02, bot, top, colors["s"], hl["s"],
              seed=37, face=FACE["s"])
    # WEST wall, full length, in two spans: room 13's slab juts 0.35 ft into the
    # hall as far as z=10.70 and the wall visibly steps there.  The step falls
    # INSIDE the guest doorway's hole, so no seam shows.
    skin_wall(m, "w", 0.02, W_STEP, bot, top, colors["w"], hl["w"], seed=53,
              face=0.35)
    skin_wall(m, "w", W_STEP, D - 0.02, bot, top, colors["w"], hl["w"], seed=59,
              face=0.0)
    return m


# ====================================================================== main
PIECES = {
    "runner":   ("Hall2F Floor Runner", piece_runner),
    "ceiling":  ("Hall2F Ceiling", piece_ceiling),
    "art":      ("Hall2F Wall Art", piece_wall_art),
    "plants":   ("Hall2F Plants", piece_plants),
    "fittings": ("Hall2F Wall Fittings", piece_fittings),
    "skins":    ("Hall2F Wall Wash Skins", piece_skins),
}

WALL_COLOR = "#cfd1d2"


def main(only=None):
    tot = 0.0
    if only in (None, "surf"):
        surfaces(ROOM, wall_color=WALL_COLOR)
    for k, (name, fn) in PIECES.items():
        if only in (None, k):
            tot += save_and_place(name, fn())
    if tot:
        print(f"  -- {tot:.1f} KB written")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
