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

ROOM, W, D, H = 2, 20.7, 23.3, 8.0
BASE = "http://127.0.0.1:5000"

MDOOR = (13.50, 16.20)              # south wall, local x -- door to room 1
PIER = (0.0, 5.20, 3.40, 7.10)      # utility room inside the footprint
PDOOR = (0.55, 3.25)                # its door, on the pier's south face
SHELF_Y = 6.34
COVE_Y = 7.62

# ------------------------------------------------------------------ palette
CABBLK = Material("a2cab", "#191a1e", roughness=0.55)
CABDK = Material("a2cabd", "#0d0e11", roughness=0.5)
SCRN = Material("a2scr", "#0a0c10", roughness=0.25, emissive="#12202c",
                emissive_strength=1.1)
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
            room=None, seg=20):
    """Contact shadow: full darkness at the piece's own footprint, feathering
    OUT over `feather` feet.  `strength` scales the whole ramp (1.0 = the
    measured house default, ~35% at the contact edge)."""
    inner = _sellipse(cx, cz, hx, hz, y, seg, room=room)
    # the core, so the band right at the edge is not a lone outline
    core = Model()
    core.add(Part([(cx, y, cz)] + inner,
                  [(0, 1 + (k + 1) % seg, 1 + k) for k in range(seg)]),
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
        m.add(Part(v, tris), SHMATS[idx])


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
    m = baseboards(W, D, doors=[("s", *MDOOR)])
    cased_opening(m, "s", W, D, SA(MDOOR[1]), SA(MDOOR[0]), top=6.83)
    door_unit(m, "s", W, D, SA(MDOOR[1]) + 0.02, SA(MDOOR[0]) - 0.02, top=6.83)

    px0, px1, pz0, pz1 = PIER
    PIERM = Material("a2pier", "#dcdbd8", roughness=0.95)
    bx(m, PIERM, px0, px1, 0.0, H - 0.02, pz0, pz1 - 0.14)
    bx(m, TRIM, px0, px1, 0.0, H - 0.02, pz1 - 0.14, pz1)         # its face
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
def upright(m, cx, cz, rot, hue, bw=2.15, bd=2.55, top=6.25, seed=1,
            riser=0.0, art2=None):
    """One arcade cabinet, authored facing +z then spun by `rot` degrees.

    bw/bd/top let a run vary its silhouette without a second model; the printed
    side art is a band of vertical strips in two tones so the flanks read as
    artwork rather than a colour block from 3 ft away.
    """
    sub = Model()
    rnd = Rnd(seed)
    body_h = top - 2.95
    cp_y = body_h + 0.14
    scr_lo, scr_hi = body_h + 0.28, top - 0.98
    mq_lo, mq_hi = top - 0.86, top - 0.28

    dark = mix(hue, "#151719", 0.60)
    art = Material("a2art" + dark[1:], dark, roughness=0.78)
    dark2 = mix(art2 or hue, "#131518", 0.72)
    art_b = Material("a2artb" + dark2[1:], dark2, roughness=0.80)
    mqc = mix(hue, "#22242c", 0.22)
    mq = Material("a2mq" + mqc[1:], mqc, roughness=0.45, emissive=mqc,
                  emissive_strength=1.15)

    if riser:
        bx(sub, CABDK, -bw / 2, bw / 2, 0.0, riser, -bd / 2, bd / 2 - 0.30)
    # carcase
    bx(sub, CABBLK, -bw / 2, bw / 2, riser, body_h, -bd / 2, bd / 2 - 0.30)
    bx(sub, CABBLK, -bw / 2, bw / 2, body_h, top, -bd / 2, bd / 2 - 0.62)
    # printed side art -- vertical strips, alternating tone, both flanks
    ns = 5
    for sx in (-bw / 2 - 0.010, bw / 2):
        for k in range(ns):
            z0 = -bd / 2 + 0.10 + k * (bd - 0.55) / ns
            z1 = z0 + (bd - 0.55) / ns * 0.94
            y1 = body_h - 0.10 - rnd.f(0.0, 0.22)
            bx(sub, art if k % 2 else art_b, sx, sx + 0.010,
               riser + 0.10, y1, z0, z1)
    # printed front panel -- in the photos this is the brightest thing on a
    # cabinet after the marquee (Marvel, TMNT, NBA Jam are all full-colour)
    front = Material("a2fr" + hue[1:], hue, roughness=0.72)
    bx(sub, art, -bw / 2 + 0.06, bw / 2 - 0.06, riser + 0.10, body_h - 0.08,
       bd / 2 - 0.32, bd / 2 - 0.30)
    bx(sub, front, -bw / 2 + 0.13, bw / 2 - 0.13, riser + 0.34, body_h - 0.42,
       bd / 2 - 0.305, bd / 2 - 0.292)
    bx(sub, art_b, -bw / 2 + 0.22, bw / 2 - 0.22, riser + 0.52, body_h - 0.62,
       bd / 2 - 0.295, bd / 2 - 0.286)
    # control panel with joysticks + buttons
    bx(sub, CPANEL, -bw / 2 + 0.04, bw / 2 - 0.04, cp_y - 0.12, cp_y,
       bd / 2 - 0.72, bd / 2 - 0.24)
    for k in range(2):
        jx = -bw / 4 + k * bw / 2
        sub.add(cylinder(0.042, 0.18, 6), CHR, at=(jx - 0.18, cp_y, bd / 2 - 0.60))
        sub.add(cylinder(0.070, 0.06, 6), BUTTONS[k],
                at=(jx - 0.18, cp_y + 0.18, bd / 2 - 0.60))
        for b in range(2):
            sub.add(cylinder(0.055, 0.032, 6), BUTTONS[(k + b) % 4],
                    at=(jx + 0.02 + b * 0.15, cp_y, bd / 2 - 0.44 + 0.05 * (b % 2)))
    # screen, raked back in a dark bezel
    bx(sub, CABDK, -bw / 2 + 0.05, bw / 2 - 0.05, scr_lo - 0.08, scr_hi + 0.10,
       bd / 2 - 0.66, bd / 2 - 0.58)
    bx(sub, SCRN, -bw / 2 + 0.16, bw / 2 - 0.16, scr_lo, scr_hi,
       bd / 2 - 0.58, bd / 2 - 0.565)
    # marquee -- a real lamp in the photo, so legitimately emissive
    bx(sub, CABDK, -bw / 2 + 0.03, bw / 2 - 0.03, mq_lo - 0.06, mq_hi + 0.06,
       bd / 2 - 0.64, bd / 2 - 0.58)
    bx(sub, mq, -bw / 2 + 0.07, bw / 2 - 0.07, mq_lo, mq_hi,
       bd / 2 - 0.58, bd / 2 - 0.56)
    # pale cap + plinth: end-on from the dollhouse quadrant an all-black run
    # merges into one wall, and these two lines break it into machines
    CAP = Material("a2cap", "#787c82", roughness=0.55)
    bx(sub, CAP, -bw / 2 - 0.012, bw / 2 + 0.012, top - 0.09, top,
       -bd / 2 - 0.012, bd / 2 - 0.60)
    bx(sub, CAP, -bw / 2 - 0.012, bw / 2 + 0.012, 0.0, 0.08,
       -bd / 2 - 0.012, bd / 2 - 0.30)

    ca, sa = math.cos(R(rot)), math.sin(R(rot))
    for part, mm in sub._parts:
        v = [(cx + x * ca + z * sa, y, cz - x * sa + z * ca)
             for (x, y, z) in part.verts]
        m._parts.append((Part(v, part.tris, part.smooth), mm))


def build_east_cabs():
    """The hero run: seven uprights down the east wall, facing west."""
    m = Model()
    zc = [1.62, 3.94, 6.26, 8.58, 10.90, 13.22, 15.54]
    cshadow(m, W - 1.32, (zc[0] + zc[-1]) / 2, 1.32,
            (zc[-1] - zc[0]) / 2 + 1.20, feather=0.85, strength=1.00,
            room=(W, D))
    for i, z in enumerate(zc):
        upright(m, W - 1.32, z, 270, HUES[i], bw=2.22, bd=2.55,
                top=5.96 + (0.18 if i % 3 == 1 else 0.0), seed=i + 1,
                riser=0.0 if i % 2 else 0.10, art2=HUES[(i * 5 + 3) % len(HUES)])
    return save_and_place("Arcade Cabinets East", m, ROOM)


def build_south_cabs():
    """Legends Ultimate, Capcom Champion, Time Crisis and T2 on the south wall,
    plus the black diagonal acoustic panel between them and the door, and Ridge
    Racer round the corner at the SW."""
    m = Model()
    run = [(2.05, 3.05, 6.30, 0), (4.95, 2.55, 5.98, 6),
           (7.55, 2.60, 6.16, 9), (10.05, 2.42, 5.90, 8)]
    cshadow(m, 5.9, D - 1.32, 5.75, 1.30, feather=0.85, strength=1.00,
            room=(W, D))
    for (cx, bw, top, hi) in run:
        upright(m, cx, D - 1.32, 180, HUES[hi], bw=bw, bd=2.55, top=top,
                seed=int(cx * 7), riser=0.0, art2=HUES[(hi + 4) % len(HUES)])
    # the blue CAPCOM lower cabinet the Champion Edition stands on
    bx(m, Material("a2capc", "#1c4c9a", roughness=0.6),
       3.62, 6.28, 0.0, 2.55, D - 2.55, D - 0.06)
    bx(m, Material("a2capy", "#e0b21c", roughness=0.5),
       4.30, 5.60, 0.42, 0.70, D - 2.60, D - 2.58)
    # black diagonal-rib acoustic panel between the run and the door
    sub = Model()
    bx(sub, ACOU, SA(13.20), SA(11.60), 3.20, 6.70, 0.0, 0.09)
    RIB = Material("a2rib", "#474b52", roughness=0.88)
    for k in range(9):
        bx(sub, RIB, SA(13.10) + k * 0.17, SA(13.04) + k * 0.17,
           3.30 + k * 0.34, 6.60, 0.09, 0.10)
    blit(m, sub, "s", W, D, 0.0)

    # ---- east of the door: the 1.2 ft stub carries the vertical RGB bar and a
    # wall-mounted mini cabinet; the Connect-4 game stands on the floor beside it
    sub = Model()
    hp = [(0.30 * math.cos(R(60 * j + 30)), 0.30 * math.sin(R(60 * j + 30)))
          for j in range(6)]
    for k in range(7):                       # hexagon segments of the light bar
        wpanel(sub, LEDS[(k + 3) % 5], hp, SA(16.85), 2.35 + k * 0.62, 0.0, 0.07)
    blit(m, sub, "s", W, D, 0.0)
    # mini cabinet hung on the wall east of the door
    bx(m, CABBLK, 17.35, 18.85, 2.45, 5.35, D - 0.62, D - 0.04)
    bx(m, SCRN, 17.52, 18.68, 3.40, 4.60, D - 0.645, D - 0.62)
    bx(m, LEDS[0], 17.50, 18.70, 4.75, 5.20, D - 0.645, D - 0.62)
    bx(m, LEDS[4], 17.50, 18.70, 2.70, 3.20, D - 0.645, D - 0.62)
    # Connect-4 on a low white console
    cshadow(m, 19.22, D - 0.95, 1.35, 0.80, feather=0.70, strength=0.82,
            room=(W, D))
    bx(m, WHTM, 17.90, 20.55, 0.0, 2.05, D - 1.70, D - 0.16)
    bx(m, TRIM, 17.83, 20.62, 2.05, 2.17, D - 1.76, D - 0.10)
    G = Material("a2game", "#17181c", roughness=0.62)
    bx(m, G, 18.35, 20.10, 2.17, 4.05, D - 1.10, D - 0.96)
    for r_ in range(5):
        for c_ in range(5):
            bx(m, WHTM, 18.47 + c_ * 0.33, 18.69 + c_ * 0.33,
               2.29 + r_ * 0.31, 2.51 + r_ * 0.31, D - 0.965, D - 0.955)

    # ---- Ridge Racer, round the corner on the west wall's south end
    cshadow(m, 1.32, 21.55, 1.30, 1.18, feather=0.80, strength=0.94,
            room=(W, D))
    upright(m, 1.32, 21.55, 90, HUES[10], bw=2.30, bd=2.55, top=6.10, seed=77,
            art2=HUES[1])
    return save_and_place("Arcade Cabinets South", m, ROOM)


# =========================================== the Funko shelf, chevrons, pinball
def build_east_shelf():
    m = Model()
    sz0, sz1 = 0.90, 17.60
    # ---- lit collectible shelf
    bx(m, SHELFW, W - 0.86, W, SHELF_Y, SHELF_Y + 0.075, sz0, sz1)
    bx(m, SHELFW, W - 0.16, W, SHELF_Y - 0.40, SHELF_Y, sz0, sz1)
    n = 34
    step = (sz1 - sz0) / n
    for i in range(n):
        z = sz0 + (i + 0.5) * step
        bx(m, LEDS[i % 5], W - 0.19, W - 0.13, SHELF_Y - 0.11, SHELF_Y - 0.03,
           z - step / 2, z + step / 2)
        hue = mix(HUES[(i * 5) % len(HUES)], "#2a2c31", 0.42)
        fm = Material("a2fig" + hue[1:], hue, roughness=0.68)
        bx(m, fm, W - 0.55, W - 0.34, SHELF_Y + 0.075, SHELF_Y + 0.20,
           z - 0.085, z + 0.085)
        bx(m, fm, W - 0.57, W - 0.32, SHELF_Y + 0.20, SHELF_Y + 0.33,
           z - 0.100, z + 0.100)

    # ---- the chevron acoustic band + the cove LED above it
    sub = Model()
    CHEV = [(-0.64, -0.44), (0.0, -0.06), (0.64, -0.44),
            (0.64, 0.0), (0.0, 0.40), (-0.64, 0.0)]
    z = 0.70
    while z < D - 1.2:
        wpanel(sub, HEXW, CHEV, z, 6.98, 0.0, 0.06)
        z += 1.44
    blit(m, sub, "e", W, D, 0.0)
    # cove: a shallow shelf with the strip tucked behind its lip
    bx(m, TRIM, W - 0.52, W, COVE_Y, COVE_Y + 0.14, 0.20, D - 0.20)
    bx(m, COVEM, W - 0.44, W - 0.34, COVE_Y + 0.14, COVE_Y + 0.22, 0.24, D - 0.24)
    # wall speaker box at the north end
    bx(m, WHTM, W - 0.70, W - 0.16, 6.55, 7.35, 0.55, 1.30)

    # ---- the Y-shaped RGB fixture, south end of the east wall
    y_fixture(m, "e", 20.55, 4.15, 1.35)

    # ---- pinball at the run's south end
    px, pz = W - 2.55, 18.75
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


def y_fixture(m, wall, at, y, ln=1.35):
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
            wpanel(sub, LEDS[(t + j * 2) % 5], rot,
                   a0 + ca * ln * f, y + sa_ * ln * f, 0.0, 0.075)
    blit(m, sub, wall, W, D, 0.0)


def hex_wall(m, wall, spots):
    """Nanoleaf-style hexagons.  `spots` are (ROOM x or z, height[, kind])."""
    conv = {"n": lambda a: a, "e": lambda a: a, "s": SA, "w": WA}[wall]
    sub = Model()
    for i, sp in enumerate(spots):
        kind = sp[2] if len(sp) > 2 else ("l" if i % 4 == 0 else
                                          ("d" if i % 4 == 2 else "w"))
        mat = LITM if kind == "l" else (HEXD if kind == "d" else HEXW)
        wpanel(sub, mat, HEXPTS, conv(sp[0]), sp[1], 0.0, 0.085)
    blit(m, sub, wall, W, D, 0.0)


def build_north():
    """North wall: hex panels, three small mounted screens, a black hexagon
    cluster, and a slim RGB floor lamp in the corner beside the utility room."""
    m = Model()
    hex_wall(m, "n",
             [(6.10, 6.45, "d"), (7.35, 7.05, "w"), (8.60, 6.40, "w"),
              (9.85, 7.05, "l"), (11.10, 6.40, "d"), (12.35, 7.05, "w"),
              (13.60, 6.40, "w"), (14.85, 7.05, "d"), (16.10, 6.40, "l"),
              (17.35, 7.05, "w"), (18.60, 6.40, "w"), (19.70, 7.05, "d"),
              (8.10, 5.25, "w"), (12.10, 5.20, "w"), (17.60, 5.25, "d")])
    # three small screens hung between the hexes
    sub = Model()
    for (a, y, w_, h_, hue) in ((8.55, 6.55, 1.35, 0.80, "#c0392b"),
                                (11.60, 6.60, 1.10, 0.66, "#e0b21c"),
                                (14.90, 6.55, 1.20, 0.72, "#2f6fd0")):
        bx(sub, CABDK, a - w_ / 2, a + w_ / 2, y - h_ / 2, y + h_ / 2, 0.0, 0.10)
        bx(sub, Material("a2sm" + hue[1:], hue, roughness=0.35, emissive=hue,
                         emissive_strength=1.6),
           a - w_ / 2 + 0.06, a + w_ / 2 - 0.06, y - h_ / 2 + 0.05,
           y + h_ / 2 - 0.05, 0.10, 0.115)
    blit(m, sub, "n", W, D, 0.0)
    # slim RGB floor lamp in the corner beside the utility room
    lx, lz = 6.05, 0.85
    cshadow(m, lx, lz, 0.52, 0.52, feather=0.55, strength=0.71, room=(W, D))
    m.add(cylinder(0.50, 0.06, 12), BLACKMET, at=(lx, 0.0, lz))
    m.add(cylinder(0.052, 4.55, 8), BLACKMET, at=(lx, 0.06, lz))
    m.add(cylinder(0.095, 3.30, 8),
          Material("a2lamp", "#e6ffd4", roughness=0.3, emissive="#d4ff96",
                   emissive_strength=3.0), at=(lx + 0.09, 1.10, lz))
    # a green vase on the floor beside it
    m.add(cylinder(0.28, 1.00, 12, r_top=0.15),
          Material("a2vase", "#5c8f7a", roughness=0.4), at=(7.30, 0.0, 0.80))
    return save_and_place("Arcade North Wall", m, ROOM)


# ==================================================== west wall: TV + hexes
def build_tv_wall():
    m = Model()
    a0, a1 = WA(16.60), WA(9.20)          # the very large flat TV
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
       WA(8.60), WA(7.35), 6.35, 7.30, 0.0, 0.05)
    blit(m, sub, "w", W, D, 0.0)
    hex_wall(m, "w",
             [(8.10, 6.20, "d"), (8.10, 4.75, "w"), (8.55, 3.30, "w"),
              (17.85, 6.30, "d"), (17.85, 4.85, "w"), (17.40, 3.40, "d"),
              (19.60, 5.55, "w"), (19.60, 4.10, "l"), (7.05, 5.50, "w")])
    # the second Y light, north of the TV (photo v3 3)
    y_fixture(m, "w", 7.05, 3.95, 1.15)
    return save_and_place("Arcade TV Wall", m, ROOM)


# ================================================== west wall: the desk run
def build_desk():
    m = Model()
    dz0, dz1 = 9.60, 20.10
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
    for kz in (dz0 + 3.9, dz0 + 5.1, dz0 + 8.2):
        bx(m, Material("a2kb", "#16181c", roughness=0.6),
           1.05, 1.72, TOPY, TOPY + 0.07, kz - 0.75, kz + 0.75)
    bx(m, Material("a2sb", "#202329", roughness=0.5),
       0.70, 0.98, TOPY, TOPY + 0.22, dz0 + 6.9, dz0 + 9.4)
    # two potted plants
    for pz in (dz0 + 6.9, dz0 + 1.1):
        m.add(cylinder(0.24, 0.30, 12, r_top=0.21), POTW, at=(2.12, TOPY, pz))
        for k in range(7):
            a = R(51 * k)
            m.add(box(0.36, 0.035, 0.17), GREEN,
                  at=(2.12 + 0.15 * math.cos(a), TOPY + 0.32 + 0.05 * (k % 3),
                      pz + 0.15 * math.sin(a)), rot_y=-a, rot_z=R(20))
    # RGB uplight cubes standing along the skirting
    for i in range(6):
        uz = dz0 + 0.9 + i * 1.85
        bx(m, WHTM, 0.14, 0.72, 0.0, 0.58, uz - 0.29, uz + 0.29)
        m.add(cylinder(0.22, 0.03, 12), LEDS[i % 5], at=(0.43, 0.58, uz))
    # the black gaming chair
    cx, cz = 3.75, dz0 + 2.6
    cshadow(m, cx, cz, 1.05, 1.05, feather=0.75, strength=0.82, room=(W, D))
    m.add(cylinder(0.16, 1.05, 10), BLACKMET, at=(cx, 0.22, cz))
    for k in range(5):
        a = R(72 * k)
        m.add(box(1.05, 0.13, 0.20), BLACKMET,
              at=(cx + 0.48 * math.cos(a), 0.10, cz + 0.48 * math.sin(a)),
              rot_y=-a)
        m.add(cylinder(0.11, 0.20, 8), BLACKMET,
              at=(cx + 0.92 * math.cos(a), 0.0, cz + 0.92 * math.sin(a)),
              rot_x=R(90))
    slab(m, BLKF2, cx - 0.88, cx + 0.88, 1.27, 1.52, cz - 0.86, cz + 0.86, r=0.13)
    slab(m, BLKF, cx + 0.38, cx + 0.80, 1.52, 3.55, cz - 0.82, cz + 0.82, r=0.13)
    slab(m, BLKF2, cx + 0.30, cx + 0.62, 3.55, 3.95, cz - 0.52, cz + 0.52, r=0.11)
    for dz in (-0.88, 0.88):
        slab(m, BLKF2, cx - 0.30, cx + 0.44, 1.52, 2.28, cz + dz - 0.09,
             cz + dz + 0.09, r=0.07)
    return save_and_place("Arcade Desk", m, ROOM)


# ===================================================== floor: rug + runner
def build_rug():
    """The very large flat oatmeal rug, a runner at the cabinet feet, and the
    contact shadows for everything that stands on them."""
    m = Model()
    x0, x1, z0, z1 = 3.10, 17.30, 3.05, 22.55
    BASE = "#757269"
    TONES = [Material("a2rug%d" % i,
                      mix(BASE, "#ffffff" if d > 0 else "#000000", abs(d)),
                      roughness=1.0)
             for i, d in enumerate((-0.105, -0.052, 0.0, 0.052, 0.105,
                                    0.026, -0.026))]
    bx(m, TONES[1], x0, x1, 0.014, 0.046, z0, z1)
    bx(m, TONES[2], x0 + 0.22, x1 - 0.22, 0.046, 0.058, z0 + 0.22, z1 - 0.22)
    # The nap.  Round 2a tried 0.60 ft BANDS: sd 17.7 (photo 12-18, on target)
    # but |d1| 1.57 against the photo's 2.8-4.9 -- the right amount of variation
    # at the wrong scale.  Round 2b tried a 0.62 x 0.40 ft CELL grid and it read
    # as a chequerboard of tiles, a clear perceptual regression.  What the photo
    # actually has is a DIRECTIONAL nap: long streaks along one axis, so pixels
    # are strongly correlated along x and only weakly along z.  So: rows 0.34 ft
    # deep (fine, which is where |d1| comes from) x 1.55 ft long (coarse, which
    # is why it does not chequer), plus a scatter of longer overlaid streaks.
    # They are QUADS on the body slab, not boxes -- a fifth of the payload.
    rnd = Rnd(9)
    cw, cd = 1.55, 0.34
    nx = int((x1 - x0 - 0.44) / cw)
    nz = int((z1 - z0 - 0.44) / cd)
    for j in range(nz):
        za = z0 + 0.22 + j * cd
        for i in range(nx):
            xa = x0 + 0.22 + i * cw
            rect_up(m, TONES[int(rnd.f(0, 6.999))], xa, xa + cw + 0.004,
                    0.0595, za, za + cd + 0.004)
        for k in range(2):
            xa = x0 + 0.3 + rnd.f(0.0, (x1 - x0) - 4.2)
            rect_up(m, TONES[int(rnd.f(0, 6.999))], xa,
                    xa + rnd.f(1.8, 3.8), 0.0605, za + 0.02, za + cd + 0.02)
    # runner in front of the east cabinets
    bx(m, Material("a2run", "#7e7b73", roughness=1.0),
       16.05, 18.15, 0.012, 0.040, 1.10, 17.20)

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
SKIN = {"n": "#747371", "e": "#e6e4e0", "s": "#fffefb", "w": "#b5b3af"}
# solved 2026-08-22 by probe2.py: skin at albedo 250 rendered
#   N 239.1 / E 187.0 / S 163.7 / W 214.7  -- spread 75.4 -- and at
# albedo 110  N 168.0 / E 75.3 / S 51.9 / W 106.0.  Two-point power fits
# (gamma N .43 E 1.11 S 1.40 W .86) inverted for a common target of 172.
# The south wall is the one the sun never reaches: it caps at 168 even
# pure white, so it is left at white and lands ~3 under the others.
# Greys are nudged 1.5% warm to sit in the room's #dcdbd8 hue.


def build_skins():
    """A full-height, corner-to-corner, NON-emissive paint skin on each wall,
    so the four walls can be brought to one value (the renderer has one sun and
    no bounce, so a single wall_color leaves an 80+ byte spread).  Roughness is
    matched to the room wall's 0.95 or the seam shows, and the skin carries a
    subtle two-tone vertical banding so it is paint, not algebraically perfect
    flat colour."""
    m = Model()
    t = 0.035
    rnd = Rnd(31)
    for wall, hexc in SKIN.items():
        base = Material("a2sk" + wall, hexc, roughness=0.95)
        alt = Material("a2skb" + wall, mix(hexc, "#000000", 0.030), roughness=0.95)
        alt2 = Material("a2skc" + wall, mix(hexc, "#ffffff", 0.028), roughness=0.95)
        total = W if wall in "ns" else D
        # the south wall's own frame runs backwards, and the skin must NOT
        # bridge the door hole or the doorway is sealed by a grey panel
        gaps = [(SA(MDOOR[1]) - 0.10, SA(MDOOR[0]) + 0.10)] if wall == "s" else []
        n = int(total / 1.85)
        for i in range(n):
            a = i * total / n
            b = (i + 1) * total / n
            mats = (base, alt, base, alt2)
            for (y0, y1) in ((0.0, 4.0), (4.0, H - 0.02)):
                mt = mats[(i + int(y0)) % 4] if rnd.f(0, 1) > 0.35 else base
                if any(a < gb and b > ga for (ga, gb) in gaps) and y0 < 7.0:
                    for (sa_, sb_) in spans(total, gaps):
                        if sb_ <= a or sa_ >= b:
                            continue
                        aa, bb = max(a, sa_), min(b, sb_)
                        bx(m, mt, aa, bb, y0, min(y1, 6.95), D - t, D)
                    if y1 > 6.95:
                        bx(m, mt, a, b, 6.95, y1, D - t, D)
                    continue
                if wall == "n":
                    bx(m, mt, a, b, y0, y1, 0.0, t)
                elif wall == "s":
                    bx(m, mt, a, b, y0, y1, D - t, D)
                elif wall == "w":
                    bx(m, mt, 0.0, t, y0, y1, a, b)
                else:
                    bx(m, mt, W - t, W, y0, y1, a, b)
    return save_and_place("Arcade Wall Wash", m, ROOM)


BUILDERS = {
    "ceiling": build_ceiling, "trim": build_trim, "skins": build_skins,
    "rug": build_rug, "east": build_east_cabs, "shelf": build_east_shelf,
    "south": build_south_cabs, "north": build_north, "tv": build_tv_wall,
    "desk": build_desk, "lounge": build_lounge, "tables": build_tables,
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
