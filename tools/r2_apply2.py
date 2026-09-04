"""Round-2 pass 2: re-level the intensities against the engine as it stands NOW.

Between my first pass and this one the engine changed centrally: FIXTURE_BASE
45 -> 28 and a new whole-room FILL light. Every fixture in the house therefore
lost ~40% of its direct term at once, and my rooms metered 24-31 centre where
they had been 37-49. The GEOMETRY of the fix (how many emitters, where, and how
far the range cutoff reaches) is what makes the light fall off and is unchanged;
only the scalar is re-levelled here.

  python r2_apply2.py
"""
import json
import urllib.request

BASE = "http://127.0.0.1:5000"
GLOW = "shade|lens|glass"

CFG = {
    # room 1 Movie
    361: {"color": "#ffa855", "glow_part": GLOW, "intensity": 2.1, "offset_y": 0.2, "range": 11},
    363: {"color": "#ffa855", "glow_part": GLOW, "intensity": 4.8, "offset_y": 0.2, "range": 12},
    # room 5 Living
    373: {"color": "#ffb877", "glow_part": GLOW, "intensity": 2.5, "offset_y": 0.2, "range": 11},
    376: {"color": "#ffb877", "glow_part": GLOW, "intensity": 3.1, "offset_y": 0.2, "range": 12},
    # room 6 Kitchen island pendants
    377: {"color": "#ffc48f", "glow_part": GLOW, "intensity": 2.4, "offset_y": 0.35, "range": 10},
    378: {"color": "#ffc48f", "glow_part": GLOW, "intensity": 2.4, "offset_y": 0.35, "range": 10},
    # room 7 Garage
    381: {"color": "#ffd9a8", "glow_part": GLOW, "intensity": 3.9, "offset_y": 0.15, "range": 12},
    384: {"color": "#ffd9a8", "glow_part": GLOW, "intensity": 3.9, "offset_y": 0.15, "range": 12},
    # room 8 Office
    385: {"color": "#ffc48f", "glow_part": GLOW, "intensity": 3.4, "offset_y": 0.2, "range": 10},
    # room 2 Arcade -- left at 3.5/range 10, it already meters 48 centre
}

if __name__ == "__main__":
    for oid, cfg in CFG.items():
        req = urllib.request.Request(
            "%s/api/house/object/%d" % (BASE, oid),
            data=json.dumps({"light_cfg": cfg}).encode(), method="PATCH",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            print("PATCH", oid, r.status, r.read().decode().strip())
