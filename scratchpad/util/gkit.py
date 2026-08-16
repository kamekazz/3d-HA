"""Utility-spaces build kit (garage / laundry / pantry).

Reuses the shell-pass kit for placement, colour and contact shadows and adds a
loft helper (car body) plus the palette these three rooms need.
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\shellpass")

from roomkit.glb import (Model, Material, box, rounded_box, cylinder, prism,
                         quad, sag_plane, torus, Part)          # noqa: F401
from roomkit.place import place
import kit as SK                                                # noqa: N812
from kit import bx, rect_down, rect_up, disc_down, ring_down, spans, wall_band  # noqa: F401
from kit import contact_shadow, mix, Rnd, surfaces               # noqa: F401

OUT = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(OUT, "glb")
R = math.radians


def save_and_place(name, m, room, fname=None):
    os.makedirs(GLB, exist_ok=True)
    path = os.path.join(GLB, (fname or name.replace(" ", "_").lower()) + ".glb")
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    size = tuple(round(hi[i] - lo[i], 2) for i in range(3))
    print("  %-26s %6.1f KB  size=%s pos=(%.2f,%.2f,%.2f) %s"
          % (name, kb, size, pos[0], pos[1], pos[2], res["action"]))
    return kb


# ------------------------------------------------------------------ palette
CONC = Material("conc", "#8d8c88", roughness=0.93)
CONC_L = Material("concl", "#9c9b96", roughness=0.93)
STEEL = Material("steel", "#8d9195", roughness=0.42, metallic=0.45)
STEEL_D = Material("steeld", "#5e6367", roughness=0.50, metallic=0.35)
BLK = Material("blk", "#26282b", roughness=0.55, metallic=0.15)
BLKR = Material("blkr", "#17181a", roughness=0.85)          # rubber
WHITE = Material("white", "#eeece7", roughness=0.62)
WHITE_A = Material("whitea", "#dcd9d3", roughness=0.66)     # shaded white return
GRAPH = Material("graph", "#454b51", roughness=0.55)        # graphite cabinet door
GRAPH_L = Material("graphl", "#5b6268", roughness=0.55)
OAKTOP = Material("oaktop", "#b08050", roughness=0.72)
OAKEDGE = Material("oakedge", "#8f6338", roughness=0.72)
PEG = Material("peg", "#c6ab7d", roughness=0.90)
RED = Material("red", "#b23127", roughness=0.48, metallic=0.10)
REDD = Material("redd", "#8a2119", roughness=0.50)
BLUE = Material("blue", "#2f5f96", roughness=0.55)
GREEN = Material("green", "#3f7a48", roughness=0.70)
YELLOW = Material("yellow", "#d9a520", roughness=0.60)
ORANGE = Material("orange", "#c8641f", roughness=0.65)
CARD = Material("card", "#b39a6e", roughness=0.92)
PLAS_G = Material("plasg", "#3d4247", roughness=0.72)
CHR = Material("chr", "#b6babd", roughness=0.28, metallic=0.60)
GLASS_D = Material("glassd", "#2c3239", roughness=0.16, metallic=0.20, opacity=0.80)
LENS = Material("glens", "#fff6de", roughness=0.30, emissive="#fff0cf",
                emissive_strength=3.2)
SILV = Material("silv", "#b7babe", roughness=0.34, metallic=0.40)
SILV_D = Material("silvd", "#8f9297", roughness=0.38, metallic=0.35)


# -------------------------------------------------------------------- loft
def section(hw, y0, y1, c=0.28):
    """8-point chamfered rectangle in the (x, y) plane, CCW seen from +z."""
    c = min(c, hw * 0.6, (y1 - y0) * 0.45)
    return [(-hw + c, y0), (hw - c, y0), (hw, y0 + c), (hw, y1 - c),
            (hw - c, y1), (-hw + c, y1), (-hw, y1 - c), (-hw, y0 + c)]


def loft(sections, caps=True):
    """sections = [(z, [(x, y), ...]), ...] with equal point counts."""
    v, t = [], []
    n = len(sections[0][1])
    for (z, pts) in sections:
        for (x, y) in pts:
            v.append((x, y, z))
    for i in range(len(sections) - 1):
        a, b = i * n, (i + 1) * n
        for k in range(n):
            k2 = (k + 1) % n
            t += [(a + k, a + k2, b + k2), (a + k, b + k2, b + k)]
    if caps:
        last = (len(sections) - 1) * n
        for i in range(1, n - 1):
            t.append((0, i + 1, i))
            t.append((last, last + i, last + i + 1))
    return Part(v, t, smooth=True)


def wheel(m, cx, cy, cz, r=1.12, w=0.72):
    m.add(cylinder(r, w, 20, anchor="center"), BLKR,
          at=(cx, cy, cz), rot_z=R(90))
    m.add(cylinder(r * 0.60, w * 0.62, 16, anchor="center"), CHR,
          at=(cx, cy, cz), rot_z=R(90))
