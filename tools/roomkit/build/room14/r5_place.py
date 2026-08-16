"""Round 5 — build and RE-PLACE room 14.  Idempotent; safe to re-run.

    python r5_place.py             # build every r5 piece + re-place everything
    python r5_place.py --no-build  # just re-place

WHAT CHANGED THIS ROUND (see each r5_*.py header for the measurement):
  1. The bed is a KING (7.10 ft over the plan's own icon), with the photo's
     plank headboard, projecting top cap and two foot drawers.
  2. Rug, coverlet, shams, pillows, dresser grain, armchair fabric and the sill
     cushion all carry TONE FIELDS (r5_raster) instead of dead-flat albedo.
  3. The invented white "Tall Chest" is deleted; the photo's pale ARMCHAIR and
     LEANING MATTRESS PANELS take its place.
  4. Density: bags + folded laundry on the dresser, a plant, a second lamp, a
     bin, a tablet + bottle + speaker on the nightstand, a cushion on the sill,
     two floor vents, a hamper of laundry.
  5. The wall-mounted TV from `Master Bed 2.jpg`, with its soundbar.
  6. The dresser is rebuilt: FOUR drawers (two over one over one) and real
     weathered plank grain.
  8. Ceiling: the recessed cans no longer render as white blobs on the floor
     from the dollhouse poses (cylinder() winds both end caps the same way, so
     the up-facing one survived the ceiling's back-face cull).

  Also: the wall art is re-sampled from the photograph, taking one piece from
  1.43 MB to 0.23 MB, and the rug from 1.13 MB to 0.14 MB, which is what brings
  the room back inside the 1.5 MB budget.

NOT CHANGED (confirmed by the round-4 critic): the footprint, the vault, the
seven openings, the dresser's WEST-wall assignment, wall/floor colours.
"""
import json
import math
import os
import struct
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TOOLS = os.path.join(ROOT, "tools")
UPLOADS = os.path.join(ROOT, "backend", "uploads", "models")
GLB = os.path.join(HERE, "glb5")
GLB4 = os.path.join(HERE, "glb4")
PY = sys.executable
API = "http://127.0.0.1:5000"
ROOM = 14

sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)
from roomkit.place import place, find_object, find_model     # noqa: E402

os.makedirs(GLB, exist_ok=True)
BUILD = "--no-build" not in sys.argv


def sh(*args):
    subprocess.run([PY] + list(args), cwd=HERE, check=True)


def api(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body else None)
    if body:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read().decode()
        return json.loads(t) if t.strip() else {}


def glb_bounds(path):
    with open(path, "rb") as fh:
        fh.read(12)
        ln, _ = struct.unpack("<II", fh.read(8))
        g = json.loads(fh.read(ln).decode("utf-8"))
    lo, hi = [1e9] * 3, [-1e9] * 3
    for prim in g["meshes"][0]["primitives"]:
        acc = g["accessors"][prim["attributes"]["POSITION"]]
        for i in range(3):
            lo[i] = min(lo[i], acc["min"][i] / 0.3048)
            hi[i] = max(hi[i], acc["max"][i] / 0.3048)
    return lo, hi


# ---------------------------------------------------------------- build ----
if BUILD:
    sh("r5_ceiling.py", os.path.join(GLB, "ceiling.glb"), "--lit", "0.095",
       "--wall", "225")
    sh("r4_base.py", os.path.join(GLB, "base.glb"), "--lit", "2.77",
       "--wall", "225")
    sh("r4_windows.py", GLB)
    sh("r5_shadows.py", os.path.join(GLB, "shadows.glb"))
    sh("r5_bed.py", os.path.join(GLB, "bed.glb"))
    sh("r5_rug.py", os.path.join(GLB, "rug.glb"))
    sh("r5_dresser.py", os.path.join(GLB, "dresser.glb"))
    sh("r5_art.py", os.path.join(GLB, "wall_art.glb"))
    sh("r5_props.py", GLB)

# ---------------------------------------------------------------- place ----
done = []


def put(name, path, pos, rot=0.0, scale=1.0):
    r = place(name, path, ROOM, pos=pos, rot_y_deg=rot, scale=scale)
    done.append((name, r["action"], tuple(round(v, 3) for v in pos), rot))


def room_scale(name, path, y=None):
    lo, hi = glb_bounds(path)
    put(name, path, ((lo[0] + hi[0]) / 2, lo[1] if y is None else y,
                     (lo[2] + hi[2]) / 2))


G = lambda n: os.path.join(GLB, n)
M = lambda i: os.path.join(UPLOADS, "model_%d.glb" % i)

room_scale("Ceiling", G("ceiling.glb"))
room_scale("Baseboards", G("base.glb"))
room_scale("Master Floor Shadows", G("shadows.glb"), y=0.050)

# --- the bed, the rug and everything measured off them ----------------------
# bed bbox z -3.805..3.795; the headboard's back face is the bbox min, so
# pos.z = 0.075 (skirting clearance) + 3.80.
put("Bed", G("bed.glb"), (10.40, 0.0, 3.875))
put("Rug", G("rug.glb"), (9.75, 0.045, 7.45))
put("Wall Art", G("wall_art.glb"), (10.40, 5.76, 0.06))
put("Nightstand", M(15), (15.05, 0.0, 1.50), 0)      # bed now ends at 13.95

# --- west wall: the rebuilt dresser, and what stands on it -----------------
put("Dresser", G("dresser.glb"), (0.873, 0.0, 5.91), 90)
put("Master Dresser Clutter", G("dresser_clutter.glb"), (0.95, 3.04, 5.20), 90)
put("Master Plant", G("plant.glb"), (0.85, 3.04, 3.95))
put("Master Lamp Small", G("lamp_small.glb"), (0.88, 3.04, 8.00))

# --- the NW corner: the photo's armchair + leaning panels, NOT a white chest
put("Master Armchair", G("armchair.glb"), (3.30, 0.0, 1.85), 18)
put("Master Lean Panels", G("lean_panels.glb"), (0.62, 0.0, 1.70), 90)

# --- east wall (unchanged round-2 GLBs, re-placed) -------------------------
put("Desk", M(9), (19.30, 0.0, 2.61), 270)
put("Chair", M(10), (17.50, 0.0, 4.20), 100)
put("Foreground Chest", M(13), (19.52, 0.0, 10.06), 270)
put("Ceiling Fan", M(14), (9.60, 8.69, 7.00), 0)

# --- the TV on the south-west wall (Master Bed 2) --------------------------
# Centred at x 5.20, i.e. inside the 2.55..7.86 stretch that the plan draws as
# SOLID wall.  It overlaps the model's second door opening (x 4.93..7.86), which
# the floor plan does not have -- see the report; the plan's only door on this
# wall is at x 0.72..3.59, which the model's other opening matches.
put("Master TV", G("tv.glb"), (5.20, 2.825, 13.151), 180)

# --- density ---------------------------------------------------------------
put("Master Bin", G("bin.glb"), (0.65, 0.0, 9.11))
put("Master Nightstand Props", G("nightstand_props.glb"), (14.80, 2.10, 1.62), 6)
put("Master Sill Cushion", G("sill_cushion.glb"), (20.10, 2.52, 3.90), 270)
put("Master Floor Vent A", G("floor_vent.glb"), (17.30, 0.012, 1.10))
put("Master Floor Vent B", G("floor_vent.glb"), (1.10, 0.012, 11.40), 90)
put("Master Laundry", G("laundry.glb"), (1.10, 0.0, 12.51), 8)

# --- windows ---------------------------------------------------------------
from r4_room import WIN, WIN_SILL, on_edge, edge          # noqa: E402
for name, (e, off, w) in WIN.items():
    path = G(name.lower().replace(" ", "_") + ".glb")
    lo, hi = glb_bounds(path)
    zc = (lo[2] + hi[2]) / 2
    cx, cz = on_edge(e, off + w / 2)
    _a, _b, _u, n, _L = edge(e)
    rot = {(0, 1): 0, (1, 0): 90, (-1, 0): 270, (0, -1): 180}[
        (int(round(n[0])), int(round(n[1])))]
    put(name, path, (cx + n[0] * zc, WIN_SILL[name] - 0.40, cz + n[1] * zc), rot)

# --- retire the invented Tall Chest ----------------------------------------
obj = find_object(ROOM, "Tall Chest")
if obj:
    api("DELETE", "/api/house/object/%d" % obj["id"])
    print("deleted object 'Tall Chest'")
mod = find_model("Tall Chest")
if mod and not mod.get("usage"):
    api("DELETE", "/api/house/model/%d" % mod["id"])
    print("deleted model 'Tall Chest'")

for row in done:
    print("%-26s %-8s pos %-24s rot %s" % row)
