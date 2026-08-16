"""Dresser + mirror — round 5 rebuild.

Round 4's dresser was a round-2 GLB with SIX drawers and a flat plastic-grey
case.  The photo (see `docs/photos-jpg/Master bedroom.jpg`, and the dresser is
much clearer in the left third of it) has:

  * FOUR drawers in three rows -- two half-width over one full over one full;
  * heavy weathered plank grain, horizontal, with real light/dark streaking --
    this is the loudest surface texture on any case good in the room;
  * dark bar pulls, one per half drawer, two per full drawer;
  * short tapered legs;
  * a near-square mirror in a wide flat wood frame above it.

Size comes from the plan icon (x 0.21..1.66, z 3.32..8.50 -> a 1.45 x 5.18 ft
footprint against the WEST wall) rather than from the photo, where the piece is
seen at about 70 degrees off square and foreshortens to two thirds.

The piece is authored facing +z (south) like everything else; r5_place turns it
90 degrees so its back is against the west wall.

TONE: the photo's drawer fronts run 124..136 against a 176 wall = 0.70..0.77,
and its sunlit end 181 = 1.03.  Round 4's dresser metered 0.78 flat, which the
critic read as plastic.  The grain ramp is authored so the field mean lands near
0.72 of the wall with real spread inside it.
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roomkit.glb import Model, Material, Part, box          # noqa: E402
from r5_raster import Field, raster, ramp, fbm, hash01      # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "dresser.glb"

W, D = 4.90, 1.45          # case, the plan's own footprint less a hair
LEG = 0.32
CASE = 2.62
TOPS = 0.10
TOP = LEG + CASE + TOPS    # 3.04
MIR_W, MIR_H = 3.55, 3.30
MIR_Y = TOP + 0.10

GRAIN = ramp("#4c4f54", "#8f9298", 7, "dgrain", roughness=0.78)
CASEM = Material("dcase", "#5f6266", roughness=0.8)
DARK = Material("dreveal", "#3b3e42", roughness=0.85)
PULL = Material("dpull", "#2f3133", roughness=0.45, metallic=0.5)
FRAME = ramp("#4a4d52", "#8b8e94", 5, "dframe", roughness=0.8)
GLASS = Material("dglass", "#b7bcc3", roughness=0.22, metallic=0.15)
GL_WALL = Material("dgl_wall", "#c9cdd3", roughness=0.22, metallic=0.1)
GL_WIN = Material("dgl_win", "#f8fafb", roughness=0.2, metallic=0.05)
GL_SLAT = Material("dgl_slat", "#d3d7dc", roughness=0.2, metallic=0.05)
GL_ART = Material("dgl_art", "#6b4b4c", roughness=0.3)
GL_HB = Material("dgl_hb", "#7c7f85", roughness=0.35)

m = Model()
NG = len(GRAIN)


def grain_fn(u, w):
    """Weathered plank: long horizontal streaks with hard cathedral figure."""
    t = 0.54
    t += (fbm(u * 0.55, w * 7.5, 1201, 3) - 0.5) * 0.42     # stretched grain
    t += (fbm(u * 0.9, w * 26.0, 1303, 2) - 0.5) * 0.22     # fine ticks
    t += 0.10 * math.sin(w * 39.0 + math.sin(u * 1.7) * 2.2)
    return max(0, min(NG - 1, int(t * NG)))


def face(fld, fn, x0, x1, y0, y1, z, cell=0.075):
    """Rasterise a +z-facing rectangle."""
    raster(fld, lambda u, w: (u, w, z), lambda u, w: (0.0, 0.0, 1.0),
           x0, x1, y0, y1, max(2, int((x1 - x0) / (cell * 2.4))),
           max(2, int((y1 - y0) / cell)), fn)


fld = Field(GRAIN)

# ---- carcase ---------------------------------------------------------------
m.add(box(W, CASE, D), CASEM, at=(0, LEG, 0))
m.add(box(W + 0.10, TOPS, D + 0.09), CASEM, at=(0, LEG + CASE, 0))
face(fld, grain_fn, -(W + 0.10) / 2, (W + 0.10) / 2, LEG + CASE, TOP,
     (D + 0.09) / 2 + 0.001)                      # top slab front edge
# top surface grain
raster(fld, lambda u, w: (u, TOP + 0.001, w), lambda u, w: (0.0, 1.0, 0.0),
       -(W + 0.10) / 2, (W + 0.10) / 2, -(D + 0.09) / 2, (D + 0.09) / 2,
       26, 8, grain_fn)

# ---- drawers: two over one over one ---------------------------------------
GAP = 0.035
ROWS = [(0.86, 2), (0.85, 1), (0.85, 1)]          # (height, count) top -> bottom
y = LEG + CASE
for hgt, n in ROWS:
    y -= hgt
    for i in range(n):
        w = (W - 0.16 - GAP * (n - 1)) / n
        cx = -(W - 0.16) / 2 + w / 2 + i * (w + GAP)
        m.add(box(w, hgt - GAP, 0.06), CASEM, at=(cx, y + GAP / 2, D / 2 + 0.02))
        face(fld, grain_fn, cx - w / 2, cx + w / 2, y + GAP / 2,
             y + hgt - GAP / 2, D / 2 + 0.051)
        for k in range(1 if n == 2 else 2):
            px = 0 if n == 2 else (k * 2 - 1) * w * 0.26
            m.add(box(min(0.95, w * 0.42), 0.055, 0.05), PULL,
                  at=(cx + px, y + hgt * 0.52, D / 2 + 0.075))
    m.add(box(W - 0.10, GAP, 0.03), DARK, at=(0, y - GAP, D / 2 + 0.035))

# ---- tapered legs ----------------------------------------------------------
for sx in (-1, 1):
    for sz in (-1, 1):
        m.add(box(0.26, LEG, 0.24), CASEM,
              at=(sx * (W / 2 - 0.20), 0, sz * (D / 2 - 0.17)))

# ---- mirror ----------------------------------------------------------------
FW = 0.24
mf = Field(FRAME)
for (a, b, c, d) in ((-MIR_W / 2, MIR_W / 2, MIR_H - FW, MIR_H),
                     (-MIR_W / 2, MIR_W / 2, 0.0, FW),
                     (-MIR_W / 2, -MIR_W / 2 + FW, FW, MIR_H - FW),
                     (MIR_W / 2 - FW, MIR_W / 2, FW, MIR_H - FW)):
    m.add(box(b - a, d - c, 0.10), FRAME[2],
          at=((a + b) / 2, MIR_Y + c, -D / 2 + 0.34))
    raster(mf, lambda u, w: (u, MIR_Y + w, -D / 2 + 0.391),
           lambda u, w: (0.0, 0.0, 1.0), a, b, c, d,
           max(2, int((b - a) / 0.30)), max(2, int((d - c) / 0.13)),
           lambda u, w: max(0, min(len(FRAME) - 1,
                                   int((0.52 + (fbm(u * 0.7, w * 8.0, 77, 2) - 0.5)
                                        * 0.5) * len(FRAME)))))
mf.emit(m)

# glass: painted in layers, because a flat pale slab reads as a switched-off TV.
# The critic's own proof that this dresser is on the WEST wall is that the
# mirror shows the north window, the red canvas AND the bed headboard -- so all
# three are painted here.
gx0, gx1 = -MIR_W / 2 + FW, MIR_W / 2 - FW
gy0, gy1 = FW, MIR_H - FW
GZ = -D / 2 + 0.345


def pane(x0, x1, y0, y1, mat, dz=0.0):
    m.add(Part([(x0, MIR_Y + y0, GZ + dz), (x1, MIR_Y + y0, GZ + dz),
                (x1, MIR_Y + y1, GZ + dz), (x0, MIR_Y + y1, GZ + dz)],
               [(0, 1, 2), (0, 2, 3)]), mat)


pane(gx0, gx1, gy0, gy1, GLASS)
pane(gx0, gx1, gy0 + (gy1 - gy0) * 0.30, gy1, GL_WALL, 0.004)
# the reflected north window, blown out, with slats
wx0, wx1 = gx0 + (gx1 - gx0) * 0.06, gx0 + (gx1 - gx0) * 0.40
wy0, wy1 = gy0 + (gy1 - gy0) * 0.26, gy0 + (gy1 - gy0) * 0.92
pane(wx0, wx1, wy0, wy1, GL_WIN, 0.008)
for i in range(11):
    yy = wy0 + (wy1 - wy0) * (i + 0.5) / 11
    pane(wx0, wx1, yy, yy + (wy1 - wy0) * 0.028, GL_SLAT, 0.012)
# the reflected red canvas and the bed headboard below it
pane(gx0 + (gx1 - gx0) * 0.52, gx0 + (gx1 - gx0) * 0.90,
     gy0 + (gy1 - gy0) * 0.62, gy0 + (gy1 - gy0) * 0.95, GL_ART, 0.008)
pane(gx0 + (gx1 - gx0) * 0.46, gx1,
     gy0 + (gy1 - gy0) * 0.16, gy0 + (gy1 - gy0) * 0.46, GL_HB, 0.008)

fld.emit(m)
m.save(OUT)
lo, hi = m.bounds()
print("bounds", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
print("%.1f KB" % (os.path.getsize(OUT) / 1024))
