# -*- coding: utf-8 -*-
"""The ROUND 7 section that _r7_splice.py puts into art_g2.py's docstring."""

HEAD = '''WHAT ROUND 7 CHANGED, AND WHY  (the four CONTROL DECKS, nothing else)
---------------------------------------------------------------------
Round 6 was rejected 0 of 4 and all four critics named the SAME surface:
"the pushbuttons are painted into the control-deck texture rather than
modelled -- flat 2-3 px coloured lozenges with no dome", "every one of the
six cabinets wears the identical control deck", and "in the photo the deck
is the largest continuous surface facing camera and it is printed edge to
edge; in the render every deck is an empty plane with a faint round ghost
decal".  All three are true of round 5's work and verifiable in
scratchpad/arc4/shots/r6_full_south.png.

WHY THE BUTTONS COULD NOT BE FIXED BY DRAWING THEM BETTER.  atlas4 packs a
deck at SIZE 52 isotropic, i.e. ~82 x 33 texels, i.e. 32-37 texels per FOOT.
A real 1.1 in arcade button is 0.092 ft = 3.1 texels.  The critics were
measuring the texture, not the drawing.  So this round:

  * the CONTROLS move to `DECKS` as geometry, with a metrology block
    (`BUTTON_METROLOGY`) that measures a real button off `v4 5` rather than
    asserting a radius, and with the standing height raised 0.026 -> 0.038 ft
    and declared as a deliberate 0.06 in over the real range;
  * the ARTWORK's job becomes the printed COLLAR each control stands in --
    0.28-0.45 ft, three to four times the button, so it survives the packing;
    and every collar is painted THROUGH `_uv()` from `DECKS` itself, so a ring
    cannot drift off the button it belongs to;
  * every deck is re-drawn edge to edge with photo-read composition and
    nothing on any of them is thinner than 2 output texels.

FOUR THINGS I CHANGED AGAINST ROUND 5 ON THE EVIDENCE, not on taste:

  1. LEGENDS ULTIMATE'S DECK IS NO LONGER INFERRED.  Round 5 declared it
     INFERRED and was right to at the magnifications it used.  `Arcade Room
     v4 3.jpg` sees the same deck from a few feet away and resolves it at
     7-10x: red ball-tops in three-ring printed targets, a magenta nebula, a
     dark trackball, a chartreuse "LEGENDS ULTIMATE" along the front edge.
     The balls are RED (round 5 guessed white) and there is NO SPINNER
     (round 5 inferred one from the product spec).
  2. CHAMPION EDITION'S DECK IS PALE, NOT DARK NAVY.  v4 4 at 30x and v4 5 at
     22x both show a light grey-white panel printed with a multicade licence
     collage.  It is now the room's one bright control panel.
  3. TIME CRISIS HAS A CHAMFERED TAN PRINTED BORDER.  v4 4 at 14x is the best
     photograph of any deck in this room and the border is the most
     distinctive printed line on the south wall.  Round 5 missed it.
  4. TERMINATOR 2'S DECK RENDERED MID GREY.  Measured: round 5 authored the
     ground at ~(26,24,33) and `shots/r6_full_south.png` meters it at
     (80,78,79) -- an ART_DK deck faces UP and renders about 3x its authored
     value in this scene.  The two ART_DK decks are now authored in TRUE
     ALBEDO and divided by `DECK_XFER` on the way in, so their hexes can be
     held against the photograph directly.

WHAT I ARGUE WITH.  T2's deck really is bare in every frame that sees it.  I
did not invent a busy graphic for it; it gets structure (chrome-keylined
holster wells, printed blue-left/red-right player bars, the machine's own
chrome shard device) and all of that is declared in `DECK_EVIDENCE` as
extrapolation rather than dressed up as a reading.

WHAT THE INTEGRATOR MUST DO: read `DECKS` instead of round 4's fixed loop, and
honour `SIZE_KEY_REQUEST`.  `HW_HINTS` and `DECK_MAT_REQUEST` are optional and
both say so.

'''
