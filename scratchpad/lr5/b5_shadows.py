"""Round 5 contact shadows.

Round 3's nine-annulus falloff was adjudicated good and is unchanged; what was
wrong was WHERE it sat.  Two things:

  1. The footprints were hand-copied constants from b4_soft.py, and round 5
     moved nearly every seat (both east sofas, the sectional, the ottomans, the
     rug).  A shadow 0.3 ft off its piece reads as a smudge on the floor, which
     is why the round-4 critic recorded "no contact shadow under the east sofas
     or armchair".  This script now reads the LIVE object positions out of the
     app, so it cannot drift from what is actually placed again.
  2. Height.  ROOM-BRIEF's four conditions are about the room SLAB (y 0.05
     beats its polygonOffset).  But this room has a rug 0.075 ft thick lying at
     y 0.004, and eight of the pieces that need a shadow stand ON it -- at the
     shared SH_Y of 0.086 that is 0.007 ft of clearance, well inside the depth
     buffer's precision at room scale, so those shadows flickered out.  Pieces
     standing on the rug are now drawn at y 0.115 (0.036 over the pile) and
     pieces on bare plank at 0.050, which is the brief's number.

The rug's own ambient halo stays at 0.020 -- it is on the plank, outside the
rug, and it is also what seats the whole decal object.
"""
import json
import math
import subprocess
import sys

from kit4 import *
from kit4 import Material, Model, shadow_mats

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"

from kit3 import _falloff


def rings(a0=0.58, tag="s", n=7):
    """The round-3 falloff at SEVEN annuli instead of nine.

    The nine-ring curve was adjudicated good and the shape is unchanged -- this
    only resamples it.  Over the ~25 px the ramp occupies in the reference
    render that is 3.5 px a band instead of 2.8, still under the eye's banding
    threshold, and it takes the decal from 228 KB to fit the room's budget.
    The round-4 report proposed exactly this trade."""
    return [Material("lrsh%s%d" % (tag, k), "#050506", roughness=1.0,
                     opacity=round(a, 4), double_sided=True)
            for k, a in enumerate(_falloff(a0=a0, n=n))]


SOLID = rings()
FAINT = rings(a0=0.22, tag="f")

Y_RUG = 0.115          # on the rug (pile top is 0.079)
Y_PLANK = 0.050        # ROOM-BRIEF: 0.05 beats the slab's polygonOffset

# rug rect in room-local feet, from b5_soft (RX, RZ, RL, RDp)
RUG = (11.90 - 14.40 / 2, 9.70 - 12.00 / 2, 11.90 + 14.40 / 2, 9.70 + 12.00 / 2)

OBJ = {o["name"]: o for o in json.loads(subprocess.check_output(
    [sys.executable, "-m", "roomkit.rooms", "5"],
    cwd=TOOLS))["facts"]["objects"]}


def at(name):
    o = OBJ[name]
    return float(o["x"]), float(o["z"]), float(o["rot_y_deg"])


def on_rug(x, z):
    return RUG[0] - 0.6 < x < RUG[2] + 0.6 and RUG[1] - 0.6 < z < RUG[3] + 0.6


def piece(name, w, d, pad=1.00, dx=0.0, dz=0.0, rot=None, **kw):
    x, z, r = at(name)
    x, z = x + dx, z + dz
    y = Y_RUG if on_rug(x, z) else Y_PLANK
    kw.setdefault("mats", SOLID)
    smooth_shadow4(m, foot_rect(x, z, w, d, r if rot is None else rot),
                   pad=pad, y_base=y, **kw)
    return x, z


m = Model()

# --- fireplace hearth on the chamfer -------------------------------------
nrm, _ = edge_normal(*EDGES[CH])
mid = ((EDGES[CH][0][0] + EDGES[CH][1][0]) / 2,
       (EDGES[CH][0][1] + EDGES[CH][1][1]) / 2)
hc = (mid[0] + nrm[0] * 0.755, mid[1] + nrm[1] * 0.755)
smooth_shadow4(m, foot_rect(hc[0], hc[1], 7.10, 1.51,
                            math.degrees(math.atan2(nrm[0], nrm[1]))),
               pad=0.80, y_base=Y_PLANK, mats=SOLID)

# --- north wall ----------------------------------------------------------
piece("Living Media Console", 5.90, 1.46, pad=0.75)
piece("Living Etagere", 1.20, 0.85, pad=0.50)

# --- seating -------------------------------------------------------------
# the sectional is the one piece whose bbox centre is NOT its body centre (the
# chaise return hangs off one end), so it keeps the anchor arithmetic
smooth_shadow4(m, foot_rect(4.35, 15.125, 7.60, 3.55), y_base=Y_RUG, mats=SOLID)
smooth_shadow4(m, foot_rect(6.80, 12.050, 2.70, 2.60), y_base=Y_RUG, mats=SOLID)
piece("Living Sofa East", 3.55, 6.20)
piece("Living Sofa East South", 3.95, 6.40)
piece("Living Armchair", 5.00, 4.00)
piece("Living Ottoman", 4.40, 2.50)
piece("Living Chaise Ottoman", 2.60, 4.20)

# --- coffee table: an OPEN X-frame on four slim legs ---------------------
CTX, CTZ, CTR = at("Living Coffee Table")
for (dx, dz) in ((-1.72, -0.88), (1.72, -0.88), (1.72, 0.88), (-1.72, 0.88)):
    r = math.radians(CTR)
    px = CTX + dx * math.cos(r) + dz * math.sin(r)
    pz = CTZ - dx * math.sin(r) + dz * math.cos(r)
    smooth_shadow4(m, foot_disc(px, pz, 0.13, seg=8), pad=0.34, y_base=Y_RUG,
                   mats=SOLID)
# core=False: round 3 drew this halo with a hard-edged solid core over an OPEN
# X-frame and its boundary read as a tonal panel in the rug.
smooth_shadow4(m, foot_rect(CTX, CTZ, 3.40, 1.70, CTR), pad=0.62,
               mats=FAINT, core=False, y_base=Y_RUG)

# --- accents -------------------------------------------------------------
TFX, TFZ, _ = at("Living Tower Fan")
smooth_shadow4(m, foot_disc(TFX, TFZ, 0.55), pad=0.45, y_base=Y_PLANK,
               mats=SOLID)
PLX, PLZ, _ = at("Living Corner Plant")
smooth_shadow4(m, foot_disc(PLX, PLZ, 0.70), pad=0.50, y_base=Y_PLANK,
               mats=SOLID)
piece("Living Pet Crate", 2.40, 1.70, pad=0.50)
BKX, BKZ, _ = at("Living Basket")
smooth_shadow4(m, foot_disc(BKX, BKZ, 0.66), pad=0.45, mats=SOLID,
               y_base=Y_RUG if on_rug(BKX, BKZ) else Y_PLANK)
piece("Living Cushions", 2.90, 2.70, pad=0.40)

# --- the rug itself ------------------------------------------------------
smooth_shadow4(m, foot_rect(11.90, 9.70, 14.40, 12.00), pad=0.55,
               y_base=0.020, mats=FAINT)

put_in_place("Living Floor Shadows", m, save(m, "shadows5"))
