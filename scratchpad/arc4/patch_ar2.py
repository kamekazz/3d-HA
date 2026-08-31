# -*- coding: utf-8 -*-
"""Round 4: wire ar2.py's cabinets to per-machine artwork.

Geometry is untouched.  Every z/x position, width, height, deck height, marquee
depth, plinth and profile style in the three run tables is carried across
verbatim; only the three artwork columns (`art`, `front art`, `marquee`) are
replaced, by the machine's roster slug.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "bsmt", "ar2.py")
s = io.open(P, encoding="utf-8").read()


def sub1(old, new):
    global s
    if s.count(old) != 1:
        raise SystemExit("pattern %d times, expected 1:\n%r" %
                         (s.count(old), old[:120]))
    s = s.replace(old, new)


# ------------------------------------------------------------------ imports
sub1("""from a2kit import (         # noqa: F401  -- round-3 texture + sweep helpers
    ART, ART_B, ART_D, ART_DK, ART_TEX, MQ_MATS, sweep, uvq, uvr, uvblit,
    noise_tex)""",
     """from a2kit import (         # noqa: F401  -- texture + sweep helpers
    ArtSet, sweep, uvq, uvblit, noise_tex)
from atlas4 import EAST_SLUGS, SOUTH_SLUGS, NORTH_SLUGS   # noqa: E402""")


# --------------------------------------------------------- upright() header
sub1('''def upright(m, cx, cz, rot, art_i, bw=2.20, bd=2.55, top=6.10, seed=1,
            style="straight", dy=2.52, mqh=0.62, mq_i=0, art_f=None,
            plinth=0.0):
    """One arcade cabinet, authored facing +z then spun by `rot` degrees."""
    sub = Model()
    rnd = Rnd(seed)
    prof, (fb, fd, ft, mq_lo, mq_hi, dy) = _profile(bd, top, style, dy, mqh, seed)
    x0, x1 = -bw / 2.0, bw / 2.0
    art_f = art_i if art_f is None else art_f
''',
     '''def upright(m, cx, cz, rot, art, slug, bw=2.20, bd=2.55, top=6.10, seed=1,
            style="straight", dy=2.52, mqh=0.62, plinth=0.0):
    """One arcade cabinet, authored facing +z then spun by `rot` degrees.

    `art` is the wall run's `a2kit.ArtSet` and `slug` names the machine in the
    round-4 roster.  Round 3 passed three integer indices into a shared 12-tile
    atlas here (`art_i` for both flanks, `art_f` for the front panel AND the
    control deck AND the screen bezel, `mq_i` for one of four pastel marquees),
    which is how sixteen cabinets ended up wearing four graphics between them.
    Now every surface takes its own panel: `<slug>.side`, `<slug>.front`,
    `<slug>.deck`, `<slug>.marquee`, and `<slug>.bezel` where the machine's art
    module authored one.
    """
    sub = Model()
    rnd = Rnd(seed)
    prof, (fb, fd, ft, mq_lo, mq_hi, dy) = _profile(bd, top, style, dy, mqh, seed)
    x0, x1 = -bw / 2.0, bw / 2.0
''')

sub1("    sweep(sub, prof, x0, x1, ART, CABBLK, uvr(art_i))",
     '    sweep(sub, prof, x0, x1, art.ART, CABBLK, art.uv(slug + ".side"))')

sub1('''    uvq(sub, ART, [(x0 + 0.08, plinth + 0.16, zf), (x1 - 0.08, plinth + 0.16, zf),
                   (x1 - 0.08, dy - 0.62, zf), (x0 + 0.08, dy - 0.62, zf)],
        uvr(art_f))''',
     '''    uvq(sub, art.ART,
        [(x0 + 0.08, plinth + 0.16, zf), (x1 - 0.08, plinth + 0.16, zf),
         (x1 - 0.08, dy - 0.62, zf), (x0 + 0.08, dy - 0.62, zf)],
        art.uv(slug + ".front"))''')

# the control deck.  `flip=True` mirrored the tile left-right, which was
# harmless when the deck art was an abstract motif and is NOT now: NBA Jam's
# logo lies on its boards, Golden Tee's deck legend is three words, Mortal
# Kombat's carries its wordmark.  Unflipped, tile-top maps to the deck's BACK
# edge and u0 to the player's left, which is how all four modules authored it.
sub1('''    uvq(sub, ART_DK, [(x0 + 0.06, dy + 0.014, fd - 0.06),
                      (x1 - 0.06, dy + 0.014, fd - 0.06),
                      (x1 - 0.06, dy + 0.014, ft + 0.04),
                      (x0 + 0.06, dy + 0.014, ft + 0.04)], uvr(art_f), flip=True)''',
     '''    uvq(sub, art.deck(slug), [(x0 + 0.06, dy + 0.014, fd - 0.06),
                              (x1 - 0.06, dy + 0.014, fd - 0.06),
                              (x1 - 0.06, dy + 0.014, ft + 0.04),
                              (x0 + 0.06, dy + 0.014, ft + 0.04)],
        art.uv(slug + ".deck"))''')

sub1('''    uvq(sub, ART_B, [(x0 + 0.05, yb0, zb0), (x1 - 0.05, yb0, zb0),
                     (x1 - 0.05, yb1, zb1), (x0 + 0.05, yb1, zb1)], uvr(art_f))''',
     '''    bez = [(x0 + 0.05, yb0, zb0), (x1 - 0.05, yb0, zb0),
           (x1 - 0.05, yb1, zb1), (x0 + 0.05, yb1, zb1)]
    if art.has(slug + ".bezel"):
        uvq(sub, art.ART, bez, art.uv(slug + ".bezel"))
    else:
        sub.add(quad(*bez), art.BEZEL)''')

sub1('''    uvq(sub, MQ_MATS[mq_i % 4],
        [(x0 + 0.06, mq_lo, mz), (x1 - 0.06, mq_lo, mz),
         (x1 - 0.06, mq_hi, mz), (x0 + 0.06, mq_hi, mz)],
        uvr(12 + (mq_i + 1) % 4))''',
     '''    uvq(sub, art.marquee(slug),
        [(x0 + 0.06, mq_lo, mz), (x1 - 0.06, mq_lo, mz),
         (x1 - 0.06, mq_hi, mz), (x0 + 0.06, mq_hi, mz)],
        art.uv(slug + ".marquee"))''')


# --------------------------------------------------------------- run tables
sub1('''EAST_RUN = [
    # (z, bw, top, style, dy, mqh, art, front art, marquee, plinth)
    (2.85, 2.34, 6.28, "slope",    2.56, 0.70, 0, 6, 0, 0.00),
    (5.11, 2.10, 5.86, "straight", 2.44, 0.55, 1, 9, 1, 0.10),
    (7.37, 2.42, 6.34, "riser",    2.60, 0.76, 2, 4, 2, 0.00),
    (9.63, 2.16, 5.98, "step",     2.48, 0.58, 3, 8, 3, 0.14),
    (11.89, 2.30, 6.22, "slope",   2.54, 0.66, 4, 1, 0, 0.00),
    (14.15, 2.04, 5.78, "straight", 2.40, 0.52, 5, 11, 2, 0.08),
    (16.41, 2.38, 6.16, "riser",   2.58, 0.72, 6, 3, 1, 0.00),
]

SOUTH_RUN = [
    (2.05, 2.95, 6.36, "step",     2.62, 0.80, 7, 2, 3, 0.00),
    (4.95, 2.42, 6.02, "straight", 2.46, 0.58, 8, 5, 0, 0.00),
    (7.55, 2.52, 6.24, "slope",    2.56, 0.68, 9, 0, 1, 0.12),
    (10.05, 2.28, 5.92, "riser",   2.42, 0.60, 10, 7, 2, 0.00),
]

NORTH_RUN = [
    (6.55, 2.44, 6.20, "slope",    2.56, 0.72, 5, 9, 2, 0.00),
    (9.00, 2.28, 6.34, "straight", 2.50, 0.64, 8, 8, 0, 0.10),
    (11.30, 2.18, 6.02, "riser",   2.44, 0.56, 1, 3, 3, 0.00),
    (13.55, 2.32, 6.26, "step",    2.54, 0.68, 11, 2, 1, 0.06),
]''',
     '''# ROUND 4: the three integer artwork columns are replaced by the machine's
# roster slug, and NOTHING else in these tables moved -- every z/x, width,
# height, deck height, marquee depth, plinth and profile style is round 3's.
# The order is the order the photographs establish, run by run: the east wall
# reads north to south, the south wall west to east, the north wall west to
# east.  EAST_RUN[6] is the slot the roster found EMPTY in all four frames that
# see the whole run; the geometry is kept (this round changed artwork, not
# layout) and it is dressed as an honest unbranded black upright with no
# licensed graphic rather than given an invented title.
EAST_RUN = [
    # (z, bw, top, style, dy, mqh, slug, plinth)
    (2.85, 2.34, 6.28, "slope",    2.56, 0.70, "star-wars-atari", 0.00),
    (5.11, 2.10, 5.86, "straight", 2.44, 0.55, "marvel-super-heroes", 0.10),
    (7.37, 2.42, 6.34, "riser",    2.60, 0.76, "marvel-vs-capcom", 0.00),
    (9.63, 2.16, 5.98, "step",     2.48, 0.58, "mortal-kombat", 0.14),
    (11.89, 2.30, 6.22, "slope",   2.54, 0.66, "nba-jam", 0.00),
    (14.15, 2.04, 5.78, "straight", 2.40, 0.52, "tmnt-turtles-in-time", 0.08),
    (16.41, 2.38, 6.16, "riser",   2.58, 0.72, "east-7-no-machine", 0.00),
]

SOUTH_RUN = [
    (2.05, 2.95, 6.36, "step",     2.62, 0.80, "legends-ultimate", 0.00),
    (4.95, 2.42, 6.02, "straight", 2.46, 0.58,
     "street-fighter-2-champion-edition", 0.00),
    (7.55, 2.52, 6.24, "slope",    2.56, 0.68, "time-crisis", 0.12),
    (10.05, 2.28, 5.92, "riser",   2.42, 0.60, "terminator-2", 0.00),
]

NORTH_RUN = [
    (6.55, 2.44, 6.20, "slope",    2.56, 0.72,
     "north-1-graffiti-multicade", 0.00),
    (9.00, 2.28, 6.34, "straight", 2.50, 0.64, "pac-man", 0.10),
    (11.30, 2.18, 6.02, "riser",   2.44, 0.56, "nfl-blitz", 0.00),
    (13.55, 2.32, 6.26, "step",    2.54, 0.68, "golden-tee-3d-golf", 0.06),
]''')


# --------------------------------------------------------------- east build
sub1('''    for i, (z, bw, top, st, dy, mqh, ai, af, mi, pl) in enumerate(EAST_RUN):
        upright(m, W - 1.32, z, 270, ai, bw=bw, bd=2.55, top=top, seed=i + 1,
                style=st, dy=dy, mqh=mqh, mq_i=mi, art_f=af, plinth=pl)''',
     '''    art = ArtSet("east", EAST_SLUGS)
    for i, (z, bw, top, st, dy, mqh, slug, pl) in enumerate(EAST_RUN):
        upright(m, W - 1.32, z, 270, art, slug, bw=bw, bd=2.55, top=top,
                seed=i + 1, style=st, dy=dy, mqh=mqh, plinth=pl)''')

# --------------------------------------------------------------- south build
sub1('''    for (cx, bw, top, st, dy, mqh, ai, af, mi, pl) in SOUTH_RUN:
        upright(m, cx, D - 1.32 - SD, 180, ai, bw=bw, bd=2.55, top=top,
                seed=int(cx * 7), style=st, dy=dy, mqh=mqh, mq_i=mi,
                art_f=af, plinth=pl)''',
     '''    art = ArtSet("south", SOUTH_SLUGS)
    for (cx, bw, top, st, dy, mqh, slug, pl) in SOUTH_RUN:
        upright(m, cx, D - 1.32 - SD, 180, art, slug, bw=bw, bd=2.55, top=top,
                seed=int(cx * 7), style=st, dy=dy, mqh=mqh, plinth=pl)''')

sub1('''    upright(m, 1.32, 21.55, 90, 10, bw=2.42, bd=2.55, top=6.06, seed=77,
            style="step", dy=2.58, mqh=0.66, mq_i=3, art_f=1)''',
     '''    upright(m, 1.32, 21.55, 90, art, "ridge-racer", bw=2.42, bd=2.55,
            top=6.06, seed=77, style="step", dy=2.58, mqh=0.66)''')

# --------------------------------------------------------------- north build
sub1('''    for (cx, bw, top, st, dy, mqh, ai, af, mi, pl) in NORTH_RUN:
        upright(m, cx, 1.32, 0, ai, bw=bw, bd=2.55, top=top,
                seed=int(cx * 11), style=st, dy=dy, mqh=mqh, mq_i=mi,
                art_f=af, plinth=pl)''',
     '''    art = ArtSet("north", NORTH_SLUGS)
    for (cx, bw, top, st, dy, mqh, slug, pl) in NORTH_RUN:
        upright(m, cx, 1.32, 0, art, slug, bw=bw, bd=2.55, top=top,
                seed=int(cx * 11), style=st, dy=dy, mqh=mqh, plinth=pl)''')

# ---- the lit display case's collectible boxes, NE corner.  Round 3 gave them
# tiles 0-11 of the old motif atlas.  They are 0.35 x 0.58 ft boxes seen from
# across the room, so what they need is varied printed colour, not identity;
# they now take a rotation of the north run's own panels.  Declared, because a
# critic is entitled to know these are cabinet art re-used at box scale.
sub1('''                uvr((s * 6 + k) % 12))''',
     '''                art.uv(BOX_ART[(s * 6 + k) % len(BOX_ART)]))''')

sub1('''def build_north_cabs():''',
     '''BOX_ART = ["pac-man.front", "nfl-blitz.side", "golden-tee-3d-golf.deck",
           "north-1-graffiti-multicade.side", "nfl-blitz.deck",
           "pac-man.side", "golden-tee-3d-golf.side",
           "north-1-graffiti-multicade.deck"]


def build_north_cabs():''')

io.open(P, "w", encoding="utf-8").write(s)
print("patched", P)
