"""Room 8 Office -- real cut openings.

Derived from docs/floor plan/Main Floor Plan App.png (the plan is rotated 180
from world: world +x -> image left, world +z -> image up) plus the room rects
from roomkit.rooms:

  room 8  x 28.8..39.4  z -4.5..7.1     -> local x 0(W)..10.6(E), z 0(N)..11.6(S)
  room 23 Bathroom  x 18.7..28.6 z -4.3..3.1  -> WEST of the office, local z 0..7.6
  room 22 Printers  x 33.2..39.4 z  7.1..12.9 -> SOUTH of the office, local x 4.4..10.6
  room 9  Laundry   x 21.9..32.9 z  7.3..13.0 -> south-west
  nothing at x > 39.4 or z < -4.5            -> NORTH and EAST are EXTERIOR

The plan draws two pale-blue window ticks on the office's left-hand exterior
edge, which is world x = 39.4 = the EAST wall; photos f and C both show two
blind-covered windows on one wall.  Photo A's "tall window" is the north one.

Rect edge order in house.js: 0 = N (x asc), 1 = E (z asc), 2 = S (x desc from
x=W), 3 = W (z desc from z=D).
"""
import json
import urllib.request

BASE = "http://127.0.0.1:5000"
ROOM = 8
W, D = 10.6, 11.6


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read() or b"{}")


def current():
    house = req("GET", "/api/house")
    for f in house["floors"]:
        for r in f["rooms"]:
            if r["id"] == ROOM:
                return r
    raise SystemExit("room 8 not found")


# type, edge, offset, width, elevation, height
WANT = [
    # west wall -- the 15-lite french door (photo B/f); hinge on the north jamb
    ("door",    3, 1.01, 3.00, 0.00, 7.00),
    # east wall -- two windows, offset measured from local z = 0
    ("window",  1, 0.45, 3.00, 1.85, 5.65),
    ("window",  1, 7.95, 3.00, 1.85, 5.65),
    # south wall -- cased opening into the printer nook (offset from x = W)
    ("passage", 2, 1.70, 3.30, 0.00, 7.20),
]


def main():
    room = current()
    have = list(room.get("openings", []))
    print("before:", [(o["type"], o["edge_index"], o["offset"], o["width"]) for o in have])

    # match by (edge, offset) so re-runs update instead of stacking
    for (t, e, off, w, el, h) in WANT:
        body = {"type": t, "edge_index": e, "offset": off, "width": w,
                "elevation": el, "height": h}
        hit = None
        for o in have:
            if o["edge_index"] == e and abs(o["offset"] - off) < 0.9 and o.get("_used") is None:
                hit = o
                break
        if hit:
            hit["_used"] = True
            req("PATCH", f"/api/house/opening/{hit['id']}", body)
            print("  patched", hit["id"], body)
        else:
            r = req("POST", f"/api/house/room/{ROOM}/opening", body)
            print("  added", r, body)

    room = current()
    print("after:", [(o["id"], o["type"], o["edge_index"], o["offset"], o["width"],
                      o["elevation"], o["height"]) for o in room["openings"]])


if __name__ == "__main__":
    main()
