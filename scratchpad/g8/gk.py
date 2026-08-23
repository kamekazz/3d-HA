"""Garage v3 build kit -- room 7 rebuilt against the owner's v3 photo drop.

Everything is authored in ROOM-LOCAL feet.  Room 7 is 20.4 (x, 0 = WEST) by
21.7 (z, 0 = NORTH) by 9.0 high, slab at world y 8.

Orientation (derived in the report; plan = docs/floor plan/Main Floor Plan App.png):
    SOUTH  z=21.7   the 16 ft sectional door, faces the driveway (+Z = frontyard)
    NORTH  z=0      service door into the house at local x 3.53-6.53, KIES banner
    EAST   x=20.4   exterior side wall: TV, pegboard, clock, boards, yellow car
    WEST   x=0      grey metal cabinets (the plan draws the run at z 7.4-15.9)
"""
import math
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\shellpass")

from roomkit.glb import (Model, Material, box, rounded_box, cylinder, prism,   # noqa: F401
                         quad, sag_plane, torus, Part, uv_quad, uv_floor,
                         png_gray, png_rgb)
from roomkit.place import place, find_model, find_object
import kit as SK                                                    # noqa: N812
from kit import bx, rect_down, rect_up, disc_down, ring_down, spans, wall_band  # noqa: F401
from kit import mix, Rnd, surfaces                                   # noqa: F401

ROOM = 7
W, D, H = 20.4, 21.7, 9.0
BASE = "http://127.0.0.1:5000"
OUT = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(OUT, "glb")
R = math.radians

# The service door opening already cut in the north wall (openings.id 4).
DOOR_X0, DOOR_X1 = 3.53, 6.53
# The sectional door.  The plan marks the rough opening at world x 20.79..38.46
# (17.7 ft); photo 5 meters the LEAF at 211.5 x 94 px = aspect 2.25, i.e. a
# standard 16 x 7 ft double door, centred in that rough opening.
BAY_X0, BAY_X1, BAY_TOP = 2.20, 18.20, 7.05

# NORTH-WALL FURRING DEPTH.  house.js builds every wall's mass OUTSIDE its own
# footprint, so the Pantry (garage-local x -0.1..3.0), the Laundry (9.6..14.0)
# and the Office printers room (14.3..20.5) each push their south wall 0.35 ft
# (WALL_THICKNESS) INTO room 7 and hide room 7's own north face behind their
# paint -- verified with a red-skin probe, scratchpad/g8/probe_red.png.  Those
# rooms belong to other agents, so the fix stays inside room 7: the north skin
# is a furred-out false wall at this depth, and EVERY north-wall piece hangs off
# it rather than off z=0.
NF = 0.42


def save_and_place(name, m, pos=None, rot=0.0, room=ROOM, fname=None,
                   on_floor=False):
    """`on_floor` clamps the seat to y=0 for a piece whose authored geometry
    dips below the slab because a rotation ran before its translate -- without
    it the app seats min-Y at that negative value and the piece sinks."""
    os.makedirs(GLB, exist_ok=True)
    path = os.path.join(GLB, (fname or name.replace(" ", "_").lower()) + ".glb")
    m.save(path)
    lo, hi = m.bounds()
    if pos is None:
        pos = ((lo[0] + hi[0]) / 2.0, 0.0 if on_floor else lo[1],
               (lo[2] + hi[2]) / 2.0)
    res = place(name, path, room, pos=pos, rot_y_deg=rot, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    size = tuple(round(hi[i] - lo[i], 2) for i in range(3))
    print("  %-24s %7.1f KB  size=%-22s pos=(%.2f,%.2f,%.2f) %s"
          % (name, kb, size, pos[0], pos[1], pos[2], res["action"]))
    return {"name": name, "kb": round(kb, 1), "size_ft": list(size),
            "pos_room_local_ft": [round(p, 3) for p in pos], "rot_y_deg": rot}


def drop(name, room=ROOM):
    """Remove a piece entirely -- object row and library model."""
    o = find_object(room, name)
    if o:
        urllib.request.urlopen(urllib.request.Request(
            "%s/api/house/object/%d" % (BASE, o["id"]), method="DELETE"))
    mo = find_model(name)
    if mo:
        try:
            urllib.request.urlopen(urllib.request.Request(
                "%s/api/house/model/%d" % (BASE, mo["id"]), method="DELETE"))
        except urllib.error.HTTPError as e:
            print("    (model %s kept: %s)" % (name, e.code))
    print("  dropped %-24s object=%s model=%s" % (name, bool(o), bool(mo)))


# ------------------------------------------------------------------ palette
# Hexes are sampled off docs/photos-jpg/Garage v3 1.jpg unless noted.
WALLW = Material("gwall", "#dad7d0", roughness=0.95)
TRIMW = Material("gtrim", "#f2f1ec", roughness=0.62)       # painted trim / steps
TRIMS = Material("gtrims", "#dcdad4", roughness=0.64)      # its shaded return
DOORW = Material("gdoorw", "#f6f5f2", roughness=0.55)      # door leaf face
DOORP = Material("gdoorp", "#e4e2dc", roughness=0.58)      # sunk door panel
BLK = Material("gblk", "#1e1f22", roughness=0.55)          # TV face, hardware
BLKM = Material("gblkm", "#2a2c30", roughness=0.45, metallic=0.35)
CHAR = Material("gchar", "#3a3d41", roughness=0.80)        # pegboard
RUB = Material("grub", "#303236", roughness=0.72)          # rubber floor base
GREY = Material("ggrey", "#9fa4a8", roughness=0.55, metallic=0.20)   # metal cabinet
GREYD = Material("ggreyd", "#7e8489", roughness=0.55, metallic=0.20)
STEEL = Material("gsteel", "#b3b7ba", roughness=0.35, metallic=0.55)
STEELD = Material("gsteeld", "#868b8f", roughness=0.40, metallic=0.45)
RED = Material("gred", "#b3251c", roughness=0.45, metallic=0.15)     # Milwaukee
REDD = Material("gredd", "#87180f", roughness=0.48)
YEL = Material("gyel", "#e5b419", roughness=0.50)          # ride-on car
YELD = Material("gyeld", "#b88c0d", roughness=0.52)
GREEN = Material("ggreen", "#4e7048", roughness=0.80)      # wreath
GREEND = Material("ggreend", "#395434", roughness=0.82)
WOOD = Material("gwood", "#b08b5c", roughness=0.70)        # eames legs, broom
WOODD = Material("gwoodd", "#8b6a41", roughness=0.72)
PLASW = Material("gplasw", "#eceae5", roughness=0.42)      # eames shell, jugs
CARD = Material("gcard", "#b7a077", roughness=0.92)
BLUE = Material("gblue", "#2f5f96", roughness=0.55)
PURP = Material("gpurp", "#6a4d93", roughness=0.55)
TEAL = Material("gteal", "#3f8f92", roughness=0.60)
ORANGE = Material("gorange", "#cc6a20", roughness=0.60)
SILV = Material("gsilv", "#c3c6c8", roughness=0.30, metallic=0.55)
BANNERW = Material("gbanw", "#eeeeea", roughness=0.75)     # vinyl banner ground
BANNERI = Material("gbani", "#c3c8cf", roughness=0.72)     # the M4 render on it
BANNERK = Material("gbank", "#3a3d42", roughness=0.72)     # the KIES wordmark
BANNERS = Material("gbans", "#d3dae4", roughness=0.74)     # its blue splash


# ------------------------------------------------------------ contact shadow
def contact(m, cx, cz, rx, rz, y=0.075, tone="#17181a", strength=0.34,
            steps=8, out=0.78, exp=1.15):
    """Alpha-blended radial falloff that runs `out` feet PAST the footprint.

    Four things have to be true at once (ROOM-BRIEF): y above the slab's
    polygonOffset fight (0.05+), ALPHA rather than an opaque colour mix, one
    coplanar non-overlapping set of annuli, and a ramp that extends outside the
    piece so the dark end is not buried under it.
    """
    seg, n = 20, 2.6
    # Roughness MATCHES the floor plane's, deliberately.  At 0.98 the decal's
    # grazing-angle Fresnel differs from the floor's and the ring rendered
    # BRIGHTER than the floor it was meant to darken -- the pale-halo failure
    # ROOM-BRIEF warns about, arriving by a different route than the opaque
    # colour mix it describes.
    rough = 0.62
    # cap: the footprint itself, at the darkest step, so a piece you can see
    # under (the ride-on car leaning on the wall) is not standing on bare floor
    cap = Material("cshcap", tone, roughness=rough,
                   opacity=round(strength / 0.005) * 0.005, double_sided=False)
    v = [(cx, y, cz)]
    for k in range(seg):
        th = 2 * math.pi * k / seg
        ct, st = math.cos(th), math.sin(th)
        v.append((min(max(cx + rx * math.copysign(abs(ct) ** (2.0 / n), ct),
                          0.03), W - 0.03), y,
                  min(max(cz + rz * math.copysign(abs(st) ** (2.0 / n), st),
                          0.03), D - 0.03)))
    m.add(Part(v, [(0, 1 + (k + 1) % seg, 1 + k) for k in range(seg)],
               smooth=True), cap)
    for i in range(steps):
        t0 = (i / steps) ** exp
        t1 = ((i + 1) / steps) ** exp
        # quantised so rings of different pieces share ONE material, which is
        # what keeps the whole room's shadows inside the 300 KB piece cap:
        # Model.add groups by material, and every distinct alpha was its own
        # primitive with its own duplicated vertices.
        a = round(strength * (1.0 - (t0 + t1) * 0.5) / 0.005) * 0.005
        if a <= 0.004:
            continue
        mat = Material("csh%03d" % int(round(a * 1000)), tone, roughness=rough,
                       opacity=a, double_sided=False)
        v, tris = [], []
        for k in range(seg):
            th = 2 * math.pi * k / seg
            ct, st = math.cos(th), math.sin(th)
            ux = math.copysign(abs(ct) ** (2.0 / n), ct)
            uz = math.copysign(abs(st) ** (2.0 / n), st)
            for (t, ) in ((t0, ), (t1, )):
                px = cx + ux * (rx + out * t)
                pz = cz + uz * (rz + out * t)
                v.append((min(max(px, 0.03), W - 0.03), y,
                          min(max(pz, 0.03), D - 0.03)))
        for k in range(seg):
            a0, b0 = 2 * k, 2 * k + 1
            a1, b1 = (2 * k + 2) % (2 * seg), (2 * k + 3) % (2 * seg)
            tris += [(a0, b1, b0), (a0, a1, b1)]        # faces UP
        # smooth=True only to SHARE vertices: the ring is flat, so its averaged
        # normal is the same straight-up vector the flat path would give.
        m.add(Part(v, tris, smooth=True), mat)


# ------------------------------------------------------------------ helpers
def panel(m, mat, wall, a0, a1, y0, y1, off=0.03):
    """A flat panel hung on one wall, `off` feet proud of its face.

    On the north wall `off` is measured from the furring face (NF), not z=0.
    """
    if wall == "n":
        off = NF + off
        m.add(quad((a0, y0, off), (a1, y0, off), (a1, y1, off), (a0, y1, off)), mat)
    elif wall == "s":
        z = D - off
        m.add(quad((a1, y0, z), (a0, y0, z), (a0, y1, z), (a1, y1, z)), mat)
    elif wall == "w":
        m.add(quad((off, y0, a1), (off, y0, a0), (off, y1, a0), (off, y1, a1)), mat)
    else:
        x = W - off
        m.add(quad((x, y0, a0), (x, y0, a1), (x, y1, a1), (x, y1, a0)), mat)


def slab(m, mat, wall, a0, a1, y0, y1, t=0.09, off=0.0):
    """A shallow box hung on one wall (art with a frame depth, boards, signs)."""
    if wall == "n":
        bx(m, mat, a0, a1, y0, y1, NF + off, NF + off + t)
    elif wall == "s":
        bx(m, mat, a0, a1, y0, y1, D - off - t, D - off)
    elif wall == "w":
        bx(m, mat, off, off + t, y0, y1, a0, a1)
    else:
        bx(m, mat, W - off - t, W - off, y0, y1, a0, a1)


def tube(m, mat, p0, p1, r=0.035, seg=8):
    """A thin cylinder between two 3-D points -- rails, handles, broom sticks."""
    dx, dy, dz = (p1[i] - p0[i] for i in range(3))
    L = math.hypot(math.hypot(dx, dy), dz)
    if L < 1e-4:
        return
    ry = math.atan2(dx, dz)
    rx = -math.asin(max(-1.0, min(1.0, dy / L))) + math.pi / 2
    m.add(cylinder(r, L, seg), mat,
          at=(p0[0], p0[1], p0[2]), rot_x=rx, rot_y=ry)
