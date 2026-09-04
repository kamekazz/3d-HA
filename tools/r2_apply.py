"""Round-2 fixture edits, all through the HTTP API (never house.db).

The defect: four ceiling emitters with range 10-14 in a 20 ft room overlap
everywhere, so nothing falls off. The cure per room is (a) fewer emitters,
(b) shorter range so the cutoff bites inside the room, (c) higher intensity to
hold the peak, and (d) where two survive, put them on the room's CENTRELINE and
separate them along the long axis -- two sources 9 ft apart on a wall 6 ft away
is a wall-washer's spacing and reads as a plateau by construction.

  python r2_apply.py [--dry]
"""
import json
import sys
import urllib.request

BASE = "http://127.0.0.1:5000"

# id -> patch body. `light_cfg` is written whole (the store replaces the column).
GLOW = "shade|lens|glass"

PATCHES = [
    # --- room 1 Movie (20.4 x 23.5) : 4 -> 2, on the centreline (local x 10.2)
    ("PATCH", 361, {"x": 10.2, "z": 8.5, "light_cfg": {
        "color": "#ffa855", "glow_part": GLOW, "intensity": 1.5,
        "offset_y": 0.2, "range": 11}}),
    ("PATCH", 363, {"x": 10.2, "z": 17.0, "light_cfg": {
        "color": "#ffa855", "glow_part": GLOW, "intensity": 3.4,
        "offset_y": 0.2, "range": 12}}),
    ("DELETE", 362, None),
    ("DELETE", 364, None),

    # --- room 2 Arcade : light_cfg ONLY. Its unlit frame is the best in the
    # house and deleting a dome would change that frame, so the four stay and
    # the pools are tightened instead: range 11 -> 10 separates them, intensity
    # 1.5 -> 3.5 holds the peak.
    ("PATCH", 365, {"light_cfg": {"color": "#ffc08a", "glow_part": GLOW,
                                  "intensity": 3.5, "offset_y": 0.2, "range": 10}}),
    ("PATCH", 366, {"light_cfg": {"color": "#ffc08a", "glow_part": GLOW,
                                  "intensity": 3.5, "offset_y": 0.2, "range": 10}}),
    ("PATCH", 367, {"light_cfg": {"color": "#ffc08a", "glow_part": GLOW,
                                  "intensity": 3.5, "offset_y": 0.2, "range": 10}}),
    ("PATCH", 368, {"light_cfg": {"color": "#ffc08a", "glow_part": GLOW,
                                  "intensity": 3.5, "offset_y": 0.2, "range": 10}}),

    # --- room 5 Living (20.5 x 17) : 4 -> 2 on the centreline (local x 10.25)
    ("PATCH", 373, {"x": 10.25, "z": 4.5, "light_cfg": {
        "color": "#ffb877", "glow_part": GLOW, "intensity": 1.8,
        "offset_y": 0.2, "range": 11}}),
    ("PATCH", 376, {"x": 10.25, "z": 12.5, "light_cfg": {
        "color": "#ffb877", "glow_part": GLOW, "intensity": 2.2,
        "offset_y": 0.2, "range": 12}}),
    ("DELETE", 374, None),
    ("DELETE", 375, None),

    # --- room 6 Kitchen (14.9 x 16.7) : the two ceiling domes go, the island
    # pendants stay and carry the room. They hang at 6.7 ft, which is the only
    # low-mounted pair in the house and the reason this room can have a real
    # vertical gradient at all.
    ("PATCH", 377, {"light_cfg": {"color": "#ffc48f", "glow_part": GLOW,
                                  "intensity": 1.8, "offset_y": 0.35, "range": 10}}),
    ("PATCH", 378, {"light_cfg": {"color": "#ffc48f", "glow_part": GLOW,
                                  "intensity": 1.8, "offset_y": 0.35, "range": 10}}),
    ("DELETE", 379, None),
    ("DELETE", 380, None),

    # --- room 7 Garage (20.4 x 21.7) : 4 -> 2 strips down the centreline
    ("PATCH", 381, {"x": 10.2, "z": 6.0, "light_cfg": {
        "color": "#ffd9a8", "glow_part": GLOW, "intensity": 2.6,
        "offset_y": 0.15, "range": 12}}),
    ("PATCH", 384, {"x": 10.2, "z": 16.0, "light_cfg": {
        "color": "#ffd9a8", "glow_part": GLOW, "intensity": 2.6,
        "offset_y": 0.15, "range": 12}}),
    ("DELETE", 382, None),
    ("DELETE", 383, None),

    # --- room 8 Office (10.6 x 11.6) : 2 -> 1, centred
    ("PATCH", 385, {"x": 5.3, "z": 5.8, "light_cfg": {
        "color": "#ffc48f", "glow_part": GLOW, "intensity": 2.0,
        "offset_y": 0.2, "range": 10}}),
    ("DELETE", 386, None),
]


def call(verb, oid, body):
    url = "%s/api/house/object/%d" % (BASE, oid)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=verb,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.status, r.read().decode()[:120]


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    only = [int(a) for a in sys.argv[1:] if a.isdigit()]
    for verb, oid, body in PATCHES:
        if only and oid not in only:
            continue
        if dry:
            print("would", verb, oid, json.dumps(body))
            continue
        try:
            print(verb, oid, call(verb, oid, body))
        except Exception as e:
            print("FAIL", verb, oid, e)
