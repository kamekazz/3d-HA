"""Round 4 — build what needs rebuilding and RE-PLACE every piece by name.

Idempotent: `roomkit.place` replaces a model's file and moves its existing
object, so re-running this never duplicates anything.  Pieces that only MOVED
(Dresser, Tall Chest, Nightstand, Desk, Chair, Foreground Chest, Wall Art,
Ceiling Fan) are re-uploaded from their own file in backend/uploads/models, so
their geometry is byte-identical to what round 2/3 built.

Openings are reset wholesale: the room's existing openings are deleted and the
seven real ones (four windows, two doors, one passage) are cut fresh.

    python r4_place.py            # build + place + cut openings
    python r4_place.py --no-build # just re-place / re-cut
"""
import json
import os
import struct
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TOOLS = os.path.join(ROOT, "tools")
UPLOADS = os.path.join(ROOT, "backend", "uploads", "models")
GLB = os.path.join(HERE, "glb4")
PY = sys.executable
API = "http://127.0.0.1:5000"
ROOM = 14

sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)
from roomkit.place import place                                # noqa: E402
from r4_room import (W_ROOM, WIN, WIN_H, WIN_SILL, DOORS, PASSAGE,
                     BED_CX, BED_POS_Z, on_edge, edge)         # noqa: E402

os.makedirs(GLB, exist_ok=True)
BUILD = "--no-build" not in sys.argv
# lit terms, measured with --probe renders (see r4_meter.py)
LIT_DOWN = os.environ.get("R4_LIT_DOWN", "0.095")
LIT_VERT = os.environ.get("R4_LIT_VERT", "2.77")
WALL = os.environ.get("R4_WALL", "225")


def sh(*args):
    subprocess.run([PY] + list(args), cwd=HERE, check=True)


def glb_bounds(path):
    """overall min/max of every primitive, in FEET."""
    with open(path, "rb") as fh:
        fh.read(12)
        ln, _ = struct.unpack("<II", fh.read(8))
        g = json.loads(fh.read(ln).decode("utf-8"))
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for prim in g["meshes"][0]["primitives"]:
        acc = g["accessors"][prim["attributes"]["POSITION"]]
        for i in range(3):
            lo[i] = min(lo[i], acc["min"][i] / 0.3048)
            hi[i] = max(hi[i], acc["max"][i] / 0.3048)
    return lo, hi


def api(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body else None)
    if body:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read().decode()
        return json.loads(t) if t.strip() else {}


# ---------------------------------------------------------------- build ----
if BUILD:
    sh("r4_ceiling.py", os.path.join(GLB, "ceiling.glb"),
       "--lit", LIT_DOWN, "--wall", WALL)
    sh("r4_base.py", os.path.join(GLB, "base.glb"),
       "--lit", LIT_VERT, "--wall", WALL)
    sh("r4_windows.py", GLB)
    sh("r4_shadows.py", os.path.join(GLB, "shadows.glb"))
    sh("r4_bed.py", os.path.join(GLB, "bed.glb"))
    # NB the SOURCE is glb4/wall_art_src.glb, round 2's pristine canvas -- not
    # uploads/model_12.glb, which place() overwrites with the re-toned result,
    # so re-running would compound the correction.
    sh("r4_art.py", os.path.join(GLB, "wall_art_src.glb"),
       os.path.join(GLB, "wall_art.glb"))
    sh("r4_rug.py", os.path.join(GLB, "rug.glb"))

# ---------------------------------------------------------------- place ----
done = []


def put(name, path, pos, rot=0.0, scale=1.0):
    r = place(name, path, ROOM, pos=pos, rot_y_deg=rot, scale=scale)
    done.append((name, r["action"], tuple(round(v, 3) for v in pos), rot))


def room_scale(name, path, y=None):
    """A piece authored in room-local coordinates seats itself."""
    lo, hi = glb_bounds(path)
    put(name, path, ((lo[0] + hi[0]) / 2, lo[1] if y is None else y,
                     (lo[2] + hi[2]) / 2))


room_scale("Ceiling", os.path.join(GLB, "ceiling.glb"))
room_scale("Baseboards", os.path.join(GLB, "base.glb"))
# y MUST clear the room slab AND its polygonOffset: house.js draws the slab at
# y 0.01 with polygonOffsetFactor -1, which pulls it toward the camera in depth
# by more than a few thousandths of a foot.  A decal at 0.005 is under the floor
# and one at 0.018 still loses the depth fight; 0.05 (0.6 in) wins and is not
# visible as a lift at any pose this room is judged from.
room_scale("Master Floor Shadows", os.path.join(GLB, "shadows.glb"), y=0.050)

put("Bed", os.path.join(GLB, "bed.glb"), (BED_CX, 0.0, BED_POS_Z))
put("Rug", os.path.join(GLB, "rug.glb"), (9.65, 0.004, 6.65))

# --- pieces that only moved: re-upload their own file ----------------------
M = lambda i: os.path.join(UPLOADS, "model_%d.glb" % i)
put("Wall Art", os.path.join(GLB, "wall_art.glb"), (BED_CX, 5.55, 0.06), 0, 0.857)
put("Dresser", M(16), (0.86, 0.0, 5.91), 90)         # WEST wall, z 3.84..7.98
put("Tall Chest", M(20), (0.72, 0.0, 1.45), 90)      # NW corner
put("Nightstand", M(15), (14.20, 0.0, 1.50), 0)      # north wall, east of bed
put("Desk", M(9), (19.30, 0.0, 2.61), 270)           # EAST wall under its window
put("Chair", M(10), (17.50, 0.0, 4.20), 100)
put("Foreground Chest", M(13), (19.52, 0.0, 10.06), 270)
put("Ceiling Fan", M(14), (9.60, 8.69, 7.00), 0)

# --- windows: casing + blind + blown pane, flush on each real opening ------
for name, (e, off, w) in WIN.items():
    path = os.path.join(GLB, name.lower().replace(" ", "_") + ".glb")
    lo, hi = glb_bounds(path)
    zc = (lo[2] + hi[2]) / 2                 # how far the piece's centre stands off
    cx, cz = on_edge(e, off + w / 2)
    y = WIN_SILL[name] - 0.40
    _a, _b, _u, n, _L = edge(e)
    rot = {(0, 1): 0, (1, 0): 90, (-1, 0): 270, (0, -1): 180}[
        (int(round(n[0])), int(round(n[1])))]
    put(name, path, (cx + n[0] * zc, y, cz + n[1] * zc), rot)

# ------------------------------------------------------------- openings ----
house = api("GET", "/api/house")
room = next(r for f in house["floors"] for r in f["rooms"] if r["id"] == ROOM)
for op in room.get("openings", []):
    api("DELETE", "/api/house/opening/%d" % op["id"])

cut = []
for name, (e, off, w) in WIN.items():
    cut.append(("window", e, off, w, WIN_H[name], WIN_SILL[name]))
for e, off, w in DOORS:
    cut.append(("door", e, off, w, 6.80, 0.0))
cut.append(("passage", PASSAGE[0], PASSAGE[1], PASSAGE[2], 7.00, 0.0))
for t, e, off, w, hh, el in cut:
    api("POST", "/api/house/room/%d/opening" % ROOM,
        {"type": t, "edge_index": e, "offset": off, "width": w,
         "height": hh, "elevation": el})

for row in done:
    print("%-22s %-8s pos %-24s rot %s" % row)
print("openings cut:", len(cut))
