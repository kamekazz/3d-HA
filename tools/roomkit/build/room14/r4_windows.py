"""Windows — round 4: REAL openings plus an inside casing/blind piece.

Round 2/3 faked every window as a flush decal because the app's opening panel
used to be a flat teal slab.  house.js now cuts a genuine hole and fills a
`window` with proper glass, so the four openings this room really has are cut
for real (see r4_place.py) and this GLB supplies only what a cut hole cannot:
the interior casing, the stool and apron, the lowered blind, and a blown-out
pane behind the blind.

The pane is deliberately kept.  The judged view is single-floor presentation
mode, where floorview.js swaps the sky for a dark studio backdrop — so a bare
hole reads as a BLACK rectangle, the opposite of the photo's blown-out windows.
The pane sits 0.01 ft inside the wall plane and carries the blow-out; the real
hole carries the dollhouse read from outside.

Sizes come from the Apple-Home plan's own window marks (r4_room.WIN): 2.87 /
2.72 / 3.00 / 2.90 ft — four ordinary 3 ft sashes, not the 4-5 ft units round 2
guessed at.
"""
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roomkit.glb import Model, Material, box
from tone import radiance_for_byte

TRIM = Material("win_trim", "#ffffff", roughness=0.55,
                emissive="#ffffff", emissive_strength=0.45)
SLAT = Material("win_slat", "#fbfbfb", roughness=0.62,
                emissive="#ffffff", emissive_strength=0.95)
RAIL = Material("win_rail", "#f4f4f4", roughness=0.6,
                emissive="#ffffff", emissive_strength=0.55)
# The gap between slats.  Without it the whole blind clipped to one flat 247
# block: every albedo over ~0.5 saturates on this wall, so the slat lines have
# to be cut by a genuinely darker strip behind them, not by shading.
GAP = Material("win_gap", "#b4b4b4", roughness=0.9)
GLASS = Material("win_glass", "#ffffff", roughness=0.25,
                 emissive="#fdfdff", emissive_strength=3.4)

DEPTH = 0.34             # stool projection == the piece's z extent
COVER = 0.86             # fraction of the opening the blind covers


def build(ow, oh, out, cover=COVER):
    """Author with the wall plane at z=0, the piece reaching +z into the room,
    and y=0 at the bottom of the apron."""
    apron_h, stool_t = 0.34, 0.06
    y_sill = apron_h + stool_t          # opening bottom, in piece coords
    m = Model()

    # apron under the stool — kept shallow (0.055) so the desk can back up to
    # the east wall without punching through it
    m.add(box(ow + 0.30, apron_h, 0.055), TRIM,
          at=(0, 0.0, 0.055 / 2 + 0.004))
    # stool / sill, the one part that projects
    m.add(box(ow + 0.62, stool_t, DEPTH), TRIM,
          at=(0, apron_h, DEPTH / 2 + 0.004))
    # side casings
    for sx in (-1, 1):
        m.add(box(0.28, oh + 0.28, 0.055), TRIM,
              at=(sx * (ow / 2 + 0.14), y_sill, 0.055 / 2 + 0.004))
    # head casing
    m.add(box(ow + 0.56, 0.28, 0.06), TRIM,
          at=(0, y_sill + oh, 0.06 / 2 + 0.004))

    # blown-out pane, just inside the wall plane
    m.add(box(ow, oh, 0.012), GLASS, at=(0, y_sill, 0.012 / 2 + 0.004))

    # blind: head rail plus a stack of slats over the top `cover` of the sash
    top = y_sill + oh - 0.03
    m.add(box(ow - 0.06, 0.15, 0.13), RAIL, at=(0, top - 0.15, 0.075))
    y = top - 0.17
    bottom = y_sill + oh * (1.0 - cover)
    pitch = 0.150
    while y > bottom:
        m.add(box(ow - 0.10, pitch - 0.020, 0.012), GAP, at=(0, y - pitch + 0.02, 0.052))
        m.add(box(ow - 0.10, 0.020, 0.095), SLAT, at=(0, y, 0.105),
              rot_x=0.22)
        y -= pitch
    # bottom rail
    m.add(box(ow - 0.06, 0.055, 0.11), RAIL, at=(0, bottom - 0.055, 0.10))

    m.save(out)
    lo, hi = m.bounds()
    return lo, hi


if __name__ == "__main__":
    from r4_room import WIN, WIN_H
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    for name in WIN:
        ow = WIN[name][2]
        lo, hi = build(ow, WIN_H[name],
                       os.path.join(outdir, name.lower().replace(" ", "_") + ".glb"))
        print("%-18s %.2f x %.2f  bbox %s -> %s"
              % (name, ow, WIN_H[name],
                 tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi)))
