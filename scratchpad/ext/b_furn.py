"""Backyard deck furniture, read off "Backyard v3 9" and "v3 5".

Four placed pieces, all standing on the deck (upper y 3.95 / lower y 3.30):
  Backyard Grill     black covered gas grill on the upper level by the rail
  Backyard Sofa      3-seat white/grey wicker sofa along the east rail
  Backyard Lounge    two armchairs, two square ottomans, wooden coffee table
  Backyard Parasol   CLOSED cream cantilever parasol on a black mast

No lights of any kind: several of the rear photographs were taken at dusk with
the string lights and deck step-lights on, and the owner asked for daytime
geometry only this round.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kit import (Model, Material, add_box, add_uv_box, cylinder, box,
                 wicker_tex, world_pos, OUT)
from roomkit.place import place

LD, UD = 2.40, 2.72        # world Y of the two deck surfaces
                           # (b_deck.py carries the height decision)

# Cooler and a shade darker than round 1's warm "#bfbab1": the photographed
# wicker meters RGB 167,165,174 -- B above R -- and round 1 rendered
# 195,193,187, warm and FLAT. The flatness was the real defect and its cause
# was structural: every wicker panel was a `box()`, which emits no UVs, so the
# weave tile sampled texel (0,0) forever. Everything wicker below is an
# `add_uv_box` now. WEAVE is texture repeats per foot: 1.6 puts one over-under
# pair at about 0.9 inch, a real strand width that still survives the mipmap
# at the exterior fly-to distance.
WEAVE = 1.6
WICKER = Material("wicker", "#b2b0b0", roughness=0.85, metallic=0.0,
                  tex=wicker_tex(11))
CUSH = Material("cushion", "#ded7c8", roughness=0.95, metallic=0.0)
TEAK = Material("teak", "#a9norm", roughness=0.7) if False else \
    Material("teak", "#a9814e", roughness=0.7, metallic=0.0)
BLACK = Material("matte_black", "#232427", roughness=0.6, metallic=0.05)
STEEL = Material("dark_steel", "#3a3c40", roughness=0.4, metallic=0.5)
CANOPY = Material("canopy_cream", "#cec4ad", roughness=0.9, metallic=0.0)
STONE = Material("planter_stone", "#8e8d89", roughness=0.95, metallic=0.0)
BLOOM = Material("hydrangea", "#c98fa4", roughness=0.95, metallic=0.0)
FOLIAGE = Material("planter_leaf", "#3e5638", roughness=1.0, metallic=0.0)


# ------------------------------------------------------------------ grill
def grill():
    m = Model()
    # covered: a soft-cornered black box over a cart, as photographed
    add_box(m, BLACK, 4.6, 2.05, 2.15, 0, 1.55, 0)
    add_box(m, BLACK, 4.35, 0.35, 1.95, 0, 3.60, 0)          # domed-ish top
    add_box(m, STEEL, 4.0, 1.45, 1.75, 0, 0.10, 0)           # cart under the cover
    for dx in (-1.75, 1.75):
        for dz in (-0.7, 0.7):
            m.add(cylinder(0.28, 0.10, 10), BLACK, at=(dx, 0.05, dz))
    return m


# ------------------------------------------------------------------- sofa
def _wicker_seat(m, w, d, seat_h=1.32, back_h=2.55, arm=True):
    add_uv_box(m, WICKER, w, 0.55, d, 0, 0.62, 0, scale=WEAVE)       # apron
    for dx in (-w / 2 + 0.22, w / 2 - 0.22):
        for dz in (-d / 2 + 0.22, d / 2 - 0.22):
            add_box(m, TEAK, 0.22, 0.62, 0.22, dx, 0, dz)            # legs
    add_box(m, CUSH, w - 0.30, 0.42, d - 0.34, 0, seat_h - 0.42, 0)
    add_uv_box(m, WICKER, w, back_h - seat_h, 0.34, 0, seat_h, -d / 2 + 0.17,
               scale=WEAVE)
    add_box(m, CUSH, w - 0.40, back_h - seat_h - 0.42, 0.30, 0, seat_h,
            -d / 2 + 0.42)
    if arm:
        for dx in (-w / 2 + 0.17, w / 2 - 0.17):
            add_uv_box(m, WICKER, 0.34, 2.02 - 0.62, d, dx, 0.62, 0, scale=WEAVE)


def sofa():
    m = Model()
    _wicker_seat(m, 7.0, 3.0)
    return m


def lounge():
    """Two armchairs, two ottomans and the light wooden coffee table.

    Authored in WORLD X/Z about the group's own centre so the pieces keep the
    photographed arrangement; the group is placed as one object.
    """
    m = Model()

    def chair(cx, cz, ry):
        sub = Model()
        _wicker_seat(sub, 2.9, 3.0)
        for part, mat in sub._parts:
            m.add(part, mat, at=(cx, 0, cz), rot_y=ry)

    chair(-3.4, 0.7, math.radians(-70))
    chair(0.4, 2.6, math.radians(180))
    # ottomans
    for (ox, oz) in ((3.0, -1.6), (-1.2, -2.4)):
        add_uv_box(m, WICKER, 2.3, 1.05, 2.3, ox, 0, oz, scale=WEAVE)
        add_box(m, CUSH, 2.05, 0.28, 2.05, ox, 1.05, oz)
        for dx in (-0.95, 0.95):
            for dz in (-0.95, 0.95):
                add_box(m, TEAK, 0.2, 0.28, 0.2, ox + dx, 0, oz + dz)
    # coffee table
    add_box(m, TEAK, 3.5, 0.22, 2.0, 0, 1.28, 0)
    for dx in (-1.55, 1.55):
        for dz in (-0.8, 0.8):
            add_box(m, TEAK, 0.18, 1.28, 0.18, dx, 0, dz)
    return m


def parasol():
    """Closed cantilever parasol: black ROUND mast, top arm, furled canopy.

    Round 1 read "closed" correctly and then built the wrong closed shape: a
    0.86 ft-radius cylinder only 6 ft long on a 0.50 ft SQUARE mast, with two
    fat black bands round it. At render scale that is a squat cream cone with
    two stripes on a chunky post, which is why it read as a bollard.

    "Backyard v3 9" (x 1000-1075, y 110-300) and "v3 2" (x~100, y 235-300)
    both show a LONG SLIM TAPER: about 7 ft of furled fabric barely a foot
    across at its widest, hanging from a cantilever arm on a slim ROUND mast,
    tied twice. Aspect in the photograph is about 1:7; round 1 built 1:3.5.
    """
    m = Model()
    add_box(m, BLACK, 1.75, 0.28, 1.75, 0, 0, 0)                  # weighted base
    m.add(cylinder(0.23, 8.9, 12), BLACK, at=(0, 0.28, 0))        # round mast
    m.add(cylinder(0.15, 3.0, 10), BLACK, at=(0, 9.02, -1.45),    # cantilever arm
          rot_x=math.pi / 2)
    m.add(cylinder(0.17, 0.55, 10), BLACK, at=(0, 8.55, -2.90))   # hub
    # furled canopy: 7.0 ft, widest 0.50 at the hub, tapering to a point
    m.add(cylinder(0.09, 7.0, 12, r_top=0.50), CANOPY, at=(0, 1.55, -2.90))
    for y in (3.9, 6.3):                       # two SLIM ties, not black bands
        m.add(cylinder(0.42, 0.09, 12), BLACK, at=(0, y, -2.90))
    return m


def planter():
    """Grey planter with a pink hydrangea, at the lower deck rail.

    "Backyard v3 9" bottom right, x 990-1090 y 655-725."""
    m = Model()
    m.add(cylinder(0.95, 1.55, 10, r_top=1.15), STONE, at=(0, 0, 0))
    m.add(cylinder(1.22, 0.14, 10), STONE, at=(0, 1.52, 0))
    for i in range(9):
        a = i / 9 * math.tau
        r = 0.36 + (i % 3) * 0.07
        m.add(cylinder(r, r * 1.5, 7), BLOOM,
              at=(math.cos(a) * 0.62, 1.60 + (i % 2) * 0.22, math.sin(a) * 0.62))
    m.add(cylinder(0.62, 0.75, 8, r_top=0.40), FOLIAGE, at=(0, 1.55, 0))
    return m


def chaise():
    """Long wicker chaise / daybed on the lower deck (v3 9, x 830-1060)."""
    m = Model()
    w, d = 2.9, 6.4
    add_uv_box(m, WICKER, w, 0.62, d, 0, 0.55, 0, scale=WEAVE)     # frame
    for dx in (-w / 2 + 0.22, w / 2 - 0.22):
        for dz in (-d / 2 + 0.25, d / 2 - 0.25):
            add_box(m, TEAK, 0.22, 0.55, 0.22, dx, 0, dz)
    add_box(m, CUSH, w - 0.30, 0.40, d - 0.35, 0, 1.17, 0)         # mattress
    add_uv_box(m, WICKER, w, 1.35, 0.32, 0, 1.17, -d / 2 + 0.16, scale=WEAVE)
    add_box(m, CUSH, w - 0.45, 0.95, 0.28, 0, 1.25, -d / 2 + 0.42)
    return m


PIECES = [
    ("Backyard Grill", grill, 11.5, -27.2, UD, 178),
    # the wicker bench sits on the UPPER level by the rail in v3 9, not below
    ("Backyard Sofa", sofa, 16.8, -30.4, UD, 268),
    ("Backyard Lounge", lounge, 11.6, -36.9, LD, 0),
    ("Backyard Parasol", parasol, 25.2, -40.0, LD, 200),
    # the lower level read as "nearly bare" against v3 9, which is packed
    ("Backyard Chaise", chaise, 21.0, -38.2, LD, 272),
    ("Backyard Planter", planter, 25.8, -34.4, LD, 0),
    ("Backyard Planter Two", planter, 4.8, -41.2, LD, 0),
]

if __name__ == "__main__":
    for name, fn, wx, wz, wy, rot in PIECES:
        m = fn()
        f = os.path.join(OUT, name.lower().replace(" ", "_") + ".glb")
        m.save(f)
        lo, hi = m.bounds()
        # these are authored about their own origin, so pos.x/z are the world
        # point minus the room anchor, shifted by the bbox centre offset
        cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        # roomkit.place rotates about the object origin AFTER bbox-centring, so
        # a rotated piece's centre offset has to be rotated with it
        ox, oz = cx * c + cz * s, -cx * s + cz * c
        pos = (wx + ox + 4.0, wy - 8.0 + lo[1], wz + oz + 22.5)
        r = place(name, f, 3, pos=pos, rot_y_deg=rot)
        print("%-18s %6.1f KB  pos %s  %s" % (
            name, os.path.getsize(f) / 1024, [round(v, 2) for v in pos], r["action"]))
