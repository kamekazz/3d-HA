"""Seed the demo house layout (hand-traced from the floor-plan screenshots in
demo/) into a running 3d-HA backend.

Idempotent: floors are matched by level rank, rooms by ha_area_id (then name),
every write is an upsert, and a second run reports 0 changes. Device
placements that end up outside their reshaped room are moved inside.

Usage:
    python demo/seed_demo.py [--base http://127.0.0.1:5000] [--no-images]
"""
import argparse
import json
import mimetypes
import os
import sys

import requests

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- geometry

def poly_of(fix):
    """Fixture room -> polygon relative to its anchor (rect if no points)."""
    if fix.get("points"):
        return [list(p) for p in fix["points"]]
    w, d = fix["width"], fix["depth"]
    return [[0, 0], [w, 0], [w, d], [0, d]]


def bbox(pts):
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    return min(xs), min(zs), max(xs) - min(xs), max(zs) - min(zs)


def point_in_polygon(px, pz, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, zi = pts[i]
        xj, zj = pts[j]
        if (zi > pz) != (zj > pz) and px < (xj - xi) * (pz - zi) / (zj - zi) + xi:
            inside = not inside
        j = i
    return inside


def interior_grid(pts, step=1.5, margin=1.0):
    """Points inside the polygon on a grid — used to re-home stray devices."""
    min_x, min_z, w, d = bbox(pts)
    out = []
    z = min_z + margin
    while z <= min_z + d - margin + 1e-9:
        x = min_x + margin
        while x <= min_x + w - margin + 1e-9:
            if point_in_polygon(x, z, pts):
                out.append((round(x, 2), round(z, 2)))
            x += step
        z += step
    return out or [(round(min_x + w / 2, 2), round(min_z + d / 2, 2))]


# ---------------------------------------------------------------- seeding

def approx(a, b, tol=0.05):
    return abs(float(a) - float(b)) <= tol


def footprint_matches(room, payload_fp):
    fp = room["footprint"]
    if not (approx(fp["x"], payload_fp["x"]) and approx(fp["z"], payload_fp["z"])
            and approx(fp["width"], payload_fp["width"])
            and approx(fp["depth"], payload_fp["depth"])):
        return False
    a, b = fp.get("points"), payload_fp.get("points")
    if (a is None) != (b is None):
        return False
    if a is not None:
        if len(a) != len(b):
            return False
        for (ax, az), (bx, bz) in zip(a, b):
            if not (approx(ax, bx) and approx(az, bz)):
                return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="http://127.0.0.1:5000")
    ap.add_argument("--no-images", action="store_true",
                    help="skip uploading the floor-plan PNGs as tracing backgrounds")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    with open(os.path.join(HERE, "demo_layout.json"), encoding="utf-8") as f:
        fixture = json.load(f)

    house = requests.get(f"{base}/api/house", timeout=30).json()
    try:
        structure = requests.get(f"{base}/api/ha/structure", timeout=30).json()
    except Exception:
        structure = None
        print("note: HA structure unavailable — rooms will still be shaped, "
              "but ha_area_name lookups are skipped")

    area_id_by_name = {}
    known_area_ids = set()
    if structure:
        for hf in structure.get("floors", []):
            for a in hf.get("areas", []):
                area_id_by_name[(a.get("name") or "").lower()] = a["area_id"]
                known_area_ids.add(a["area_id"])

    floors = sorted(house["floors"], key=lambda f: f["level"])
    rooms_by_area = {r["ha_area_id"]: r for f in house["floors"]
                     for r in f["rooms"] if r.get("ha_area_id")}
    all_rooms = [r for f in house["floors"] for r in f["rooms"]]

    stats = {"floors_created": 0, "floors_updated": 0, "rooms_created": 0,
             "rooms_updated": 0, "rooms_unchanged": 0, "devices_moved": 0,
             "images_uploaded": 0}

    for rank, ffix in enumerate(fixture["floors"]):
        # ---- floor: match by level rank (0 = lowest existing floor)
        if rank < len(floors):
            floor = floors[rank]
        else:
            level = max((f["level"] for f in floors), default=-1) + 1
            r = requests.post(f"{base}/api/house/floor",
                              json={"name": ffix["name"], "level": level,
                                    "floor_height": ffix["floor_height"]},
                              timeout=30)
            r.raise_for_status()
            floor = {"id": r.json()["id"], "level": level, "rooms": [],
                     "floor_height": ffix["floor_height"]}
            floors.append(floor)
            stats["floors_created"] += 1
        if not approx(floor.get("floor_height", 0), ffix["floor_height"]):
            requests.patch(f"{base}/api/house/floor/{floor['id']}",
                           json={"floor_height": ffix["floor_height"]}, timeout=30)
            stats["floors_updated"] += 1

        # ---- rooms: upsert keyed on ha_area_id, then name
        for rfix in ffix["rooms"]:
            area_id = rfix.get("ha_area_id") or area_id_by_name.get(
                (rfix.get("ha_area_name") or "").lower())
            room = rooms_by_area.get(area_id) if area_id else None
            if room is None:
                room = next((r for r in all_rooms
                             if r["name"].lower() == rfix["name"].lower()), None)

            rel = poly_of(rfix)
            _, _, w, d = bbox(rel)
            is_rect = not rfix.get("points")
            payload_fp = {"x": rfix["x"], "z": rfix["z"], "width": w, "depth": d,
                          "points": None if is_rect else rel}
            payload = {"floor_id": floor["id"], "height": rfix.get("height", 8),
                       "color": rfix["color"], "footprint": payload_fp}

            if room is None:
                payload["name"] = rfix["name"]
                if area_id and area_id in known_area_ids:
                    payload["ha_area_id"] = area_id
                r = requests.post(f"{base}/api/house/room", json=payload, timeout=30)
                r.raise_for_status()
                print(f"created room {rfix['name']}")
                stats["rooms_created"] += 1
                continue

            unchanged = (footprint_matches(room, payload_fp)
                         and approx(room["height"], payload["height"])
                         and room["color"].lower() == payload["color"].lower()
                         and room["floor_id"] == floor["id"])
            if unchanged:
                stats["rooms_unchanged"] += 1
            else:
                r = requests.patch(f"{base}/api/house/room/{room['id']}",
                                   json=payload, timeout=30)
                r.raise_for_status()
                print(f"reshaped room {room['name']}")
                stats["rooms_updated"] += 1

            # ---- devices: pull strays back inside the (new) shape
            free = [p for p in interior_grid(rel)]
            taken = 0
            for dev in room.get("devices", []):
                px, pz = dev["position"]["x"], dev["position"]["z"]
                if point_in_polygon(px, pz, rel):
                    continue
                nx, nz = free[taken % len(free)]
                taken += 1
                requests.patch(f"{base}/api/house/device/{dev['id']}",
                               json={"x": nx, "z": nz}, timeout=30)
                stats["devices_moved"] += 1

        # ---- tracing image
        if not args.no_images and ffix.get("plan_image"):
            path = os.path.join(HERE, ffix["plan_image"])
            if os.path.exists(path):
                floor_full = requests.get(f"{base}/api/house", timeout=30).json()
                current = next((f for f in floor_full["floors"]
                                if f["id"] == floor["id"]), {})
                if not current.get("plan_image"):
                    mime = mimetypes.guess_type(path)[0] or "image/png"
                    with open(path, "rb") as fh:
                        r = requests.post(
                            f"{base}/api/house/floor/{floor['id']}/plan",
                            files={"file": (os.path.basename(path), fh, mime)},
                            timeout=60)
                    r.raise_for_status()
                    stats["images_uploaded"] += 1
                requests.patch(f"{base}/api/house/floor/{floor['id']}",
                               json={"plan_scale": ffix["plan_scale"],
                                     "plan_x": ffix["plan_x"],
                                     "plan_z": ffix["plan_z"]}, timeout=30)

    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    sys.exit(main())
