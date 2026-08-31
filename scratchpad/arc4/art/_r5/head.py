"""Round-5 printed cabinet artwork, group 1 (four machines).

    Marvel Super Heroes (east 1) / Marvel vs Capcom (east 2) /
    Mortal Kombat (east 3) / NFL Blitz (north 3)

WHY THIS FILE CHANGED SHAPE.  Round 4 gave every machine its own marquee and
that worked.  Below the marquee it did not: three independent critics, judging
separately, wrote down the same defect in the same words -- one flat-black
front panel with the SAME centred grey coin-door rectangle at the same size and
place, and the SAME two-joystick / row-of-flat-squares deck, on every cabinet,
with only the trim colour and a small floated logo to tell them apart.  They
were right; `shots/r4_mq_east.png` shows it plainly.

Round 5 therefore rewrites `.side`, `.front` and `.deck` for all four machines
and KEEPS the marquees (redrawn here in this module's own kernel, same
composition the photographs establish, because the round-4 marquees for Mortal
Kombat, Marvel vs Capcom and NFL Blitz lived in art_g2 / art_g3 and this round
reshuffled which module owns which machine).  Nothing in this file is a recolour
of anything else in this file:

  machine              front ground        coin door                deck
  -------------------  ------------------  -----------------------  ------------
  Marvel Super Heroes  black + teal comic  NONE PROUD -- a flush     dark navy,
                       collage, full type   printed plate low LEFT   6+6, bat-top
  Marvel vs Capcom     charcoal + a royal  ONE small black box,      PALE SILVER,
                       blue riser third     dead centre, cup below   6+6, ball-top
  Mortal Kombat        cracked stone,      ONE WIDE LOW bronze       teal-blue,
                       ember glow           twin door, two cups      6+6 small
  NFL Blitz            black + nebula      TWO near-black doors,     violet
                       haze, chrome badge   upper half, white dots   nebula, 3+1

WHAT THE INTEGRATOR MUST CONSUME
--------------------------------
1.  ``ASPECT[key]`` -- width/height of the real quad the panel is mapped onto,
    computed from ar2.py's own numbers for THESE machines (see the table beside
    it).  Round 4 used one aspect for every machine and stretched most panels;
    a marquee authored square onto a 3.5:1 band is why round 3's marquees read
    as pattern.  Everything here is authored pre-compensated in a frame ``A``
    wide and 1 tall and squeezed into the square atlas tile on the way out.
2.  ``DECKS[slug]`` -- the joystick / button GEOMETRY spec, because ar2.py's
    ``upright()`` places those and this module cannot.  Frame and units are
    documented on the table itself.  The painted button sockets in each `.deck`
    panel are generated FROM this same table by ``_deck_sockets()``, so the
    printed ring and the physical button cannot drift apart.
3.  ``COIN[slug]`` -- the coin-door geometry, same idea: a list (Blitz has two
    doors, Marvel Super Heroes has none) in the `.front` panel's own frame, and
    the plate is painted into the front art at the same coordinates.
4.  ``MATERIAL_HINT[key]`` -- these are true printed albedos.  A deck put
    through ``ART_DK`` (#4c4c4c) loses its colour; see the table.

SOURCE LAYOUT.  ``art_g1.py`` is the file the integrator uses; it is
concatenated from the pieces in ``art/_r5/`` (head / kernel / collage /
helpers / one file per machine / tables) by

    cat _r5/head.py _r5/kernel.py _r5/collage.py _r5/helpers.py         _r5/m_msh.py _r5/m_mvc.py _r5/m_mk.py _r5/m_blitz.py         _r5/tables.py > art_g1.py

If you edit art_g1.py directly, delete ``_r5/`` so nobody regenerates over
your change.  ``_r5/art_g1_r4.bak.py`` is round 4's module, kept only so
``bytes_g1_r5.py`` can measure the delta.

Self-checks: ``preview_g1_r5.py`` -> wrap_g1.png (every panel at ship
resolution, assembled as a front elevation and a flank at real feet),
``compare_g1_r5.py`` -> compare_g1_r5.png (those beside the owner's crops),
``bytes_g1_r5.py`` -> the payload table.

Pure stdlib.  ``paint(px, ox, oy, tile)`` writes ``px[y][x] = (r, g, b)`` into
the square (ox, oy)-(ox+tile, oy+tile), with a 4x4 ordered dither and
round-to-8 quantisation so the shared PNG stays small.
"""
