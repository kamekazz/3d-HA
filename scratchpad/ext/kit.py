"""Shared helpers for the two exterior yards (rooms 11 Frontyard / 3 Backyard).

Everything is authored in WORLD feet and then shifted so the GLB's own bbox is
what roomkit.place seats: the app centres a model's bbox on pos.x/pos.z and puts
its MIN-Y at pos.y, and an outdoor room's objects hang off the first-floor group
at world y = 8.  The shell GLB's real ground is world y 2.13 (house pad) / 0.16
(driveway), i.e. 5.9 ft BELOW that group, so `world_pos` below does the
conversion once and every script uses it.
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import (Model, Material, Part, box, cylinder, prism, quad,
                         uv_quad, png_rgb)

OUT = os.path.dirname(os.path.abspath(__file__))

# room footprint anchors (from roomkit.rooms)
FP = {11: (-4.0, 35.0), 3: (-4.0, -22.5)}
FLOOR_Y = 8.0            # world Y of the first-floor group objects hang off

GRADE_HI = 2.13          # shell terrain under the house / lawn
GRADE_LO = 0.16          # shell terrain on the driveway strip and east yard


def world_pos(model, room, base_world_y):
    """(pos, ) for roomkit.place from a model authored in world X/Z.

    `base_world_y` is the world height the model's authored y=0 sits at.
    """
    lo, hi = model.bounds()
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    fx, fz = FP[room]
    return (cx - fx, base_world_y + lo[1] - FLOOR_Y, cz - fz)


def rng(seed):
    a = seed & 0xFFFFFFFF

    def n():
        nonlocal a
        a = (a * 1664525 + 1013904223) & 0xFFFFFFFF
        return a / 4294967296.0
    return n


# ---------------------------------------------------------------- textures

def board_tex(seed=7, px=96, boards=4, base=238, seam=150, grain=13):
    """Composite decking: `boards` planks across the tile, dark seams, grain.

    Near white so it MULTIPLIES the material colour (glTF baseColor = factor x
    texel), which is how the piece keeps one authored grey while still carrying
    fine-scale variation -- the sd-is-scale-blind lesson: a flat plank reads as
    plastic however well its average value is matched.
    """
    r = rng(seed)
    bw = px // boards
    tone = [base - 14 + int(r() * 28) for _ in range(boards)]
    rows = []
    for y in range(px):
        row = []
        for x in range(px):
            b = x // bw
            v = tone[b] + int((r() - 0.5) * grain)
            if x % bw == 0 or x % bw == bw - 1:
                v = seam + int(r() * 12)
            # lengthwise grain streaks
            if (x * 7 + y * 3) % 29 == 0:
                v -= 9
            v = max(0, min(255, v))
            row.append((v, v, v - 2 if v > 2 else 0))
        rows.append(row)
    return png_rgb(rows)


def wicker_tex(seed=11, px=64, base=250, dark=138):
    """Open basket weave for the outdoor furniture.

    Round 1's version was correct in principle and invisible in practice for
    two separate reasons, both fixed here:

    1. `box()` emits NO UVs, so every wicker panel sampled texel (0,0) and
       rendered as flat paint. Use `uv_box()` below for anything carrying a
       texture. (Metered: photo RGB 167,165,174 with a strong basketweave;
       round 1 rendered 195,193,187 with none.)
    2. Even sampled correctly the weave was too faint -- 242 against 196 on a
       4 px cell is a 19% modulation. A real basketweave alternates a lit
       strand against a shadowed GAP, which is nearer 45%.

    So: 8 px cells (one full over-under pair), warp and weft that swap which
    is on top per cell, and a dark gap line between strands.
    """
    r = rng(seed)
    rows = []
    for y in range(px):
        row = []
        for x in range(px):
            cx, cy = x % 8, y % 8
            over = ((x // 8) + (y // 8)) % 2 == 0   # which strand is on top
            gap = cx == 0 or cy == 0               # the shadow between strands
            if gap:
                v = dark
            elif over:
                # horizontal strand on top: shade across its width
                v = base - int(abs(cy - 4) / 4.0 * 46)
            else:
                v = base - int(abs(cx - 4) / 4.0 * 46) - 16
            v += int((r() - 0.5) * 14)
            v = max(0, min(255, v))
            row.append((v, v, min(255, v + 3)))    # the photo reads B > R
        rows.append(row)
    return png_rgb(rows)


def uv_box(w, h, d, scale=1.0, anchor="base"):
    """Axis-aligned box WITH per-face planar UVs, so a tiled texture shows.

    `roomkit.glb.box()` emits no UVs at all -- a `tex=` on it samples texel
    (0,0) and renders as flat paint, which is why round 1's wicker had no
    weave. Each face gets its own quad (24 verts) so the tiling never smears
    across a corner; `scale` is texture repeats per foot.
    """
    y0, y1 = (0.0, h) if anchor == "base" else (-h / 2, h / 2)
    x0, x1, z0, z1 = -w / 2, w / 2, -d / 2, d / 2
    faces = [
        # (verts CCW seen from outside, u-extent, v-extent)
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], w, h),   # +z
        ([(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)], w, h),   # -z
        ([(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], d, h),   # +x
        ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], d, h),   # -x
        ([(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], w, d),   # +y
        ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], w, d),   # -y
    ]
    verts, tris, uvs = [], [], []
    for vs, uw, vh in faces:
        b = len(verts)
        verts += vs
        uvs += [(0, 0), (uw * scale, 0), (uw * scale, vh * scale), (0, vh * scale)]
        tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    return Part(verts, tris, uv=uvs)


def add_uv_box(m, mat, w, h, d, x, y, z, ry=0.0, scale=1.0):
    m.add(uv_box(w, h, d, scale), mat, at=(x, y, z), rot_y=ry)


# ---------------------------------------------------------------- geometry

def bx(w, h, d, x, y, z, ry=0.0):
    """box centred on x/z with its BASE at y, as a (part, transform) tuple."""
    return box(w, h, d), dict(at=(x, y, z), rot_y=ry)


def add_box(m, mat, w, h, d, x, y, z, ry=0.0):
    m.add(box(w, h, d), mat, at=(x, y, z), rot_y=ry)


def deck_surface(x0, z0, x1, z1, y, tile=1.5, cell=0.8, angle=math.pi / 4,
                 shadows=()):
    """Decking plane as one subdivided, UV-tiled, vertex-coloured Part.

    Boards run at `angle` (the rear photographs lay them on the diagonal), and
    every furniture CONTACT SHADOW is baked in as a vertex-colour darkening
    instead of a separate decal quad: a decal would either z-fight the deck or,
    if opaque, erase the board texture under it. `shadows` is a list of
    (cx, cz, rx, rz, strength) in world feet -- the ramp is run PAST the
    footprint (rx/rz already include the spill) with exponent 1.15, which is
    what stops all the darkness landing under the object where nobody sees it.
    """
    nx = max(2, int(round((x1 - x0) / cell)))
    nz = max(2, int(round((z1 - z0) / cell)))
    ca, sa = math.cos(angle), math.sin(angle)
    verts, uvs, cols = [], [], []
    for iz in range(nz + 1):
        for ix in range(nx + 1):
            x = x0 + (x1 - x0) * ix / nx
            z = z0 + (z1 - z0) * iz / nz
            verts.append((x, y, z))
            uvs.append(((x * ca + z * sa) / tile, (-x * sa + z * ca) / tile))
            f = 1.0
            for (cx, cz, rx, rz, s) in shadows:
                d = math.hypot((x - cx) / rx, (z - cz) / rz)
                if d < 1.0:
                    f -= s * (1.0 - d) ** 1.15
            f = max(0.35, f)
            cols.append((f, f, f))
    tris = []
    for iz in range(nz):
        for ix in range(nx):
            a = iz * (nx + 1) + ix
            b, c, dd = a + 1, a + nx + 1, a + nx + 2
            tris += [(a, c, b), (b, c, dd)]
    return Part(verts, tris, smooth=True, colors=cols, uv=uvs)


def railing(m, mat_rail, x0, z0, x1, z1, y, h=3.0, spacing=0.46,
            baluster=0.11, newels=True):
    """One straight run of white square-baluster railing with flat newel caps."""
    dx, dz = x1 - x0, z1 - z0
    L = math.hypot(dx, dz)
    if L < 0.3:
        return
    ux, uz = dx / L, dz / L
    ry = math.atan2(-uz, ux) if abs(dz) > abs(dx) else 0.0
    horiz = abs(dx) >= abs(dz)
    tw, td = (L, 0.30) if horiz else (0.30, L)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    add_box(m, mat_rail, tw, 0.22, td if horiz else 0.34, cx, y + h - 0.22, cz)
    add_box(m, mat_rail, tw if horiz else 0.26, 0.12, 0.26 if horiz else td,
            cx, y + 0.30, cz)
    n = max(1, int(L / spacing))
    for i in range(1, n):
        t = i / n
        x, z = x0 + dx * t, z0 + dz * t
        add_box(m, mat_rail, baluster, h - 0.52, baluster, x, y + 0.42, z)
    if newels:
        for (x, z) in ((x0, z0), (x1, z1)):
            add_box(m, mat_rail, 0.36, h + 0.14, 0.36, x, y, z)
            add_box(m, mat_rail, 0.50, 0.13, 0.50, x, y + h + 0.14, z)


def stair(m, mat_tread, mat_riser, x0, z0, w, run_dir, top_y, bot_y,
          tread=1.05, width_axis='x'):
    """A straight flight from `top_y` down to `bot_y`, stepping along run_dir.

    run_dir is (dx, dz) unit-ish; width_axis says which axis the treads span.
    """
    rise_total = top_y - bot_y
    steps = max(1, int(round(rise_total / 0.62)))
    r = rise_total / steps
    dx, dz = run_dir
    for i in range(steps):
        y = top_y - (i + 1) * r
        cx = x0 + dx * tread * (i + 0.5)
        cz = z0 + dz * tread * (i + 0.5)
        if width_axis == 'x':
            add_box(m, mat_tread, w, 0.13, tread + 0.12, cx, y, cz)
            add_box(m, mat_riser, w - 0.1, r, 0.10, cx, y - r,
                    cz - dz * (tread / 2 + 0.05))
        else:
            add_box(m, mat_tread, tread + 0.12, 0.13, w, cx, y, cz)
            add_box(m, mat_riser, 0.10, r, w - 0.1,
                    cx - dx * (tread / 2 + 0.05), y - r, cz)
