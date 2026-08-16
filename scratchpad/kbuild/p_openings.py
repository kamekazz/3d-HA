"""Real cut openings for room 6 -- the critic's #1 defect.

Photos C and F are DEFINED by looking over a half-wall pass-through at the
living room and its stone fireplace; round 1 built a solid full-height wall and
faked the bay window as a flush decal.  house.js `buildRoom` cuts a genuine hole
(`shape.holes.push`) per opening row, so these are real holes in the wall shape.

Openings are indexed by EDGE of the room polygon (edge i runs POLY[i] ->
POLY[i+1]) with `offset` measured along that edge from POLY[i]:

    0 SOUTH  (14.87,16.74)->(2.28,16.74)   offset runs EAST -> WEST
    2 bay south facet, 3 bay front, 4 bay north facet
    6 NORTH  (2.28,0)->(14.87,0)           offset runs WEST -> EAST
    7 EAST   (14.87,0)->(14.87,16.74)      offset runs NORTH -> SOUTH

Idempotent: every opening on room 6 is deleted and re-created on each run.
"""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000"
ROOM = 6

# type != 'door' renders the app's glass panel (faint cool tint, 22% opacity);
# 'door' renders an opaque painted panel.  The pass-through and the two cased
# doorways want to be SEEN THROUGH, so they are glass-type holes, which read as
# open air; only real windows carry a sash, built as model geometry on top.
OPENINGS = [
    # --- north wall: the living-room side ---------------------------------
    # walk-through beside the bay, floor to header
    dict(type="passage", edge_index=6, offset=0.15, width=3.15,
         elevation=0.0, height=7.60),
    # THE pass-through: the half-wall runs to y 3.30 and it is open above
    dict(type="passage", edge_index=6, offset=3.75, width=7.45,
         elevation=3.30, height=4.30),

    # --- east wall: cased opening to the first-floor hallway/stairs -------
    dict(type="passage", edge_index=7, offset=11.55, width=3.40,
         elevation=0.0, height=7.20),

    # --- south wall: cased opening through to Dining ----------------------
    dict(type="passage", edge_index=0, offset=9.29, width=3.00,
         elevation=0.0, height=7.20),

    # --- the bay: three real windows --------------------------------------
    dict(type="window", edge_index=4, offset=0.53, width=1.50,
         elevation=2.20, height=4.30),
    dict(type="window", edge_index=3, offset=0.45, width=4.59,
         elevation=2.20, height=4.30),
    dict(type="window", edge_index=2, offset=0.53, width=1.50,
         elevation=2.20, height=4.30),
]


def req(method, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(f"{BASE}{path}", data=body, method=method)
    if body:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=30) as resp:
        txt = resp.read().decode()
        return json.loads(txt) if txt.strip() else {}


def main():
    house = req("GET", "/api/house")
    room = next(r for f in house["floors"] for r in f["rooms"] if r["id"] == ROOM)
    for op in room.get("openings", []):
        req("DELETE", f"/api/house/opening/{op['id']}")
    print(f"removed {len(room.get('openings', []))} old openings")
    for op in OPENINGS:
        res = req("POST", f"/api/house/room/{ROOM}/opening", op)
        print(f"  edge {op['edge_index']} off {op['offset']:5.2f} "
              f"w {op['width']:4.2f} y {op['elevation']:4.2f}"
              f"+{op['height']:4.2f} {op['type']:8s} -> id {res.get('id')}")


if __name__ == "__main__":
    main()
