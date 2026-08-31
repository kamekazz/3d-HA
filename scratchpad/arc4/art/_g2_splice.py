"""Rebuild art_g2.py = new docstring + round-4 helpers + round-4 legacy
machines + round-5 south-run machines + exports.  Re-runnable."""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "art_g2.py")
BAK = os.path.join(HERE, "art_g2_r4.bak.py")

orig = io.open(BAK if os.path.exists(BAK) else SRC,
               encoding="utf-8").read().split("\n")
if not os.path.exists(BAK):
    io.open(BAK, "w", encoding="utf-8").write("\n".join(orig))
    print("saved round-4 backup ->", os.path.basename(BAK))

# locate the round-4 landmarks by content, not by line number
def find(pat, start=0):
    for i in range(start, len(orig)):
        if re.match(pat, orig[i]):
            return i
    raise SystemExit("landmark not found: " + pat)

i_prim = find(r"^# -+ primitives")
i_mvc = find(r"^#  MARVEL VS CAPCOM")
i_exp = find(r"^# -+ export")

HELPERS = orig[i_prim:i_mvc - 2]          # drops the "# ====" banner line
LEGACY = orig[i_mvc - 2:i_exp - 2]

HEAD = '''"""Round-5 cabinet artwork, agent G2 -- the ARCADE ROOM'S SOUTH RUN.

    SOUTH_RUN[0]  legends-ultimate                     Legends Ultimate
    SOUTH_RUN[1]  street-fighter-2-champion-edition    SFII: Champion Edition
    SOUTH_RUN[2]  time-crisis                          Time Crisis
    SOUTH_RUN[3]  terminator-2                         Terminator 2

WHAT CHANGED FROM ROUND 4, AND WHY
----------------------------------
Three independent critics rejected round 4 in the same words: "all three
cabinets are one asset recoloured -- the same flat-black front panel with the
SAME centred grey coin-door rectangle at the same size and position, and the
same two-joystick deck (one red top, one blue top) over the same row of flat
square buttons; only the trim colour and a small floated logo differ."  That
is verifiable in scratchpad/arc4/shots/r4_mq_south.png and it is correct.

Round 5 rebuilds everything below the marquee:

  * FULL-BLEED panels.  Every side / front / deck tile carries its own ground
    colour edge to edge -- Time Crisis is red with gold trim, Champion
    Edition royal blue, Legends Ultimate a black licence grid, T2 machined
    gunmetal.  No panel is a dark field with a logo floated on it.
  * THE COIN DOOR IS ARTWORK, and no two are alike: Time Crisis has a big
    steel plate dead centre with two slots, a chrome bar and a return cup;
    T2 a small nearly-black plate offset RIGHT; Champion Edition a narrow
    dark service plate low LEFT on the blue base; Legends Ultimate has NONE,
    because it is a home cabinet and no frame shows one.
  * CONTROL DECKS have their own printed graphic AND their own control
    layout.  The controls are geometry, so they are exported as `DECKS`
    for ar2.upright to consume -- see the contract above that table.  Counts
    and kinds: 2 ball-tops + 12 convex buttons + trackball + spinner /
    2 bat-tops + 14 buttons / 2 light guns + 3 buttons / 2 light guns +
    2 buttons.  Not one flat square button survives.
  * THE CRT IS NOT BLACK -- but neither is it an attract loop.  All four of
    these machines photograph DARK, so `.screen` paints dark glass with the
    room reflected in it, plus the one bright thing any frame shows: the pale
    yellow instruction card burning along the bottom of Champion Edition's
    monitor, and Time Crisis's dim olive game image.  Declared, and dark on
    purpose.

Terminator 2's MARQUEE is round 4's, untouched -- it reads cleanly in the
judged frame and the brief says keep it.  The other three marquees are new
here because those machines moved onto this agent's run this round; they are
drawn to the same roster descriptions round 4 worked from.

HOW THE INTEGRATOR USES THIS
----------------------------
`PANELS` maps "<slug>.<panel>" to `paint(px, ox, oy, tile)`, painting one
`tile` x `tile` square into a shared atlas.  `tile` should be `TILE` (256);
smaller works but the letterforms lose their edges, which is exactly why
atlas4 supersamples.

`DECKS`, `FRONT_RECT` and `COIN` (inside DECKS) are the geometry contract.
`LEGACY_PANELS` holds round 4's marvel-vs-capcom / nfl-blitz /
east-7-no-machine so that merging this module can never collide with whoever
owns those machines now.

THREE THINGS THAT ARE GEOMETRY, NOT ART:

1. ASPECT.  The tile is square and no panel it lands on is.  Round 4 used ONE
   aspect table for every machine; the south run's widths differ by 30%
   (Legends Ultimate 2.95 ft against T2's 2.28), so three of the four were
   pre-squeezed wrong.  `A` below is PER MACHINE, computed from each row of
   ar2.SOUTH_RUN.  If a cabinet is re-proportioned by more than ~15%, change
   `A` and re-run -- do not stretch the atlas.
2. ORIENTATION.  On the flank tile, sweep's uvof puts the cabinet FRONT at
   the tile's RIGHT edge and the cabinet TOP at the tile's TOP.  On the deck,
   front and marquee tiles, tile LEFT is local -x, which for a south-wall
   machine (rot 180) is the VIEWER'S LEFT; on the deck tile the tile TOP is
   the deck's BACK (screen end).  `flip` is off and must stay off.
3. MATERIALS.  `.side`, `.front` and `.marquee` are true albedo for ART
   (#ffffff).  `.deck` tiles are authored bright for ART_DK (#4c4c4c) -- an
   up-facing surface collects roughly twice what a vertical one does -- EXCEPT
   `time-crisis.deck`, whose red-orange ground needs the lighter ART_D
   (#c9c9c9) or it lands as brown mud.  a2kit.DECK_MAT already lists
   time-crisis as "D"; keep it.  `.screen` needs a DARK factor material,
   darker than ART_DK; #3a3a3a is about right.

THIS FILE IS GENERATED.  art_g2.py = _g2_splice.py applied to
art_g2_r4.bak.py (round 4, kept verbatim for its helper library and its three
legacy machines) + _g2_frag.py (round 5 machines) + _g2_export.py (PANELS,
DECKS, FRONT_RECT, EVIDENCE).  Edit the fragments and re-run
    $PY scratchpad/arc4/art/_g2_splice.py
then preview_g2r5.py / compare_g2r5.py / bytes_g2r5.py.  Editing art_g2.py by
hand is fine for the integrator -- just be aware a re-splice would drop it.

Pure stdlib.  The 4x4 ordered dither and round-to-8 quantisation are copied
from a2kit._paint and are what keeps the PNG small; atlas4 re-quantises to 16
levels after its box-average.  Full-tile fbm noise grounds were REMOVED this
round -- they cost bytes and are invisible under the dither at panel scale.
"""

import math

TILE = 256

# --- copied verbatim from a2kit so the two atlases quantise identically
_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

# ROUND 4's single aspect table.  Kept because the three legacy machines at
# the foot of this file were authored against it.  MY four machines use `A`.
ASPECT = {
    "marquee": 3.40,
    "side": 0.49,
    "front": 1.25,
    "deck": 2.35,
    "riser": 6.20,
}

'''

FRAG = io.open(os.path.join(HERE, "_g2_frag.py"), encoding="utf-8").read()
EXPORT = io.open(os.path.join(HERE, "_g2_export.py"), encoding="utf-8").read()

out = (HEAD + "\n".join(HELPERS).rstrip() + "\n\n\n"
       + "# " + "=" * 71 + "\n"
       + "#  ROUND 4 LEGACY -- machines that moved to other agents' runs in\n"
       + "#  round 5.  Exported as LEGACY_PANELS, not PANELS.  Unchanged.\n"
       + "# " + "=" * 71 + "\n"
       + "\n".join(LEGACY).rstrip() + "\n\n\n"
       + FRAG.rstrip() + "\n\n\n" + EXPORT.rstrip() + "\n")

io.open(SRC, "w", encoding="utf-8").write(out)
print("wrote %s  (%d lines)" % (os.path.basename(SRC), out.count("\n")))
