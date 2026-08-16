"""Room 2 -- Arcade Room, 20.7 (x, W-E) x 23.3 (z, N-S) x 8.0 ft.

ORIENTATION (derived, see the build report).  The photo is taken from the SOUTH
looking NORTH, standing in the doorway from the Movie Room:

  south wall z=23.3  shared with the Movie Room -- the door at local x 13.5-16.2
                     (the plan's wall gap, world x 11.4-14.1; the same door the
                     Movie Room photo shows from the other side).  Behind camera.
  west  wall x=0     the long run of Arcade1Up uprights, the collectible shelf,
                     the duct bulkhead with its chevron panels and cove LED, and
                     the pinball at the north end
  north              the plan puts a 5.3 x 6.5 ft utility room inside this
                     footprint's NW corner (world x -2.3..3.2, z -9.0..-5.3).
                     Its south face is the wall the photo's white six-panel door
                     sits in -- 5.3 ft wide, which is exactly the width of the
                     door plus the wall cabinet beside it.
  east  wall x=20.7  the five full-size uprights (T2, Time Crisis, Champion
                     Edition, Legends Ultimate, Ridge Racer) under hex panels

Run:  python ar.py
"""

import json
import urllib.request

from bkit import *          # noqa: F401,F403

ROOM, W, D, H = 2, 20.7, 23.3, 8.0
BASE = "http://127.0.0.1:5000"

MDOOR = (13.50, 16.20)         # south wall, local x -- the door to room 1
PIER = (0.0, 5.30, 0.0, 6.50)  # utility room inside the footprint: x0,x1,z0,z1
PDOOR = (2.45, 5.15)           # its door, on the pier's south face
SHELF_Y = 6.10
BULK_Y, BULK_D = 6.92, 1.35    # duct bulkhead over the west run


# ----------------------------------------------------------------- palette
CABBLK = Material("arcab", "#191a1e", roughness=0.55)       # cabinet carcase
CABDK = Material("arcabd", "#0e0f12", roughness=0.5)
SCRN = Material("arscr", "#0a0c10", roughness=0.25, emissive="#12202c",
                emissive_strength=1.2)
CPANEL = Material("arcp", "#2c2e34", roughness=0.6)
CHR = Material("archr", "#adb2b6", roughness=0.28, metallic=0.55)
BLKF = Material("arblkf", "#131418", roughness=0.95)        # the black lounge
BLKF2 = Material("arblkf2", "#1d1f24", roughness=0.95)
KNIT = Material("arknit", "#9c9a96", roughness=1.0)         # grey pouf
WHTM = Material("arwht", "#e7e5e0", roughness=0.5)
HEXW = Material("arhexw", "#eceae5", roughness=0.6)         # matte hex panel
HEXD = Material("arhexd", "#3a3d42", roughness=0.6)
ACOU = Material("aracou", "#2f3238", roughness=0.9)         # acoustic panel
SHELFW = Material("arshelf", "#efedE8".lower(), roughness=0.55)
POSTER = Material("arpost", "#20242b", roughness=0.7)

# marquee / side-art hues, straight off the photo's cabinets
HUES = ["#a3202a", "#1f3f7a", "#c8871c", "#1d6b3a", "#5f2d7a",
        "#b8452a", "#1d7f9c", "#8e1f3c", "#3b3f46", "#c02a55"]

BUTTONS = [Material("arb%d" % i, c, roughness=0.35, emissive=c,
                    emissive_strength=0.8)
           for i, c in enumerate(("#d02b2b", "#2f7fd0", "#d8b026", "#2fa54f"))]


def api(method, path, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def drop_object(name):
    """The shell pass placed one 'Arcade Cabinets' object; this build replaces it
    with a west and an east run, so the old row has to go or it doubles up."""
    with urllib.request.urlopen(f"{BASE}/api/house", timeout=30) as r:
        house = json.loads(r.read().decode())
    for f in house["floors"]:
        for rm in f["rooms"]:
            for o in rm.get("objects", []):
                if o.get("name") == name:
                    req = urllib.request.Request(
                        f"{BASE}/api/house/object/{o['id']}", method="DELETE")
                    urllib.request.urlopen(req, timeout=30).read()
                    print(f"  deleted stale object {name!r}")


def openings():
    """One real cut opening: the door to the Movie Room.  Edge 2 is the south
    wall (W,D)->(0,D), so its offset runs BACKWARDS from x=W."""
    with urllib.request.urlopen(f"{BASE}/api/house", timeout=30) as r:
        house = json.loads(r.read().decode())
    room = next(rm for f in house["floors"] for rm in f["rooms"] if rm["id"] == ROOM)
    have = {(o["edge_index"], o["type"]): o for o in room.get("openings", [])}
    spec = dict(edge_index=2, type="door", offset=W - MDOOR[1],
                width=MDOOR[1] - MDOOR[0], height=6.83, elevation=0.0)
    key = (2, "door")
    if key in have:
        api("PATCH", f"/api/house/opening/{have[key]['id']}", spec)
        print("  opening south door updated")
    else:
        api("POST", f"/api/house/room/{ROOM}/opening", spec)
        print("  opening south door created")


# =================================================== ceiling + duct bulkhead
def build_ceiling():
    m = ceiling(W, D, H,
                cans=[(8.4, 2.4), (14.6, 2.4),
                      (7.2, 8.2), (13.9, 8.2), (18.6, 8.2),
                      (7.2, 14.6), (13.9, 14.6), (18.6, 14.6),
                      (8.6, 20.6), (15.4, 20.6)],
                speakers=[(6.9, 5.4, 0.52), (16.4, 5.4, 0.52),
                          (6.9, 18.4, 0.52), (16.4, 18.4, 0.52)],
                vents=[(11.5, 11.4, 1.00, 0.55)])

    # ---- the duct bulkhead over the west run, with its chevron acoustic
    # panels and the cove LED that washes the ceiling in the photo
    z0, z1 = PIER[3], D - 0.4
    bx(m, TRIM, 0.0, BULK_D, BULK_Y, H - 0.02, z0, z1)
    for i in range(int((z1 - z0) / 1.30)):
        c = z0 + 0.65 + i * 1.30
        for (dz, dy) in ((-0.30, 0.0), (0.30, 0.0)):
            m.add(prism([(0.0, -0.42), (0.34, 0.0), (0.0, 0.42)], 0.05),
                  HEXW, at=(BULK_D + 0.05, BULK_Y + 0.26 + dy, c + dz),
                  rot_z=R(90))
    LED = Material("arled", "#f2f6ff", roughness=0.3, emissive="#cfe4ff",
                   emissive_strength=3.0)
    bx(m, LED, BULK_D - 0.10, BULK_D - 0.02, H - 0.16, H - 0.06, z0, z1)
    return save_and_place("Arcade Ceiling", m, ROOM)


# ================================================= skirting, doors, the pier
def build_trim():
    m = baseboards(W, D, doors=[("s", *MDOOR)])
    cased_opening(m, "s", W, D, *MDOOR, top=6.83)

    # ---- the utility room that sits inside this footprint's NW corner.
    # Not decoration: without it the photo's far wall (and its door) has
    # nothing to sit in, and the west cabinet run has no north end.
    px0, px1, pz0, pz1 = PIER
    bx(m, Material("arpier", "#dcdbd8", roughness=0.95),
       px0, px1, 0.0, H - 0.02, pz0, pz1 - 0.16)
    bx(m, TRIM, px0, px1, 0.0, H - 0.02, pz1 - 0.16, pz1)          # its face
    # skirting + a slim cap on the face, gapped at the door
    for a, b in spans(px1 - px0, [(PDOOR[0] - CASE_W, PDOOR[1] + CASE_W)]):
        bx(m, TRIM, a, b, 0.0, BB_H, pz1, pz1 + BB_T)
    # the pier face already looks south (+z), which is the direction
    # panel_door authors in, so it needs no wall mapping at all
    panel_door(m, WHITEWD, PDOOR[0] + 0.03, PDOOR[1] - 0.03, 0.0, 6.83,
               pz1 - 0.02, pz1 + 0.10)
    for a, b in ((PDOOR[0] - CASE_W, PDOOR[0] + 0.03),
                 (PDOOR[1] - 0.03, PDOOR[1] + CASE_W)):
        bx(m, TRIM, a, b, 0.0, 6.83 + CASE_W, pz1, pz1 + 0.20)
    bx(m, TRIM, PDOOR[0] - CASE_W, PDOOR[1] + CASE_W, 6.83, 6.83 + CASE_W,
       pz1, pz1 + 0.20)
    m.add(cylinder(0.075, 0.05, 10), BLACKMET,
          at=(PDOOR[1] - 0.36, 3.05, pz1 + 0.22), rot_x=R(90))

    # the small wall-mounted cabinet beside that door
    bx(m, CABBLK, 0.55, 2.15, 2.55, 5.45, pz1, pz1 + 0.60)
    bx(m, SCRN, 0.72, 1.98, 3.55, 4.75, pz1 + 0.60, pz1 + 0.625)
    mq = Material("armqw", HUES[7], roughness=0.5, emissive=HUES[7],
                  emissive_strength=1.4)
    bx(m, mq, 0.70, 2.00, 4.90, 5.35, pz1 + 0.60, pz1 + 0.625)
    bx(m, mq, 0.70, 2.00, 1.20, 2.45, pz1 + 0.58, pz1 + 0.60)
    return save_and_place("Arcade Baseboards", m, ROOM)


# ================================================================= cabinets
def upright(m, cx, cz, rot, hue, kind="mini", seed=1):
    """One arcade cabinet, authored facing +z, then spun into place.

    `kind` 'mini' is an Arcade1Up-style 1.95 ft x 5.85 ft riser cabinet (the
    west run); 'full' is a 2.15 ft x 6.30 ft commercial upright (the east run).
    Twelve distinct cabinets would blow the payload, so there is one of each and
    the marquee / side-art hue is what varies -- exactly what the photo's runs
    read as from 50 degrees up."""
    sub = Model()
    rnd = Rnd(seed)
    if kind == "mini":
        bw, bd, base_h, body_h, cp_y = 1.95, 1.90, 1.02, 3.12, 3.24
        scr_lo, scr_hi, mq_lo, mq_hi, top = 3.42, 4.86, 4.96, 5.56, 5.85
    else:
        bw, bd, base_h, body_h, cp_y = 2.15, 2.55, 0.0, 3.34, 3.46
        scr_lo, scr_hi, mq_lo, mq_hi, top = 3.62, 5.30, 5.42, 6.02, 6.30

    dark = mix(hue, "#14161a", 0.52)          # printed art, not a colour block
    art = Material("arart" + dark[1:], dark, roughness=0.75)
    mqc = mix(hue, "#20222a", 0.28)
    mq = Material("armq" + mqc[1:], mqc, roughness=0.45, emissive=mqc,
                  emissive_strength=1.0)

    if base_h:
        bx(sub, CABDK, -bw / 2, bw / 2, 0.0, base_h, -bd / 2, bd / 2 - 0.30)
        bx(sub, art, -bw / 2 - 0.008, -bw / 2, 0.10, base_h - 0.08,
           -bd / 2 + 0.10, bd / 2 - 0.40)
        bx(sub, art, bw / 2, bw / 2 + 0.008, 0.10, base_h - 0.08,
           -bd / 2 + 0.10, bd / 2 - 0.40)
    # carcase
    bx(sub, CABBLK, -bw / 2, bw / 2, base_h, body_h, -bd / 2, bd / 2 - 0.30)
    bx(sub, CABBLK, -bw / 2, bw / 2, body_h, top, -bd / 2, bd / 2 - 0.62)
    # side art on both flanks
    for sx in (-bw / 2 - 0.008, bw / 2):
        bx(sub, art, sx, sx + 0.008, base_h + 0.12, body_h - 0.10,
           -bd / 2 + 0.10, bd / 2 - 0.42)
    # front lower bezel, in the artwork hue
    bx(sub, art, -bw / 2 + 0.06, bw / 2 - 0.06, base_h + 0.10, body_h - 0.08,
       bd / 2 - 0.32, bd / 2 - 0.30)
    # control panel, tilted, with joysticks and buttons
    bx(sub, CPANEL, -bw / 2 + 0.04, bw / 2 - 0.04, cp_y - 0.12, cp_y,
       bd / 2 - 0.72, bd / 2 - 0.24)
    for k in range(2):
        jx = -bw / 4 + k * bw / 2
        sub.add(cylinder(0.045, 0.19, 6), CHR, at=(jx - 0.18, cp_y, bd / 2 - 0.60))
        sub.add(cylinder(0.075, 0.07, 8), BUTTONS[k], at=(jx - 0.18, cp_y + 0.19,
                                                          bd / 2 - 0.60))
        for b in range(3):
            sub.add(cylinder(0.058, 0.035, 6), BUTTONS[(k + b) % 4],
                    at=(jx + 0.02 + b * 0.15, cp_y, bd / 2 - 0.44 + 0.06 * (b % 2)))
    # screen, raked back
    bx(sub, CABDK, -bw / 2 + 0.05, bw / 2 - 0.05, scr_lo - 0.08, scr_hi + 0.10,
       bd / 2 - 0.66, bd / 2 - 0.58)
    bx(sub, SCRN, -bw / 2 + 0.16, bw / 2 - 0.16, scr_lo, scr_hi,
       bd / 2 - 0.58, bd / 2 - 0.565)
    # marquee -- real light in the photo, so it is legitimately emissive
    bx(sub, CABDK, -bw / 2 + 0.03, bw / 2 - 0.03, mq_lo - 0.06, mq_hi + 0.06,
       bd / 2 - 0.64, bd / 2 - 0.58)
    bx(sub, mq, -bw / 2 + 0.07, bw / 2 - 0.07, mq_lo, mq_hi,
       bd / 2 - 0.58, bd / 2 - 0.56)
    # a pale cap and a pale plinth: seen end-on from the dollhouse quadrant a
    # run of all-black cabinets merges into one wall, and these break it up
    CAP = Material("arcap", "#7c8086", roughness=0.55)
    bx(sub, CAP, -bw / 2 - 0.012, bw / 2 + 0.012, top - 0.10, top,
       -bd / 2 - 0.012, bd / 2 - 0.60)
    bx(sub, CAP, -bw / 2 - 0.012, bw / 2 + 0.012, 0.0, 0.09,
       -bd / 2 - 0.012, bd / 2 - 0.30)

    ca, sa = math.cos(R(rot)), math.sin(R(rot))
    for part, mm in sub._parts:
        v = [(cx + x * ca + z * sa, y, cz - x * sa + z * ca)
             for (x, y, z) in part.verts]
        m._parts.append((Part(v, part.tris, part.smooth), mm))


def build_west():
    """Six uprights, the collectible shelf above them, the pinball at the north
    end, and the posters leaning in the south corner."""
    m = Model()
    z0, pitch = 8.35, 2.07
    contact_shadow(m, 1.35, z0 + 3 * pitch - 0.2, 1.55, 3 * pitch + 0.4,
                   y=0.010, strength=0.30, steps=9, room=(W, D))
    for i in range(6):
        upright(m, 1.05, z0 + 1.03 + i * pitch, 90, HUES[i], "mini", seed=i + 1)

    return save_and_place("Arcade Cabinets West", m, ROOM)


def build_west_shelf():
    """The collectible shelf, the pinball and the leaning posters -- split out of
    the cabinet run to keep every piece under the 300 KB per-piece budget."""
    m = Model()
    # ---- collectible shelf: a white ledge with an under-lit strip and a long
    # row of small figures, which is what reads from the dollhouse pose
    sz0, sz1 = 7.40, 21.60
    bx(m, SHELFW, 0.0, 0.80, SHELF_Y, SHELF_Y + 0.075, sz0, sz1)
    bx(m, SHELFW, 0.0, 0.14, SHELF_Y - 0.42, SHELF_Y, sz0, sz1)
    LEDS = [Material("arls%d" % i, c, roughness=0.3, emissive=c,
                     emissive_strength=2.4)
            for i, c in enumerate(("#ff5fa8", "#ffd24a", "#5fe08a", "#4fc9ff",
                                   "#b07dff"))]
    n = 34
    for i in range(n):
        z = sz0 + (i + 0.5) * (sz1 - sz0) / n
        bx(m, LEDS[i % 5], 0.10, 0.16, SHELF_Y - 0.10, SHELF_Y - 0.02,
           z - (sz1 - sz0) / n / 2, z + (sz1 - sz0) / n / 2)
        # the figure: a body box and a bigger head, in a toy palette
        hue = HUES[(i * 3) % len(HUES)]
        fm = Material("arfig" + hue[1:], hue, roughness=0.6)
        bx(m, fm, 0.22, 0.50, SHELF_Y + 0.075, SHELF_Y + 0.30, z - 0.13, z + 0.13)
        bx(m, WHTM if i % 3 else fm, 0.20, 0.52, SHELF_Y + 0.30,
           SHELF_Y + 0.52, z - 0.15, z + 0.15)

    # ---- pinball machine at the north end of the run
    px, pz = 1.55, 6.05
    contact_shadow(m, px, pz, 1.35, 2.30, y=0.010, strength=0.26, steps=8)
    bx(m, CABDK, px - 1.15, px + 1.15, 0.0, 2.55, pz - 2.15, pz + 2.15)
    bx(m, Material("arpf", "#123028", roughness=0.35, emissive="#0f3a2c",
                   emissive_strength=1.0),
       px - 1.05, px + 1.05, 2.55, 2.62, pz - 2.05, pz + 1.55)
    bx(m, CABBLK, px - 1.15, px + 1.15, 2.55, 5.55, pz - 2.35, pz - 2.05)
    bx(m, Material("armqpin", HUES[3], roughness=0.45, emissive=HUES[3],
                   emissive_strength=1.5),
       px - 1.02, px + 1.02, 3.60, 5.35, pz - 2.05, pz - 2.03)
    for dz in (-1.9, 1.3):
        for dx in (-0.95, 0.95):
            m.add(cylinder(0.055, 2.55, 8), CHR, at=(px + dx, 0.0, pz + dz))

    # ---- framed posters leaning in the south-west corner
    for i, dz in enumerate((21.30, 21.85, 22.35)):
        m.add(box(1.55 + 0.2 * i, 2.30 + 0.25 * i, 0.09), POSTER,
              at=(1.05, 0.0, dz), rot_y=R(90), rot_x=R(7))
    contact_shadow(m, 0.95, 21.9, 0.95, 1.30, y=0.010, strength=0.22, steps=8)
    return save_and_place("Arcade West Shelf", m, ROOM)


def build_east():
    """Five full-size uprights on the east wall under the hex light panels."""
    m = Model()
    z0, pitch = 0.85, 2.52
    contact_shadow(m, W - 1.45, z0 + 2.5 * pitch, 1.70, 2.5 * pitch + 0.6,
                   y=0.010, strength=0.30, steps=9, room=(W, D))
    for i in range(5):
        upright(m, W - 1.35, z0 + 1.26 + i * pitch, 270, HUES[(i + 5) % len(HUES)],
                "full", seed=20 + i)
    # a dark acoustic panel where the run meets the north wall
    bx(m, ACOU, W - 0.10, W - 0.06, 3.40, 6.60, 0.25, 0.85)
    hex_wall(m, "e", W, D, [(1.1, 6.75), (2.4, 7.35), (3.7, 6.70),
                            (5.1, 7.30), (6.5, 6.65), (7.9, 7.28),
                            (9.3, 6.72), (10.7, 7.32), (12.1, 6.68),
                            (13.4, 7.25)])
    return save_and_place("Arcade Cabinets East", m, ROOM)


def hex_wall(m, wall, W, D, spots, r=0.72):
    """Nanoleaf-style hexagons: `spots` are (along-wall, height) pairs."""
    pts = [(r * math.cos(R(60 * k + 30)), r * math.sin(R(60 * k + 30)))
           for k in range(6)]
    sub = Model()
    for i, (a, y) in enumerate(spots):
        lit = (i % 3 == 0)
        mat = (Material("arhexl", "#f4f8ff", roughness=0.4, emissive="#cfe2ff",
                        emissive_strength=1.8) if lit else
               (HEXD if i % 3 == 1 else HEXW))
        p = Model()
        p.add(prism(pts, 0.085), mat)
        for part, mm in p._parts:
            sub._parts.append((Part([(a + x, y + z, py) for (x, py, z) in part.verts],
                                    part.tris, part.smooth), mm))
    blit(m, sub, wall, W, D, 0.0)


def build_north():
    """The north wall: an acoustic panel and a spread of hex panels."""
    m = Model()
    sub = Model()
    bx(sub, ACOU, 6.15, 7.85, 3.30, 6.70, 0.0, 0.09)
    for k in range(9):                    # the diagonal ribs on it
        bx(sub, Material("aracou2", "#4a4e55", roughness=0.85),
           6.25 + k * 0.18, 6.31 + k * 0.18, 3.40 + k * 0.32, 6.60,
           0.09, 0.10)
    blit(m, sub, "n", W, D, 0.0)
    hex_wall(m, "n", W, D, [(9.3, 6.55), (10.6, 7.15), (11.9, 6.50),
                            (13.2, 7.10), (14.5, 6.45), (15.8, 7.05),
                            (17.1, 6.50), (18.4, 7.10), (19.5, 6.45),
                            (12.5, 5.35), (15.1, 5.30), (17.8, 5.35)])
    # a slim floor lamp glowing beside the pier, and a green vase
    lx, lz = 6.05, 0.95
    contact_shadow(m, lx, lz, 0.62, 0.62, y=0.010, strength=0.20, steps=8)
    m.add(cylinder(0.52, 0.06, 14), BLACKMET, at=(lx, 0.0, lz))
    m.add(cylinder(0.055, 4.60, 8), BLACKMET, at=(lx, 0.06, lz))
    m.add(cylinder(0.10, 3.40, 8), Material("arlamp", "#eaffd0", roughness=0.3,
                                            emissive="#d8ff9a",
                                            emissive_strength=3.2),
          at=(lx + 0.10, 1.10, lz))
    m.add(cylinder(0.30, 1.05, 12, r_top=0.16), Material("arvase", "#5c8f7a",
                                                         roughness=0.4),
          at=(7.35, 0.0, 0.85))
    # the Connect-4 style game leaning on the pier face
    G = Material("argame", "#17181c", roughness=0.6)
    contact_shadow(m, 9.55, 1.05, 1.55, 0.95, y=0.010, strength=0.24, steps=8)
    bx(m, WHTM, 8.35, 10.75, 0.0, 2.10, 0.16, 1.55)      # low white cabinet
    bx(m, TRIM, 8.28, 10.82, 2.10, 2.22, 0.10, 1.62)
    bx(m, G, 8.70, 10.40, 2.22, 4.10, 0.62, 0.76)
    for r_ in range(5):
        for c_ in range(5):
            m.add(cylinder(0.115, 0.04, 8), WHTM,
                  at=(8.92 + c_ * 0.32, 2.44 + r_ * 0.32, 0.76), rot_x=R(90))
    return save_and_place("Arcade North Wall", m, ROOM)


# ==================================================================== floor
def build_rug():
    m = Model()
    x0, x1, z0, z1 = 3.40, 19.30, 2.40, 20.70
    A = Material("arrugA", "#9d9b96", roughness=1.0)
    B = Material("arrugB", "#918f8a", roughness=1.0)
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) * 0.53,
                   (z1 - z0) * 0.53, y=0.006, strength=0.08, room=(W, D))
    bx(m, B, x0, x1, 0.014, 0.048, z0, z1)
    bx(m, A, x0 + 0.28, x1 - 0.28, 0.048, 0.060, z0 + 0.28, z1 - 0.28)
    Y = 0.062
    contact_shadow(m, 10.2, 12.3, 3.2, 2.2, y=Y, strength=0.32, room=(W, D))
    contact_shadow(m, 15.1, 9.6, 2.4, 1.3, y=Y, strength=0.24, room=(W, D))
    contact_shadow(m, 18.9, 14.9, 1.5, 1.6, y=Y, strength=0.22, room=(W, D))
    contact_shadow(m, 19.0, 17.9, 1.1, 1.1, y=Y, strength=0.24, room=(W, D))
    return save_and_place("Arcade Floor Rug", m, ROOM)


# =================================================================== lounge
def build_lounge():
    """The black modular chaise in the middle of the rug: four wedge-backed
    seats fanned around a common base, which is what the photo shows."""
    m = Model()
    cx, cz = 10.20, 12.30
    slab(m, BLKF2, cx - 2.85, cx + 2.85, 0.0, 0.88, cz - 1.75, cz + 1.75, r=0.24)
    for i, (dx, dz, w_, d_, rot, h) in enumerate((
            (-1.72, -0.45, 2.15, 2.05, 12, 2.15),
            (-0.05, -0.72, 1.95, 1.90, -6, 1.95),
            (1.50, -0.30, 2.05, 2.00, 8, 2.25),
            (-0.90, 0.90, 1.95, 1.85, 186, 1.80),
            (1.15, 0.98, 2.00, 1.95, 174, 2.00))):
        sub = Model()
        # seat pad
        slab(sub, BLKF, -w_ / 2, w_ / 2, 0.70, 1.46, -d_ / 2, d_ / 2, r=0.30)
        # raked back: six slices climbing toward the rear edge
        for k in range(6):
            t = (k + 0.5) / 6.0
            hh = 1.46 + (h - 1.46) * t ** 1.4
            bx(sub, BLKF2, -w_ / 2 + 0.06, w_ / 2 - 0.06, 1.20, hh,
               -d_ / 2 + 0.02 + k * 0.115, -d_ / 2 + 0.13 + k * 0.115)
        slab(sub, BLKF, -w_ / 2 + 0.02, w_ / 2 - 0.02, h - 0.22, h,
             -d_ / 2 + 0.02, -d_ / 2 + 0.72, r=0.16)
        ca, sa = math.cos(R(rot)), math.sin(R(rot))
        for part, mm in sub._parts:
            m._parts.append((Part([(cx + dx + x * ca + z * sa, y,
                                    cz + dz - x * sa + z * ca)
                                   for (x, y, z) in part.verts],
                                  part.tris, part.smooth), mm))
    return save_and_place("Arcade Lounge", m, ROOM)


# ======================================================= high table + stools
def build_tables():
    m = Model()
    # black-topped adjustable table on white/chrome legs
    tx, tz = 15.10, 9.60
    bx(m, BLKF, tx - 2.25, tx + 2.25, 2.28, 2.42, tz - 0.95, tz + 0.95)
    bx(m, BLKF2, tx - 2.25, tx + 2.25, 1.95, 2.28, tz - 0.92, tz - 0.86)
    for dx in (-1.75, 1.75):
        bx(m, CHR, tx + dx - 0.09, tx + dx + 0.09, 0.0, 2.28, tz - 0.10, tz + 0.10)
        bx(m, CHR, tx + dx - 0.13, tx + dx + 0.13, 0.0, 0.10, tz - 0.75, tz + 0.75)
    # two white-framed stools with dark tops
    for (sx, sz, sh) in ((18.75, 14.35, 1.95), (19.55, 15.95, 1.72)):
        bx(m, Material("arstool", "#2c3138", roughness=0.7),
           sx - 0.85, sx + 0.85, sh, sh + 0.16, sz - 0.75, sz + 0.75)
        for dx in (-0.70, 0.70):
            for dz in (-0.60, 0.60):
                m.add(cylinder(0.045, sh, 6), WHTM, at=(sx + dx, 0.0, sz + dz))
    # grey knit pouf
    m.add(puff(2.10, 1.30, 2.10, r=0.55, seg=16, rings=8), KNIT,
          at=(19.00, 0.0, 17.90))
    return save_and_place("Arcade Tables", m, ROOM)


if __name__ == "__main__":
    print("room 2 Arcade Room")
    drop_object("Arcade Cabinets")
    surfaces(ROOM, wall_color="#dcdbd8", floor_color="#6b6967",
             floor_texture="wood")
    openings()
    out = [build_ceiling(), build_trim(), build_rug(), build_west(),
           build_west_shelf(), build_east(), build_north(),
           build_lounge(), build_tables()]
    print("total %.1f KB" % sum(p["kb"] for p in out))
