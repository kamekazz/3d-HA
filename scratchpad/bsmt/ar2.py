"""Room 2 -- Arcade Room, 20.7 (x, W-E) x 23.3 (z, N-S) x 8.0 ft.  ROUND 2.

ORIENTATION -- re-derived 2026-08-22 from the basement plan, and it is 180
degrees on X from round 1.  See the build report; the short version:

  The HA basement plan image is the world ROTATED 180 degrees (plan-up = +z,
  plan-LEFT = +x).  Two independent anchors prove it, both to <0.3 ft:
    * the plan's stair enclosure wall lands at world x 15.14; the `stairs` row
      for the basement is x 15.1..18.4   (the un-rotated reading puts it at
      x -2.5, 17.6 ft out)
    * the plan's only party-wall door gap is world x 11.15..14.20; openings 103
      (this room) and 3 (Movie Room) are both world x 11.4..14.1

  With that registration the SOUTH wall (z=23.3) is the ONLY wall of this room
  with any opening: 13.5 ft of solid wall (local x 0..13.2), the Movie Room door
  (13.5..16.2), a 1.2 ft stub, then a 3.2 ft opening to the stair landing
  (17.5..20.7, NOT cut here -- see the report).  `Arcade Room.jpg` / `v3 4` show
  a far wall carrying a door with ~13 ft of cabinets on ONE side and a narrow
  stub + a recess on the other, so that far wall IS the south wall, the camera
  looks SOUTH, and therefore:

  east  x=20.7   THE ROOM.  ~7 uprights + the pinball, the lit Funko shelf over
                 them, the chevron acoustic band and the cove LED, the Y light
  south z=23.3   Legends Ultimate / Capcom Champion / Time Crisis / T2, the
                 black diagonal acoustic panel, then the Movie Room door
  west  x=0      the white sit-stand desk run, the very large TV with its bias
                 strip, hex panels, the floor RGB uplights, Ridge Racer at the
                 SW corner
  north z=0      hex panels + three small mounted screens
  NW             a 5.2 x 3.7 ft utility room stands inside the footprint at
                 x 0..5.2, z 3.4..7.1 (plan: world x -3.0..3.1, z -8.5..-4.8).
                 Its south face carries the white six-panel door that photo
                 `v3 1` shows straight ahead.

Run:  python ar2.py            (idempotent -- re-run freely)
"""

import json
import math
import urllib.request

from bkit import *          # noqa: F401,F403
from a2kit import (         # noqa: F401  -- texture + sweep helpers
    ArtSet, sweep, uvq, uvblit, noise_tex)
import atlas4                                            # noqa: E402
from atlas4 import EAST_SLUGS, SOUTH_SLUGS, NORTH_SLUGS   # noqa: E402
from decks5 import (                                      # noqa: E402
    deck_for, coin_for, front_rect, front_z, button_cap, ball_top)
from roomkit.glb import uv_quad          # noqa: E402

ROOM, W, D, H = 2, 20.7, 23.3, 8.0
BASE = "http://127.0.0.1:5000"

MDOOR = (13.50, 16.20)              # south wall, local x -- door to room 1
PIER = (0.0, 5.20, 3.40, 7.10)      # utility room inside the footprint
PDOOR = (0.55, 3.25)                # its door, on the pier's south face
# THE SOUTH WALL IS SHARED WITH THE MOVIE ROOM AND ITS FACE IS NOT AT z = D.
# `house.js` extrudes every wall OUTWARD from its own footprint line
# (WALL_THICKNESS 0.35, geo.translate(0, 0, -t)), so on a party wall each room's
# wall mass lands inside its NEIGHBOUR.  From in here the surface you see at the
# south end is the MOVIE ROOM's north wall, standing 0.35 ft proud of z = D.
# Round 2 authored the skin, the door, the acoustic panel and the RGB bar at
# depth 0.0-0.10 and every one of them is buried behind it -- the far wall in a
# round-2 render is the neighbour's paint, not ours.  Author south content at
# depth >= SD.  (This is RESUME's finding 1; it also means the Movie Room's
# opening 3 no longer registers with our door 103 -- see the report.)
SD = 0.40
SHELF_Y = 6.34
COVE_Y = 7.62

# ------------------------------------------------------------------ palette
CABBLK = Material("a2cab", "#191a1e", roughness=0.55)
CABDK = Material("a2cabd", "#0d0e11", roughness=0.5)
# ROUND 6.  Every CRT in this room photographs DARK -- fifteen frames, day and
# night, and not one lit attract screen among them (the report lists which
# frame settles each machine).  So this is the material of a switched-off
# monitor, and the whole job is to make it read as GLASS and not as a hole cut
# in the cabinet.  Round 5's "#0a0c10" + emissive #12202c at strength 1.1 did
# the opposite: glTF emissive is a flat untextured factor with no falloff, so
# every screen in the room rendered as ONE UNIFORM NAVY SLAB (measured: luma
# 18.7, sd 2.18 across a whole screen) brighter than its own bezel and
# unaffected by the room -- a dim television, which is precisely what the
# photographs do not show.
#
# MEASURED NEGATIVE RESULT, so nobody spends the afternoon on it twice: the
# obvious fix is to let the glass mirror the room, since `scene.environment` is
# a PMREM of three's RoomEnvironment (scene.js) and `daylight.js` runs
# envMapIntensity to 1.15 in daylight.  It does not work on this surface.  A
# probe material of "#ffffff", roughness 0.05, metallic 1.0 -- a PERFECT MIRROR
# -- rendered these screens at luma 8.4 with sd 0.69, i.e. darker than round
# 5's flat slab and with no spatial variation whatever.  Metallic 1.0 at
# "#3a3d42" measured luma 1.10.  There is no usable environment reflection
# here, and any plan that leans on one is dead on arrival.
#
# So the glass is DIFFUSE, lit by the room like everything else in it: no
# emissive doing the work, a low roughness that still lets a direct light throw
# a real moving glint (one lands on Marvel vs Capcom in the probe frame), and
# the surface variation comes from `crt()` -- curvature plus a vertex-colour
# top-to-bottom gradient and a darkened rim.  "#3f434a" is solved from a probe:
# a flat "#303338" metered luma 22.2 on this quad, and the vertex grade's mean
# factor puts "#3f434a" at the same place.  There is NO emissive at all now: a
# switched-off screen emits nothing, and on the night ramp these panels are lit
# by whatever `roomlights.js` is running exactly as the black cabinet round
# them is, so they go dark WITH the room instead of floating out of it.
SCRN = Material("a2scr", "#42464d", roughness=0.34, metallic=0.10)
CPANEL = Material("a2cp", "#2c2e34", roughness=0.6)
CHR = Material("a2chr", "#adb2b6", roughness=0.28, metallic=0.55)
BLKF = Material("a2blkf", "#131418", roughness=0.98)        # the black lounge
BLKF2 = Material("a2blkf2", "#1c1e23", roughness=0.98)
WHTM = Material("a2wht", "#e9e7e2", roughness=0.5)
DESKW = Material("a2desk", "#f1efea", roughness=0.42)
HEXW = Material("a2hexw", "#e6e4df", roughness=0.62)        # matte hex panel
HEXD = Material("a2hexd", "#33363b", roughness=0.62)
ACOU = Material("a2acou", "#2b2e34", roughness=0.92)
SHELFW = Material("a2shelf", "#efede8", roughness=0.55)
GREEN = Material("a2green", "#4e7d46", roughness=0.85)
POTW = Material("a2pot", "#f3f1ec", roughness=0.5)

# printed side-art / marquee hues taken off the photos' cabinets
HUES = ["#b0202a", "#1f3f7a", "#c8871c", "#1d6b3a", "#5f2d7a",
        "#b8452a", "#1d7f9c", "#8e1f3c", "#3b3f46", "#c02a55",
        "#d8b026", "#2f6fd0"]

BUTTONS = [Material("a2b%d" % i, c, roughness=0.35, emissive=c,
                    emissive_strength=0.9)
           for i, c in enumerate(("#d02b2b", "#2f7fd0", "#d8b026", "#2fa54f"))]

# every RGB fixture in this room draws from one small strip palette, so the
# emissive pieces stay a handful of materials rather than one per LED
RGB = [("#ff4fa0", 3.0), ("#ffc24a", 3.0), ("#57e08a", 3.0),
       ("#49c6ff", 3.0), ("#a97dff", 3.0)]
LEDS = [Material("a2led%d" % i, c, roughness=0.3, emissive=c,
                 emissive_strength=s) for i, (c, s) in enumerate(RGB)]
COVEM = Material("a2cove", "#f0f6ff", roughness=0.3, emissive="#cfe3ff",
                 emissive_strength=2.8)


# `blit`/`_blit` author on a wall in that wall's OWN frame, and for the south
# and west walls that frame runs BACKWARDS from room coordinates (s: world x =
# W - a;  w: world z = D - a).  Round 1 drew the Movie Room door casing straight
# from room coordinates and put it 9 ft from the hole.  Everything below is
# authored in ROOM coordinates and converted here.
def SA(x):      # room x  -> south-wall along-coordinate
    return W - x


def WA(z):      # room z  -> west-wall along-coordinate
    return D - z


def wpanel(sub, mat, pts, a, y, d0=0.0, d1=0.09):
    """A flat polygon standing on a wall, given in that wall's (along, height)
    frame -- built by explicit vertex construction rather than a rotation, so
    the winding is whatever `prism` produced and cannot come out inside-out."""
    p = Model()
    p.add(prism(pts, d1 - d0), mat)
    for part, mm in p._parts:
        sub._parts.append((Part([(a + px, y + pz, d0 + py)
                                 for (px, py, pz) in part.verts],
                                part.tris, part.smooth), mm))


SH_N = 6
# ONE coplanar layer of NON-OVERLAPPING annuli, each carrying its own alpha.
# Ten stacked translucent layers (kit.contact_shadow's shape) metered as a 0.5%
# darkening in this scene -- coincident transparent triangles inside a single
# primitive do not accumulate here, which is why several rooms have shipped
# shadows that meter as no shadow at all.  These do not overlap, so what is
# authored is what renders.
SHMATS = [Material("a2sh%d" % j, "#24242a", roughness=0.98,
                   opacity=round(0.50 * (1.0 - j / float(SH_N)) ** 1.25 + 0.015,
                                 4))
          for j in range(SH_N)]


def _sellipse(cx, cz, ex, ez, y, seg=28, n=2.6, room=None):
    pts = []
    for k in range(seg):
        t = 2 * math.pi * k / seg
        ct, st = math.cos(t), math.sin(t)
        px = cx + ex * math.copysign(abs(ct) ** (2.0 / n), ct)
        pz = cz + ez * math.copysign(abs(st) ** (2.0 / n), st)
        if room:
            px = min(max(px, 0.05), room[0] - 0.05)
            pz = min(max(pz, 0.05), room[1] - 0.05)
        pts.append((px, y, pz))
    return pts


def cshadow(m, cx, cz, hx, hz, feather=0.80, y=0.050, strength=1.0,
            room=None, seg=16):
    """Contact shadow: full darkness at the piece's own footprint, feathering
    OUT over `feather` feet.  `strength` scales the whole ramp (1.0 = the
    measured house default, ~35% at the contact edge)."""
    inner = _sellipse(cx, cz, hx, hz, y, seg, room=room)
    # the core, so the band right at the edge is not a lone outline
    core = Model()
    core.add(Part([(cx, y, cz)] + inner,
                  [(0, 1 + (k + 1) % seg, 1 + k) for k in range(seg)],
                  smooth=True),
             SHMATS[0] if strength > 0.85 else SHMATS[min(SH_N - 1, 2)])
    for part, mm in core._parts:
        m._parts.append((part, mm))
    for j in range(SH_N):
        f0 = feather * (j / float(SH_N)) ** 1.0
        f1 = feather * ((j + 1) / float(SH_N)) ** 1.0
        a = _sellipse(cx, cz, hx + f0, hz + f0, y, seg, room=room)
        b = _sellipse(cx, cz, hx + f1, hz + f1, y, seg, room=room)
        v = a + b
        tris = []
        for k in range(seg):
            k2 = (k + 1) % seg
            tris += [(k, seg + k2, seg + k), (k, k2, seg + k2)]
        idx = min(SH_N - 1, int(j / max(0.15, strength)))
        # smooth=True on a COPLANAR fan/band is not smoothing -- every face
        # shares one normal -- but it makes `_weld` share vertices instead of
        # emitting three per triangle, which is a 3x saving on every shadow in
        # the room and most of what pays for the north wall.
        m.add(Part(v, tris, smooth=True), SHMATS[idx])


def plant(m, cx, cz, h, scale=1.0, seed=1, pot=None, on=0.0):
    """A leafy floor/desk plant.  Round 2's were under-scaled two-inch tufts;
    the photos' are 2-3 ft of broad leaf on a long stem."""
    rnd = Rnd(seed)
    pr = 0.30 * scale
    m.add(cylinder(pr, 0.46 * scale, 12, r_top=pr * 0.82), pot or POTW,
          at=(cx, on, cz))
    m.add(cylinder(pr * 0.80, 0.06, 10),
          Material("a2soil", "#3a352e", roughness=0.95),
          at=(cx, on + 0.44 * scale, cz))
    n = 7
    for k in range(n):
        a = R(360.0 * k / n + rnd.f(-14, 14))
        lean = 0.30 + rnd.f(0.0, 0.42)
        ln = (h - 0.46 * scale) * (0.55 + rnd.f(0.0, 0.5))
        ex, ez = math.cos(a) * lean * ln, math.sin(a) * lean * ln
        m.add(box(0.035 * scale, ln, 0.035 * scale), GREEN,
              at=(cx + ex * 0.30, on + 0.40 * scale, cz + ez * 0.30),
              rot_z=R(-18 * lean), rot_y=-a)
        m.add(box(0.44 * scale, 0.030, 0.30 * scale), GREEN,
              at=(cx + ex, on + 0.40 * scale + ln * 0.86, cz + ez),
              rot_y=-a, rot_z=R(26))


def api(method, path, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def house():
    with urllib.request.urlopen(f"{BASE}/api/house", timeout=30) as r:
        return json.loads(r.read().decode())


def drop_objects(names):
    h = house()
    for f in h["floors"]:
        for rm in f["rooms"]:
            if rm["id"] != ROOM:
                continue
            for o in rm.get("objects", []):
                if o.get("name") in names:
                    req = urllib.request.Request(
                        f"{BASE}/api/house/object/{o['id']}", method="DELETE")
                    urllib.request.urlopen(req, timeout=30).read()
                    print(f"  deleted stale object {o['name']!r}")


def openings():
    """One real cut opening: the Movie Room door.  Edge 2 is the south wall and
    runs (W,D)->(0,D), so its offset counts BACK from x=W."""
    room = next(rm for f in house()["floors"] for rm in f["rooms"]
                if rm["id"] == ROOM)
    have = {(o["edge_index"], o["type"]): o for o in room.get("openings", [])}
    spec = dict(edge_index=2, type="door", offset=W - MDOOR[1],
                width=MDOOR[1] - MDOOR[0], height=6.83, elevation=0.0)
    if (2, "door") in have:
        api("PATCH", f"/api/house/opening/{have[(2, 'door')]['id']}", spec)
        print("  opening south door verified")
    else:
        api("POST", f"/api/house/room/{ROOM}/opening", spec)
        print("  opening south door created")


# ================================================================== ceiling
def build_ceiling():
    m = ceiling(W, D, H,
                cans=[(9.0, 2.6), (15.2, 2.6),
                      (7.6, 11.6), (13.4, 11.6),
                      (9.0, 20.8), (15.2, 20.8)],
                speakers=[(17.2, 4.2, 0.54), (17.2, 12.4, 0.54),
                          (17.2, 19.8, 0.54), (5.0, 15.4, 0.54)],
                vents=[(11.2, 11.4, 1.00, 0.55)])
    # smoke detector
    m.add(cylinder(0.28, 0.09, 14), Material("a2smk", "#f2f1ee", roughness=0.5),
          at=(11.6, H - 0.11, 6.2))
    return save_and_place("Arcade Ceiling", m, ROOM)


# ================================== skirting, doors, the NW utility room block
def build_trim():
    m = baseboards(W, D, doors=[("s", 0.0, W)])
    # the south skirting runs on the VISIBLE south face, SD in from z = D
    sk = [(MDOOR[0] - CASE_W, MDOOR[1] + CASE_W)]
    for a, b in spans(W, sk):
        bx(m, TRIM, a, b, 0.0, BB_H - 0.06, D - SD - BB_T, D - SD)
        bx(m, TRIM, a, b, BB_H - 0.06, BB_H, D - SD - BB_T * 0.72, D - SD)
    # the Movie Room door.  Its leaf and casing have to stand clear of the
    # neighbour's wall mass, so it is built as a real 0.40 ft reveal: lining
    # back to our own z = D, leaf and casing on the room side of SD.
    sub = Model()
    a0, a1 = SA(MDOOR[1]), SA(MDOOR[0])
    for (aa, bb) in ((a0 - 0.05, a0), (a1, a1 + 0.05)):
        bx(sub, TRIM, aa, bb, 0.0, 6.83, 0.0, SD)
    bx(sub, TRIM, a0, a1, 6.83, 6.88, 0.0, SD)
    panel_door(sub, WHITEWD, a0 + 0.05, a1 - 0.05, 0.0, 6.83, SD + 0.02,
               SD + 0.17)
    for (aa, bb) in ((a0 - CASE_W, a0 + 0.03), (a1 - 0.03, a1 + CASE_W)):
        bx(sub, TRIM, aa, bb, 0.0, 6.83 + CASE_W, SD, SD + 0.20)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, 6.83, 6.83 + CASE_W, SD, SD + 0.20)
    sub.add(cylinder(0.080, 0.05, 12), BLACKMET,
            at=(a0 + 0.36, 3.05, SD + 0.22), rot_x=R(90))
    blit(m, sub, "s", W, D, 0.0)

    # ---- the NW utility closet.  Round 2 left this a raw white cuboid: no
    # skirting, no cap, and blank north and west faces, which are exactly the
    # two the dollhouse quadrant puts in the foreground.
    px0, px1, pz0, pz1 = PIER
    PIERM = Material("a2pier", "#dcdbd8", roughness=0.95)
    bx(m, PIERM, px0, px1, 0.0, H - 0.02, pz0, pz1 - 0.14)
    bx(m, TRIM, px0, px1, 0.0, H - 0.02, pz1 - 0.14, pz1)         # its face
    # skirting round the other three faces, and a two-step cap at the head
    bx(m, TRIM, px0, px1, 0.0, BB_H, pz0 - BB_T, pz0)
    bx(m, TRIM, px1, px1 + BB_T, 0.0, BB_H, pz0 - BB_T, pz1 + BB_T)
    bx(m, TRIM, px0 - 0.04, px1 + 0.16, H - 0.46, H - 0.30,
       pz0 - 0.16, pz1 + 0.16)
    bx(m, TRIM, px0 - 0.02, px1 + 0.10, H - 0.30, H - 0.02,
       pz0 - 0.10, pz1 + 0.10)
    # its north face is the alcove's back wall -- give it a picture rail and
    # two framed prints so it is not 5 ft of blank plaster in the hero frame
    RAIL = Material("a2rail", "#e6e4df", roughness=0.7)
    bx(m, RAIL, px0, px1, 5.30, 5.44, pz0 - 0.06, pz0)
    for (a, b, hue) in ((0.55, 2.25, "#243040"), (2.75, 4.55, "#2c2333")):
        bx(m, BLACKMET, a, b, 2.55, 4.95, pz0 - 0.055, pz0 - 0.005)
        bx(m, Material("a2pr" + hue[1:], hue, roughness=0.7),
           a + 0.07, b - 0.07, 2.62, 4.88, pz0 - 0.075, pz0 - 0.055)
    for a, b in spans(px1 - px0, [(PDOOR[0] - CASE_W, PDOOR[1] + CASE_W)]):
        bx(m, TRIM, a, b, 0.0, BB_H, pz1, pz1 + BB_T)
    # the face already looks +z, which is the direction panel_door authors in
    panel_door(m, WHITEWD, PDOOR[0] + 0.03, PDOOR[1] - 0.03, 0.0, 6.83,
               pz1 - 0.02, pz1 + 0.10)
    for a, b in ((PDOOR[0] - CASE_W, PDOOR[0] + 0.03),
                 (PDOOR[1] - 0.03, PDOOR[1] + CASE_W)):
        bx(m, TRIM, a, b, 0.0, 6.83 + CASE_W, pz1, pz1 + 0.20)
    bx(m, TRIM, PDOOR[0] - CASE_W, PDOOR[1] + CASE_W, 6.83, 6.83 + CASE_W,
       pz1, pz1 + 0.20)
    m.add(cylinder(0.075, 0.05, 10), BLACKMET,
          at=(PDOOR[1] - 0.34, 3.05, pz1 + 0.22), rot_x=R(90))
    # the little white bin standing beside the door (photo v3 1)
    m.add(cylinder(0.44, 1.05, 14, r_top=0.40), WHTM, at=(4.30, 0.0, pz1 + 0.55))
    return save_and_place("Arcade Baseboards", m, ROOM)


# ================================================================== cabinets
# ROUND 3.  Round 2's uprights were the same box seven times with the hue
# swapped -- three flat colour fields (marquee / screen / lower panel) and a
# control panel that projected 0.06 ft past the carcase.  Both are fixed here:
#
#   * the body is a SWEPT SIDE PROFILE (a2kit.sweep), so the silhouette is real
#     geometry: base, apron, a control deck standing 0.70 ft proud of the
#     carcase front, a raked screen face, a marquee that overhangs, a stepped
#     or straight head.  Four profiles, and width / height / deck height /
#     marquee depth all vary per machine, so no two read alike end-on.
#   * every visible panel carries PRINTED ARTWORK rather than a hue.  ROUND 4
#     replaced what that artwork IS: round 3 sampled a shared 16-tile atlas in
#     which twelve tiles were one drawing in twelve hues, and its critic counted
#     one machine repeated sixteen times.  Now each machine is drawn
#     individually and takes its OWN `<slug>.marquee/.side/.front/.deck` out of
#     its wall run's `a2kit.ArtSet` -- see scratchpad/arc4/atlas4.py.
#
# It is also five times cheaper -- ~160 verts a machine against ~850 for the
# box stack -- which is what buys the north wall inside the payload cap.

DECK_OUT = 0.70                     # control-deck projection past the carcase

STYLES = ("straight", "slope", "step", "riser")


# ---------------------------------------------------------------------------
# ROUND 5 -- per-machine control hardware and coin doors.
#
# Round 4 built ONE deck and ONE coin door for all sixteen cabinets, inline in
# `upright()`: two chrome shafts with a red and a blue cube on top, six flat
# square buttons cycling four shared colours, and a 0.68 x 0.62 ft grey plate
# dead centre on every front.  Three independent critics named that as the
# defect.  `decks5.py` merges the four art modules' own specifications (they
# each invented a different schema; see its docstring) and everything below
# just builds what it returns.  No layout, colour or size is chosen here.
#
# COST.  A button is cheap but not free, and the room has ~1 KB of headroom.
# `button_cap` is art_g1's measured recipe -- a welded domed octagon fan, 9
# verts / 8 tris / 310 B in a saved GLB -- against 669 B for a flat unwelded
# 8-gon, 813 B for `cylinder(r, h, 8)` and 2350 B for `prism(octagon, h)`.
# 129 buttons and 21 sticks across the room come in at +6.9 KB of geometry over
# round 4's 128 flat squares and 32 cubes, which is what per-machine hardware
# costs.
# COST, and why the hardware is VERTEX-COLOURED rather than one material per
# colour.  This room's 129 buttons, 21 sticks, 4 guns, 2 trackballs, a yoke and
# a steering wheel carry about 30 distinct colours.  `Model.add` groups by
# material INSTANCE and `save()` writes one glTF primitive per group, so a
# material per colour cost 44 primitives on the east run alone -- and a
# primitive is ~0.9 KB of accessors, bufferViews and JSON before a single
# triangle is in it.  MEASURED: 44 materials 158.3 KB of geometry on east,
# 3 materials + COLOR_0 91.7 KB, for identical geometry.  COLOR_0 is 4 bytes a
# vertex; a primitive is a thousand.
#
# Triangles still matter (~78 bytes each after welding), so the caps are cheap
# on purpose: `button_cap` is art_g1's measured recipe -- a welded domed n-gon
# fan, no side wall -- at 6 segments, and ball tops are seg 6 / rings 2.  At
# 0.05-0.07 ft a button is 1.2 in across and seen from 6-10 ft; a hexagon reads
# round and an octagon costs a third more for nothing.
HW = Material("a2hw", "#ffffff", roughness=0.42)      # vertex-coloured plastic
HWM = Material("a2hwm", "#ffffff", roughness=0.26, metallic=0.55)   # chrome
# ROUND 7 -- THE a2hw ROUGHNESS DEFECT, AND WHY IT IS A SECOND MATERIAL AND NOT
# A NEW NUMBER ON THE OLD ONE.
#
# The round-6 integrator flagged a2hw's 0.42 as blowing out every up-facing cap
# in the room, and all four art modules asked for it to move -- but they asked
# in two directions.  art_g0's BUTTON_MAT_REQUEST wants 0.70-0.72, art_g2's
# HW_HINTS wants 0.55-0.62, and art_g1's CONTROL_FINISH wants 0.26-0.28 because
# its four machines' ball tops are BLACK and it wants them glossy.  They are
# not really disagreeing: a rough value protects a pale up-facing crown from
# the ceiling cans, and a smooth one gives a dark crown the one small highlight
# the photograph shows.  Both are true, and the surface they are true about is
# the same surface.
#
# a2hw is NOT the button material -- it also carries coin-door plates, gun
# bodies, holster channels, the Star Wars yoke and Ridge Racer's wheel, all of
# which are vertical or near-vertical and which round 6 rendered acceptably at
# 0.42.  Moving 0.42 would have changed all of those to fix the caps.  So the
# up-facing hardware gets its own material and the value is METERED, not
# chosen: see the round-7 report's roughness sweep.  The cost is exactly one
# extra glTF primitive per cabinet GLB.
BTN = Material("a2btn", "#ffffff", roughness=0.70)   # crowns + ball tops, UP
_MATS = {}


def cmat(col, rough=0.40, metal=0.0, emis=None, es=0.0):
    """A cached Material, for the FEW things that genuinely cannot be vertex
    coloured -- glTF emissive is a flat per-material factor.  Two survive:
    Legends Ultimate's lit white front-lip strip and Ridge Racer's two big
    white buttons, both of which the photographs show lit."""
    key = (col, rough, metal, emis, es)
    m = _MATS.get(key)
    if m is None:
        m = Material("a2c%02d" % len(_MATS), col, roughness=rough,
                     metallic=metal, emissive=emis, emissive_strength=es)
        _MATS[key] = m
    return m


def _hexf(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16) / 255.0, int(c[2:4], 16) / 255.0,
            int(c[4:6], 16) / 255.0)


def cpart(part, col):
    """Paint every vertex of `part` one colour, in place."""
    part.colors = [_hexf(col)] * len(part.verts)
    return part


def cbx(m, col, x0, x1, y0, y1, z0, z1, mat=None):
    """`bx` in a vertex colour."""
    if x1 - x0 <= 0 or y1 - y0 <= 0 or z1 - z0 <= 0:
        return
    m.add(cpart(box(x1 - x0, y1 - y0, z1 - z0), col), mat or HW,
          at=((x0 + x1) / 2.0, y0, (z0 + z1) / 2.0))


def cface(m, col, x0, x1, y0, y1, z, mat=None):
    """A single forward-facing quad in a vertex colour -- 2 triangles where a
    box is 12.  Coin slots, return cups and door bezels are RELIEF, 0.006 ft
    proud, and every one of them is already drawn into the machine's printed
    front artwork at the same coordinates; building them as boxes cost 30 KB
    across the room for detail no camera can resolve as a solid."""
    m.add(cpart(quad((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)), col),
          mat or HW)


# ------------------------------------------------------- extruded profiles
# A LIGHT GUN IS A SILHOUETTE, NOT A BLOCK.  Round 5 built each of the room's
# four guns as a coloured box standing on a darker box on a plate; from the
# judged south poses they read as a red slab and a blue slab, the crudest
# objects in the room.  What a gun is at 0.6 ft is one CONCAVE side profile --
# backstrap, receiver, a step down to the barrel, the muzzle, the frame, the
# trigger guard's front and bottom straps, the recess behind them and the
# raked grip -- pushed across the gun's width.  `prism()` cannot build it:
# its caps are a triangle FAN from vertex 0, which folds over itself on any
# concave outline, so the caps are ear-clipped here.
#
# COST, and why this is nearly free.  `_weld` duplicates a vertex per face on
# a flat-shaded part (~84 bytes a triangle) and shares them on a smooth one
# (~28 a vertex + 12 a triangle).  Splitting the extrusion into TWO smooth
# parts gets flat shading where it belongs without paying for it: every
# vertex of the CAP part touches only cap triangles, which all share one
# normal, so averaging them returns that exact normal and the two big side
# faces stay dead flat; every vertex of the BAND part touches only its two
# neighbouring side quads, so the outline's edges round over the way moulded
# plastic does.  MEASURED (marginal, 41 copies minus 1, in a saved GLB): the
# 13-point gun plus its 8-point holster is 3264 bytes against the 3456 of the
# three boxes it replaces -- 76 triangles for 36 and yet 192 bytes CHEAPER,
# because a flat box pays for 24 unshared vertices to carry 12 triangles.
def _in_tri(p, a, b, c):
    d = ((b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1]))
    if abs(d) < 1e-12:
        return False
    u = ((b[1] - c[1]) * (p[0] - c[0]) + (c[0] - b[0]) * (p[1] - c[1])) / d
    v = ((c[1] - a[1]) * (p[0] - c[0]) + (a[0] - c[0]) * (p[1] - c[1])) / d
    return u >= -1e-9 and v >= -1e-9 and u + v <= 1.0 + 1e-9


def _earclip(p):
    """Triangulate a simple CCW polygon, concave allowed."""
    idx, out, guard = list(range(len(p))), [], 0
    while len(idx) > 2 and guard < 4 * len(p) * len(p):
        guard += 1
        m = len(idx)
        for k in range(m):
            a, b, c = idx[(k - 1) % m], idx[k], idx[(k + 1) % m]
            if ((p[b][0] - p[a][0]) * (p[c][1] - p[a][1])
                    - (p[b][1] - p[a][1]) * (p[c][0] - p[a][0])) <= 1e-10:
                continue                                   # reflex corner
            if any(_in_tri(p[j], p[a], p[b], p[c])
                   for j in idx if j not in (a, b, c)):
                continue
            out.append((a, b, c))
            idx.pop(k)
            break
        else:
            break
    return out


def _extrude(prof, w, cols):
    """A concave (a, b) profile pushed `w` feet along local +z.

    Returns (caps, band) -- see the note above for why they are two parts.
    Local axes: a -> +x, b -> +y, the extrusion centred on z.  `cols` is one
    '#rrggbb' per profile point, so a gun can be dark at the grip and its own
    colour at the body without a second material or a second primitive.
    """
    p = list(prof)
    c = list(cols)
    n = len(p)
    if sum(p[i][0] * p[(i + 1) % n][1] - p[(i + 1) % n][0] * p[i][1]
           for i in range(n)) < 0.0:                       # force CCW
        p.reverse()
        c.reverse()
    h = w / 2.0
    v = [(a, b, -h) for (a, b) in p] + [(a, b, h) for (a, b) in p]
    fc = [_hexf(k) for k in c] * 2
    tri = _earclip(p)
    caps = Part(v, [(a, cc, b) for (a, b, cc) in tri]      # -z, wound back
                + [(a + n, b + n, cc + n) for (a, b, cc) in tri],
                smooth=True, colors=fc)
    side = []
    for i in range(n):
        j = (i + 1) % n
        side += [(i, j, i + n), (j, j + n, i + n)]
    return caps, Part(v, side, smooth=True, colors=fc)


# The gun's side profile, normalised to its length: a forward from the
# backstrap, b up from the grip's heel.  Read off docs/photos-jpg/Arcade Room
# v4 4.jpg px (60,170)-(115,210), the one frame in the room where a light
# gun's outline actually resolves -- Time Crisis's blue gun, showing a chunky
# receiver, a stepped barrel, a guard and a strongly raked grip.
_GUN_PROFILE = (
    (0.150, 0.660),   # backstrap top
    (0.560, 0.660),   # receiver top, front
    (0.640, 0.585),   # step down to the barrel
    (1.000, 0.575),   # muzzle, top
    (1.000, 0.495),   # muzzle, bottom
    (0.610, 0.485),   # under the barrel, back to the frame
    (0.500, 0.300),   # trigger guard, front strap
    (0.430, 0.248),   # trigger guard, bottom front
    (0.320, 0.285),   # trigger guard, bottom rear (open backed)
    (0.345, 0.430),   # up into the trigger recess
    (0.300, 0.430),   # frame underside / top of the grip front
    (0.172, 0.052),   # grip front, bottom
    (0.000, 0.021),   # grip heel
)
# indices whose vertices take the GRIP colour rather than the body's
_GUN_GRIP = (10, 11, 12, 0)
_GUN_PITCH = math.radians(12.0)   # nose-up, resting in the holster


# ---------------------------------------------------------------------------
# ROUND 7 -- A BUTTON IS AN OBJECT, NOT A DECAL.
#
# Four critics rejected round 6 with one sentence between them: "the
# pushbuttons are painted into the control-deck texture rather than modelled:
# flat 2-3 px coloured lozenges with no dome, no rim shadow and no specular".
# They were describing real geometry, and they were still right about it.
# `art_g1.button_cap` -- which rounds 5 and 6 used for every cap in the room --
# is a DOMED FAN AND NOTHING ELSE: an apex vertex, one ring at y = h*(1-dome),
# and `seg` triangles between them.  It has no side wall at all, so it does not
# touch the deck: what stands on a machine here is a shallow disc floating
# 0.015 ft above the artwork with open air under its rim.  At NBA Jam's numbers
# the whole cap rises 0.0126 ft across a 0.055 ft radius, i.e. 13 degrees off
# flat, and there is no silhouette anywhere to break it.  That is a lozenge.
#
# `btn_geo` builds the object the photograph shows -- docs/photos-jpg/Arcade
# Room v4 6.jpg px (460,360)-(600,440) at 10x is the closest any frame gets to
# a button in this room and it resolves Marvel Super Heroes' seven caps
# completely: a coloured translucent CROWN standing proud on a FLANGE that
# flares down to the panel, each one sitting in its own dark seat ring, each
# one carrying one small specular.  Three parts of that are geometry:
#
#   ring 0   y = 0,          radius r        the flange where it meets the deck
#   ring 1   y = h - rise,   radius cap_r    the shoulder
#   apex     y = h                           the crown
#
# so the wall between rings 0 and 1 is a truncated cone that faces sideways and
# DOWN-AND-OUT, and in a room with one overhead sun it renders darker than both
# the deck it stands on and the cap it carries.  That is the rim the critics
# asked for and it is not painted: it moves with the camera, it is on the far
# side at the far end of a run, and it disappears from a plan view -- the test
# ROOM-BRIEF sets for anything that looks like baked light.
#
# COST, MEASURED, because the room has single-digit KB of headroom.  One part,
# smooth, seg 6: 13 vertices / 18 triangles against `button_cap`'s 7 / 6.
# Over the room's 152 caps that is +5.7 KB of geometry.  It is paid for twice
# over by dropping the emissive from every cap (decks5._btn, -20.8 KB across
# the three cabinet GLBs -- 26 fewer glTF primitives), which is the same change
# art_g1's CONTROL_FINISH asked for on rendering grounds.  Smooth is what makes
# it affordable: the round-6 gun agent measured a smooth multi-part extrusion
# CHEAPER than the flat boxes it replaced (-192 bytes for +40 triangles),
# because a flat-shaded face duplicates its vertices to carry its normal.  A
# button gets the same treatment for the same reason -- and a moulded plastic
# crown really does round over at the shoulder, so the smooth normal is also
# the right one.
def btn_geo(r, cap_r, h, rise, seg=6):
    """One arcade pushbutton as (verts, tris, smooth).  Origin on the deck."""
    cap_r = max(0.004, min(cap_r, r * 0.96))
    rise = max(0.002, min(rise, h * 0.80))
    hw = max(0.002, h - rise)
    v = []
    for (rr, yy) in ((r, 0.0), (cap_r, hw)):
        for i in range(seg):
            a = 2.0 * math.pi * (i + 0.5) / seg
            v.append((math.cos(a) * rr, yy, math.sin(a) * rr))
    v.append((0.0, h, 0.0))
    ap = 2 * seg
    t = []
    for i in range(seg):
        j = (i + 1) % seg
        t.append((i, j, j + seg))
        t.append((i, j + seg, i + seg))
        t.append((i + seg, j + seg, ap))
    return v, t, True


# The one authored albedo this round moves, and it is metered, not taste.
# A near-white sphere facing straight up is the brightest thing a control deck
# can carry in this room: at #f2f2ec Golden Tee's trackball rendered a flat
# clipped cap with no shading across its whole crown.  ROOM-BRIEF's rule for
# this is explicit -- a piece and a wall do not render alike at the same
# albedo, and an up-facing surface collects about twice what a vertical one
# does -- so the fix is to author the ball where it RENDERS at the photograph's
# value, not where it prints.  `_TB_CEIL` is the highest albedo that still
# leaves the crown a gradient rather than a plateau; anything paler is only
# darker in the file and identical in the frame.
_TB_CEIL = 0.78

# ...and the same argument at the other end of the scale.  ROUND 7, METERED.
# docs/photos-jpg/Arcade Room v4 6.jpg px (460,360)-(600,440) at 10x resolves
# Marvel Super Heroes' deck completely.  Metered on that crop: the pale panel
# 185.4, a white cap 223.9, a red cap 91.7, a blue cap 110.2 -- and the BLACK
# BALL TOP 48.8, i.e. 0.26 of its own panel.  Round 6 rendered that panel at
# 177.2, within 5% of the photograph, and its black ball tops at 5.8 out of
# 255.  Eight times too dark, on the largest piece of hardware any of these
# machines carries.
#
# It is not a roughness problem and I measured that rather than assuming it:
# sweeping a2btn 0.42 / 0.62 / 0.72 moves the white cap 234.3 / 234.3 / 234.3
# and the blue 121.9 / 120.4 / 118.2 -- the coloured caps do not care at all --
# and moves the black ball only 3.7 / 5.8 / 7.4.  There is no roughness that
# reaches 48.8 from an authored 22/23/27.  It is the renderer: one sun, no
# bounce, and a sphere whose whole lower half faces a floor that returns
# nothing.  The photograph's 48.8 is mostly sheen off a curved black plastic
# surface, and this scene has no source to put there.
#
# So dark HARDWARE is lifted to a metered floor, exactly the way a2kit already
# lifts printed artwork with ART_D / ART_DK / ART_DM for the same reason, and
# it is declared here and in rooms/2.json rather than quietly folded into an
# art module's authored hex.  It applies ONLY to vertex-coloured parts on the
# BTN material -- crowns, ball tops, bat tops, the trackball -- never to the
# carcase, the T-molding, the coin doors or the guns, which meter correctly.
# `_HW_FLOOR` is solved from the render, see the report's table.
_HW_FLOOR = 44.0


def _hw(c):
    """Lift a hardware colour to the metered floor, hue preserved."""
    if _HW_FLOOR <= 0.0:
        return c
    h = c.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = max(r, g, b)
    if m >= _HW_FLOOR or m == 0:
        return c
    k = _HW_FLOOR / float(m)
    return "#%02x%02x%02x" % (min(255, int(r * k)), min(255, int(g * k)),
                              min(255, int(b * k)))


def _tb_col(c):
    h = c.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = max(r, g, b)
    if m <= _TB_CEIL * 255.0:
        return c
    k = _TB_CEIL * 255.0 / m
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))


def controls(sub, slug, bw, ft, fd, dy):
    """Build one machine's control deck from its `decks5` spec.

    Round 4 built the same two chrome shafts with a red and a blue cube on top
    and the same six flat square buttons here regardless of `slug`.  Nothing
    below chooses a layout, a colour or a size -- every number comes from the
    art module that read it off the owner's photographs (`decks5.why`).
    """
    spec = deck_for(slug, bw)
    if not spec:
        return
    aw = bw - 0.12
    zb, ze = ft + 0.04, fd - 0.06
    y = dy + 0.014                      # the deck ART plane; parts sit ON it

    def X(t):
        return -bw / 2.0 + 0.06 + t * aw

    def Z(v):
        return zb + v * (ze - zb)

    for b in spec["buttons"]:
        rise = b["rise"] if b["profile"] == "convex" else b["h"] * 0.14
        # seg 6 on every cap.  seg 5 was measured first and saves 3.9 KB over
        # the room's 152 buttons, but a pentagon reads as a pentagon in the
        # dollhouse quadrant and on the two close deck frames, and the 3.9 KB
        # is not needed -- the uint16 index change below pays for far more.
        seg = 6
        v, t, sm = btn_geo(b["r"], b["cap_r"], b["h"], rise, seg)
        pt = Part(v, t, smooth=sm)
        at = (X(b["t"]), y, Z(b["v"]))
        if b["emis"]:
            # the ONLY emissive buttons in the room: art_g3 flagged Ridge
            # Racer's two big white ones as lit, and nothing else is.  Every
            # other cap in the room lost its emissive this round -- see
            # decks5._btn.
            sub.add(pt, cmat(b["col"], 0.34, 0.0, b["col"], 0.75), at=at)
        else:
            sub.add(cpart(pt, _hw(b["col"])), BTN, at=at)

    for s in spec["sticks"]:
        x, z = X(s["t"]), Z(s["v"])
        y0 = y
        if s["washer_r"] > 0.001 and s["washer_col"]:
            sub.add(cpart(cylinder(s["washer_r"], 0.014, 6), s["washer_col"]),
                    HWM, at=(x, y0, z))
            y0 += 0.010
        # 4 segments: a joystick shaft is 0.055 ft across -- two thirds of an
        # inch -- and seen from six feet.  6 segments cost 30% more for a
        # difference no frame resolves.
        sub.add(cpart(cylinder(s["shaft_r"], s["shaft_h"], 4), s["shaft_col"]),
                HWM, at=(x, y0, z))
        top = s["top"]
        if top == "ball":
            r = s["top_r"]
            v, t, sm = ball_top(r, seg=6, rings=3)
            sub.add(cpart(Part(v, t, smooth=sm), _hw(s["top_col"])), BTN,
                    at=(x, y0 + s["shaft_h"] - r * 0.4, z))
        elif top == "bat":
            sub.add(cpart(cylinder(s["top_r"], s["top_h"], 6,
                                   r_top=s["top_r"] * 0.8), _hw(s["top_col"])),
                    BTN, at=(x, y0 + s["shaft_h"], z))

    tb = spec["trackball"]
    if tb:
        x, z, r = X(tb["t"]), Z(tb["v"]), tb["r"]
        sub.add(cpart(cylinder(r * 1.28, 0.018, 10), tb["bezel"]), HW,
                at=(x, y, z))
        v, t, sm = ball_top(r, seg=8, rings=4)
        # ROUND 7.  Seated so exactly the upper hemisphere stands proud of the
        # bezel, as before -- what changed is the material and one ring.
        # Golden Tee's ball is the object the round-6 integrator flagged as
        # "a bright white dome": it is 3 in across, it faces straight up, it
        # was authored #f2f2ec (albedo 242) and it ran through a2hw at
        # roughness 0.42, so it returned both the sun and the ceiling cans and
        # clipped.  It is NOT white in the photograph -- `roster/W_gt_deck_nn`
        # shows a pale ball on a bright green fairway, lighter than the deck
        # but well inside it.  It now runs through BTN like every other
        # up-facing cap and its albedo is metered against the fairway rather
        # than authored at paper white (see `_TB_CEIL`).  rings 3 -> 4 costs
        # 8 verts and is what stops a 40 px dome faceting.
        sub.add(cpart(Part(v, t, smooth=sm), _tb_col(tb["col"])), BTN,
                at=(x, y + 0.018 - r, z))

    sp = spec["spinner"]
    if sp:
        sub.add(cpart(cylinder(sp["r"], 0.055, 8, r_top=sp["r"] * 0.88),
                      sp["col"]), HWM, at=(X(sp["t"]), y, Z(sp["v"])))

    for g in spec["guns"]:
        x, z, ang = X(g["t"]), Z(g["v"]), R(g["yaw"])
        if abs(g["yaw"]) < 0.01:
            # DECLARED INFERENCE.  art_g2 read Time Crisis's two guns as lying
            # at +24 and -8 deg and those stand; T2's pair carries yaw 0, which
            # is the schema's default and not a reading -- its note records
            # only "blue LEFT and red RIGHT".  Left at 0 both guns point their
            # muzzles straight at any camera square to the south wall, which is
            # every judged south frame, and a gun seen end-on is a blob.  So a
            # gun whose angle was NOT read is splayed 26 deg outward from the
            # deck centre, which is how a two-gun deck's holsters actually sit.
            ang = R(-26.0 if g["t"] < 0.5 else 26.0)
        L = g["len"]
        dx, dz = math.sin(ang), math.cos(ang)
        yb = y
        gw = L * 0.235                               # across the gun
        # The deck is only 0.92 ft front to back and a gun is 0.58-0.62, so the
        # gun is centred on its printed socket: butt 0.48 L behind it, muzzle
        # 0.52 L in front, which fits the 0.44-0.48 ft either side.
        bx_, bz_ = x - dx * L * 0.48, z - dz * L * 0.48
        if g["cradle"]:
            # The moulded holster SOCKET the butt drops into -- a U channel: a
            # floor with a wall either side, its CROSS-SECTION extruded along
            # the gun and only as long as the grip, so the barrel overhangs it
            # the way a holstered gun's does.  `rot_y = ang` and not `ang - 90`
            # because this profile's `a` runs ACROSS the gun where the gun's
            # own runs along it.  Round 5 built this as a flat plate the full
            # width of the deck slot, which read as a pedestal.
            hw, ch, fl, wt = gw * 0.5 + 0.030, 0.075, 0.020, 0.026
            cu = ((-hw, 0.0), (hw, 0.0), (hw, ch), (hw - wt, ch),
                  (hw - wt, fl), (-hw + wt, fl), (-hw + wt, ch), (-hw, ch))
            cc = [g["cradle_col"] or "#20202a"] * 8
            for pt in _extrude(cu, L * 0.42, cc):
                sub.add(pt, HW,
                        at=(bx_ + dx * L * 0.095, yb, bz_ + dz * L * 0.095),
                        rot_y=ang)
            yb += fl
        # ONE concave profile carries grip, frame, trigger guard, receiver and
        # barrel -- see `_GUN_PROFILE`.  Round 5's three boxes could not carry
        # a guard at all (a box has no hole and no notch) and its "gun" was a
        # coloured bar on a dark bar.  Two light guns are all that
        # distinguishes Time Crisis and T2 from a fighting cabinet, so the
        # shape has to survive a 1400 px frame from eight feet.
        cp, sp_ = math.cos(_GUN_PITCH), math.sin(_GUN_PITCH)
        px_, pz_ = _GUN_PROFILE[12]                  # pitch about the heel
        prof = [((a - px_) * cp - (b - pz_) * sp_ + px_,
                 (a - px_) * sp_ + (b - pz_) * cp + pz_)
                for (a, b) in _GUN_PROFILE]
        drop = min(b for (_, b) in prof)
        prof = [(a * L, (b - drop) * L) for (a, b) in prof]
        gc = [g["grip"] if i in _GUN_GRIP else g["body"]
              for i in range(len(prof))]
        for pt in _extrude(prof, gw, gc):
            sub.add(pt, HW, at=(bx_, yb, bz_), rot_y=ang - math.pi / 2.0)

    yk = spec["yoke"]
    if yk:
        x, z = X(yk["t"]), Z(yk["v"])
        sub.add(cpart(cylinder(yk["column_r"], yk["column_h"], 6),
                      yk["column_col"]), HW, at=(x, y, z))
        cy = y + yk["cy"]
        hs, br = yk["half_span"], yk["bar_r"]
        sub.add(cpart(box(hs * 2.0, br * 2.0, br * 2.0), yk["bar_col"]), HW,
                at=(x, cy - br, z))
        gb = yk["grip_buttons"]
        for sgn in (-1.0, 1.0):
            sub.add(cpart(cylinder(yk["grip_r"], yk["grip_h"], 6),
                          yk["grip_col"]), HW, at=(x + sgn * hs, cy - br, z))
            v, t, sm = button_cap(gb["d"] / 2.0, gb["h"], 6)
            sub.add(cpart(Part(v, t, smooth=sm), gb["col"]), HW,
                    at=(x + sgn * hs, cy - br + yk["grip_h"], z))

    wh = spec["wheel"]
    if wh:
        x, z = X(wh["t"]), Z(wh["v"])
        cy = y + wh["cy"]
        rake = R(wh["rake_deg"])
        sub.add(cpart(cylinder(wh["column_r"], wh["cy"] * 0.95, 6),
                      wh["column_col"]), HW, at=(x, y, z))
        sub.add(cpart(torus(wh["r"], wh["rim_r"], 12, 5), wh["rim_col"]), HW,
                at=(x, cy, z), rot_x=rake)
        sub.add(cpart(cylinder(wh["hub_r"], 0.05, 8), wh["hub_col"]), HW,
                at=(x, cy, z), rot_x=rake)
        for k in range(wh["spokes"]):
            ang = 2.0 * math.pi * k / wh["spokes"] + math.pi / 2.0
            sub.add(cpart(box(wh["spoke_r"] * 2.0, wh["spoke_r"] * 1.2,
                              wh["r"]), wh["spoke_col"]), HW,
                    at=(x, cy, z), rot_y=ang, rot_x=rake)

    lp = spec["lip"]
    if lp:
        # art_g2: a lit white strip along Legends Ultimate's front lip, and it
        # IS resolved in v3 4 and v4 8.  A fixture the photograph shows, at the
        # size the photograph shows it -- which is the only emissive ROOM-BRIEF
        # allows.
        bx(sub, cmat(lp["col"], 0.35, 0.0, lp["emissive"], lp["strength"]),
           -bw / 2.0 + 0.09, bw / 2.0 - 0.09, dy - 0.012, dy - 0.012 + lp["h"],
           ze - 0.045, ze + 0.010)


def coindoors(sub, slug, bw, dy, plinth, zf):
    """Build this machine's coin door(s) -- 0, 1 or 2 of them, its own size,
    its own colour, its own place on the panel.  Every rect is ALSO painted
    into the front artwork at the same coordinates, so a machine with an empty
    list still reads; the boxes only add relief."""
    for d in coin_for(slug, bw, dy, plinth):
        x0, x1, y0, y1 = d["x0"], d["x1"], d["y0"], d["y1"]
        if x1 - x0 <= 0.01 or y1 - y0 <= 0.01:
            continue
        pr = max(0.010, d["proud"])
        if d.get("boss"):                       # a bare plunger, no plate
            sub.add(cpart(cylinder((x1 - x0) / 2.0, pr, 6), d["plate"]), HW,
                    at=((x0 + x1) / 2.0, (y0 + y1) / 2.0, zf + pr),
                    rot_x=R(-90))
            continue
        if d["trim"]:
            cface(sub, d["trim"], x0 - 0.020, x1 + 0.020, y0 - 0.020,
                  y1 + 0.020, zf + pr * 0.45, mat=HWM)
        cbx(sub, d["plate"], x0, x1, y0, y1, zf, zf + pr)   # the door IS solid
        n = d["slots"]
        if n:
            sw = min(0.026, (x1 - x0) / (n * 5.0))
            for k in range(n):
                cx = x0 + (x1 - x0) * (k + 0.5) / n
                cface(sub, "#08080b", cx - sw, cx + sw,
                      y1 - (y1 - y0) * 0.30, y1 - (y1 - y0) * 0.08,
                      zf + pr + 0.004)
        c = d.get("cup")
        if c:
            cface(sub, c["col"], c["x0"], c["x1"], c["y"] - 0.11,
                  c["y"] + 0.02, zf + pr + 0.004)


# ---------------------------------------------------------------------------
# ROUND 8 -- T-MOLDING.  A cabinet's colour is a BEAD, not a paint job.
#
# `sweep()` gives the machine its silhouette as one swept side profile: the two
# flanks carry the printed side art and the perimeter comes out as a band of
# quads in the BODY material.  Rounds 4-7 handed that band the machine's accent
# hue, so the whole carcase -- top, back, head front, apron, deck skirt, and the
# strip of front face either side of the printed panel -- was flood-filled
# green, maroon or gold.  Two round-7 critics named it and the photographs are
# unambiguous (see `a2kit.TMOLD`'s note and the crop it cites): the body is
# black and the colour is a raised plastic bead ~3/4 in wide running the seam
# between the flank and the perimeter face.
#
# WHERE IT RUNS.  The seam IS the profile outline at x0 and at x1, so one strip
# per flank gets all three runs the commission asks for at once -- the perimeter
# of the front face, the deck's front edge and the side panel's edge -- because
# the profile passes through all of them.  Two edges are dropped: the floor edge
# (prof[0] -> prof[1]) and the back edge (prof[-1] -> prof[0]).  Neither is ever
# in frame -- every machine stands against a wall -- and together they are ~20%
# of the strip.
#
# COST, and why it is a SMOOTH THREE-POINT SECTION and not boxes.  Round 6
# measured that a smooth multi-part extrusion is CHEAPER than flat-shaded boxes,
# because `glb._weld` duplicates a vertex per face when a part is flat and
# shares them when it is smooth (~28 B/vert + 6 B/tri smooth against ~84 B/tri
# flat).  The section here is three points -- a landing 0.006 ft off the flank,
# a crown 0.030 ft proud, a landing 0.006 ft off the perimeter face -- swept as
# ONE smooth strip per flank, so 3 verts and 4 triangles per profile edge with
# every vertex shared along the run.  Smooth is also what makes it read: the
# crown's averaged normal turns across the section, so the bead carries a
# specular LINE rather than two flat facets, which is exactly what the
# photograph shows (v4 7: the Turtles bead peaks (176,222,177) against a body
# metering 41-56).
#
# The bead is vertex-coloured into ONE material for the whole run, so it costs
# no glTF primitive at all -- `a2tm` is smoother than the body (0.30 against
# 0.55) because it is glossy plastic against painted melamine, and it is its own
# material rather than a2hw's 0.42 for that reason.
#
# NEITHER LANDING IS COPLANAR WITH THE SURFACE IT SITS ON.  ROOM-BRIEF records
# z-fighting twice as a class of bug in this project: the inner landing stands
# 0.006 ft off the flank plane and 0.006 ft off the perimeter face, and the
# strip is proud of both everywhere in between, so no two surfaces share a
# depth anywhere on the machine.
BEAD_A = (-0.006, 0.006)     # (dx outward past the flank, height off the face)
BEAD_B = (0.016, 0.030)      # the crown
BEAD_C = (0.056, 0.006)      # the landing on the perimeter face
TM = Material("a2tm", "#ffffff", roughness=0.30)     # vertex-coloured plastic


def _poly_ccw(p):
    s = 0.0
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        s += a[0] * b[1] - b[0] * a[1]
    return s > 0.0


def tmold(sub, prof, x0, x1, col):
    """The T-molding bead down both seams of one swept cabinet body.

    `prof` is the same closed (z, y) profile `sweep()` was handed -- already
    plinth-shifted -- so the bead lands exactly on the silhouette.
    """
    n = len(prof)
    if n < 4:
        return
    ccw = _poly_ccw(prof)
    en = []                                   # unit OUTWARD normal per edge
    for i in range(n):
        az, ay = prof[i]
        bz, by = prof[(i + 1) % n]
        dz, dy = bz - az, by - ay
        L = math.hypot(dz, dy) or 1.0
        en.append((dy / L, -dz / L) if ccw else (-dy / L, dz / L))
    lo, hi = 1, n - 1                         # points; edges lo .. hi-1
    ring = []
    for k in range(lo, hi + 1):
        e0 = en[k - 1] if k > lo else en[lo]
        e1 = en[k] if k < hi else en[hi - 1]
        mz, my = e0[0] + e1[0], e0[1] + e1[1]
        L = math.hypot(mz, my) or 1.0
        mz, my = mz / L, my / L
        c = max(0.40, mz * e1[0] + my * e1[1])       # mitre, clamped
        ring.append((prof[k], (mz / c, my / c)))
    # `sgn` points INWARD along x: +1 at the x0 seam, -1 at the x1 seam.  Only
    # BEAD_A's dx is negative, so only the outer lip of the bead stands proud of
    # the flank and the crown and the landing sit on the machine.
    for (xe, sgn) in ((x0, 1.0), (x1, -1.0)):
        verts, cols = [], []
        for ((pz, py), (nz, ny)) in ring:
            for (dx, off) in (BEAD_A, BEAD_B, BEAD_C):
                verts.append((xe + sgn * dx, py + ny * off, pz + nz * off))
        tris = []
        for j in range(len(ring) - 1):
            a, b = j * 3, (j + 1) * 3
            for t in (0, 1):
                q0, q1 = a + t, b + t
                if sgn > 0:
                    tris.append((q0, q1, q1 + 1))
                    tris.append((q0, q1 + 1, q0 + 1))
                else:
                    tris.append((q0, q1 + 1, q1))
                    tris.append((q0, q0 + 1, q1 + 1))
        sub.add(cpart(Part(verts, tris, smooth=True), col), TM)


def tmold_deck(sub, x0, x1, fd, dy, col):
    """The bead across the control deck's LEADING EDGE, x0 to x1.

    `tmold()` runs the two flank seams, which gives the deck's edge its bead
    only at the two ends.  The photographs put one across the full width as
    well -- the roster says so for the machine it can read best ("Green
    T-molding round the deck edge", tmnt) and `ref/v47_right.png` shows the
    green strip running the whole leading edge of that deck.  Same three-point
    section, swept along x instead of along the profile: 6 verts, 4 triangles,
    ~192 bytes a machine.

    C lands at (fd-0.030, dy+0.016), which clears the deck box's own top face
    (y dy+0.010, z <= fd-0.04) and the printed deck quad (y dy+0.014, z <=
    fd-0.06); A stands 0.006 ft proud of the deck's front face at z = fd.
    Nothing here is coplanar with anything.
    """
    sec = [(fd + 0.006, dy - 0.050), (fd + 0.021, dy + 0.021),
           (fd - 0.030, dy + 0.016)]
    verts = [(x, y, z) for x in (x0, x1) for (z, y) in sec]
    tris = [(0, 3, 4), (0, 4, 1), (1, 4, 5), (1, 5, 2)]
    sub.add(cpart(Part(verts, tris, smooth=True), col), TM)


def _profile(bd, top, style, dy, mqh, seed=0):
    """The (z, y) side profile of one machine, CCW, front at +z."""
    hd = bd / 2.0
    back = -hd
    fb = hd - 0.30                  # carcase front
    fd = fb + DECK_OUT              # deck front -- the number round 2 got wrong
    ft = hd - 0.62                  # screen / marquee plane
    mq_lo = top - mqh - 0.18
    mq_hi = top - 0.18
    base = [(back, 0.0), (fb, 0.0), (fb, dy - 0.55),
            (fd, dy - 0.26), (fd, dy), (ft, dy)]
    if style == "slope":
        head = [(ft, dy + 0.04), (ft - 0.34, mq_lo - 0.06), (ft + 0.05, mq_lo),
                (ft + 0.05, mq_hi), (ft - 0.18, top), (back, top)]
    elif style == "step":
        head = [(ft, mq_lo - 0.10), (ft - 0.40, mq_lo - 0.10),
                (ft - 0.40, top), (back, top)]
    elif style == "riser":
        head = [(ft - 0.20, mq_lo - 0.30), (ft + 0.10, mq_lo - 0.22),
                (ft + 0.10, mq_hi + 0.10), (ft - 0.26, top), (back, top)]
    else:                                                    # straight
        head = [(ft, mq_hi + 0.06), (ft - 0.06, top), (back, top)]
    return base + head, (fb, fd, ft, mq_lo, mq_hi, dy)


def crt(sub, mat, p, rect=None, bulge=0.060, n=2):
    """ROUND 6.  A monitor face as a shallow cap, where round 5 had a flat quad.

    `p` is the screen rectangle's four corners (bl, br, tr, tl, as `uvq` takes
    them) and this draws that rectangle pushed out along its own normal by
    `bulge * (1-(2u-1)^2) * (1-(2v-1)^2)` -- flush with the bezel all round the
    rim, proud at the centre.  Two things follow that a flat quad cannot do,
    and between them they are what makes a DARK screen read as glass rather
    than as a rectangular hole: the environment reflection sweeps ACROSS the
    face as the camera moves, instead of the whole panel changing value
    together on one shared normal; and the rim, tilted away from the room,
    falls into the soft edge shading a recessed tube has.  Both are lit by the
    scene, so neither survives the camera standing still -- which is the test
    ROOM-BRIEF sets for anything that looks like baked light.

    `rect` is an atlas UV rect for the four south machines that carry printed
    screen art, None for the twelve that carry none.
    """
    p0, p1, p2, p3 = p
    ux, uy, uz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    vx, vy, vz = p3[0] - p0[0], p3[1] - p0[1], p3[2] - p0[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    nx, ny, nz = nx / ln, ny / ln, nz / ln
    u0, v0, u1, v1 = rect if rect else (0.0, 0.0, 1.0, 1.0)
    verts, uvs, cols = [], [], []
    for j in range(n + 1):
        v = j / float(n)
        for i in range(n + 1):
            u = i / float(n)
            k = bulge * (1.0 - (2.0 * u - 1.0) ** 2) * (1.0 - (2.0 * v - 1.0) ** 2)
            a = [(1 - u) * (1 - v) * p0[c] + u * (1 - v) * p1[c]
                 + u * v * p2[c] + (1 - u) * v * p3[c] for c in range(3)]
            verts.append((a[0] + nx * k, a[1] + ny * k, a[2] + nz * k))
            uvs.append((u0 + (u1 - u0) * u, v1 + (v0 - v1) * v))
            # THE GRADIENT.  A near-vertical sheet of dark glass in a room with
            # a bright ceiling and a dark floor is brighter across its top and
            # darker across its bottom -- read it off any of the daylight
            # frames (v4 6 Golden Tee, v4 7 NBA Jam).  It is a GRADIENT, not a
            # highlight: it does not name a light source, it does not stay put
            # in the wrong place when the camera moves, and it is the one thing
            # this renderer cannot supply on its own -- `scene.environment` is
            # measured below as contributing nothing here (see the report's
            # mirror probe: a perfect white mirror on this quad renders luma
            # 8.4, sd 0.7).  `rim` darkens the whole perimeter, which is the
            # soft edge shading a tube recessed behind a bezel has.
            rim = 0.90 if (i in (0, n) or j in (0, n)) else 1.0
            g = (0.66 + 0.34 * v) * rim
            cols.append((g, g, g))
    tris = []
    for j in range(n):
        for i in range(n):
            q = j * (n + 1) + i
            tris.append((q, q + 1, q + n + 2))
            tris.append((q, q + n + 2, q + n + 1))
    sub.add(Part(verts, tris, smooth=True, colors=cols,
                 uv=(uvs if rect else None)), mat)


def upright(m, cx, cz, rot, art, slug, bw=2.20, bd=2.55, top=6.10, seed=1,
            style="straight", dy=2.52, mqh=0.62, plinth=0.0):
    """One arcade cabinet, authored facing +z then spun by `rot` degrees.

    `art` is the wall run's `a2kit.ArtSet` and `slug` names the machine in the
    round-4 roster.  Round 3 passed three integer indices into a shared 12-tile
    atlas here (`art_i` for both flanks, `art_f` for the front panel AND the
    control deck AND the screen bezel, `mq_i` for one of four pastel marquees),
    which is how sixteen cabinets ended up wearing four graphics between them.
    Now every surface takes its own panel: `<slug>.side`, `<slug>.front`,
    `<slug>.deck`, `<slug>.marquee`, and `<slug>.bezel` where the machine's art
    module authored one.
    """
    sub = Model()
    rnd = Rnd(seed)
    prof, (fb, fd, ft, mq_lo, mq_hi, dy) = _profile(bd, top, style, dy, mqh, seed)
    x0, x1 = -bw / 2.0, bw / 2.0
    if plinth:                                  # a raised base, some machines
        bx(sub, CABDK, x0 - 0.01, x1 + 0.01, 0.0, plinth, -bd / 2, fb)
        prof = [(z, y + plinth) for (z, y) in prof]
        mq_lo += plinth
        mq_hi += plinth
        dy += plinth
    sweep(sub, prof, x0, x1, art.ART, art.carcase(slug),
          art.uv(slug + ".side"))
    tmold(sub, prof, x0, x1, art.bead(slug))
    tmold_deck(sub, x0, x1, fd, dy, art.bead(slug))

    # printed lower front panel (its own tile, so the flanks and the face are
    # not the same graphic).  ROUND 5: the rect is per-machine -- art_g2's four
    # south cabinets print their artwork all the way to the floor and its
    # FRONT_RECT says so, where round 4 stopped every panel at plinth + 0.16.
    zf = fb + 0.008 + front_z(slug)
    fx0, fx1, fy0, fy1 = front_rect(slug, bw, dy, plinth)
    uvq(sub, art.ART,
        [(fx0, fy0, zf), (fx1, fy0, zf), (fx1, fy1, zf), (fx0, fy1, zf)],
        art.uv(slug + ".front"))
    # ROUND 5: this machine's OWN coin door(s), or none.  Round 4's single
    # centred grey plate is gone -- see `coindoors`.
    coindoors(sub, slug, bw, dy, plinth, zf)

    # control deck: joysticks + buttons on the projecting top
    dz0, dz1 = ft + 0.18, fd - 0.14
    # the deck carries printed control-panel art, dark: round 3a shipped it as
    # a flat #2c2e34 slab and an UP-facing face of that albedo metered ~145 in
    # this daylight render -- a pale grey shelf across every machine
    bx(sub, CABDK, x0 + 0.03, x1 - 0.03, dy - 0.03, dy + 0.010, ft + 0.02, fd - 0.04)
    uvq(sub, art.deck(slug), [(x0 + 0.06, dy + 0.014, fd - 0.06),
                              (x1 - 0.06, dy + 0.014, fd - 0.06),
                              (x1 - 0.06, dy + 0.014, ft + 0.04),
                              (x0 + 0.06, dy + 0.014, ft + 0.04)],
        art.uv(slug + ".deck"))
    # ROUND 5: this machine's OWN controls.  Round 4 built the same two chrome
    # shafts with a red and a blue cube on top and the same six flat squares
    # here regardless of `slug`, which is the sentence three critics wrote.
    controls(sub, slug, bw, ft, fd, dy)

    # Screen + marquee ride the PROFILE's own front plane.  Round 3a put them
    # at a fixed ft - 0.04, which is INSIDE the body for the straight and step
    # silhouettes -- two of the four machines rendered as a blank grey slab.
    rk = {"straight": (0.02, 0.02), "step": (0.02, 0.02),
          "slope": (0.02, -0.30), "riser": (0.02, -0.16)}[style]
    zb0, zb1 = ft + rk[0], ft + rk[1]
    yb0, yb1 = dy + 0.30, mq_lo - 0.10
    # printed bezel round the screen -- in the photos the monitor surround is
    # part of the machine's artwork, not a black frame
    bez = [(x0 + 0.05, yb0, zb0), (x1 - 0.05, yb0, zb0),
           (x1 - 0.05, yb1, zb1), (x0 + 0.05, yb1, zb1)]
    if art.has(slug + ".bezel"):
        uvq(sub, art.ART, bez, art.uv(slug + ".bezel"))
    else:
        sub.add(quad(*bez), art.BEZEL)
    fy0, fy1 = dy + 0.46, mq_lo - 0.26
    t0 = (fy0 - yb0) / max(0.01, yb1 - yb0)
    t1 = (fy1 - yb0) / max(0.01, yb1 - yb0)
    zs0 = zb0 + (zb1 - zb0) * t0 + 0.014
    zs1 = zb0 + (zb1 - zb0) * t1 + 0.014
    scr = [(x0 + 0.17, fy0, zs0), (x1 - 0.17, fy0, zs0),
           (x1 - 0.17, fy1, zs1), (x0 + 0.17, fy1, zs1)]
    if art.has(slug + ".screen"):
        # ROUND 5.  art_g2 painted the four SOUTH monitors.  All four are dark
        # in every frame and no attract loop is invented; what the panels carry
        # is what is photographed -- Champion Edition's pale yellow instruction
        # card along the bottom edge, Time Crisis's dim olive game image, room
        # reflections on the rest.  The factor material is dark on purpose: a
        # CRT is glass, and `art.ART` at white would render these as four lit
        # televisions.
        # ROUND 6 keeps every one of those panels and only curves the glass
        # they are printed on -- see `crt`.
        crt(sub, art.SCREEN, scr, art.uv(slug + ".screen"))
    else:
        # ROUND 6.  The other twelve carry no printed screen art because the
        # photographs show nothing on them to print: all twelve are dark in
        # every frame that sees them, in daylight and in the night set.  They
        # get the same curved dark glass, unpainted.
        crt(sub, SCRN, scr)
    # marquee -- a real backlit lamp in the photos, so legitimately emissive,
    # and it carries a printed title band rather than a colour field
    mz = ft + {"straight": 0.03, "slope": 0.08, "riser": 0.13,
               "step": -0.37}[style]
    uvq(sub, art.marquee(slug),
        [(x0 + 0.06, mq_lo, mz), (x1 - 0.06, mq_lo, mz),
         (x1 - 0.06, mq_hi, mz), (x0 + 0.06, mq_hi, mz)],
        art.uv(slug + ".marquee"))
    # ROUND 8 -- THE PALE CAP IS GONE, AND IT IS NOT A SAVING, IT IS A
    # CORRECTION.  Round 3 ran a #787c82 strip across every machine's top
    # because "end-on from the dollhouse quadrant an all-black run merges into
    # one mass, and this line breaks it into machines".  Two photographs say
    # there is no such strip: `Arcade Room v4 7.jpg` px (40,105)-(200,180) at 7x
    # (crop shots/_ph_tops.png) shows NFL Blitz's and Golden Tee's heads as flat
    # black to the top edge, and `Arcade Room v3 4.jpg` px (100,520)-(520,700)
    # at 3x (crop shots/_ph_v34_tops.png) shows the whole east run as five black
    # carcases each OUTLINED by its own bright T-molding bead -- gold on Marvel
    # vs Capcom, maroon on MK and NBA Jam, green on the Turtles -- and nothing
    # pale anywhere on a cabinet top.  The bead `tmold()` now runs is the real
    # feature that does the job this strip was standing in for, and it does it
    # from every camera in the room rather than only from above.  (It is also
    # 14.6 KB across the three GLBs, which is most of what the bead costs; that
    # is a consequence, not the reason -- see the round-8 report.)

    ca, sa = math.cos(R(rot)), math.sin(R(rot))
    for part, mm in sub._parts:
        v = [(cx + x * ca + z * sa, y, cz - x * sa + z * ca)
             for (x, y, z) in part.verts]
        m._parts.append((Part(v, part.tris, part.smooth, part.colors,
                              part.uv), mm))


# ---- the machines, one row per wall.  Widths, heights, deck heights, marquee
# depths, plinths and profiles all differ; the photos' run is jagged, not a
# comb, and that is most of what "seven of the same box" meant.
# ROUND 4: the three integer artwork columns are replaced by the machine's
# roster slug, and NOTHING else in these tables moved -- every z/x, width,
# height, deck height, marquee depth, plinth and profile style is round 3's.
# The order is the order the photographs establish, run by run: the east wall
# reads north to south, the south wall west to east, the north wall west to
# east.  EAST_RUN[6] is the slot the roster found EMPTY in all four frames that
# see the whole run; the geometry is kept (this round changed artwork, not
# layout) and it is dressed as an honest unbranded black upright with no
# licensed graphic rather than given an invented title.
EAST_RUN = [
    # (z, bw, top, style, dy, mqh, slug, plinth)
    (2.85, 2.34, 6.28, "slope",    2.56, 0.70, "star-wars-atari", 0.00),
    (5.11, 2.10, 5.86, "straight", 2.44, 0.55, "marvel-super-heroes", 0.10),
    (7.37, 2.42, 6.34, "riser",    2.60, 0.76, "marvel-vs-capcom", 0.00),
    (9.63, 2.16, 5.98, "step",     2.48, 0.58, "mortal-kombat", 0.14),
    (11.89, 2.30, 6.22, "slope",   2.54, 0.66, "nba-jam", 0.00),
    (14.15, 2.04, 5.78, "straight", 2.40, 0.52, "tmnt-turtles-in-time", 0.08),
    (16.41, 2.38, 6.16, "riser",   2.58, 0.72, "east-7-no-machine", 0.00),
]

SOUTH_RUN = [
    (2.05, 2.95, 6.36, "step",     2.62, 0.80, "legends-ultimate", 0.00),
    (4.95, 2.42, 6.02, "straight", 2.46, 0.58,
     "street-fighter-2-champion-edition", 0.00),
    (7.55, 2.52, 6.24, "slope",    2.56, 0.68, "time-crisis", 0.12),
    (10.05, 2.28, 5.92, "riser",   2.42, 0.60, "terminator-2", 0.00),
]

NORTH_RUN = [
    (6.55, 2.44, 6.20, "slope",    2.56, 0.72,
     "north-1-graffiti-multicade", 0.00),
    (9.00, 2.28, 6.34, "straight", 2.50, 0.64, "pac-man", 0.10),
    (11.30, 2.18, 6.02, "riser",   2.44, 0.56, "nfl-blitz", 0.00),
    (13.55, 2.32, 6.26, "step",    2.54, 0.68, "golden-tee-3d-golf", 0.06),
]


# ---------------------------------------------------------------------------
# ROUND 5: hand atlas4 the TRUE world aspect of every quad.
#
# atlas4 now packs each panel isotropically -- w = S*sqrt(A), h = S/sqrt(A) --
# so `A` decides how a panel's pixel budget is split between its two axes, and
# for art_g1's machines it also decides the shape its `.rect` path draws at.
# The four art modules each published an aspect table, but art_g2's is ONE
# number per panel class for four cabinets 2.28-2.95 ft wide, and art_g3 warned
# that round 4's single per-class table "stretched every front by ~24%".  These
# are the real numbers, computed from the run tables and `_profile` below --
# the only place in the project that knows them.
def _aspects():
    out = {}
    for run in (EAST_RUN, SOUTH_RUN, NORTH_RUN):
        for (_, bw, top, style, dy0, mqh, slug, pl) in run:
            prof, (fb, fd, ft, mq_lo, mq_hi, dy) = _profile(
                2.55, top, style, dy0, mqh)
            if pl:
                prof = [(z, y + pl) for (z, y) in prof]
                mq_lo += pl
                mq_hi += pl
                dy += pl
            zs = [p[0] for p in prof]
            ys = [p[1] for p in prof]
            fx0, fx1, fy0, fy1 = front_rect(slug, bw, dy, pl)
            out[slug + ".side"] = (max(zs) - min(zs)) / (max(ys) - min(ys))
            out[slug + ".front"] = (fx1 - fx0) / max(0.01, fy1 - fy0)
            out[slug + ".deck"] = (bw - 0.12) / 0.92
            out[slug + ".marquee"] = (bw - 0.12) / max(0.01, mq_hi - mq_lo)
            rk = {"straight": (0.02, 0.02), "step": (0.02, 0.02),
                  "slope": (0.02, -0.30), "riser": (0.02, -0.16)}[style]
            zb0, zb1 = ft + rk[0], ft + rk[1]
            yb0, yb1 = dy + 0.30, mq_lo - 0.10
            out[slug + ".bezel"] = (bw - 0.10) / max(
                0.01, math.hypot(yb1 - yb0, zb1 - zb0))
            fy0s, fy1s = dy + 0.46, mq_lo - 0.26
            t0 = (fy0s - yb0) / max(0.01, yb1 - yb0)
            t1 = (fy1s - yb0) / max(0.01, yb1 - yb0)
            zs0 = zb0 + (zb1 - zb0) * t0
            zs1 = zb0 + (zb1 - zb0) * t1
            out[slug + ".screen"] = (bw - 0.34) / max(
                0.01, math.hypot(fy1s - fy0s, zs1 - zs0))
    return out


atlas4.set_aspects(_aspects())


def build_east_cabs():
    """The hero run: seven uprights down the east wall, facing west."""
    m = Model()
    cshadow(m, W - 1.45, (EAST_RUN[0][0] + EAST_RUN[-1][0]) / 2, 1.55,
            (EAST_RUN[-1][0] - EAST_RUN[0][0]) / 2 + 1.25, feather=0.85,
            strength=1.00, room=(W, D))
    art = ArtSet("east", EAST_SLUGS)
    for i, (z, bw, top, st, dy, mqh, slug, pl) in enumerate(EAST_RUN):
        upright(m, W - 1.32, z, 270, art, slug, bw=bw, bd=2.55, top=top,
                seed=i + 1, style=st, dy=dy, mqh=mqh, plinth=pl)
    return save_and_place("Arcade Cabinets East", m, ROOM)


def build_south_cabs():
    """Legends Ultimate, Capcom Champion, Time Crisis and T2 on the south wall,
    plus the black diagonal acoustic panel between them and the door, the black
    hex cluster above the T2 group, and Ridge Racer round the SW corner."""
    m = Model()
    cshadow(m, 5.9, D - 1.85, 5.95, 1.45, feather=0.85, strength=1.00,
            room=(W, D))
    art = ArtSet("south", SOUTH_SLUGS)
    for (cx, bw, top, st, dy, mqh, slug, pl) in SOUTH_RUN:
        upright(m, cx, D - 1.32 - SD, 180, art, slug, bw=bw, bd=2.55, top=top,
                seed=int(cx * 7), style=st, dy=dy, mqh=mqh, plinth=pl)
    # the blue CAPCOM lower cabinet the Champion Edition stands on
    # The blue CAPCOM base box is UNCHANGED.  art_g2 asked for its front face
    # to move back so Champion Edition's printed base art could be seen; that
    # would have driven it through the control deck (see decks5.FRONT_Z).  The
    # printed quad is pushed forward onto this box's face instead.
    bx(m, Material("a2capc", "#1c4c9a", roughness=0.6),
       3.62, 6.28, 0.0, 2.55, D - 2.55 - SD, D - 0.06 - SD)
    # the yellow trim rail, dropped from y 0.42-0.70 to 0.14-0.36: round 3 put
    # it where the blue box was a blank field, and art_g2's printed base art
    # now puts the red CAPCOM wordmark exactly there.  It reads as a kick rail
    # at the new height and stops cutting the wordmark in half.
    bx(m, Material("a2capy", "#e0b21c", roughness=0.5),
       4.30, 5.60, 0.14, 0.36, D - 2.62 - SD, D - 2.56 - SD)
    # black diagonal-rib acoustic panel between the run and the door
    sub = Model()
    bx(sub, ACOU, SA(13.20), SA(11.60), 3.20, 6.70, 0.0, 0.09)
    RIB = Material("a2rib", "#474b52", roughness=0.88)
    for k in range(9):
        bx(sub, RIB, SA(13.10) + k * 0.17, SA(13.04) + k * 0.17,
           3.30 + k * 0.34, 6.60, 0.09, 0.10)
    blit(m, sub, "s", W, D, SD)
    # black / iridescent hexes over the T2 group -- `v3 4`, far wall upper band
    hex_wall(m, "s",
             [(6.40, 6.95, "d"), (7.65, 7.35, "w"), (8.90, 6.95, "d"),
              (10.15, 7.35, "d"), (11.40, 6.95, "w"), (5.15, 7.35, "d"),
              (3.90, 6.95, "d"), (2.65, 7.35, "w")], d0=SD)

    # ---- east of the door: the 1.2 ft stub carries the vertical RGB bar and a
    # wall-mounted mini cabinet; the Connect-4 game stands on the floor beside it
    sub = Model()
    hp = [(0.30 * math.cos(R(60 * j + 30)), 0.30 * math.sin(R(60 * j + 30)))
          for j in range(6)]
    for k in range(7):                       # hexagon segments of the light bar
        wpanel(sub, LEDS[(k + 3) % 5], hp, SA(16.85), 2.35 + k * 0.62, 0.0, 0.07)
    blit(m, sub, "s", W, D, SD)
    # mini cabinet hung on the wall east of the door
    bx(m, CABBLK, 17.35, 18.85, 2.45, 5.35, D - 1.02, D - 0.44)
    bx(m, SCRN, 17.52, 18.68, 3.40, 4.60, D - 1.045, D - 1.02)
    bx(m, LEDS[0], 17.50, 18.70, 4.75, 5.20, D - 1.045, D - 1.02)
    bx(m, LEDS[4], 17.50, 18.70, 2.70, 3.20, D - 1.045, D - 1.02)
    # Connect-4 on a low white console
    cshadow(m, 19.22, D - 1.35, 1.35, 0.80, feather=0.70, strength=0.82,
            room=(W, D))
    bx(m, WHTM, 17.90, 20.55, 0.0, 2.05, D - 2.10, D - 0.56)
    bx(m, TRIM, 17.83, 20.62, 2.05, 2.17, D - 2.16, D - 0.50)
    G = Material("a2game", "#17181c", roughness=0.62)
    bx(m, G, 18.35, 20.10, 2.17, 4.05, D - 1.50, D - 1.36)
    zc4 = D - 1.365
    for r_ in range(5):                        # quads, not boxes: 25 discs of
        for c_ in range(5):                    # Connect-4 cost 29 KB as solids
            a, b = 18.47 + c_ * 0.33, 18.69 + c_ * 0.33
            y_, y2 = 2.29 + r_ * 0.31, 2.51 + r_ * 0.31
            m.add(quad((b, y_, zc4), (a, y_, zc4), (a, y2, zc4), (b, y2, zc4)),
                  WHTM)

    # ---- Ridge Racer, round the corner on the west wall's south end
    cshadow(m, 1.40, 21.55, 1.45, 1.30, feather=0.80, strength=0.94,
            room=(W, D))
    upright(m, 1.32, 21.55, 90, art, "ridge-racer", bw=2.42, bd=2.55,
            top=6.06, seed=77, style="step", dy=2.58, mqh=0.66)
    return save_and_place("Arcade Cabinets South", m, ROOM)


# ============================================ north wall: the frontal machines
# The boxed collectibles in the NE glass cabinet are stand-ins: rather than
# thirty more textures, each box face samples a WINDOW of a machine panel that
# is already in this run's atlas, so it costs nothing.  ROUND 5 crops the
# window.  Round 4 mapped whole panels, which was harmless while the artwork
# was blurry -- but the round-5 panels are legible, and `nfl-blitz.side`'s
# chrome lockup started reading as the words NFL BLITZ across six collectible
# boxes in a row.  A 0.34 x 0.52 window of the same panel gives colour and
# pattern with no wordmark, which is what a boxed figure reads as from eight
# feet.  Still zero extra bytes.
BOX_ART = ["pac-man.front", "nfl-blitz.side", "golden-tee-3d-golf.deck",
           "north-1-graffiti-multicade.side", "nfl-blitz.deck",
           "pac-man.side", "golden-tee-3d-golf.side",
           "north-1-graffiti-multicade.deck"]
BOX_WIN = [(0.10, 0.34), (0.52, 0.12), (0.28, 0.46), (0.62, 0.30),
           (0.36, 0.08), (0.06, 0.20), (0.48, 0.40), (0.20, 0.24)]


def subuv(rect, a0, b0, a1, b1):
    """A sub-rectangle of a packed panel's UV rect, in 0..1 panel space."""
    u0, v0, u1, v1 = rect
    return (u0 + (u1 - u0) * a0, v0 + (v1 - v0) * b0,
            u0 + (u1 - u0) * a1, v0 + (v1 - v0) * b1)


def build_north_cabs():
    """`Arcade Room v3 1` shows FOUR frontal uprights on the north wall --
    Pac-Man and three others -- a tall glass-fronted lit Funko display cabinet
    in the NE corner and a large plush in a net bag hung over it.  Round 2 built
    none of them, which is why the room's north half was dead floor."""
    m = Model()
    cshadow(m, (NORTH_RUN[0][0] + NORTH_RUN[-1][0]) / 2, 1.45,
            (NORTH_RUN[-1][0] - NORTH_RUN[0][0]) / 2 + 1.35, 1.55,
            feather=0.85, strength=1.00, room=(W, D))
    art = ArtSet("north", NORTH_SLUGS)
    for (cx, bw, top, st, dy, mqh, slug, pl) in NORTH_RUN:
        upright(m, cx, 1.32, 0, art, slug, bw=bw, bd=2.55, top=top,
                seed=int(cx * 11), style=st, dy=dy, mqh=mqh, plinth=pl)

    # ---- the glass-fronted lit Funko display cabinet, NE corner
    fx0, fx1, fz0, fz1, fh = 17.45, 20.00, 0.06, 1.36, 5.55
    cshadow(m, (fx0 + fx1) / 2, (fz0 + fz1) / 2, (fx1 - fx0) / 2,
            (fz1 - fz0) / 2, feather=0.70, strength=0.86, room=(W, D))
    CASEW = Material("a2case", "#f0eee9", roughness=0.42)
    bx(m, CASEW, fx0, fx1, 0.0, 0.42, fz0, fz1)                  # plinth
    for (a, b) in ((fx0, fx0 + 0.10), (fx1 - 0.10, fx1)):        # stiles
        bx(m, CASEW, a, b, 0.42, fh, fz0, fz1)
    bx(m, CASEW, fx0, fx1, fh - 0.16, fh, fz0, fz1)              # head
    bx(m, CASEW, fx0, fx1, 0.42, fh, fz0, fz0 + 0.10)            # back
    nsh = 5
    for s in range(nsh):
        sy = 0.60 + s * ((fh - 1.05) / nsh)
        bx(m, CASEW, fx0 + 0.10, fx1 - 0.10, sy, sy + 0.055, fz0 + 0.08, fz1 - 0.16)
        bx(m, LEDS[s % 5], fx0 + 0.12, fx1 - 0.12, sy - 0.045, sy - 0.005,
           fz0 + 0.12, fz1 - 0.30)
        for k in range(6):
            bxx = fx0 + 0.20 + k * ((fx1 - fx0 - 0.40) / 6.0)
            bxw = (fx1 - fx0 - 0.40) / 6.0 - 0.03
            uvq(m, art.ART, [(bxx, sy + 0.055, fz1 - 0.20),
                         (bxx + bxw, sy + 0.055, fz1 - 0.20),
                         (bxx + bxw, sy + 0.055 + 0.58, fz1 - 0.20),
                         (bxx, sy + 0.055 + 0.58, fz1 - 0.20)],
                subuv(art.uv(BOX_ART[(s * 6 + k) % len(BOX_ART)]),
                      *(BOX_WIN[(s * 6 + k) % len(BOX_WIN)]
                        + (BOX_WIN[(s * 6 + k) % len(BOX_WIN)][0] + 0.34,
                           BOX_WIN[(s * 6 + k) % len(BOX_WIN)][1] + 0.52))))
    bx(m, GLASS, fx0 + 0.10, fx1 - 0.10, 0.42, fh - 0.16, fz1 - 0.09, fz1 - 0.05)

    # ---- the plush in a net bag, hung above and west of the case
    px, py, pz = 16.30, 4.35, 0.75
    PLUSH = Material("a2plush", "#f0ece2", roughness=0.98)
    m.add(puff(1.45, 1.55, 1.20, r=0.52, seg=10, rings=5), PLUSH,
          at=(px, py, pz))
    for dx in (-0.44, 0.44):
        m.add(puff(0.42, 0.50, 0.34, r=0.15, seg=8, rings=4), PLUSH,
              at=(px + dx, py + 1.30, pz))
    bx(m, Material("a2eye", "#1a1c20", roughness=0.4),
       px - 0.34, px - 0.18, py + 0.95, py + 1.10, pz + 0.52, pz + 0.56)
    bx(m, Material("a2eye2", "#1a1c20", roughness=0.4),
       px + 0.18, px + 0.34, py + 0.95, py + 1.10, pz + 0.52, pz + 0.56)
    NET = Material("a2net", "#d8d4cc", roughness=0.9, opacity=0.42)
    for k in range(7):                       # the net bag, crossed strands
        t = -0.72 + k * 0.24
        bx(m, NET, px + t - 0.018, px + t + 0.018, py - 0.10, py + 2.05,
           pz + 0.58, pz + 0.60)
    for k in range(5):
        bx(m, NET, px - 0.78, px + 0.78, py + 0.10 + k * 0.42,
           py + 0.14 + k * 0.42, pz + 0.58, pz + 0.60)
    m.add(cylinder(0.05, 0.34, 8), BLACKMET, at=(px, py + 2.05, pz + 0.30),
          rot_x=R(90))

    # ---- the black speaker on a stand that stands between them (photo v3 1)
    sx, sz = 15.10, 1.05
    cshadow(m, sx, sz, 0.60, 0.60, feather=0.60, strength=0.74, room=(W, D))
    m.add(cylinder(0.62, 0.07, 12), BLACKMET, at=(sx, 0.0, sz))
    m.add(cylinder(0.075, 2.35, 8), BLACKMET, at=(sx, 0.07, sz))
    bx(m, CABBLK, sx - 0.52, sx + 0.52, 2.35, 3.95, sz - 0.42, sz + 0.42)
    m.add(cylinder(0.30, 0.03, 12), Material("a2spk", "#2a2d33", roughness=0.9),
          at=(sx, 3.15, sz + 0.44), rot_x=R(90))
    return save_and_place("Arcade Cabinets North", m, ROOM)


# ============================================= west wall: the two gaming booths
def razer_chair(m, cx, cz, rot=180, scale=1.0):
    """The black gaming chair -- two booths and the desk all use it."""
    sub = Model()
    sub.add(cylinder(0.16, 1.05, 10), BLACKMET, at=(0.0, 0.22, 0.0))
    for k in range(5):
        a = R(72 * k)
        sub.add(box(1.00, 0.13, 0.20), BLACKMET,
                at=(0.46 * math.cos(a), 0.10, 0.46 * math.sin(a)), rot_y=-a)
        sub.add(cylinder(0.11, 0.20, 8), BLACKMET,
                at=(0.88 * math.cos(a), 0.11, 0.88 * math.sin(a)), rot_x=R(90))
    slab(sub, BLKF2, -0.86, 0.86, 1.27, 1.52, -0.84, 0.84, r=0.13)
    slab(sub, BLKF, 0.38, 0.78, 1.52, 3.48, -0.80, 0.80, r=0.13)
    slab(sub, BLKF2, 0.30, 0.60, 3.48, 3.92, -0.50, 0.50, r=0.11)
    for dz in (-0.86, 0.86):
        slab(sub, BLKF2, -0.30, 0.44, 1.52, 2.26, dz - 0.09, dz + 0.09, r=0.07)
    ca, sa = math.cos(R(rot)), math.sin(R(rot))
    for part, mm in sub._parts:
        m._parts.append((Part([(cx + x * ca + z * sa, y * scale,
                                cz - x * sa + z * ca)
                               for (x, y, z) in part.verts],
                              part.tris, part.smooth), mm))


BOOTHS = [(7.55, 10.35), (10.95, 13.75)]     # local z spans of the two openings
BOOTH_D = 1.55                               # how far the bay stands proud


def build_booths():
    """`Arcade Room v3 1` (crop 0,430-560,850) and `v3 2` both show two deep
    lit gaming bays on the west wall, each with a Razer chair, a wall monitor,
    a worktop and headset hooks.  Round 2 left this as open floor and disclosed
    it; it is a prominent feature of two of the four photographs.

    The plan's west wall is the exterior foundation, so the bays cannot be cut
    INTO it: they are built as a stud bay standing BOOTH_D proud of the wall
    with two openings through it, which is what the photo's ~1 ft white reveals
    read as anyway."""
    m = Model()
    z0, z1 = BOOTHS[0][0] - 0.34, BOOTHS[1][1] + 0.34
    BAY = Material("a2bay", "#e9e7e2", roughness=0.86)
    HEAD = 6.70
    piers = [(z0, BOOTHS[0][0]), (BOOTHS[0][1], BOOTHS[1][0]),
             (BOOTHS[1][1], z1)]
    for (a, b) in piers:
        bx(m, BAY, 0.0, BOOTH_D, 0.0, H - 0.02, a, b)
        bx(m, TRIM, 0.0, BOOTH_D + 0.02, 0.0, BB_H, a, b)          # skirting
    bx(m, BAY, 0.0, BOOTH_D, HEAD, H - 0.02, z0, z1)               # header
    for (a, b) in BOOTHS:
        bx(m, TRIM, BOOTH_D - 0.055, BOOTH_D, 0.0, HEAD + 0.08, a - 0.09, a)
        bx(m, TRIM, BOOTH_D - 0.055, BOOTH_D, 0.0, HEAD + 0.08, b, b + 0.09)
        bx(m, TRIM, BOOTH_D - 0.055, BOOTH_D, HEAD, HEAD + 0.08, a, b)
    DARK = Material("a2booth", "#1a1c21", roughness=0.9)
    for i, (a, b) in enumerate(BOOTHS):
        # the cavity: dark lining on the three inner faces
        bx(m, DARK, 0.02, 0.07, 0.0, HEAD, a, b)                   # back
        bx(m, DARK, 0.02, BOOTH_D - 0.06, 0.0, HEAD, a, a + 0.05)
        bx(m, DARK, 0.02, BOOTH_D - 0.06, 0.0, HEAD, b - 0.05, b)
        bx(m, DARK, 0.02, BOOTH_D - 0.06, HEAD - 0.05, HEAD, a, b)
        # RGB strips down both reveals -- the cyan/green edges in the photo
        for zz in (a + 0.055, b - 0.095):
            bx(m, LEDS[(i * 2) % 5], BOOTH_D - 0.34, BOOTH_D - 0.30,
               0.45, HEAD - 0.30, zz, zz + 0.04)
        # wall monitor
        bx(m, BLACKMET, 0.09, 0.19, 3.10, 5.30, a + 0.34, b - 0.34)
        bx(m, Material("a2bms", "#0b0e13", roughness=0.15, emissive="#12202e",
                       emissive_strength=1.0),
           0.19, 0.205, 3.20, 5.20, a + 0.42, b - 0.42)
        # worktop with a keyboard and a pad
        bx(m, WHTM, 0.07, BOOTH_D - 0.24, 2.30, 2.40, a + 0.10, b - 0.10)
        bx(m, Material("a2kb2", "#16181c", roughness=0.6),
           0.42, 1.10, 2.40, 2.46, a + 0.62, b - 0.62)
        # headset hooks
        for zz in (a + 0.26, b - 0.26):
            bx(m, BLACKMET, 0.16, 0.42, 5.55, 5.63, zz - 0.03, zz + 0.03)
            m.add(cylinder(0.24, 0.34, 8), BLKF2, at=(0.36, 5.20, zz),
                  rot_x=R(90))
        cshadow(m, BOOTH_D + 0.55, (a + b) / 2.0, 0.95, 0.95, feather=0.72,
                strength=0.80, room=(W, D))
        razer_chair(m, BOOTH_D - 0.30, (a + b) / 2.0, rot=90)
    return save_and_place("Arcade Booths", m, ROOM)


# =========================================== the Funko shelf, chevrons, pinball
def build_east_shelf():
    m = Model()
    sz0, sz1 = 2.10, 18.00
    # ---- lit collectible shelf.  Round 2 spaced 24 two-box figures with no
    # under-shelf glow; `v3 4` crop (0,480)-(650,900) has ~40 PACKED and lit
    # from beneath, and the wall behind them takes the colour.
    bx(m, SHELFW, W - 0.86, W, SHELF_Y, SHELF_Y + 0.075, sz0, sz1)
    bx(m, SHELFW, W - 0.16, W, SHELF_Y - 0.40, SHELF_Y, sz0, sz1)
    n = 40
    step = (sz1 - sz0) / n
    nseg = 10
    for k in range(nseg):                      # the under-shelf glow itself
        a = sz0 + k * (sz1 - sz0) / nseg
        b = sz0 + (k + 1) * (sz1 - sz0) / nseg
        bx(m, BRIGHT[k % 5], W - 0.30, W - 0.11, SHELF_Y - 0.115,
           SHELF_Y - 0.045, a, b)
        # the lit back panel the figures stand against
        bx(m, LEDS[(k + 2) % 5], W - 0.055, W - 0.03,
           SHELF_Y + 0.075, SHELF_Y + 0.52, a, b)
    for i in range(n):
        z = sz0 + (i + 0.5) * step
        hue = mix(HUES[(i * 5) % len(HUES)], "#2a2c31", 0.30)
        fm = Material("a2fig" + hue[1:], hue, roughness=0.68)
        h = 0.30 + 0.10 * ((i * 7) % 3)
        bx(m, fm, W - 0.50, W - 0.30, SHELF_Y + 0.075, SHELF_Y + h,
           z - step * 0.47, z + step * 0.47)

    # ---- the chevron acoustic band + the cove LED above it
    # The round-2 band was a ghost: one flat panel at the wall's own value, no
    # facet shading.  Each chevron is now TWO facets at different values with a
    # cast line under it, so it reads as folded acoustic felt.
    sub = Model()
    CH_L = [(-0.64, -0.44), (0.0, -0.06), (0.0, 0.40), (-0.64, 0.0)]
    CH_R = [(0.0, -0.06), (0.64, -0.44), (0.64, 0.0), (0.0, 0.40)]
    FACE_A = Material("a2chva", "#f4f2ee", roughness=0.72)
    FACE_B = Material("a2chvb", "#c9c6c0", roughness=0.72)
    FACE_S = Material("a2chvs", "#a8a5a0", roughness=0.85)
    z = 0.70
    while z < D - 1.2:
        wpanel(sub, FACE_S, [(-0.66, -0.50), (0.0, -0.12), (0.66, -0.50),
                             (0.66, -0.44), (0.0, -0.06), (-0.66, -0.44)],
               z, 6.98, 0.0, 0.03)
        wpanel(sub, FACE_A, CH_L, z, 6.98, 0.0, 0.075)
        wpanel(sub, FACE_B, CH_R, z, 6.98, 0.0, 0.055)
        z += 1.44
    blit(m, sub, "e", W, D, 0.0)
    # cove: a shallow shelf with the strip tucked behind its lip
    bx(m, TRIM, W - 0.52, W, COVE_Y, COVE_Y + 0.14, 0.20, D - 0.20)
    bx(m, COVEM, W - 0.44, W - 0.34, COVE_Y + 0.14, COVE_Y + 0.22, 0.24, D - 0.24)
    # wall speaker box at the north end
    bx(m, WHTM, W - 0.70, W - 0.16, 6.55, 7.35, 0.55, 1.30)

    # ---- the Y-shaped RGB fixture, south end of the east wall
    y_fixture(m, "e", 20.55, 4.15, 1.35, bright=True)

    # ---- pinball at the run's south end
    px, pz = W - 2.55, 19.05
    cshadow(m, px, pz, 2.22, 1.18, feather=0.75, strength=0.88, room=(W, D))
    bx(m, CABDK, px - 2.20, px + 2.20, 1.75, 2.55, pz - 1.15, pz + 1.15)
    bx(m, Material("a2pf", "#1a2b34", roughness=0.3, emissive="#16323c",
                   emissive_strength=0.55),
       px - 2.05, px + 1.55, 2.55, 2.62, pz - 1.05, pz + 1.05)
    bx(m, GLASS, px - 2.05, px + 1.55, 2.62, 2.70, pz - 1.05, pz + 1.05)
    bx(m, CABBLK, px + 1.55, px + 2.20, 2.55, 5.45, pz - 1.15, pz + 1.15)
    bx(m, Material("a2mqpin", "#2b6b52", roughness=0.45, emissive="#2f7d5e",
                   emissive_strength=1.5),
       px + 1.53, px + 1.55, 3.55, 5.25, pz - 1.02, pz + 1.02)
    for dx in (-1.85, 1.35):
        for dz in (-0.95, 0.95):
            m.add(cylinder(0.052, 1.75, 8), CHR, at=(px + dx, 0.0, pz + dz))
    # low glass collectible case beyond it
    bx(m, CABDK, W - 2.30, W - 0.15, 0.0, 1.55, 20.30, 22.10)
    bx(m, GLASS, W - 2.25, W - 0.20, 1.55, 2.35, 20.35, 22.05)
    for i in range(4):
        hue = HUES[(i * 3 + 1) % len(HUES)]
        bx(m, Material("a2cs" + hue[1:], hue, roughness=0.6),
           W - 2.00 + i * 0.44, W - 1.76 + i * 0.44, 1.55, 2.05,
           20.90, 21.30)
    return save_and_place("Arcade East Shelf", m, ROOM)


# ============================================================ hex panel walls
HEXPTS = [(0.74 * math.cos(R(60 * k + 30)), 0.74 * math.sin(R(60 * k + 30)))
          for k in range(6)]
LITM = Material("a2hexl", "#f2f7ff", roughness=0.4, emissive="#c7dcff",
                emissive_strength=1.7)


BRIGHT = [Material("a2ybr%d" % i, c, roughness=0.25, emissive=c,
                   emissive_strength=9.0)
          for i, c in enumerate(("#ff4fa0", "#ffc24a", "#57e08a",
                                 "#49c6ff", "#a97dff"))]


def y_fixture(m, wall, at, y, ln=1.35, bright=False, d0=0.0):
    """The three-armed RGB light bar.  `at` is a ROOM x (n/s) or z (e/w)."""
    conv = {"n": lambda a: a, "e": lambda a: a, "s": SA, "w": WA}[wall]
    a0 = conv(at)
    sub = Model()
    for j, ang in enumerate((90, 210, 330)):
        ca, sa_ = math.cos(R(ang)), math.sin(R(ang))
        for t in range(4):
            f = (t + 0.5) / 4.0
            seg = ln / 4.0 * 1.04
            pts = [(-seg / 2, -0.075), (seg / 2, -0.075),
                   (seg / 2, 0.075), (-seg / 2, 0.075)]
            cs, sn = math.cos(R(ang)), math.sin(R(ang))
            rot = [(px * cs - pz * sn, px * sn + pz * cs) for (px, pz) in pts]
            wpanel(sub, (BRIGHT if bright else LEDS)[(t + j * 2) % 5], rot,
                   a0 + ca * ln * f, y + sa_ * ln * f, 0.0, 0.075)
    blit(m, sub, wall, W, D, d0)


def hex_wall(m, wall, spots, d0=0.0):
    """Nanoleaf-style hexagons.  `spots` are (ROOM x or z, height[, kind])."""
    conv = {"n": lambda a: a, "e": lambda a: a, "s": SA, "w": WA}[wall]
    sub = Model()
    for i, sp in enumerate(spots):
        kind = sp[2] if len(sp) > 2 else ("l" if i % 4 == 0 else
                                          ("d" if i % 4 == 2 else "w"))
        mat = LITM if kind == "l" else (HEXD if kind == "d" else HEXW)
        wpanel(sub, mat, HEXPTS, conv(sp[0]), sp[1], 0.0, 0.085)
    blit(m, sub, wall, W, D, d0)


def build_north():
    """North wall: hex panels, three small mounted screens, a black hexagon
    cluster, and a slim RGB floor lamp in the corner beside the utility room."""
    m = Model()
    # the hex band now sits ABOVE the four frontal machines (photo `v3 1`
    # crop 500,440-900,830 -- hexes and the three art frames clear their tops)
    hex_wall(m, "n",
             [(6.10, 6.95, "d"), (7.35, 7.45, "w"), (8.60, 6.90, "w"),
              (9.85, 7.45, "l"), (11.10, 6.90, "d"), (12.35, 7.45, "w"),
              (13.60, 6.90, "w"), (14.85, 7.45, "d"), (16.10, 6.90, "l"),
              (17.35, 7.45, "w"), (18.60, 6.90, "w"), (19.70, 7.45, "d"),
              (4.55, 6.95, "w"), (3.30, 7.45, "d"), (2.05, 6.95, "l")])
    # three small screens hung between the hexes
    sub = Model()
    for (a, y, w_, h_, hue) in ((8.55, 7.05, 1.35, 0.80, "#c0392b"),
                                (11.60, 7.10, 1.10, 0.66, "#e0b21c"),
                                (14.90, 7.05, 1.20, 0.72, "#2f6fd0")):
        bx(sub, CABDK, a - w_ / 2, a + w_ / 2, y - h_ / 2, y + h_ / 2, 0.0, 0.10)
        bx(sub, Material("a2sm" + hue[1:], hue, roughness=0.35, emissive=hue,
                         emissive_strength=1.6),
           a - w_ / 2 + 0.06, a + w_ / 2 - 0.06, y - h_ / 2 + 0.05,
           y + h_ / 2 - 0.05, 0.10, 0.115)
    blit(m, sub, "n", W, D, 0.0)
    # the second Y light, over the NW alcove (photo `v3 3`)
    y_fixture(m, "n", 3.10, 4.55, 1.15, bright=True)
    # slim RGB floor lamp -- moved into the NW alcove, which the four frontal
    # machines now occupy from x 5.4 east
    lx, lz = 4.35, 1.05
    cshadow(m, lx, lz, 0.52, 0.52, feather=0.55, strength=0.71, room=(W, D))
    m.add(cylinder(0.50, 0.06, 12), BLACKMET, at=(lx, 0.0, lz))
    m.add(cylinder(0.052, 4.55, 8), BLACKMET, at=(lx, 0.06, lz))
    m.add(cylinder(0.095, 3.30, 8),
          Material("a2lamp", "#e6ffd4", roughness=0.3, emissive="#d4ff96",
                   emissive_strength=3.0), at=(lx + 0.09, 1.10, lz))
    # a green vase on the floor beside it
    m.add(cylinder(0.28, 1.00, 12, r_top=0.15),
          Material("a2vase", "#5c8f7a", roughness=0.4), at=(2.55, 0.0, 0.95))
    # a large leafy floor plant in the alcove, and a low storage cube
    plant(m, 1.75, 1.05, 2.55, scale=1.35, seed=4)
    cshadow(m, 3.10, 2.75, 0.95, 0.75, feather=0.65, strength=0.78, room=(W, D))
    bx(m, Material("a2cube", "#26282d", roughness=0.8),
       2.30, 3.90, 0.0, 1.35, 2.10, 3.40)
    return save_and_place("Arcade North Wall", m, ROOM)


# ==================================================== west wall: TV + hexes
def build_tv_wall():
    m = Model()
    a0, a1 = WA(20.70), WA(14.40)         # the very large flat TV
    ty0, ty1 = 3.25, 6.55
    sub = Model()
    # bias light behind it, then the panel over the top of it
    bx(sub, LEDS[3], a0 - 0.22, a1 + 0.22, ty0 - 0.22, ty1 + 0.22, 0.04, 0.09)
    bx(sub, Material("a2tvb", "#17181b", roughness=0.5),
       a0, a1, ty0, ty1, 0.09, 0.20)
    bx(sub, Material("a2tvs", "#0b0d10", roughness=0.13, emissive="#0d151d",
                     emissive_strength=0.7),
       a0 + 0.05, a1 - 0.05, ty0 + 0.05, ty1 - 0.05, 0.20, 0.215)
    # small poster north of the TV
    bx(sub, Material("a2post", "#26303c", roughness=0.7),
       WA(21.90), WA(20.90), 4.40, 5.70, 0.0, 0.05)
    blit(m, sub, "w", W, D, 0.0)
    hex_wall(m, "w",
             [(21.60, 6.30, "d"), (21.60, 4.85, "w"), (21.15, 3.40, "d"),
              (22.85, 5.55, "w"), (22.85, 4.10, "l"),
              (14.05, 6.30, "d"), (14.05, 4.85, "w"), (14.50, 3.40, "w"),
              (15.30, 6.85, "l")])
    # the large leafy floor plant at the west wall's south end
    cshadow(m, 3.00, 18.60, 1.10, 1.10, feather=0.72, strength=0.84,
            room=(W, D))
    plant(m, 3.00, 18.60, 3.30, scale=1.45, seed=23)
    return save_and_place("Arcade TV Wall", m, ROOM)


# ================================================== west wall: the desk run
def build_desk():
    m = Model()
    # z 9.6 in round 2 -- the two gaming bays now hold 7.2..14.1 of the west
    # wall, which is where `v3 1` and `v3 2` both put them, so the desk run
    # starts where they end.  It is an L in the photo: the wall run plus a
    # return arm out into the room, which is what carries the two monitors.
    dz0, dz1 = 14.30, 20.90
    TOPY = 2.46
    cshadow(m, 1.39, (dz0 + dz1) / 2, 1.35, (dz1 - dz0) / 2, feather=0.80,
            strength=0.76, room=(W, D))
    # white desktop with a slim edge
    bx(m, DESKW, 0.06, 2.72, TOPY - 0.12, TOPY, dz0, dz1)
    bx(m, Material("a2deske", "#dedbd5", roughness=0.5),
       0.06, 2.72, TOPY - 0.155, TOPY - 0.12, dz0, dz1)
    # sit-stand legs: a column on a Y foot
    for lz in (dz0 + 1.4, (dz0 + dz1) / 2, dz1 - 1.4):
        bx(m, DESKW, 1.05, 1.45, 0.16, TOPY - 0.155, lz - 0.20, lz + 0.20)
        for ang in (0, 130, 230):
            ca, sa = math.cos(R(ang)), math.sin(R(ang))
            m.add(box(1.55, 0.16, 0.26), DESKW,
                  at=(1.25 + ca * 0.72, 0.0, lz + sa * 0.72), rot_y=R(-ang))
    # a lower glass/white console shelf under the north end
    bx(m, DESKW, 0.10, 1.90, 1.28, 1.36, dz0 + 0.2, dz0 + 3.6)
    for (cz, hue) in ((dz0 + 0.9, "#d8d5cf"), (dz0 + 2.0, "#c9c6c0"),
                      (dz0 + 3.0, "#dedbd5")):
        bx(m, Material("a2ret" + hue[1:], hue, roughness=0.5),
           0.35, 1.55, 1.36, 1.72, cz - 0.42, cz + 0.42)
    # monitors: a wide one and two smaller, on arms
    for (mz, mw, mh) in ((dz0 + 2.20, 3.10, 1.55), (dz0 + 6.00, 2.10, 1.20)):
        bx(m, BLACKMET, 0.55, 0.70, TOPY, TOPY + 0.55, mz - 0.12, mz + 0.12)
        bx(m, Material("a2mon", "#1a1c20", roughness=0.35),
           0.62, 0.78, TOPY + 0.42, TOPY + 0.42 + mh, mz - mw / 2, mz + mw / 2)
        bx(m, Material("a2mons", "#0c0f14", roughness=0.12, emissive="#101a24",
                       emissive_strength=0.8),
           0.78, 0.795, TOPY + 0.50, TOPY + 0.34 + mh,
           mz - mw / 2 + 0.06, mz + mw / 2 - 0.06)
    # keyboards, a remote, a soundbar
    for kz in (dz0 + 2.1, dz0 + 3.3, dz0 + 5.4):
        bx(m, Material("a2kb", "#16181c", roughness=0.6),
           1.05, 1.72, TOPY, TOPY + 0.07, kz - 0.75, kz + 0.75)
    bx(m, Material("a2sb", "#202329", roughness=0.5),
       0.70, 0.98, TOPY, TOPY + 0.22, dz0 + 4.3, dz0 + 6.1)
    # two potted plants -- round 2's were 4-inch tufts against the photo's
    # 1.5-2 ft of broad leaf
    for pz in (dz0 + 4.6, dz0 + 1.0):
        plant(m, 2.12, pz, 1.55, scale=0.80, seed=int(pz * 13), on=TOPY)
    # RGB uplight cubes standing along the skirting
    for i in range(5):
        uz = dz0 + 0.9 + i * 1.30
        bx(m, WHTM, 0.14, 0.72, 0.0, 0.58, uz - 0.29, uz + 0.29)
        m.add(cylinder(0.22, 0.03, 12), LEDS[i % 5], at=(0.43, 0.58, uz))
    # the L's return arm, out into the room
    az0, az1 = dz1 - 2.30, dz1
    bx(m, DESKW, 2.72, 5.60, TOPY - 0.12, TOPY, az0, az1)
    bx(m, Material("a2deske", "#dedbd5", roughness=0.5),
       2.72, 5.60, TOPY - 0.155, TOPY - 0.12, az0, az1)
    bx(m, DESKW, 4.90, 5.30, 0.16, TOPY - 0.155, az0 + 0.9, az0 + 1.3)
    for ang in (40, 170, 280):
        ca, sa = math.cos(R(ang)), math.sin(R(ang))
        m.add(box(1.45, 0.16, 0.26), DESKW,
              at=(5.10 + ca * 0.68, 0.02, az0 + 1.1 + sa * 0.68), rot_y=R(-ang))
    bx(m, Material("a2kb", "#16181c", roughness=0.6),
       3.30, 4.70, TOPY, TOPY + 0.07, az0 + 0.75, az0 + 1.30)
    plant(m, 5.05, az0 + 0.55, 1.45, scale=0.75, seed=61, on=TOPY)
    # the black gaming chair -- round 2 built it with its casters at y 0, which
    # put the whole desk's bbox min at -0.11 and sank the piece into the slab
    cx, cz = 4.10, dz1 - 3.70
    cshadow(m, cx, cz, 1.05, 1.05, feather=0.75, strength=0.82, room=(W, D))
    razer_chair(m, cx, cz, rot=90)
    return save_and_place("Arcade Desk", m, ROOM)


# ===================================================== floor: rug + runner
RUG_TEX = noise_tex(64, 238, 34, 23, seed=9, streak=0.70)
RUGM = Material("a2rugt", "#7e7a71", roughness=1.0, tex=RUG_TEX)
RUNM = Material("a2runt", "#88857c", roughness=1.0, tex=RUG_TEX)


def build_rug():
    """The very large flat oatmeal rug, a runner at the cabinet feet, and the
    contact shadows for everything that stands on them.

    ROUND 3: the nap is now a TILED TEXTURE, not a raster of quads.  Round 2's
    quad field metered sd 8.25 against the photo's 6.76 -- on target -- but
    |d1| 0.59 against 2.68, i.e. the right amount of variation four times too
    coarse, and it cost 127 KB.  A 64 px directional-streak tile repeating
    every 2 ft puts the variation at ~1.3 render pixels for ~3 KB, which is the
    lever ROOM-BRIEF's "sd is SCALE-BLIND" section keeps pointing at.
    """
    m = Model()
    x0, x1, z0, z1 = 3.10, 17.30, 3.05, 22.55
    EDGE = Material("a2rugd", "#6f6c64", roughness=1.0)
    bx(m, EDGE, x0, x1, 0.014, 0.052, z0, z1)
    TILE_FT = 3.2
    m.add(uv_quad((x0 + 0.20, 0.058, z1 - 0.20), (x1 - 0.20, 0.058, z1 - 0.20),
                  (x1 - 0.20, 0.058, z0 + 0.20), (x0 + 0.20, 0.058, z0 + 0.20),
                  (0.0, (z1 - z0) / TILE_FT), ((x1 - x0) / TILE_FT,
                                               (z1 - z0) / TILE_FT),
                  ((x1 - x0) / TILE_FT, 0.0), (0.0, 0.0)), RUGM)
    # runner in front of the east cabinets
    rx0, rx1, rz0, rz1 = 15.95, 18.15, 2.20, 18.10
    bx(m, EDGE, rx0, rx1, 0.012, 0.038, rz0, rz1)
    m.add(uv_quad((rx0 + 0.10, 0.042, rz1 - 0.10), (rx1 - 0.10, 0.042, rz1 - 0.10),
                  (rx1 - 0.10, 0.042, rz0 + 0.10), (rx0 + 0.10, 0.042, rz0 + 0.10),
                  (0.0, (rz1 - rz0) / TILE_FT),
                  ((rx1 - rx0) / TILE_FT, (rz1 - rz0) / TILE_FT),
                  ((rx1 - rx0) / TILE_FT, 0.0), (0.0, 0.0)), RUNM)

    Y = 0.115                       # shadows for pieces standing ON the rug
    cshadow(m, 9.80, 12.50, 2.15, 3.15, feather=0.85, y=Y, strength=1.00,
            room=(W, D))
    return save_and_place("Arcade Floor Rug", m, ROOM)


# =================================================================== lounge
def build_lounge():
    """The black modular chaise: two long wedge-backed pads on a common base,
    which is what the photos show -- one sculptural piece, not a sofa."""
    m = Model()
    cx, cz = 9.80, 12.50
    slab(m, BLKF2, cx - 2.10, cx + 2.10, 0.0, 0.72, cz - 3.10, cz + 3.10, r=0.26)
    for (dx, dz, w_, d_, rot, h) in ((-0.55, -1.70, 3.05, 3.10, 4, 2.45),
                                     (0.55, 1.70, 3.05, 3.20, 184, 2.15)):
        sub = Model()
        slab(sub, BLKF, -w_ / 2, w_ / 2, 0.60, 1.32, -d_ / 2, d_ / 2, r=0.32)
        nk = 16
        stp = 0.86 / nk
        for k in range(nk):
            t = 1.0 - (k + 0.5) / nk
            hh = 1.16 + (h - 1.16) * math.sin(t * math.pi / 2) ** 0.85
            bx(sub, BLKF2, -w_ / 2 + 0.05, w_ / 2 - 0.05, 1.02, hh,
               -d_ / 2 + 0.02 + k * stp, -d_ / 2 + 0.02 + (k + 1.9) * stp)
        slab(sub, BLKF, -w_ / 2 + 0.02, w_ / 2 - 0.02, h - 0.26, h,
             -d_ / 2 + 0.02, -d_ / 2 + 0.78, r=0.18)
        ca, sa = math.cos(R(rot)), math.sin(R(rot))
        for part, mm in sub._parts:
            m._parts.append((Part([(cx + dx + x * ca + z * sa, y,
                                    cz + dz - x * sa + z * ca)
                                   for (x, y, z) in part.verts],
                                  part.tris, part.smooth), mm))
    return save_and_place("Arcade Lounge", m, ROOM)


# =============================================== the black-draped folding table
def build_tables():
    m = Model()
    tx, tz = 11.60, 19.35
    # chrome folding frame
    for dx in (-1.95, 1.95):
        bx(m, CHR, tx + dx - 0.07, tx + dx + 0.07, 0.0, 2.32, tz - 0.82, tz - 0.68)
        bx(m, CHR, tx + dx - 0.07, tx + dx + 0.07, 0.0, 2.32, tz + 0.68, tz + 0.82)
        bx(m, CHR, tx + dx - 0.07, tx + dx + 0.07, 2.18, 2.32, tz - 0.82, tz + 0.82)
    # the black cloth: a top and four skirts that hang unevenly
    CL = Material("a2cloth", "#131418", roughness=0.99)
    bx(m, CL, tx - 2.30, tx + 2.30, 2.32, 2.42, tz - 1.10, tz + 1.10)
    m.add(sag_plane(4.60, 0.90, 0.06, 10, 3, y=0.0, edge_drop=0.05), CL,
          at=(tx, 2.42, tz))
    for (a, b, c, e, y0) in ((tx - 2.30, tx + 2.30, tz - 1.14, tz - 1.10, 1.55),
                             (tx - 2.30, tx + 2.30, tz + 1.10, tz + 1.14, 1.62),
                             (tx - 2.34, tx - 2.30, tz - 1.14, tz + 1.14, 1.72),
                             (tx + 2.30, tx + 2.34, tz - 1.14, tz + 1.14, 1.68)):
        bx(m, CL, a, b, y0, 2.42, c, e)
    # a power strip and its lead on the floor beside it
    bx(m, WHTM, tx - 1.10, tx + 0.30, 0.0, 0.14, tz + 1.65, tz + 1.95)
    cshadow(m, tx, tz, 2.35, 1.15, feather=0.75, y=0.118, strength=0.76,
            room=(W, D))
    return save_and_place("Arcade Tables", m, ROOM)


# ==================================================== per-wall albedo skins
SKIN = {"n": "#71706e", "e": "#e2e0dc", "s": "#fffefb", "w": "#b0aeaa"}
# RE-SOLVED 2026-08-23 by probe2.py against the TEXTURED skin and the corrected
# south plane.  At #fafafa the four walls render N 235.3 / E 185.8 / S 160.2 /
# W 213.5 and at #6e6e6e they render N 165.2 / E 73.2 / S 50.6 / W 105.3; the
# two-point power fits (gamma N 0.431, E 1.135, S 1.403, W 0.861) inverted for a
# common target of 170 give 118 / 231 / 255 / 192, then ONE measured nudge (the fits landed
# N 173.1 / E 173.9 / S 162.6 / W 182.9) and 1.5% warm to sit
# in the room's #dcdbd8 hue.  The south wall is the one the sun never reaches --
# it reaches only 165 at pure white, so it is left white and lands ~5 under.


WALL_TEX = noise_tex(64, 250, 6.0, 4.0, seed=41, streak=0.20)
WALL_TILE = 2.6


def build_skins():
    """A full-height, corner-to-corner, NON-emissive paint skin on each wall,
    so the four walls can be brought to one value (the renderer has one sun and
    no bounce, so a single wall_color leaves an 80+ byte spread).

    ROUND 3: each skin is now ONE textured quad rather than ~24 tone-banded
    boxes -- 8 KB against 101, and the fine grain comes from a 64 px tile at
    2.6 ft rather than from 1.85 ft bands.  The hexes are the round-2 solved
    values lifted by 1/0.980 to cancel the tile's mean of 250/255; the south
    wall was already at white and simply loses that 2%."""
    m = Model()
    t = 0.035
    tf = WALL_TILE

    def skin(wall, hexc, a0, a1, y0, y1):
        mat = Material("a2sk" + wall, hexc, roughness=0.95, tex=WALL_TEX)
        u0, u1 = a0 / tf, a1 / tf
        v0, v1 = y0 / tf, y1 / tf
        if wall == "n":
            p = [(a0, y0, t), (a1, y0, t), (a1, y1, t), (a0, y1, t)]
        elif wall == "s":
            zz = D - SD - 0.01     # in front of the Movie Room's wall mass
            p = [(a1, y0, zz), (a0, y0, zz), (a0, y1, zz), (a1, y1, zz)]
        elif wall == "w":
            p = [(t, y0, a1), (t, y0, a0), (t, y1, a0), (t, y1, a1)]
        else:
            p = [(W - t, y0, a0), (W - t, y0, a1), (W - t, y1, a1),
                 (W - t, y1, a0)]
        m.add(Part(p, [(0, 1, 2), (0, 2, 3)],
                   uv=[(u0, v1), (u1, v1), (u1, v0), (u0, v0)]), mat)

    skin("n", SKIN["n"], 0.0, W, 0.0, H - 0.02)
    skin("e", SKIN["e"], 0.0, D, 0.0, H - 0.02)
    skin("w", SKIN["w"], 0.0, D, 0.0, H - 0.02)
    # the south skin must NOT bridge the door hole or the doorway is sealed
    skin("s", SKIN["s"], 0.0, MDOOR[0], 0.0, H - 0.02)
    skin("s", SKIN["s"], MDOOR[1], W, 0.0, H - 0.02)
    skin("s", SKIN["s"], MDOOR[0], MDOOR[1], 6.95, H - 0.02)
    return save_and_place("Arcade Wall Wash", m, ROOM)


BUILDERS = {
    "ceiling": build_ceiling, "trim": build_trim, "skins": build_skins,
    "rug": build_rug, "east": build_east_cabs, "shelf": build_east_shelf,
    "south": build_south_cabs, "north": build_north, "tv": build_tv_wall,
    "desk": build_desk, "lounge": build_lounge, "tables": build_tables,
    "ncab": build_north_cabs, "booths": build_booths,
}


if __name__ == "__main__":
    import sys
    print("room 2 Arcade Room -- round 2 (orientation corrected)")
    which = sys.argv[1:] or list(BUILDERS)
    if not sys.argv[1:]:
        drop_objects({"Arcade Cabinets", "Arcade Cabinets West",
                      "Arcade West Shelf"})
        surfaces(ROOM, wall_color="#dcdbd8", floor_color="#6e6b68",
                 floor_texture="wood")
        openings()
    out = [BUILDERS[k]() for k in which]
    print("total %.1f KB" % sum(p.get("kb", 0) for p in out))
