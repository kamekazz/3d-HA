"""Frontyard: the three things the front photographs put ON the covered porch.

The shell GLB already models the porch itself - roof, square columns, railing,
steps and the dark front door with its sidelights and coach lamps - so nothing
structural is rebuilt here. What is missing is what the owner keeps on it:

  Frontyard Porch Bench     white slatted bench/glider at the west end with the
                            pink-red cushions of "Front of the house.jpg"
  Frontyard Porch Planters  the pair of white urns flanking the front door,
                            clipped topiary above white flowers
  Frontyard Door Wreath     the wreath on the door, in all three v3 shots

Measured anchors (shell, world feet): porch floor y = 2.13, porch front edge
z = 40.6, house front wall z = 29.5, entry alcove recessed to z = 27.6 over
x 11..18, door centred x = 15.2, porch spans x -7..20.3.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kit import Model, Material, add_box, OUT
from roomkit.glb import cylinder as cyl, torus as tor
from roomkit.place import place

PORCH_Y = 2.13
DOOR_Z = 27.62
DOOR_X = 15.25

WHITE = Material("porch_white", "#ece9e3", roughness=0.6, metallic=0.0)
CUSHION = Material("porch_cushion", "#a8464b", roughness=0.95, metallic=0.0)
CUSHION2 = Material("porch_cushion_pale", "#d9a3a2", roughness=0.95, metallic=0.0)
LEAF = Material("topiary", "#3d5c39", roughness=1.0, metallic=0.0)
BLOOM = Material("bloom_white", "#e7e5dc", roughness=0.95, metallic=0.0)
WREATH = Material("wreath", "#33452f", roughness=1.0, metallic=0.0)
RIBBON = Material("wreath_ribbon", "#8d2f30", roughness=0.9, metallic=0.0)


def bench():
    """4.4 ft white slatted bench, back to the house, cushions on the seat."""
    m = Model()
    for dx in (-1.95, 1.95):                       # end frames
        add_box(m, WHITE, 0.22, 1.35, 1.55, dx, 0, 0)
        add_box(m, WHITE, 0.22, 1.05, 0.20, dx, 1.35, -0.62)
    add_box(m, WHITE, 4.4, 0.16, 1.55, 0, 1.28, 0)       # seat deck
    for i, dy in enumerate((0.10, 0.52, 0.94)):          # back slats
        add_box(m, WHITE, 4.4, 0.30, 0.14, 0, 1.44 + dy, -0.68)
    add_box(m, WHITE, 4.6, 0.16, 0.28, 0, 2.66, -0.68)   # top rail
    add_box(m, CUSHION, 4.1, 0.28, 1.35, 0, 1.44, 0.02)  # seat cushion
    for dx in (-1.25, 0.0, 1.25):                        # back pillows
        add_box(m, CUSHION2, 1.1, 0.85, 0.26, dx, 1.72, -0.50)
    return m


def _urn(m, x, z):
    m.add(cyl(0.62, 1.55, 12, r_top=0.80), WHITE, at=(x, 0, z))
    m.add(cyl(0.86, 0.14, 12), WHITE, at=(x, 1.52, z))
    # white flowers spilling over the rim, clipped topiary above
    for a in range(8):
        t = a / 8 * math.tau
        m.add(cyl(0.30, 0.26, 6), BLOOM,
              at=(x + math.cos(t) * 0.66, 1.58, z + math.sin(t) * 0.66))
    add_box(m, LEAF, 0.20, 1.1, 0.20, x, 1.7, z)
    m.add(cyl(0.62, 0.90, 10, r_top=0.50), LEAF, at=(x, 1.80, z))
    m.add(cyl(0.44, 0.70, 10, r_top=0.30), LEAF, at=(x, 2.80, z))


def planters():
    m = Model()
    _urn(m, DOOR_X - 3.0, 0.0)
    _urn(m, DOOR_X + 3.0, 0.0)
    return m


def wreath():
    m = Model()
    # torus() is built in the XZ plane; stand it up so it faces the street
    m.add(tor(0.92, 0.24, 20, 8), WREATH, rot_x=math.pi / 2)
    add_box(m, RIBBON, 0.30, 0.62, 0.12, 0, 0.86, 0.10)
    return m


if __name__ == "__main__":
    jobs = [
        # name, model, world x, world z, world base y, rot deg
        ("Frontyard Porch Bench", bench(), 0.6, 31.6, PORCH_Y, 0),
        ("Frontyard Porch Planters", planters(), DOOR_X, 30.35, PORCH_Y, 0),
        ("Frontyard Door Wreath", wreath(), DOOR_X, DOOR_Z + 0.30, PORCH_Y + 5.05, 0),
    ]
    for name, m, wx, wz, wy, rot in jobs:
        f = os.path.join(OUT, name.lower().replace(" ", "_") + ".glb")
        m.save(f)
        lo, hi = m.bounds()
        # room 11's footprint anchor is (-4.0, 35.0); place() centres the bbox
        # on pos.x/pos.z and seats min-Y at pos.y, and objects hang off the
        # first-floor group at world y = 8.
        pos = (wx + 4.0, wy - 8.0 + lo[1], wz - 35.0)
        r = place(name, f, 11, pos=pos, rot_y_deg=rot)
        print("%-26s %6.1f KB  pos %s  %s" % (
            name, os.path.getsize(f) / 1024, [round(v, 2) for v in pos], r["action"]))
