"""Master bed — round 5.  A KING, and every soft surface carries a tone field.

WHY IT IS A KING NOW.  Round 3 "proved" a queen off three photo anchors and
rounds 3 and 4 carried that forward, while layout.json contradicted itself: its
own `_wall_derivation` records the Apple-Home plan's bed icon at local
x 6.85..13.95 (7.10 ft) and its `_north_wall_budget` then built a 5.35 ft queen
inside it.  The queen measurement was an artifact of the camera: the primary
photo is taken from the room's EAST side (see r5_notes -- the entry vestibule is
against the east wall, not centred), so the headboard is seen at ~25 degrees off
square and foreshortens by about a quarter.  Re-measured against things at the
SAME depth and obliquity instead of against the frame:

  * the two decorative shams span photo x 575..810 = 235 px; the headboard cap
    spans 607..890 = 283 px for the plan's 7.10 ft, i.e. 39.9 px/ft on that
    wall, so the pair of shams is 5.89 ft -> 2.95 ft each.  That is a 36 in KING
    pillow, not a 30 in queen one.
  * the headboard's height reads 4.3-4.4 ft against the nightstand beside it
    (2.20 ft over 142 px = 64.5 px/ft at that depth), which is a king panel.

So: mattress 6.33 x 6.67 (a real king), frame 6.75, headboard 7.10 spanning the
plan's own x 6.85..13.95, overall length 7.55.

THE HEADBOARD is the photo's: a wide horizontal-plank field between two end
stiles, under a top cap that OVERHANGS both sides and projects forward.

THE SOFT SURFACES are tone fields (r5_raster), not geometry.  Round 4 metered
the duvet at sigma 2.8 against the photo's ~12 while carrying a wrinkle term and
a hand-meshed fall -- in this scene, with one sun and a big isotropic hemisphere
term, tilting a normal buys almost no contrast.  The knit coverlet's diamond
lattice, the shams' diamond quilting and their grey piping are all albedo now.
"""
import math
import sys
import os

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roomkit.glb import Model, Material, Part, box, rounded_box   # noqa: E402
from r5_raster import Field, raster, ramp, fbm                    # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "bed.glb"

# ---- greys: round 4's, re-metered and kept (frame landed 178 on a 225 wall =
# 0.79; the photo's frame runs 0.37 shaded to 0.98 sunlit, mean ~0.72) --------
OAK = Material("bedoak", "#717379", roughness=0.72)          # plank field
OAK_S = Material("bedoak_stile", "#616468", roughness=0.70)  # stiles/rails/posts
OAK_D = Material("bedoak_dark", "#484c50", roughness=0.75)   # reveals
MATT = Material("mattress", "#dcdedf", roughness=0.95)
PULL = Material("pull", "#3c3c3e", roughness=0.5, metallic=0.4)

# knit coverlet: photo 192.9 +/- 12.3 against a 176.2 wall = 1.095 of the wall.
# 1.095 of OUR 225 wall is 246, which leaves no room at all for a +/-12 sigma
# before it clips at 255, so the mean is deliberately parked a little low and
# the spread is spent instead -- a flat 246 field is what round 4 shipped and
# what the critic failed.
KNIT = ramp("#8b8e90", "#f2f4f4", 5, "knit", roughness=0.99)
# shams: photo 193.0 +/- 22.0.  Greyer than the sleeping pillows, which is what
# the photo shows, plus a genuinely darker piping tone so the flange reads as a
# line at distance instead of as shading.
SHAM = ramp("#82888a", "#f6f8f8", 5, "sham", roughness=0.96)
PIPE = Material("sham_pipe", "#8e9294", roughness=0.9)
PILLOW = ramp("#a4a7a9", "#fbfcfc", 4, "pil", roughness=0.97)

# ---- dimensions (feet) ----------------------------------------------------
HB_W = 7.10        # headboard cap, = the plan's bed icon x 6.85..13.95
PANEL_W = 6.78     # plank field + stiles, under the overhanging cap
W = 6.75           # frame width over the side rails
MW, ML = 6.33, 6.67   # king mattress
L = 7.55           # headboard back face to foot face
HB_H = 4.42
RAIL_TOP = 1.55
RAIL_BOT = 0.62
DECK = 1.35
MATT_H = 0.88
MTOP = DECK + MATT_H          # 2.23

z_head = -L / 2               # -3.775
z_foot = L / 2                # +3.775

m = Model()

# ---- headboard ------------------------------------------------------------
ST = 0.34                      # end stiles
m.add(box(ST, HB_H - 0.26, 0.22), OAK_S, at=(-(PANEL_W / 2 - ST / 2), 0, z_head + 0.11))
m.add(box(ST, HB_H - 0.26, 0.22), OAK_S, at=(PANEL_W / 2 - ST / 2, 0, z_head + 0.11))
# the cap: overhangs the panel on BOTH sides and projects forward -- the single
# most recognisable line of this headboard in the photo.
m.add(box(HB_W, 0.17, 0.36), OAK_S, at=(0, HB_H - 0.17, z_head + 0.16))
m.add(box(HB_W - 0.09, 0.05, 0.40), OAK, at=(0, HB_H - 0.22, z_head + 0.17))  # cap reveal
# horizontal plank field between the stiles, proud of them
fw = PANEL_W - 2 * ST
y0, y1 = 1.18, HB_H - 0.26
NP = 6
for i in range(NP):
    hh = (y1 - y0) / NP
    m.add(box(fw, hh - 0.030, 0.12), OAK, at=(0, y0 + i * hh, z_head + 0.17))
    m.add(box(fw, 0.030, 0.07), OAK_D, at=(0, y0 + i * hh + hh - 0.030, z_head + 0.15))
# blank panel behind the mattress
m.add(box(fw, y0, 0.12), OAK_S, at=(0, 0, z_head + 0.16))

# ---- side rails, foot, plinth --------------------------------------------
RT = 0.19
for sx in (-1, 1):
    m.add(box(RT, RAIL_TOP - RAIL_BOT, L - 0.55), OAK_S,
          at=(sx * (W / 2 - RT / 2), RAIL_BOT, 0.12))
    m.add(box(RT + 0.04, 0.07, L - 0.55), OAK,
          at=(sx * (W / 2 - RT / 2), RAIL_TOP - 0.07, 0.12))     # rail cap
# foot rail + cap
m.add(box(W, RAIL_TOP - RAIL_BOT, 0.22), OAK_S, at=(0, RAIL_BOT, z_foot - 0.11))
m.add(box(W + 0.05, 0.07, 0.26), OAK, at=(0, RAIL_TOP - 0.07, z_foot - 0.11))
# TWO storage drawers in the foot plinth -- the photo has two, round 4 had one
DW, DH, DY = (W - 0.50) / 2, 0.80, 0.30
for sx in (-1, 1):
    cx = sx * (DW + 0.09) / 2
    m.add(box(DW, DH, 0.10), OAK, at=(cx, DY, z_foot - 0.30))
    m.add(box(DW, 0.032, 0.06), OAK_D, at=(cx, DY + DH, z_foot - 0.31))
    m.add(box(0.86, 0.055, 0.05), PULL, at=(cx, DY + DH * 0.52, z_foot - 0.24))
m.add(box(W - 0.34, DY, 0.10), OAK_D, at=(0, 0, z_foot - 0.34))       # recessed toe
# corner feet
for sx in (-1, 1):
    for sz, zz in ((-1, z_head + 0.42), (1, z_foot - 0.16)):
        m.add(box(0.30, RAIL_BOT, 0.28), OAK_S, at=(sx * (W / 2 - 0.15), 0, zz))

# ---- mattress -------------------------------------------------------------
m.add(rounded_box(MW, MATT_H, ML, r=0.10, seg=3), MATT, at=(0, DECK, 0.10))

# ---------------------------------------------------------------------------
# KNIT COVERLET -- a tone field, not a wrinkle field
# ---------------------------------------------------------------------------
# The photo's coverlet is a heavy diamond-lattice knit: broad diamonds picked
# out in dotted stitch over a plain ground, plus the ordinary cloth mottle.  It
# covers the mattress from just below the pillows to over the foot rail, breaks
# over the side rails, and throws one big fold at the near foot corner.
CX0, CX1 = -(MW + 0.57) / 2, (MW + 0.57) / 2
CZ0, CZ1 = z_head + 1.95, z_foot - 0.19
CTOP = MTOP + 0.09
FALL = 0.80          # cloth falls to just under the rail cap, as the
                     # photo has it; at 0.56 the mattress showed as a
                     # big white block down both sides of the bed


def cov_y(x, z):
    """coverlet height: flat on top, falling over the two side edges + foot."""
    ex = min(x - CX0, CX1 - x)
    ez = CZ1 - z
    e = min(ex, ez)
    t = 1.0 - min(1.0, max(0.0, e / 0.34))
    y = CTOP - FALL * (t * t * (3 - 2 * t))
    # one big soft fold thrown toward the near foot corner, as in the photo
    fx, fz = (x - (CX0 + 0.9)) / 1.5, (z - (CZ1 - 1.4)) / 1.9
    y += 0.085 * math.exp(-(fx * fx + fz * fz))
    y += 0.020 * math.sin(x * 2.2 + z * 1.4)
    return y


def cov_pt(u, w):
    return (u, cov_y(u, w), w)


def cov_nrm(_u, _w):
    return (0.0, 1.0, 0.0)


NK = len(KNIT)
DIA_U, DIA_W = 0.78, 0.78       # diamond lattice pitch, feet.  At the
                                # photo's 1.28 the lattice covered so little
                                # of the field that the coverlet still
                                # metered sigma 4.8 against the photo's 12.


def knit_fn(u, w):
    a = ((u / DIA_U) + (w / DIA_W)) % 1.0
    b = ((u / DIA_U) - (w / DIA_W)) % 1.0
    # distance to the nearest lattice line, 0 on a line
    d = min(abs(a - 0.5), abs(b - 0.5)) * 2.0
    t = 0.60
    t -= 0.30 * math.exp(-(d / 0.13) ** 2)              # the dark lattice line
    t -= 0.10 * math.exp(-((d - 0.30) / 0.14) ** 2)     # the dotted inner rank
    t -= 0.07 * math.exp(-((d - 0.62) / 0.14) ** 2)     # second rank
    # NOTE the mottle stays LOW frequency on purpose.  A fine stitch grain
    # flips the quantised tone every cell or two, which defeats the run merge
    # and triples the payload for texture nobody can resolve at room distance.
    t += (fbm(u * 2.1, w * 2.1, 91, 3) - 0.5) * 0.48    # cloth mottle
    t += (fbm(u * 4.6, w * 4.6, 271, 2) - 0.5) * 0.16   # coarse stitch grain
    # the fall over the edges reads darker, as cloth in its own shade does
    ex = min(u - CX0, CX1 - u, CZ1 - w)
    if ex < 0.34:
        t -= 0.46 * (1.0 - max(0.0, ex) / 0.34)
    return max(0, min(NK - 1, int(t * NK)))


fld = Field(KNIT)
raster(fld, cov_pt, cov_nrm, CX0, CX1, CZ0, CZ1, 68, 72, knit_fn)
fld.emit(m)

# short skirts carrying the cloth from where the fall ends down to the rail cap,
# so the coverlet does not stop in mid-air over the frame
SK = KNIT[0]


def skirt(x0, x1, z0, z1, y0, y1):
    v = [(x0, y0, z0), (x1, y0, z1), (x1, y1, z1), (x0, y1, z0)]
    m.add(Part(v, [(0, 1, 2), (0, 2, 3)]), SK)


for sx in (-1, 1):
    x = sx * (CX1 - 0.001)
    skirt(x, x, CZ0 + 0.05, CZ1, CTOP - FALL, RAIL_TOP - 0.02)
skirt(CX0, CX1, CZ1, CZ1, CTOP - FALL, RAIL_TOP - 0.02)

# ---------------------------------------------------------------------------
# PILLOWS -- two quilted shams reclined on the headboard, two flat sleepers
# ---------------------------------------------------------------------------
SHAM_W, SHAM_H, SHAM_T = 2.95, 1.74, 0.44
GAP = 0.17
SH_TILT = -0.34                        # reclined against the headboard


def quilt_fn_for(hw, hh):
    n = len(SHAM)

    def fn(u, w):
        eu, ew = hw - abs(u), hh - abs(w)
        e = min(eu, ew)
        if e < 0.0:
            return None
        if e < 0.085:                     # the piped flange: darkest tone
            return 0
        t = 0.64
        p = 0.46                          # quilt pitch
        a = ((u / p) + (w / p)) % 1.0
        b = ((u / p) - (w / p)) % 1.0
        d = min(abs(a - 0.5), abs(b - 0.5)) * 2.0
        t -= 0.34 * math.exp(-(d / 0.19) ** 2)
        t += (fbm(u * 3.0, w * 3.0, 33, 3) - 0.5) * 0.22
        if e < 0.20:
            t -= 0.18 * (1.0 - (e - 0.085) / 0.115)
        return max(1, min(n - 1, int(t * n)))
    return fn


def puff_surface(hw, hh, thick, cx, cy, cz, tilt):
    """A pillow face: bulged rectangle, tilted about X, centred at (cx,cy,cz)."""
    ct, st = math.cos(tilt), math.sin(tilt)

    def pt(u, w):
        bulge = math.cos(math.pi * 0.5 * min(1.0, abs(u) / hw)) * \
            math.cos(math.pi * 0.5 * min(1.0, abs(w) / hh))
        d = thick * bulge
        x, y, z = u, w, d
        y, z = y * ct - z * st, y * st + z * ct
        return (cx + x, cy + y, cz + z)

    def nrm(u, w):
        return (0.0, -st, ct)
    return pt, nrm


sh_f = Field(SHAM)
for sx in (-1, 1):
    cx = sx * (SHAM_W + GAP) / 2
    cy = MTOP + SHAM_H / 2 - 0.10
    cz = z_head + 0.90
    pt, nrm = puff_surface(SHAM_W / 2, SHAM_H / 2, 0.30, cx, cy, cz, SH_TILT)
    raster(sh_f, pt, nrm, -SHAM_W / 2, SHAM_W / 2, -SHAM_H / 2, SHAM_H / 2,
           34, 22, quilt_fn_for(SHAM_W / 2, SHAM_H / 2))
    # the body behind the face, so the sham has depth from every angle
    m.add(rounded_box(SHAM_W, SHAM_H, SHAM_T, r=0.15, seg=4), PIPE,
          at=(cx, cy - SHAM_H / 2, cz - 0.10), rot_x=SH_TILT)
sh_f.emit(m)

PIL_W, PIL_D, PIL_T = 3.02, 1.52, 0.62
pl_f = Field(PILLOW)


def sleep_fn(u, w):
    n = len(PILLOW)
    eu, ew = PIL_W / 2 - abs(u), PIL_D / 2 - abs(w)
    e = min(eu, ew)
    if e < 0.0:
        return None
    t = 0.80 + (fbm(u * 3.2, w * 3.2, 7, 3) - 0.5) * 0.34
    if e < 0.16:
        t -= 0.30 * (1.0 - e / 0.16)
    return max(0, min(n - 1, int(t * n)))


for sx in (-1, 1):
    cx = sx * (PIL_W + GAP) / 2
    pt, nrm = puff_surface(PIL_W / 2, PIL_D / 2, PIL_T * 0.5,
                           cx, MTOP + PIL_T * 0.5 - 0.06, z_head + 1.92, -1.30)
    raster(pl_f, pt, nrm, -PIL_W / 2, PIL_W / 2, -PIL_D / 2, PIL_D / 2,
           22, 12, sleep_fn)
    m.add(rounded_box(PIL_W, PIL_T, PIL_D, r=0.24, seg=4), PILLOW[1],
          at=(cx, MTOP - 0.03, z_head + 1.92), rot_x=-0.12)
pl_f.emit(m)

m.save(OUT)
lo, hi = m.bounds()
print("bounds lo", tuple(round(v, 3) for v in lo), "hi", tuple(round(v, 3) for v in hi))
print("size", tuple(round(hi[i] - lo[i], 3) for i in range(3)))
print("size on disk %.1f KB" % (os.path.getsize(OUT) / 1024))
