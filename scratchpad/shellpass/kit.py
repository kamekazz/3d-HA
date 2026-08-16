"""Shell-pass kit -- shared helpers for the twelve untouched rooms.

A "shell" is two pieces per room:

    "<Room> Ceiling"     one-sided downward plane + crown + cans/fixtures
    "<Room> Baseboards"  skirting (gapped at doorways) + chair rail /
                         wainscot + door casings + door leaves

Both names match objects.js SURFACE_RE (floor|ceiling|wall wash|baseboards|
crown) so they stay pickable:false and never swallow a click.  Defining
furniture goes in its own object and must NOT match that pattern.

Everything is authored in ROOM-LOCAL feet and placed at rot 0 with
pos = (bbox centre x, bbox min y, bbox centre z) -- the seat the app gives a
model.  See tools/roomkit/ROOM-BRIEF.md.
"""

import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from roomkit.glb import (Model, Material, box, rounded_box, cylinder, prism,
                         quad, sag_plane, torus, Part)          # noqa: F401
from roomkit.place import place

OUT = os.path.dirname(os.path.abspath(__file__))
BASE = "http://127.0.0.1:5000"
R = math.radians


# --------------------------------------------------------------- placement
def save_and_place(name, m, room, fname=None):
    path = os.path.join(OUT, "glb", (fname or name.replace(" ", "_").replace(".", "").lower()) + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=1.0)
    size = tuple(round(hi[i] - lo[i], 3) for i in range(3))
    print(f"  {name:30s} size={size}  pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f})  {res['action']}")
    return {"name": name, "size_ft": list(size),
            "pos": [round(p, 3) for p in pos], "rot": 0}


def surfaces(room, **kw):
    """PATCH /api/house/room/<id> -- wall_color / floor_color / floor_texture."""
    body = json.dumps(kw).encode()
    req = urllib.request.Request(f"{BASE}/api/house/room/{room}", data=body,
                                 method="PATCH")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()
    print(f"  surfaces room {room}: {kw}")


# ------------------------------------------------------------------ colour
def mix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    return "#%02x%02x%02x" % tuple(
        int(round(int(a[i:i + 2], 16) + (int(b[i:i + 2], 16) - int(a[i:i + 2], 16)) * t))
        for i in (0, 2, 4))


class Rnd:
    def __init__(self, s):
        self.s = s

    def f(self, a=0.0, b=1.0):
        self.s = (self.s * 1103515245 + 12345) % (1 << 31)
        return a + (b - a) * (((self.s >> 9) % 100000) / 100000.0)


# --------------------------------------------------------------- materials
# NO EMISSIVE on trim runs: two rounds of critics rejected glowing crown /
# baseboard fins.  White trim at roughness 0.6 already collects ~1.7x what a
# room wall of the same albedo does, which is the value step we want.
TRIM = Material("trim", "#f7f6f3", roughness=0.60)
TRIM_D = Material("trimd", "#e4e2dd", roughness=0.62)      # shaded trim return
# The ceiling plane faces straight DOWN and collects almost no light in this
# renderer -- without emissive it reads as a dark grey lid.  This is the one
# room-scale emissive allowed (same call room 15 made and passed with).
CEIL = Material("ceil", "#ffffff", roughness=0.95, emissive="#b0b0b0",
                double_sided=False)
CEIL_FLAT = Material("ceilflat", "#fdfdfc", roughness=0.6, emissive="#a8a8a8",
                     double_sided=False)
CAN_CONE = Material("cancone", "#e8e8e6", roughness=0.5, emissive="#828280",
                    double_sided=False)
LENS = Material("lens", "#fff7e6", roughness=0.3, emissive="#fff2d6",
                emissive_strength=6.0, double_sided=False)
VENT = Material("vent", "#c2c4c4", roughness=0.6, emissive="#8e8e8e",
                double_sided=False)

WHITEWD = Material("whitewd", "#f4f3f0", roughness=0.62)
DOORSHADE = Material("doorshade", "#cdcac4", roughness=0.7)
BLACKMET = Material("blackmet", "#232326", roughness=0.45, metallic=0.35)
CHROME = Material("chrome", "#b8bcbe", roughness=0.30, metallic=0.55)
GLASS = Material("glass", "#eef5f7", roughness=0.42, opacity=0.17)
MARBLE = Material("marble", "#eceaea", roughness=0.35)
TILEW = Material("tilew", "#e9e7e4", roughness=0.45)
GROUT = Material("grout", "#b9b6b2", roughness=0.85)
PORC = Material("porc", "#f6f6f5", roughness=0.32)           # sanitaryware
DARKWD = Material("darkwd", "#3b3d40", roughness=0.7)
GREYCAB = Material("greycab", "#a9adb0", roughness=0.62)
CARPETM = Material("carpetm", "#8f8f8c", roughness=0.98)


# ---------------------------------------------------------------- geometry
def bx(m, mat, x0, x1, y0, y1, z0, z1):
    if x1 - x0 <= 0 or y1 - y0 <= 0 or z1 - z0 <= 0:
        return
    m.add(box(x1 - x0, y1 - y0, z1 - z0), mat,
          at=((x0 + x1) / 2.0, y0, (z0 + z1) / 2.0))


def rect_down(m, mat, x0, x1, y, z0, z1):
    m.add(quad((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)), mat)


def rect_up(m, mat, x0, x1, y, z0, z1):
    m.add(quad((x0, y, z1), (x1, y, z1), (x1, y, z0), (x0, y, z0)), mat)


def disc_down(m, mat, cx, cz, y, r, seg=24):
    v = [(cx, y, cz)] + [(cx + r * math.cos(2 * math.pi * i / seg), y,
                          cz + r * math.sin(2 * math.pi * i / seg))
                         for i in range(seg)]
    t = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    m.add(Part(v, t), mat)


def ring_down(m, mat, cx, cz, y, r0, r1, seg=24):
    v, t = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((cx + r0 * math.cos(a), y, cz + r0 * math.sin(a)))
        v.append((cx + r1 * math.cos(a), y, cz + r1 * math.sin(a)))
    for i in range(seg):
        a0, b0 = 2 * i, 2 * i + 1
        a1, b1 = (2 * i + 2) % (2 * seg), (2 * i + 3) % (2 * seg)
        t += [(a0, b0, b1), (a0, b1, a1)]
    m.add(Part(v, t), mat)


def spans(total, gaps):
    """[0,total] minus every (a,b) in gaps -> list of surviving intervals."""
    out, cur = [], 0.0
    for a, b in sorted(gaps):
        a, b = max(0.0, a), min(total, b)
        if a > cur:
            out.append((cur, a))
        cur = max(cur, b)
    if cur < total:
        out.append((cur, total))
    return [(a, b) for a, b in out if b - a > 0.06]


def wall_band(m, mat, wall, W, D, y0, y1, depth, gaps=(), shrink=0.0):
    """A run along one wall, projecting `depth` into the room.

    wall: 'n' (z=0), 's' (z=D), 'w' (x=0), 'e' (x=W).  `gaps` are intervals
    along that wall's own axis (x for n/s, z for w/e) -- doorways.
    """
    total = W if wall in "ns" else D
    for a, b in spans(total, gaps):
        a, b = a + shrink, b - shrink
        if b - a <= 0.02:
            continue
        if wall == "n":
            bx(m, mat, a, b, y0, y1, 0.0, depth)
        elif wall == "s":
            bx(m, mat, a, b, y0, y1, D - depth, D)
        elif wall == "w":
            bx(m, mat, 0.0, depth, y0, y1, a, b)
        else:
            bx(m, mat, W - depth, W, y0, y1, a, b)


# ------------------------------------------------------------------- SHELL
BB_H = 0.52          # 6 1/4 in skirting -- this house runs tall baseboards
BB_T = 0.075
CROWN_H = 0.46
CASE_W = 0.28
DOOR_TOP = 6.75


def ceiling(W, D, H, cans=(), crown=True, fixtures=(), vents=(),
            speakers=(), ceil_mat=None, hole=None):
    """One-sided ceiling plane wound to face INTO the room (invisible from
    above -- verify with the `plan` pose, you must still see the floor),
    plus a three-step crown and the photo's ceiling fixtures.

    cans      [(x, z), ...]              recessed cans
    fixtures  [(x, z, r), ...]           flush-mount discs
    vents     [(x, z, w, d), ...]        supply registers
    speakers  [(x, z, r), ...]           in-ceiling speaker grilles
    """
    m = Model()
    Y = H - 0.01
    cm = ceil_mat or CEIL
    if hole:                      # a stairwell: four rects round the opening
        hx0, hx1, hz0, hz1 = hole
        for (a, b, c, d) in ((0, W, 0, hz0), (0, W, hz1, D),
                             (0, hx0, hz0, hz1), (hx1, W, hz0, hz1)):
            if b - a > 0.02 and d - c > 0.02:
                m.add(quad((a, Y, c), (b, Y, c), (b, Y, d), (a, Y, d)), cm)
    else:
        m.add(quad((0, Y, 0), (W, Y, 0), (W, Y, D), (0, Y, D)), cm)

    if crown:
        # three stepped runs -- a flat cap reads as a painted line, not moulding
        for y0, y1, dep in ((H - CROWN_H, H - 0.30, 0.055),
                            (H - 0.30, H - 0.145, 0.115),
                            (H - 0.145, H - 0.008, 0.185)):
            mat = TRIM if dep > 0.09 else TRIM_D
            for w in "nswe":
                wall_band(m, mat, w, W, D, y0, y1, dep)

    for (cx, cz) in cans:
        ring_down(m, CEIL_FLAT, cx, cz, Y - 0.022, 0.255, 0.345)
        ring_down(m, CAN_CONE, cx, cz, Y - 0.070, 0.215, 0.258)
        disc_down(m, LENS, cx, cz, Y - 0.092, 0.222)
    for (cx, cz, r) in fixtures:
        ring_down(m, CEIL_FLAT, cx, cz, Y - 0.030, r * 0.80, r)
        disc_down(m, LENS, cx, cz, Y - 0.115, r * 0.82)
    for (cx, cz, r) in speakers:
        ring_down(m, CEIL_FLAT, cx, cz, Y - 0.020, r * 0.84, r)
        disc_down(m, CAN_CONE, cx, cz, Y - 0.035, r * 0.86)
    for (vx, vz, vw, vd) in vents:
        rect_down(m, CEIL_FLAT, vx - vw / 2, vx + vw / 2, Y - 0.028,
                  vz - vd / 2, vz + vd / 2)
        n = max(3, int(vd / 0.13))
        for i in range(n):
            z = vz - vd / 2 + (i + 0.5) * vd / n
            rect_down(m, VENT, vx - vw / 2 + 0.06, vx + vw / 2 - 0.06,
                      Y - 0.048, z - 0.035, z + 0.035)
    return m


def baseboards(W, D, doors=(), rail=None, wainscot=None, rail_mat=None):
    """Skirting on all four walls, gapped at every doorway, optionally with a
    chair rail and/or a wainscot panel below it.

    doors:    [(wall, a, b), ...]      openings along that wall's axis
    rail:     y of the chair-rail top, or None
    wainscot: hex colour of the panel below the rail, or None
    """
    m = Model()
    gaps = {w: [] for w in "nswe"}
    for (w, a, b) in doors:
        gaps[w].append((a - CASE_W, b + CASE_W))

    for w in "nswe":
        wall_band(m, TRIM, w, W, D, 0.0, BB_H - 0.06, BB_T, gaps[w])
        wall_band(m, TRIM, w, W, D, BB_H - 0.06, BB_H, BB_T * 0.72, gaps[w])

    if wainscot:
        WM = Material("wains", wainscot, roughness=0.72)
        for w in "nswe":
            wall_band(m, WM, w, W, D, BB_H, rail - 0.14, 0.042, gaps[w])
    if rail:
        rm = rail_mat or TRIM
        for w in "nswe":
            wall_band(m, rm, w, W, D, rail - 0.14, rail - 0.035, 0.085, gaps[w])
            wall_band(m, rm, w, W, D, rail - 0.035, rail, 0.052, gaps[w])
    return m


# -------------------------------------------------------------------- door
def panel_door(m, mat, x0, x1, y0, y1, z_back, z_front, rows=3):
    """Six-panel leaf.  A flat white panel on a flat white leaf has no shading
    at all in this renderer, so each panel gets a darker reveal behind it."""
    bx(m, mat, x0, x1, y0, y1, z_back, z_front)
    w, h = x1 - x0, y1 - y0
    sx, sy = 0.135 * w, 0.075 * h
    heights = [0.30, 0.30, 0.40] if rows == 3 else [0.45, 0.55]
    tot = sum(heights)
    y = y0 + sy
    for frac in reversed(heights):
        ph = (h - sy * (len(heights) + 1)) * frac / tot
        for cxx in ((x0 + sx, x0 + w / 2 - sx / 2), (x0 + w / 2 + sx / 2, x1 - sx)):
            bx(m, DOORSHADE, cxx[0] - 0.035, cxx[1] + 0.035,
               y - 0.035, y + ph + 0.035, z_front, z_front + 0.020)
            bx(m, mat, cxx[0], cxx[1], y, y + ph, z_front + 0.018, z_front + 0.056)
        y += ph + sy


def _oriented(m, wall, W, D, a0, a1, y0, y1, d0, d1, mat, panels=1,
              handle=True, top=None):
    """Build a door unit on `wall`, authored in the wall's own frame then
    mapped into room coordinates.  d0/d1 are depths INTO the room."""
    sub = Model()
    top = top if top is not None else y1
    if panels == 1:
        panel_door(sub, mat, a0 + 0.03, a1 - 0.03, y0, top, 0.0, d1 - d0)
    else:
        mid = (a0 + a1) / 2
        panel_door(sub, mat, a0 + 0.03, mid - 0.02, y0, top, 0.0, d1 - d0)
        panel_door(sub, mat, mid + 0.02, a1 - 0.03, y0, top, 0.0, d1 - d0)
    # casing
    for a, b in ((a0 - CASE_W, a0 + 0.03), (a1 - 0.03, a1 + CASE_W)):
        bx(sub, TRIM, a, b, y0, top + CASE_W, 0.0, 0.20)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, top, top + CASE_W, 0.0, 0.20)
    if handle:
        hx = a0 + 0.36 if panels == 1 else (a0 + a1) / 2 - 0.24
        sub.add(cylinder(0.080, 0.05, 12), BLACKMET,
                at=(hx, 3.05, (d1 - d0) + 0.05), rot_x=R(90))
        sub.add(box(0.07, 0.07, 0.28), BLACKMET,
                at=(hx + 0.10, 3.01, (d1 - d0) + 0.18))
    _blit(m, sub, wall, W, D, d0)


def _blit(m, sub, wall, W, D, depth0):
    """Map a wall-frame sub-model (x along the wall, z = depth INTO the room)
    onto `wall` of a W x D room.

    All four maps are proper rotations about Y (det +1 in the xz plane), so the
    winding is preserved and nothing needs flipping -- a flipped face here is
    exactly the "pure black slab" the round-2 critic found.
    """
    for part, mat in sub._parts:
        v = []
        for (x, y, z) in part.verts:
            if wall == "n":                       # z=0 wall, room is +z
                v.append((x, y, depth0 + z))
            elif wall == "s":                     # z=D wall, room is -z
                v.append((W - x, y, D - depth0 - z))
            elif wall == "w":                     # x=0 wall, room is +x
                v.append((depth0 + z, y, D - x))
            else:                                 # x=W wall, room is -x
                v.append((W - depth0 - z, y, x))
        m._parts.append((Part(v, part.tris, part.smooth), mat))


def door_unit(m, wall, W, D, a0, a1, mat=None, panels=1, handle=True,
              top=DOOR_TOP, depth=0.145):
    _oriented(m, wall, W, D, a0, a1, 0.0, top, 0.0, depth, mat or WHITEWD,
              panels=panels, handle=handle, top=top)


def cased_opening(m, wall, W, D, a0, a1, top=7.0):
    """Trim only -- for a real cut `passage` you do not want a leaf in."""
    sub = Model()
    for a, b in ((a0 - CASE_W, a0 + 0.03), (a1 - 0.03, a1 + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, top + CASE_W, 0.0, 0.20)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, top, top + CASE_W, 0.0, 0.20)
    _blit(m, sub, wall, W, D, 0.0)


# ------------------------------------------------------------------ window
def window_unit(m, wall, W, D, a0, a1, sill=2.10, head=6.40, blinds=True):
    """A white-blind window with casing, stool and apron, drawn flush on the
    wall.  Sits over a real cut opening where one exists; on its own it still
    reads as a window from inside, which is what the dollhouse shot sees."""
    sub = Model()
    PANE = Material("pane", "#ffffff", roughness=0.2, emissive="#ffffff",
                    emissive_strength=2.6)
    SLAT = Material("slat", "#f6f5f2", roughness=0.7)
    bx(sub, PANE, a0, a1, sill, head, 0.030, 0.048)
    bx(sub, TRIM, a0 - 0.16, a1 + 0.16, sill - 0.11, sill, 0.0, 0.245)
    bx(sub, TRIM, a0 + 0.14, a1 - 0.14, sill - 0.46, sill - 0.11, 0.0, 0.075)
    bx(sub, TRIM, a0 - CASE_W, a0, sill - 0.11, head, 0.0, 0.085)
    bx(sub, TRIM, a1, a1 + CASE_W, sill - 0.11, head, 0.0, 0.085)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, head, head + CASE_W, 0.0, 0.085)
    if blinds:
        bx(sub, SLAT, a0 + 0.02, a1 - 0.02, head - 0.22, head - 0.02, 0.055, 0.155)
        n = int((head - 0.32 - sill - 0.06) / 0.170)
        for i in range(n):
            y = head - 0.32 - i * 0.170
            sub.add(box(a1 - a0 - 0.05, 0.014, 0.130), SLAT,
                    at=((a0 + a1) / 2, y, 0.105), rot_x=R(28))
    _blit(m, sub, wall, W, D, 0.0)


# ------------------------------------------------------- contact shadow
def contact_shadow(m, cx, cz, rx, rz, y=0.012, tone="#2a2a28", strength=0.32,
                   steps=12, room=None):
    """A SMOOTH radial falloff, built as `steps` concentric translucent quads.

    Nested HARD rings read as a bullseye decal (round 2's critic), so every
    layer carries the same small alpha and the darkness comes from how many of
    them overlap: centre = 1-(1-a)^steps, outer edge = a.  `room` = (W, D)
    clamps the blob inside the footprint -- a shadow poking through a wall is
    visible from outside the room.
    """
    a = round(1.0 - (1.0 - strength) ** (1.0 / steps), 4)
    mat = Material(f"cshadow{int(strength * 100)}", tone, roughness=0.98,
                   opacity=a)
    seg, n = 30, 2.7            # superellipse: 2 = ellipse, big = rectangle
    for i in range(steps):
        s = 1.0 - 0.90 * (i / steps)
        v = [(cx, y + i * 0.0013, cz)]
        for k in range(seg):
            t = 2 * math.pi * k / seg
            ct, st = math.cos(t), math.sin(t)
            px = cx + rx * s * math.copysign(abs(ct) ** (2.0 / n), ct)
            pz = cz + rz * s * math.copysign(abs(st) ** (2.0 / n), st)
            if room:
                px = min(max(px, 0.05), room[0] - 0.05)
                pz = min(max(pz, 0.05), room[1] - 0.05)
            v.append((px, y + i * 0.0013, pz))
        # wound so the face points UP
        tris = [(0, 1 + (k + 1) % seg, 1 + k) for k in range(seg)]
        m.add(Part(v, tris), mat)
