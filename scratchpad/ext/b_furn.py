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
from kit import (Model, Material, add_box, cylinder, box, wicker_tex,
                 world_pos, OUT)
from roomkit.place import place

LD, UD = 3.30, 3.95        # world Y of the two deck surfaces

WICKER = Material("wicker", "#bfbab1", roughness=0.85, metallic=0.0,
                  tex=wicker_tex(11))
CUSH = Material("cushion", "#ded7c8", roughness=0.95, metallic=0.0)
TEAK = Material("teak", "#a9norm", roughness=0.7) if False else \
    Material("teak", "#a9814e", roughness=0.7, metallic=0.0)
BLACK = Material("matte_black", "#232427", roughness=0.6, metallic=0.05)
STEEL = Material("dark_steel", "#3a3c40", roughness=0.4, metallic=0.5)
CANOPY = Material("canopy_cream", "#cec4ad", roughness=0.9, metallic=0.0)


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
    add_box(m, WICKER, w, 0.55, d, 0, 0.62, 0)               # apron
    for dx in (-w / 2 + 0.22, w / 2 - 0.22):
        for dz in (-d / 2 + 0.22, d / 2 - 0.22):
            add_box(m, TEAK, 0.22, 0.62, 0.22, dx, 0, dz)    # legs
    add_box(m, CUSH, w - 0.30, 0.42, d - 0.34, 0, seat_h - 0.42, 0)
    add_box(m, WICKER, w, back_h - seat_h, 0.34, 0, seat_h, -d / 2 + 0.17)
    add_box(m, CUSH, w - 0.40, back_h - seat_h - 0.42, 0.30, 0, seat_h,
            -d / 2 + 0.42)
    if arm:
        for dx in (-w / 2 + 0.17, w / 2 - 0.17):
            add_box(m, WICKER, 0.34, 2.02 - 0.62, d, dx, 0.62, 0)


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
        add_box(m, WICKER, 2.3, 1.05, 2.3, ox, 0, oz)
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
    """Closed cantilever parasol: black mast, top arm, furled cream canopy."""
    m = Model()
    add_box(m, BLACK, 1.9, 0.30, 1.9, 0, 0, 0)                    # weighted base
    add_box(m, BLACK, 0.50, 8.3, 0.50, 0, 0.30, 0)                # mast
    add_box(m, BLACK, 0.40, 0.40, 3.0, 0, 8.20, -1.40)            # cantilever arm
    # furled canopy hanging from the arm's outer end
    m.add(cylinder(0.86, 6.0, 10, r_top=0.60), CANOPY, at=(0, 2.1, -2.75))
    for y in (3.4, 5.6):                       # the ties round a furled canopy
        m.add(cylinder(0.90, 0.16, 10), BLACK, at=(0, y, -2.75))
    m.add(cylinder(0.22, 0.7, 8), BLACK, at=(0, 8.2, -2.75))
    return m


PIECES = [
    ("Backyard Grill", grill, 11.5, -27.2, UD, 178),
    ("Backyard Sofa", sofa, 18.6, -37.0, LD, 268),
    ("Backyard Lounge", lounge, 11.6, -36.9, LD, 0),
    ("Backyard Parasol", parasol, 22.6, -39.6, LD, 200),
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
