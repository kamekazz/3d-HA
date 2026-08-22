"""RECORD of the 2026-08 footprint re-trace from the Apple Home floor-plan scans.

Room footprints are ground truth again - do NOT re-run this to "fix" a room.
It is kept only so the plan->model transform (scales + cross-floor
registration) does not have to be re-derived from the images.


Scales (px per foot), derived from interior partition thickness (4.5 in) and
cross-checked against a 16 ft garage door, a 36 in front door, a 30 in range,
a pair of 36 in king pillows and 42 in stair widths:
    Main   Floor Plan App.png : 22.400 px/ft
    Second Floor Plan App.png : 27.592 px/ft
    Basement Floor Plan App.png: 35.974 px/ft
The three plans cross-register on shared exterior walls, so every floor is
mapped through the SAME model transform anchored on the main floor.
"""
import json
import urllib.request

API = "http://127.0.0.1:5000"

S1 = 22.400        # main floor px/ft
S2 = 27.592        # second floor px/ft
SB = 35.974        # basement px/ft

# --- main floor plan px -> model ft -----------------------------------------
def MX1(px): return 41.700 - px / S1
def MZ1(py): return 59.200 - py / S1

# --- second floor plan px -> model ft (registered: x2=461<->x1=517,
#     x2=1027<->x1=976.5, y2=1720.5<->y1=1603.5) --------------------------
def MX2(px): return 18.620 + (461.0 - px) / S2
def MZ2(py): return -12.385 + (1720.5 - py) / S2

# --- basement plan px -> model ft (registered: xb=155<->x1=517,
#     yb=212<->y1=542) -----------------------------------------------------
def MXB(px): return 18.620 + (155.0 - px) / SB
def MZB(py): return 35.004 - (py - 212.0) / SB


def rect(MX, MZ, x0, x1, y0, y1):
    """plan px box -> model {x,z,width,depth}, rounded to 0.1 ft."""
    mx = round(min(MX(x0), MX(x1)), 1)
    mz = round(min(MZ(y0), MZ(y1)), 1)
    return {"x": mx, "z": mz,
            "width": round(abs(x1 - x0) / _s(MX), 1),
            "depth": round(abs(y1 - y0) / _s(MX), 1),
            "points": None}


def _s(MX):
    return {MX1: S1, MX2: S2, MXB: SB}[MX]


def poly(MX, MZ, pts_px):
    """plan px polygon -> model room with points relative to bbox min."""
    m = [(MX(x), MZ(y)) for x, y in pts_px]
    x0 = min(p[0] for p in m)
    z0 = min(p[1] for p in m)
    return {"x": round(x0, 2), "z": round(z0, 2),
            "points": [[round(p[0] - x0, 2), round(p[1] - z0, 2)] for p in m]}


ROOMS = {}

# ============================ FIRST FLOOR (level 1) =========================
ROOMS[7]  = rect(MX1, MZ1,  52,  510,  550, 1036)   # Garage
ROOMS[9]  = rect(MX1, MZ1, 197,  443, 1036, 1163)   # Laundry
ROOMS[10] = rect(MX1, MZ1, 443,  513, 1036, 1163)   # Pantry
ROOMS[22] = rect(MX1, MZ1,  52,  190, 1036, 1167)   # Office printers (nook)
ROOMS[8]  = rect(MX1, MZ1,  52,  289, 1167, 1426)   # Office
ROOMS[23] = rect(MX1, MZ1, 293,  515, 1256, 1422)   # Bathroom
ROOMS[12] = rect(MX1, MZ1, 524,  694,  604, 1223)   # First floor hallway
# Dining - east bay window (canted returns)
ROOMS[4] = poly(MX1, MZ1, [(700, 546), (977, 546), (977, 625), (1028, 651),
                           (1028, 754), (977, 780), (977, 840), (700, 840)])
# Kitchen - east bay window (canted returns)
ROOMS[6] = poly(MX1, MZ1, [(695, 845), (977, 845), (977, 970), (1028, 996),
                           (1028, 1119), (977, 1145), (977, 1220), (695, 1220)])
# Living room - chamfered SE corner
ROOMS[5] = poly(MX1, MZ1, [(518, 1223), (977, 1223), (977, 1492),
                           (868, 1603), (518, 1603)])
# outdoor pads, re-hugged to the new envelope
ROOMS[11] = {"x": -4.0, "z": 35.0,  "width": 31.0, "depth": 8.0,  "points": None}
ROOMS[3]  = {"x": -4.0, "z": -22.5, "width": 32.0, "depth": 10.0, "points": None}

# ============================ SECOND FLOOR (level 2) ========================
ROOMS[15] = rect(MX2, MZ2, 684, 1029, 428.5, 752)   # Rios Room
ROOMS[26] = rect(MX2, MZ2, 461,  684, 491,   732)   # bath (2F)
ROOMS[25] = rect(MX2, MZ2, 790, 1028, 752,   901)   # "Room 7" = closet by Rios
ROOMS[13] = rect(MX2, MZ2, 683, 1028, 901,  1200)   # Guest Room
ROOMS[13]["width"] = 12.4                            # butt to the hallway wall
ROOMS[27] = rect(MX2, MZ2,  87,  461, 804,  1037)   # Master Closet
ROOMS[16] = rect(MX2, MZ2,  53,  461, 1037, 1386.5) # Master Bath
ROOMS[24] = rect(MX2, MZ2, 812, 1027, 1200, 1354.5) # Bathroom closet
# Hallway (2F) - re-traced 2026-08-22 by fix_2f_hallway.py, which also placed
# the five doors.  The original rect(461, 684, 736, 1198) missed the east arm
# (px 684..790) that fronts the Rios closet and the guest room, and had no
# stairwell.  The 20 px step in the north edge at px 683 is real: the 2F
# bathroom's south wall is at py 732, Rios Room's at py 752.
ROOMS[17] = poly(MX2, MZ2, [(461, 1010), (580, 1010), (580, 732), (683.4, 732),
                            (683.4, 752.5), (790, 752.5), (790, 901),
                            (683.4, 901), (683.4, 1198), (461, 1198)])
# Stairwell - the north (unhatched, so floored) half of the strip the partition
# at px 580 walls off; the stair cut is py 904..1010 and carries no room.
ROOMS[28] = rect(MX2, MZ2, 461,  580, 732,   904)   # Stairwell
# Master Bedroom - L, includes the entry vestibule off the hallway.  Hand-edited
# down from 8 verts to 7 after the re-trace: the vestibule now runs the full
# px 461..810 instead of px 461..597.
ROOMS[14] = poly(MX2, MZ2, [(461, 1354.5), (461, 1205), (810, 1205),
                            (810, 1354.5), (1027, 1354.5),
                            (1027, 1720.5), (461, 1720.5)])

# ============================ BASEMENT (level 0) ============================
ROOMS[1] = rect(MXB, MZB, 283, 893,  217, 1061)     # Movie Room
ROOMS[2] = rect(MXB, MZB, 155, 900, 1061, 1900)     # Arcade Room

STAIRS = {
    # basement -> first floor (footprint read off the basement plan)
    3: {"x": round(MXB(283), 1), "z": round(MZB(925), 1),
        "width": round(120 / SB, 1), "depth": round(445 / SB, 1)},
    # first floor -> second floor
    7: {"x": round(MX1(608), 1), "z": round(MZ1(1006), 1),
        "width": round(84 / S1, 1), "depth": round(229 / S1, 1)},
}


def patch(path, body):
    req = urllib.request.Request(API + path, method="PATCH",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.status, r.read().decode()


FLOOR_OF = {1: 0, 2: 0,
            3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1,
            22: 1, 23: 1,
            13: 2, 14: 2, 15: 2, 16: 2, 17: 2, 24: 2, 25: 2, 26: 2, 27: 2,
            28: 2}


def bbox(b):
    if b.get("points"):
        xs = [p[0] for p in b["points"]]
        zs = [p[1] for p in b["points"]]
        return (b["x"] + min(xs), b["x"] + max(xs),
                b["z"] + min(zs), b["z"] + max(zs))
    return (b["x"], b["x"] + b["width"], b["z"], b["z"] + b["depth"])


def polygon_of(b):
    if b.get("points"):
        return [(b["x"] + p[0], b["z"] + p[1]) for p in b["points"]]
    return [(b["x"], b["z"]), (b["x"] + b["width"], b["z"]),
            (b["x"] + b["width"], b["z"] + b["depth"]),
            (b["x"], b["z"] + b["depth"])]


def inside(poly_pts, x, z):
    c = False
    n = len(poly_pts)
    for i in range(n):
        x1, z1 = poly_pts[i]
        x2, z2 = poly_pts[(i + 1) % n]
        if (z1 > z) != (z2 > z):
            if x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
                c = not c
    return c


def raster_check():
    step = 0.25
    for lvl in (0, 1, 2):
        ids = [r for r in ROOMS if FLOOR_OF[r] == lvl]
        polys = {r: polygon_of(ROOMS[r]) for r in ids}
        clash = {}
        area = 0.0
        x0 = min(min(p[0] for p in q) for q in polys.values())
        x1 = max(max(p[0] for p in q) for q in polys.values())
        z0 = min(min(p[1] for p in q) for q in polys.values())
        z1 = max(max(p[1] for p in q) for q in polys.values())
        n = 0
        x = x0 + step / 2
        while x < x1:
            z = z0 + step / 2
            while z < z1:
                hit = [r for r in ids if inside(polys[r], x, z)]
                if hit:
                    n += 1
                if len(hit) > 1:
                    clash[tuple(sorted(hit))] = clash.get(tuple(sorted(hit)), 0) + 1
                z += step
            x += step
        area = n * step * step
        print("L%d covered %.0f sq ft; overlaps: %s"
              % (lvl, area, {k: round(v * step * step, 1) for k, v in clash.items()} or "none"))


def check():
    bad = 0
    for lvl in (0, 1, 2):
        ids = [r for r in ROOMS if FLOOR_OF[r] == lvl]
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                ax0, ax1, az0, az1 = bbox(ROOMS[a])
                bx0, bx1, bz0, bz1 = bbox(ROOMS[b])
                ox = min(ax1, bx1) - max(ax0, bx0)
                oz = min(az1, bz1) - max(az0, bz0)
                if ox > 0.05 and oz > 0.05:
                    print("  OVERLAP L%d rooms %d/%d  %.2f x %.2f ft"
                          % (lvl, a, b, ox, oz))
                    bad += 1
        print("L%d: %d rooms, %.0f sq ft (bbox sum)"
              % (lvl, len(ids),
                 sum((bbox(ROOMS[r])[1] - bbox(ROOMS[r])[0])
                     * (bbox(ROOMS[r])[3] - bbox(ROOMS[r])[2]) for r in ids)))
    print("bbox overlaps:", bad)


if __name__ == "__main__":
    import sys
    check()
    dry = "--apply" not in sys.argv
    for rid in sorted(ROOMS):
        b = ROOMS[rid]
        print("room %-3d %s" % (rid, json.dumps(b)))
        if not dry:
            print("   ->", patch("/api/house/room/%d" % rid, b))
    for sid in sorted(STAIRS):
        b = STAIRS[sid]
        print("stairs %-3d %s" % (sid, json.dumps(b)))
        if not dry:
            print("   ->", patch("/api/house/stairs/%d" % sid, b))
