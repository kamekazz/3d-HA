"""Upload a .glb to the model library and place it in a room, idempotently.

Re-running with the same `--name` replaces that model's file and updates its
object row instead of stacking duplicates, so a builder can iterate on one piece
without cleaning up after itself.

    python -m roomkit.place --name "Bed" --glb bed.glb --room 14 \
        --pos 8,0,4 --rot 90 --scale 1

Coordinates are ROOM-RELATIVE feet (the same numbers the room editor shows):
x/z from the room footprint's min corner, y up from the floor slab.
--rot is degrees about Y, counter-clockwise seen from above.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")


def _req(method, path, data=None, raw=None, ctype=None):
    url = f"{BASE}{path}"
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    req = urllib.request.Request(url, data=body, method=method)
    if body is not None:
        req.add_header("Content-Type", ctype or "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt.strip() else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:400]}")


def _multipart(fields, filename, content):
    b = "----roomkit7be3f1"
    out = []
    for k, v in fields.items():
        out.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    out.append(
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: model/gltf-binary\r\n\r\n".encode())
    out.append(content)
    out.append(f"\r\n--{b}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={b}"


def find_model(name):
    for m in _req("GET", "/api/house/models"):
        if m["name"] == name:
            return m
    return None


def find_object(room_id, name):
    house = _req("GET", "/api/house")
    for floor in house.get("floors", []):
        for room in floor.get("rooms", []):
            if room["id"] != room_id:
                continue
            for o in room.get("objects", []):
                if o.get("name") == name:
                    return o
    return None


def upload(name, glb_path):
    """Create or replace the library model called `name`. Returns its id."""
    with open(glb_path, "rb") as fh:
        content = fh.read()
    existing = find_model(name)
    if existing:
        # No replace-file endpoint: overwrite the deterministic upload path in
        # place so the id (and every object pointing at it) survives.
        dest = os.path.join(os.path.dirname(__file__), "..", "..", "backend",
                            "uploads", "models", existing["filename"])
        with open(os.path.abspath(dest), "wb") as fh:
            fh.write(content)
        return existing["id"]
    body, ctype = _multipart({"name": name}, os.path.basename(glb_path), content)
    return _req("POST", "/api/house/model", raw=body, ctype=ctype)["id"]


def place(name, glb_path, room_id, pos=(0, 0, 0), rot_y_deg=0.0, scale=1.0):
    import math
    model_id = upload(name, glb_path)
    payload = {
        "model_id": model_id, "name": name,
        "x": float(pos[0]), "y": float(pos[1]), "z": float(pos[2]),
        "rot_y": math.radians(rot_y_deg), "scale": float(scale),
    }
    obj = find_object(room_id, name)
    if obj:
        _req("PATCH", f"/api/house/object/{obj['id']}", payload)
        return {"model_id": model_id, "object_id": obj["id"], "action": "updated"}
    res = _req("POST", f"/api/house/room/{room_id}/object", payload)
    return {"model_id": model_id, "object_id": res["id"], "action": "created"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--glb", required=True)
    p.add_argument("--room", type=int, required=True)
    p.add_argument("--pos", default="0,0,0", help="room-relative x,y,z in feet")
    p.add_argument("--rot", type=float, default=0.0, help="degrees about Y")
    p.add_argument("--scale", type=float, default=1.0)
    a = p.parse_args()
    pos = [float(v) for v in a.pos.split(",")]
    print(json.dumps(place(a.name, a.glb, a.room, pos, a.rot, a.scale)))


if __name__ == "__main__":
    sys.exit(main())
