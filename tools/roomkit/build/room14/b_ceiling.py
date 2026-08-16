"""Vaulted ceiling — round 3: the ridge moves OFF CENTRE, east, to local x 9.0.

Round 2 put the ridge at the room's centre (x 7.5) and got a symmetric tent.
Re-measured off the photo:

  * the apex of the gable sits at photo x ~712, and the wall art's centre (which
    is centred on the headboard) is at photo x 748 and the headboard centre 745.
    In the photo the apex is essentially OVER THE BED, 0.6 ft west of the art's
    centre -- not over the middle of the room.
  * the bed centre re-solves to local x 9.75 this round (queen, nightstand
    between it and the east wall), so the ridge lands at x ~9.0-9.4. 9.0 is used:
    it keeps the ceiling above the fan (x 7.5) at 13.42 ft, still a workable
    downrod.
  * peak stays 14.5 ft: the apex sits ~358 px above the eave line in the photo at
    ~53 px/ft on the north wall = 6.75 ft of rise over the 8 ft wall.

  h(x) = 8 + 6.5*x/9.0        west of the ridge   (8.67:12, 35.8 deg)
  h(x) = 8 + 6.5*(15-x)/6.0   east of the ridge   (13.0:12, 47.3 deg)

Two UNEQUAL slopes, which is what the critic asked for and what the photo shows:
the west plane is the big shallow one that fills the upper-left of the frame, the
east plane a short steep return.

TONE IS UNCHANGED from round 2 (the critic passed the tone, only the pitch
failed). The band emissive strengths are read straight back out of the round-2
GLB: strength = radiance_for_byte(target) - 0.045, the 0.045 being all the light
a downward plane actually collects in this scene.

Footprint is the room's real L polygon (0,0),(15,0),(15,23.5),(9,23.5),(9,16),
(0,16) -- rooms.points is no longer NULL -- so nothing is built outside the room.
"""
import math
import sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import Model, Material, Part, cylinder

OUT = sys.argv[1] if len(sys.argv) > 1 else "../glb/ceiling.glb"

RIDGE_X = 9.0
PEAK = 14.5
EAVE = 8.0
W, D = 15.0, 23.5
LEG_X = 9.0          # leg spans x 9..15, z 16..23.5
MAIN_Z = 16.0

RISE = PEAK - EAVE


def h(x):
    return EAVE + RISE * x / RIDGE_X if x <= RIDGE_X else \
        EAVE + RISE * (W - x) / (W - RIDGE_X)


# ---- materials: verbatim from the round-2 build ---------------------------
CEIL_BASE = "#f3f3f4"
EMIS = "#fffefc"
W_STR = [1.11, 0.98, 0.91, 0.82, 0.76, 0.72]     # eave -> ridge, 6 bands
E_STR = [0.48, 0.49, 0.52, 0.54]                 # ridge -> eave, 4 bands

MW = [Material("ceil_w%d" % i, CEIL_BASE, roughness=0.96, emissive=EMIS,
               emissive_strength=s, double_sided=False) for i, s in enumerate(W_STR)]
ME = [Material("ceil_e%d" % i, CEIL_BASE, roughness=0.96, emissive=EMIS,
               emissive_strength=s, double_sided=False) for i, s in enumerate(E_STR)]
GABLE = Material("gable", "#d5d4d3", roughness=0.95, emissive="#d5d4d3",
                 emissive_strength=0.09, double_sided=False)


def tri(a, b, c):
    return Part([a, b, c], [(0, 1, 2)])


def quad4(a, b, c, d):
    return Part([a, b, c, d], [(0, 1, 2), (0, 2, 3)])


m = Model()

# ---- slope panels, wound to face DOWN into the room -----------------------
def slope_band(x0, x1, z0, z1, mat):
    a = (x0, h(x0), z0)
    b = (x1, h(x1), z0)
    c = (x1, h(x1), z1)
    d = (x0, h(x0), z1)
    # (a,b,c) normal = (dh*dz, -dx*dz, 0) -> -y component, i.e. downward
    m.add(quad4(a, b, c, d), mat)


NW = len(W_STR)
for i in range(NW):
    x0 = RIDGE_X * i / NW
    x1 = RIDGE_X * (i + 1) / NW
    slope_band(x0, x1, 0.0, MAIN_Z, MW[i])

NE = len(E_STR)
for i in range(NE):
    x0 = RIDGE_X + (W - RIDGE_X) * i / NE
    x1 = RIDGE_X + (W - RIDGE_X) * (i + 1) / NE
    slope_band(x0, x1, 0.0, D, ME[i])      # east side runs the full depth (the leg)

# ---- gable ends (vertical, carry their value in albedo) -------------------
SK = EAVE - 0.12       # skirt down behind the wall top so there is no seam


def _fan(v, axis, face):
    """Triangle-fan a convex polygon, then flip the whole fan if its normal does
    not point the way we asked.  Winding a gable backwards makes it invisible
    from inside and you see the sky through it -- so it is checked, not assumed."""
    n = len(v)
    tris = [(0, i, i + 1) for i in range(1, n - 1)]
    a, b, c = v[0], v[1], v[2]
    u = [b[i] - a[i] for i in range(3)]
    w = [c[i] - a[i] for i in range(3)]
    nz = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
          u[0] * w[1] - u[1] * w[0])
    if nz[axis] * face < 0:
        tris = [(t[0], t[2], t[1]) for t in tris]
    return Part(v, tris)


def vgable(pts, z, face):
    """pts: [(x,y)] convex polygon in the z-plane. face=+1 -> normal +z."""
    m.add(_fan([(p[0], p[1], z) for p in pts], 2, face), GABLE)


def xgable(pts, x, face):
    """pts: [(z,y)] convex polygon in the x-plane. face=+1 -> normal +x."""
    m.add(_fan([(x, p[1], p[0]) for p in pts], 0, face), GABLE)


# north wall gable, z = 0, faces +z (into the room)
vgable([(0, SK), (0, EAVE), (RIDGE_X, PEAK), (W, EAVE), (W, SK)], 0.0, +1)
# main-area south wall gable, z = 16, x 0..9, faces -z
vgable([(0, SK), (0, EAVE), (LEG_X, h(LEG_X)), (LEG_X, SK)], MAIN_Z, -1)
# leg south wall gable, z = 23.5, x 9..15, faces -z
vgable([(LEG_X, SK), (LEG_X, PEAK), (W, EAVE), (W, SK)], D, -1)
# leg west wall, x = 9, z 16..23.5, faces +x
xgable([(MAIN_Z, SK), (D, SK), (D, PEAK), (MAIN_Z, PEAK)], LEG_X, +1)

# ---- recessed cans, lying in the slope plane ------------------------------
sys.path.insert(0, ".")
from tone import radiance_for_byte, lin_to_srgb, aces


def byte_of(strength):
    r = strength + 0.045
    return round(255 * lin_to_srgb(aces((r, r, r))[0]))


A_W = math.atan2(RISE, RIDGE_X)          # west slope angle
A_E = math.atan2(RISE, W - RIDGE_X)      # east slope angle

CANS = [(3.9, 2.3), (3.3, 9.4), (11.7, 7.0), (12.2, 19.0)]
made = {}
for (cx, cz) in CANS:
    if cx <= RIDGE_X:
        i = min(NW - 1, int(cx / (RIDGE_X / NW)))
        s, rot = W_STR[i], A_W
    else:
        i = min(NE - 1, int((cx - RIDGE_X) / ((W - RIDGE_X) / NE)))
        s, rot = E_STR[i], -A_E
    b = byte_of(s)
    key = b
    if key not in made:
        rim = Material("trim%d" % b, "#d8d6d2", roughness=0.96, emissive=EMIS,
                       emissive_strength=s, double_sided=False)
        ap = Material("can%d" % b, "#fbfbfa", roughness=0.96, emissive=EMIS,
                      emissive_strength=max(0.05, radiance_for_byte(min(255, b + 10)) - 0.045),
                      double_sided=False)
        made[key] = (rim, ap)
    rim, ap = made[key]
    y = h(cx)
    # rim ring then the bright aperture just inside it
    m.add(cylinder(0.27, 0.02, seg=20, anchor="center"), rim,
          at=(cx, y - 0.012, cz), rot_z=rot)
    m.add(cylinder(0.21, 0.02, seg=20, anchor="center"), ap,
          at=(cx, y - 0.030, cz), rot_z=rot)

m.save(OUT)
lo, hi = m.bounds()
print("bounds", tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi))
print("h(0)=%.2f h(7.5)=%.2f h(9)=%.2f h(9.75)=%.2f h(15)=%.2f" %
      (h(0), h(7.5), h(9), h(9.75), h(15)))
print("west %.1f deg (%.2f:12), east %.1f deg (%.2f:12)" %
      (math.degrees(A_W), 12 * RISE / RIDGE_X, math.degrees(A_E), 12 * RISE / (W - RIDGE_X)))
print("band bytes west", [byte_of(s) for s in W_STR], "east", [byte_of(s) for s in E_STR])
