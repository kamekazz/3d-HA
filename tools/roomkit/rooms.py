"""Per-room geometry facts and camera poses, derived from the live house.

The master-bedroom build hard-coded its room's numbers into BRIEF.md and
poses.json. That does not scale to twenty rooms, and poses.json is a shared file
parallel agents would race on. This module computes the same facts for ANY room
straight from `/api/house`, so a builder agent gets its brief by running:

    python -m roomkit.rooms 14            # facts + poses for room 14
    python -m roomkit.rooms --list        # every room, one line each

Every pose it prints is ready to hand to `roomkit.shot --pose-json`.

Coordinate conventions (the same ones place() uses):
  * room-LOCAL feet: origin at the footprint's min corner, +x east, +z south,
    y up from the room's floor slab.
  * world feet: local + (footprint.x, slabY, footprint.z).
  * a floor's slab Y is the sum of `floor_height` for every floor below it.
"""

import argparse
import json
import math
import os
import urllib.request

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")

EYE = 5.6          # camera eye height above the slab, feet — a standing adult
DOLL_ELEV = 50.0   # dollhouse view elevation in degrees (Sims-4-like)


def fetch_house():
    with urllib.request.urlopen(f"{BASE}/api/house", timeout=30) as r:
        return json.loads(r.read().decode())


def slab_heights(house):
    """level -> world Y of that floor's slab."""
    out, y = {}, 0.0
    for f in sorted(house.get("floors", []), key=lambda f: f["level"]):
        out[f["level"]] = y
        y += f.get("floor_height") or 10.0
    return out


def find_room(house, room_id):
    for floor in house.get("floors", []):
        for room in floor.get("rooms", []):
            if room["id"] == room_id:
                return floor, room
    raise SystemExit(f"no room with id {room_id}")


def room_facts(house, room_id):
    floor, room = find_room(house, room_id)
    fp = room["footprint"]
    slab = slab_heights(house)[floor["level"]]
    w, d = fp["width"], fp["depth"]
    h = room["height"]

    pts = fp.get("points")
    poly = [[round(px, 3), round(pz, 3)] for px, pz in pts] if pts else None

    return {
        "room_id": room_id,
        "name": room["name"],
        "floor": {"id": floor["id"], "name": floor["name"], "level": floor["level"],
                  "floor_height": floor.get("floor_height")},
        "slab_world_y": round(slab, 3),
        "wall_height": h,
        "local": {"x": [0, round(w, 3)], "z": [0, round(d, 3)], "y": [0, h]},
        "world": {"x": [round(fp["x"], 3), round(fp["x"] + w, 3)],
                  "z": [round(fp["z"], 3), round(fp["z"] + d, 3)],
                  "y": [round(slab, 3), round(slab + h, 3)]},
        "origin_world": [round(fp["x"], 3), round(slab, 3), round(fp["z"], 3)],
        "polygon_local": poly,
        "is_polygon": poly is not None,
        "walls": {"north_z": 0, "south_z": round(d, 3),
                  "west_x": 0, "east_x": round(w, 3)},
        "surfaces": {k: room.get(k) for k in
                     ("wall_color", "floor_color", "wall_texture", "floor_texture")},
        "ha_area_id": room.get("ha_area_id"),
        "objects": [{"name": o.get("name"),
                     "x": (o.get("position") or o)["x"],
                     "y": (o.get("position") or o)["y"],
                     "z": (o.get("position") or o)["z"],
                     "rot_y_deg": round(math.degrees(o.get("rot_y") or 0), 1),
                     "scale": o.get("scale")}
                    for o in room.get("objects", [])],
        "openings": len(room.get("openings", [])),
        "device_count": len(room.get("placements", [])),
    }


def _l2w(f, lx, ly, lz):
    ox, oy, oz = f["origin_world"]
    return [round(ox + lx, 3), round(oy + ly, 3), round(oz + lz, 3)]


def poses_for(f, size=(1100, 850)):
    """Standard poses for a room. All in WORLD feet, ready for --pose-json."""
    w = f["local"]["x"][1]
    d = f["local"]["z"][1]
    h = f["wall_height"]
    cx, cz = w / 2, d / 2
    inset = 0.9        # keep the eye just inside the wall, never in it
    sz = list(size)

    def pose(pos, target, fov, size_=None):
        return {"pos": pos, "target": target, "fov": fov, "size": size_ or sz}

    # A corner pose per corner, looking at the diagonally opposite corner —
    # this is the "standing in the doorway" shot most interior photos are.
    corners = {}
    for key, (lx, lz, tx, tz) in {
        "corner_se": (w - inset, d - inset, cx * 0.35, cz * 0.15),
        "corner_sw": (inset, d - inset, w - cx * 0.35, cz * 0.15),
        "corner_ne": (w - inset, inset, cx * 0.35, d - cz * 0.15),
        "corner_nw": (inset, inset, w - cx * 0.35, d - cz * 0.15),
    }.items():
        corners[key] = pose(_l2w(f, lx, EYE, lz),
                            _l2w(f, tx, EYE * 0.62, tz), 75, [900, 1200])

    # Wall-facing poses from the room centre — used to check one wall at a time.
    walls = {
        "look_n": pose(_l2w(f, cx, EYE, cz), _l2w(f, cx, EYE * 0.8, 0), 70),
        "look_s": pose(_l2w(f, cx, EYE, cz), _l2w(f, cx, EYE * 0.8, d), 70),
        "look_e": pose(_l2w(f, cx, EYE, cz), _l2w(f, w, EYE * 0.8, cz), 70),
        "look_w": pose(_l2w(f, cx, EYE, cz), _l2w(f, 0, EYE * 0.8, cz), 70),
    }

    # Straight down — reads like the floor plan, good for checking layout.
    span = max(w, d)
    plan = pose(_l2w(f, cx, span * 1.25 + h, cz), _l2w(f, cx, 0, cz), 45, [900, 900])

    # The dollhouse shot: a 50-degree orbit looking down into the room, framed so
    # the whole footprint fits. This is the Sims-4 angle.
    #
    # There are four of them on purpose. frontend/js/cutaway.js fades out the two
    # walls NEAREST the camera — that is what lets you see in. Pick the quadrant
    # whose dropped pair is the two walls you do NOT care about: a single fixed
    # south-east angle drops the south and east walls, and in a room whose content
    # is on those walls you lose it. Shoot the diagonal opposite the content.
    # (Pieces mounted on a dropped wall now fade with it, so they no longer hang
    # in mid-air — but the wall itself is still gone, content and all.)
    el = math.radians(DOLL_ELEV)
    dist = span * 1.45 + h
    dolls = {}
    for key, az_deg in (("doll_se", 35), ("doll_sw", -35),
                        ("doll_ne", 145), ("doll_nw", -145)):
        az = math.radians(az_deg)
        dolls[key] = pose(
            _l2w(f, cx + dist * math.cos(el) * math.sin(az), h + dist * math.sin(el),
                 cz + dist * math.cos(el) * math.cos(az)),
            _l2w(f, cx, h * 0.28, cz), 42, [1200, 900])
    dolls["doll"] = dolls["doll_se"]   # backwards-compatible default

    return {**corners, **walls, "plan": plan, **dolls}


def floor_doll_pose(house, level, size=(1400, 950), az_deg=35.0, el_deg=DOLL_ELEV):
    """The Sims-4 dollhouse shot of a WHOLE floor: a ~50-degree orbit looking
    down into every room on that level, framed to fit the floor's footprint."""
    slab = slab_heights(house)[level]
    floor = next(f for f in house["floors"] if f["level"] == level)
    rooms = [r for r in floor.get("rooms", []) if r["height"] > 2.0]  # skip yards
    if not rooms:
        raise SystemExit(f"level {level} has no rooms")
    xs = [r["footprint"]["x"] for r in rooms] + \
         [r["footprint"]["x"] + r["footprint"]["width"] for r in rooms]
    zs = [r["footprint"]["z"] for r in rooms] + \
         [r["footprint"]["z"] + r["footprint"]["depth"] for r in rooms]
    h = max(r["height"] for r in rooms)
    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    span = max(max(xs) - min(xs), max(zs) - min(zs))
    el, az = math.radians(el_deg), math.radians(az_deg)
    dist = span * 1.15 + h
    return {
        "pos": [round(cx + dist * math.cos(el) * math.sin(az), 3),
                round(slab + h + dist * math.sin(el), 3),
                round(cz + dist * math.cos(el) * math.cos(az), 3)],
        "target": [round(cx, 3), round(slab + h * 0.3, 3), round(cz, 3)],
        "fov": 40, "size": list(size),
    }


def brief(room_id):
    house = fetch_house()
    f = room_facts(house, room_id)
    return {"facts": f, "poses": poses_for(f),
            "level_for_shot": f["floor"]["level"]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("room", nargs="?", type=int)
    p.add_argument("--list", action="store_true")
    p.add_argument("--poses-only", action="store_true")
    p.add_argument("--floor-doll", type=int, metavar="LEVEL",
                   help="print the whole-floor dollhouse pose for a level")
    a = p.parse_args()

    house = fetch_house()
    if a.floor_doll is not None:
        print(json.dumps(floor_doll_pose(house, a.floor_doll)))
        return
    if a.list or a.room is None:
        slabs = slab_heights(house)
        for floor in sorted(house.get("floors", []), key=lambda f: f["level"]):
            for room in sorted(floor.get("rooms", []), key=lambda r: r["id"]):
                fp = room["footprint"]
                print(f"{room['id']:>3}  L{floor['level']}  {room['name']:<24} "
                      f"{fp['width']:>6.1f} x {fp['depth']:>6.1f} ft  h={room['height']:<5.1f} "
                      f"slabY={slabs[floor['level']]:<6.1f} "
                      f"objs={len(room.get('objects', []))} "
                      f"{'poly' if fp.get('points') else 'rect'}")
        return

    out = brief(a.room)
    print(json.dumps(out["poses"] if a.poses_only else out, indent=2))


if __name__ == "__main__":
    main()
