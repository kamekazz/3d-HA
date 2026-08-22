"""RECORD of the 2026-08-22 second-floor hallway + door re-trace.

The hallway (room 17) was missing its whole east arm - the stretch that fronts
the Rios closet and the guest room - so two of the five doors had no wall to
sit on, and the remaining openings had drifted off their gaps.  This script
re-derives the hallway footprint and all five doors from the plan scan and
PATCHes them in.  It is idempotent: re-running it is a no-op.

Ground truth: docs/floor plan/Second Floor Plan App.png (1080x2424), with the
hallway outlined and its five doors marked by hand in
docs/floor plan/Gemini_Generated_Image_i28ml3i28ml3i28m.jpg.

Method: the plan's wall fill is exactly rgb(227,225,217) on rgb(244,243,240)
background, ~10 px thick.  Threshold on that colour, walk each wall line and
read the runs and the gaps; a gap is a door.  Map px -> model ft through the
transform already recorded in plan_retrace.py (S2 = 27.592 px/ft).  Two
independent cross-checks that the transform still holds: existing openings 128
(2F bath) and 132 (master bed) land within 0.05 ft of the measured gaps.

Two apparent gaps were rejected as UI-card occlusion - the screenshot's
floating white control cards sit at px 682-1001/py 537-658, px 570-691/py
844-965, px 833-954/py 993-1114, px 117-442/py 1129-1250 and px 689-810/py
1457-1578.  The second hides the hallway/guest-room corner and is what produced
the phantom guest-room opening 111, deleted below.

Measured wall lines (plan px -> model ft):
    hallway west wall        px  461   -> x 18.620
    stairwell partition      px  580   -> x 14.307   py 729..1010
    hallway stem east wall   px  683   -> x 10.574
    hallway arm east wall    px  790   -> x  6.697
    2F-bathroom wall         py  732   -> z 23.441
    Rios Room wall           py  751   -> z 22.752
    arm south wall           py  901   -> z 17.316
    hallway south wall       py 1198   -> z  6.552

Measured door gaps:
    2F bathroom    py  732  px 584-661
    Rios Room      py  751  px 704-774
    Rios closet    px  790  py 781-861
    Guest room     py  901  px 704-780
    Master bedroom py 1198  px 495-574
    Master closet  py 1354  px 929-1006   (room 24, opens into the master bed)
"""
import json
import urllib.request
import urllib.error

API = "http://127.0.0.1:5000"

S2 = 27.592                                        # second floor px/ft


def MX2(px):
    return 18.620 + (461.0 - px) / S2              # model +x runs WEST


def MZ2(py):
    return -12.385 + (1720.5 - py) / S2            # model +z runs NORTH


FLOOR_2F_LEVEL = 2
HALLWAY = 17

# --- the corrected hallway footprint ---------------------------------------
# Already CCW (shoelace > 0) and already bbox-min at (0,0), so normalize_points
# passes it through untouched and the edge indices below stay valid.
HALL_FOOTPRINT = {
    "x": 6.70, "z": 6.55, "width": 11.92, "depth": 16.89,
    "points": [[11.92, 6.81], [7.61, 6.81], [7.61, 16.89], [3.86, 16.89],
               [3.86, 16.15], [0.00, 16.15], [0.00, 10.77], [3.86, 10.77],
               [3.86, 0.00], [11.92, 0.00]],
}

# edge 0 (11.92,6.81)->(7.61,6.81)  len  4.31  stairwell mouth - NO WALL
# edge 1 (7.61,6.81)->(7.61,16.89)  len 10.08  stairwell partition, solid
# edge 2 (7.61,16.89)->(3.86,16.89) len  3.75  <-> 2F bathroom (26)
# edge 3 (3.86,16.89)->(3.86,16.15) len  0.74  jog between the two wall lines
# edge 4 (3.86,16.15)->(0,16.15)    len  3.86  <-> Rios Room (15)
# edge 5 (0,16.15)->(0,10.77)       len  5.38  <-> Rios closet (25)
#   edge 4 sits at z 22.70 rather than the measured 22.752 so it lands exactly
#   on Rios Room's own south wall - 0.6 in of trace noise, not worth an overlap
# edge 6 (0,10.77)->(3.86,10.77)    len  3.86  <-> Guest Room (13)
# edge 7 (3.86,10.77)->(3.86,0)     len 10.77  <-> Guest Room (13), solid
# edge 8 (3.86,0)->(11.92,0)        len  8.06  <-> Master Bed vestibule (14)
# edge 9 (11.92,0)->(11.92,6.81)    len  6.81  <-> Master Bath (16), solid

DOOR = {"type": "door", "height": 6.85, "elevation": 0.0}


def void(width):
    """A passage spanning its whole edge floor-to-ceiling.

    house.js:250 reads that as "this edge is not a wall" and skips building it
    outright; elevation 0.005 / height 7.995 against an 8 ft room is the
    existing convention in this DB.
    """
    return {"type": "passage", "edge_index": 0, "offset": 0.0,
            "width": width, "height": 7.995, "elevation": 0.005}


HALL_OPENINGS = [
    void(4.60),                                            # stairwell mouth
    dict(DOOR, edge_index=2, offset=0.150, width=2.790),   # 2F bathroom
    dict(DOOR, edge_index=4, offset=0.747, width=2.537),   # Rios Room
    dict(DOOR, edge_index=5, offset=1.088, width=2.899),   # Rios closet
    dict(DOOR, edge_index=6, offset=0.362, width=2.754),   # Guest room
    dict(DOOR, edge_index=8, offset=3.968, width=2.863),   # Master bedroom
]

# --- the stairwell, promoted from a bare notch to a room --------------------
# As a void the whole strip (x 14.31..18.62, z 13.37..23.44) had no west wall,
# so the house had an open exterior gap above the master closet, where the
# master closet's own east wall stops at z 20.83.
#
# The room is only the NORTH half of the strip, because a room slab covers its
# whole footprint (house.js:431) and a slab over the whole strip floors the
# staircase over.  The plan draws tread hatching at py 915..990 (z 14.52..17.24)
# and nothing north of it, i.e. z 17.20..23.44 is solid 2F floor and the rest is
# the stair cut.  Trimming to that keeps the exterior wall (the exposed run is
# z 20.83..23.44, inside the room) and leaves the stairs visible coming up.
#
# Rect edges are 0 = z-min (south, over the stair cut), 1 = x-max (west,
# exterior), 2 = z-max (north, shared with the 2F bathroom), 3 = x-min (east,
# the hallway partition).
STAIRWELL = {
    "name": "Stairwell", "floor_id": None, "height": 8.0,
    "color": "#8fa8bf", "wall_color": "#cfd1d2",
    "floor_color": "#504f4b", "floor_texture": "wood",
    "footprint": {"x": 14.31, "z": 17.20, "width": 4.31, "depth": 6.24},
}
STAIRWELL_OPENINGS = [void(4.60)]

# --- the far side of each door ---------------------------------------------
# An opening cuts only its own room's wall, so every door needs a matching row
# in the room on the other side (RESUME.md open item 4).
NEIGHBOUR_DOORS = {
    13: [dict(DOOR, edge_index=2, offset=0.687, width=2.754)],   # Guest Room  -> hallway
    14: [dict(DOOR, edge_index=1, offset=1.232, width=2.863),    # Master Bed  -> hallway
         dict(DOOR, edge_index=3, offset=4.311, width=2.791)],   # Master Bed  -> closet 24
    15: [dict(DOOR, edge_index=0, offset=9.276, width=2.537)],   # Rios Room   -> hallway
    24: [dict(DOOR, edge_index=0, offset=0.768, width=2.791)],   # closet      -> master bed
    25: [dict(DOOR, edge_index=1, offset=1.465, width=2.899)],   # Rios closet -> hallway
    26: [dict(DOOR, edge_index=0, offset=0.872, width=2.790)],   # 2F bathroom -> hallway
}

# Openings traced from occluded or stale geometry.  111 cuts the hallway stem's
# east wall, which the plan shows solid - it was read off the region a UI card
# covers.  79 targets edge_index 7 on a 7-vertex polygon, so it has never
# rendered at all.
STALE_OPENINGS = (111, 79)

# Stairs 7 ran 1.06 ft north past the stairwell's north wall into the bathroom.
STAIRS = {7: {"z": 13.5, "depth": 9.8}}

# The circulation round hand-built a "Hall2F Doors" GLB to stand door leaves in
# the four openings room 17 had then (rooms/17.json records their world spans:
# 14.55..17.45 @ z6.6, 11.40..14.20 @ z23.3, and two on x=10.5 at z18.50..21.20
# and z14.55..17.28).  Against the corrected footprint the first two coincide
# with the engine's own door panels, the third stands free in the middle of the
# new east arm - the round's own notes call that doorway "a real gap in the plan
# but the layout has NO room behind it", which is exactly the arm that was
# missing - and the fourth is buried in the solid stem wall.  The engine now
# cuts and fills all five doorways on both sides, so the GLB is stale.  Its
# casings go with it; a roomkit round can re-cut them against the new edges.
STALE_OBJECTS = ("Hall2F Doors",)


# --- http -------------------------------------------------------------------
def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, method=method, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def get(path):
    return _req("GET", path)[1]


def _write(method, path, body=None):
    st, out = _req(method, path, body)
    if st >= 400 and not (method == "DELETE" and st == 404):
        raise SystemExit("%s %s -> %s %s" % (method, path, st, out))
    return out


def patch(path, body):
    return _write("PATCH", path, body)


def post(path, body):
    return _write("POST", path, body)


def delete(path):
    return _write("DELETE", path)


# --- reconcile --------------------------------------------------------------
def floor_of(house, level):
    for f in house["floors"]:
        if f["level"] == level:
            return f
    raise SystemExit("no floor at level %d" % level)


def same(op, want):
    return (op["type"] == want["type"]
            and op["edge_index"] == want["edge_index"]
            and abs(op["offset"] - want["offset"]) < 0.01
            and abs(op["width"] - want["width"]) < 0.01
            and abs(op["height"] - want["height"]) < 0.01
            and abs(op["elevation"] - want["elevation"]) < 0.005)


def sync_openings(room, wanted, exclusive):
    """Make room's openings match wanted.

    exclusive=True replaces every opening on the room (the hallway and the
    stairwell own all of theirs).  exclusive=False only touches the ones that
    sit on a wanted edge, so windows on other walls survive.
    """
    n = 0
    spare = list(room.get("openings") or [])
    for want in wanted:
        hit = next((o for o in spare if same(o, want)), None)
        if hit:
            spare.remove(hit)
            continue
        # an opening already on this edge is the same door, just misplaced
        near = next((o for o in spare if o["edge_index"] == want["edge_index"]), None)
        if near:
            spare.remove(near)
            patch("/api/house/opening/%d" % near["id"], want)
            print("    opening %3d  edge %d  off %.3f  w %.3f  %s  (moved)"
                  % (near["id"], want["edge_index"], want["offset"],
                     want["width"], want["type"]))
        else:
            post("/api/house/room/%d/opening" % room["id"], want)
            print("    opening NEW  edge %d  off %.3f  w %.3f  %s"
                  % (want["edge_index"], want["offset"], want["width"], want["type"]))
        n += 1
    if exclusive:
        for op in spare:
            delete("/api/house/opening/%d" % op["id"])
            print("    opening %3d  deleted (was edge %d)"
                  % (op["id"], op["edge_index"]))
            n += 1
    return n


def footprint_matches(room, want):
    fp = room["footprint"]
    for k in ("x", "z", "width", "depth"):
        if abs(fp[k] - want[k]) > 0.02:
            return False
    have, wp = fp.get("points"), want.get("points")
    if (not have) != (not wp):
        return False
    if not wp:
        return True
    if len(have) != len(wp):
        return False
    return all(abs(a[0] - b[0]) < 0.02 and abs(a[1] - b[1]) < 0.02
               for a, b in zip(have, wp))


def shift_contents(room, dx, dz):
    """Move a room's furniture and device markers by (dx, dz) feet.

    Objects and placements are stored RELATIVE to the room's footprint anchor
    (`objects.js:128` sets `root.position = fp.x + o.position.x`), so moving the
    anchor drags everything in the room with it.  Room 17's anchor moves west by
    3.80 ft when the east arm is added, which would slide fourteen hand-placed
    pieces - including the hand-built stair flight - straight through a wall.
    """
    n = 0
    for o in room.get("objects") or []:
        pos = o["position"]
        patch("/api/house/object/%d" % o["id"],
              {"x": pos["x"] + dx, "z": pos["z"] + dz})
        n += 1
    for d in room.get("devices") or []:
        pos = d["position"]
        patch("/api/house/device/%d" % d["id"],
              {"x": pos["x"] + dx, "z": pos["z"] + dz})
        n += 1
    return n


def main():
    house = get("/api/house")
    floor = floor_of(house, FLOOR_2F_LEVEL)
    rooms = {r["id"]: r for r in floor["rooms"]}
    changed = 0

    # 1. hallway footprint, before any opening is written against it
    if footprint_matches(rooms[HALLWAY], HALL_FOOTPRINT):
        print("hallway footprint already correct")
    else:
        was = rooms[HALLWAY]["footprint"]
        dx = was["x"] - HALL_FOOTPRINT["x"]
        dz = was["z"] - HALL_FOOTPRINT["z"]
        patch("/api/house/room/%d" % HALLWAY, {"footprint": HALL_FOOTPRINT})
        print("hallway footprint -> %d verts, %.2f x %.2f ft"
              % (len(HALL_FOOTPRINT["points"]),
                 HALL_FOOTPRINT["width"], HALL_FOOTPRINT["depth"]))
        changed += 1
        if abs(dx) > 0.001 or abs(dz) > 0.001:
            moved = shift_contents(rooms[HALLWAY], dx, dz)
            print("  anchor moved (%+.2f, %+.2f) ft - %d pieces compensated"
                  % (-dx, -dz, moved))
            changed += moved
        house = get("/api/house")
        floor = floor_of(house, FLOOR_2F_LEVEL)
        rooms = {r["id"]: r for r in floor["rooms"]}

    # the edge indices above are only valid if normalize_points kept the ring
    stored = rooms[HALLWAY]["footprint"].get("points")
    want = [[round(a, 4), round(b, 4)] for a, b in HALL_FOOTPRINT["points"]]
    if stored != want:
        raise SystemExit("hallway ring was reordered on write - re-derive the "
                         "edge indices from %r" % (stored,))

    # 2. the stairwell room
    well = next((r for r in rooms.values() if r["name"] == "Stairwell"), None)
    if well is None:
        body = dict(STAIRWELL, floor_id=floor["id"])
        rid = post("/api/house/room", body)["id"]
        print("stairwell -> new room %d" % rid)
        changed += 1
        house = get("/api/house")
        floor = floor_of(house, FLOOR_2F_LEVEL)
        rooms = {r["id"]: r for r in floor["rooms"]}
        well = rooms[rid]
    elif not footprint_matches(well, STAIRWELL["footprint"]):
        patch("/api/house/room/%d" % well["id"],
              {"footprint": STAIRWELL["footprint"]})
        print("stairwell %d footprint corrected" % well["id"])
        changed += 1

    # 3. openings
    print("Hallway %d:" % HALLWAY)
    changed += sync_openings(rooms[HALLWAY], HALL_OPENINGS, exclusive=True)
    print("Stairwell %d:" % well["id"])
    changed += sync_openings(well, STAIRWELL_OPENINGS, exclusive=True)
    for rid, wanted in sorted(NEIGHBOUR_DOORS.items()):
        print("%s %d:" % (rooms[rid]["name"], rid))
        changed += sync_openings(rooms[rid], wanted, exclusive=False)

    # 4. stale rows
    live = {o["id"] for f in house["floors"] for r in f["rooms"]
            for o in (r.get("openings") or [])}
    for oid in STALE_OPENINGS:
        if oid in live:
            delete("/api/house/opening/%d" % oid)
            print("stale opening %d deleted" % oid)
            changed += 1

    # 5. stale hand-built pieces
    for r in floor["rooms"]:
        for o in r.get("objects") or []:
            if o["name"] in STALE_OBJECTS:
                delete("/api/house/object/%d" % o["id"])
                print("stale object %d %r deleted from room %d"
                      % (o["id"], o["name"], r["id"]))
                changed += 1

    # 6. stairs
    for sid, want in STAIRS.items():
        st = next((s for f in house["floors"] for s in (f.get("stairs") or [])
                   if s["id"] == sid), None)
        if st and any(abs(st[k] - v) > 0.02 for k, v in want.items()):
            patch("/api/house/stairs/%d" % sid, want)
            print("stairs %d -> z %.2f depth %.2f"
                  % (sid, want["z"], want["depth"]))
            changed += 1

    print("\n%d change(s)" % changed if changed else "\nalready up to date")


if __name__ == "__main__":
    main()
