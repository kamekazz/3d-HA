def _row(v, us, cols, r, h, du=0.0, profile="convex", role=None):
    return [{"u": u + du, "v": v, "r": r, "h": h, "shape": "round",
             "profile": profile, "col": c, "role": role}
            for (u, c) in zip(us, cols)]


def _starts(v, us, r=0.034, h=0.026, col="#e6e9ef"):
    return [{"u": u, "v": v, "r": r, "h": h, "shape": "round",
             "profile": "convex", "col": col, "role": "start"} for u in us]


def _stk(u, v, base_r=0.080, top_col="#16171b", shaft_h=0.155):
    """One joystick.  Every stick in this run is the SAME hardware -- a 35 mm
    ball top on a chromed shaft -- because that is what v4 6 shows on all
    three east machines, and inventing four different sticks to look varied is
    the mistake this round exists to undo."""
    return {"u": u, "v": v, "base_r": base_r, "shaft_r": 0.024,
            "shaft_h": shaft_h, "top": "ball", "top_r": 0.057,
            "top_h": 0.110, "shaft_col": "#b9bec6", "top_col": top_col,
            "finish": "gloss_dark"}


_RED, _GRN, _BLU = "#cc2f26", "#35a84a", "#2a4fd0"
_WHT, _YEL, _ORA = "#eef0f4", "#e8cf28", "#e8801c"
_AMB = "#f0c024"

# ------------------------------------------------------------------- DECKS
# ROUND 7.  The layouts are re-read off ONE photograph that round 5 did not
# use: docs/photos-jpg/Arcade Room v4 6.jpg, which stands close to the north
# end of the east run and looks down onto three of my four control panels at
# once.  Upscaled crops (LANCZOS 11-20x) are in
# scratchpad/arc4/art/ref_g1r7/ -- g1_msh_deck.png, g1_mvc_deck.png,
# g1_mk_deck.png -- and a hue/saturation/value character dump of the Mortal
# Kombat and Marvel vs Capcom crops is what the button counts below come from
# rather than from eyeballing a blur.
#
# FRAME -- UNCHANGED FROM ROUND 5, deliberately, because decks5.py already
# normalises it and ar2.controls() already builds from it:
#
#     u in [-0.5, +0.5]  across the deck art quad's WIDTH  (bw - 0.12 ft),
#                        u = 0 at the cabinet centreline
#     v in [0, 1]        from the deck's BACK edge (z = ft + 0.04, nearest the
#                        screen) to its FRONT edge (z = fd - 0.06)
#     x = u * (bw - 0.12);  z = (ft + 0.04) + v * 0.92;  y = dy + 0.014
#
# ALL LENGTHS IN FEET.  "r" is the cap RADIUS, "h" is how far it stands PROUD
# of the deck art plane.
#
# ------------------------------------------------------------------------
# HOW BIG A BUTTON IS, WITH THE ARITHMETIC, because a critic measured round
# 6's at "2-3px lozenges" and "make them bigger" is not a specification.
#
# WHAT THE HARDWARE IS.  A standard arcade pushbutton plunger is 28 mm across
# (1.10 in) -> r 0.0459 ft.  Its bezel / mounting nut flange is 33-36.5 mm
# (1.30-1.44 in) -> r 0.054-0.060 ft.  It stands 10-13 mm (0.40-0.50 in)
# above the bezel -> h 0.033-0.043 ft.
#
# WHAT THE PHOTOGRAPH GIVES.  In v4 6 the joystick balls and the button caps
# are in the same crop at the same scale, and a ball top is a known 35 mm.
# Measured off g1_mvc_deck.png / g1_mk_deck.png, the caps run 1.17-1.43x the
# ball's diameter, i.e. 41-50 mm (r 0.067-0.082 ft).  That is larger than any
# standard bezel made, and I do not believe it: at 7 px per ball every cap
# carries a specular that bleeds a pixel or more each side.  So THE PHOTOGRAPH
# MEASURES BIGGER THAN WHAT I AM SPECIFYING, and this is the honest statement
# of it -- I have taken the bezel outer, 0.058-0.068 ft, which is 15-20% under
# the photo's own reading and 26-48% over round 6.
#
# WHAT IT RENDERS AT.  Judged pose `full_east`: camera 12.7 ft off the near
# end of the east run and 18.2 ft off the far end, 1400x900 at fov 76, so
# 45.3 px/ft near and 31.6 px/ft far.
#
#     round 6 cap r 0.040-0.048, no printed collar   3.6 - 2.5 px  <- the bug
#     round 7 cap r 0.058-0.068                      5.6 - 3.9 px
#     round 7 cap + its printed collar (1.34x)       7.4 - 5.2 px
#     round 7 collar + contact shadow (1.70x)        9.4 - 6.6 px
#
# and h 0.034-0.040 ft is 1.5-1.8 px of relief on the near machines, which is
# what puts a lit crown and a shaded flank on a 6 px disc.  Both halves are
# needed: the geometry gives the dome and the specular, `_collar` gives the
# rim shadow, and neither alone answers the critics' sentence.
#
# SPACING, DECLARED AS A DEPARTURE.  Real button pitch is 36 mm centre to
# centre (0.118 ft) -- bezels touch.  At my collar size 0.118 ft would make
# the PRINTED collars overlap and the cluster would read as one lozenge
# again, which is the defect.  So pitch runs 0.139-0.202 ft, 18-70% wider
# than the real hardware.  That is a legibility decision and it is the one
# place in this spec where I have knowingly moved a dimension off the photo.
#
# ------------------------------------------------------------------------
# WHAT EACH MACHINE HAS, AND WHERE IT COMES FROM.
#
#  mortal-kombat        5 primary in the MK ARC (3 back / 2 front, offset into
#                       the gaps) + 2 blue auxiliaries + 1 start.  NOT a 3x3.
#                       g1_mk_deck.png resolves, in ONE station, a yellow, two
#                       reds and two whites, with two blues visible in colour
#                       that the hue dump loses against the blue field -- so
#                       seven caps plus a white admin oval set well back.  I
#                       lay the five that are the franchise's own panel
#                       (HP / BLOCK / HK over LP / LK) as the arc, and the
#                       remaining two as smaller blue auxiliaries at the back.
#                       Biggest caps of the three fighters (r 0.064).
#  marvel-vs-capcom     8: RED x3 over GREEN x3 over BLUE x2, plus a start.
#                       g1_mvc_deck.png shows three distinct colour bands per
#                       station, in that order front-ward.  The fighting six
#                       are the red and green rows; the blue pair is real and
#                       is built.
#  marvel-super-heroes  6 in the Capcom 2x3, plus a start.  DECLARED CHOICE,
#                       NOT A READING: g1_msh_deck.png resolves this deck's
#                       ARTWORK completely and its caps not at all -- they sit
#                       inside a print carrying the same yellows, greens and
#                       reds.  So the COUNT and the ARRANGEMENT are the real
#                       cabinet's standard Capcom CPS layout and the colours
#                       are the ones the print shows around them.
#  nfl-blitz            3 big in a row + 1 turbo, plus a start.  Blitz's own
#                       panel is three buttons a side and v3 1 px (660,640)-
#                       (780,720) shows a single row of large caps across the
#                       deck, not a fighting cluster.  Biggest caps in the
#                       room (r 0.068) because it is the sports cabinet.
#
# THE TWO CAPCOM MACHINES REALLY ARE ALIKE, AND I AM NOT INVENTING A
# DIFFERENCE.  Marvel Super Heroes and Marvel vs Capcom are both CPS-2
# fighting cabinets and both wear a 3-across cluster on a 2-player deck at
# essentially the same pitch; the photographs show them alike and the brief
# says to say so.  What separates them in the render is (a) the DECK ART --
# MSH's cyan comic collage against MvC's granite laminate, which is the
# largest visual difference between any two decks in this room -- (b) MvC's
# third blue row, which the photo resolves and MSH's does not, and (c) the
# cap colours, warm on MSH and red/green/blue on MvC.  Nothing else.
#
# MATERIALS -- THE ROUND-6 BLOWOUT, WHICH IS PARTLY MY FAULT AND IS FIXED
# HERE.  The integrator flagged that a2kit's shared `a2hw` is roughness 0.42
# so every up-facing cap blows out against the ceiling cans.  Two things:
#   1. Round 5 gave Marvel vs Capcom WHITE ball tops (#f2f3f6).  That is
#      wrong -- g1_mvc_deck.png and g1_mk_deck.png both show BLACK balls with
#      a small specular.  All four of my machines now carry #16171b tops, and
#      that alone removes four white domes from the run.
#   2. Every control below carries a "finish" key naming the material class it
#      wants.  `gloss_dark` and `gloss_col` are roughness 0.26-0.30, NOT
#      a2hw's 0.42: on a convex cap a lower roughness concentrates the
#      highlight into a small bright spot and lets the rest of the dome take
#      its own colour, which is what makes it read as a shiny button; 0.42
#      spreads the environment over the whole crown and it reads as a white
#      blob.  `chrome` is the shaft.  decks5._from_g1 currently drops this
#      key, which is harmless -- it is a request to the engine agent, not a
#      contract, and the geometry is correct without it.
DECKS = {
    # -------------------------------------------------- Marvel Super Heroes
    "marvel-super-heroes": {
        "width_ft": 1.98, "depth_ft": 0.92,
        "note": "6 per player in the Capcom 2x3.  COUNT AND ARRANGEMENT ARE "
                "A DECLARED CHOICE: v4 6 resolves this deck's print and not "
                "its caps.  Colours are the print's own.",
        "sticks": [_stk(-0.400, 0.600, base_r=0.078),
                   _stk(0.042, 0.600, base_r=0.078)],
        "buttons": (
            _row(0.335, (-0.266, -0.186, -0.106), (_YEL, _GRN, _RED),
                 0.058, 0.036) +
            _row(0.545, (-0.256, -0.176, -0.096), (_BLU, _WHT, _ORA),
                 0.058, 0.036) +
            _row(0.335, (0.176, 0.256, 0.336), (_YEL, _GRN, _RED),
                 0.058, 0.036) +
            _row(0.545, (0.186, 0.266, 0.346), (_BLU, _WHT, _ORA),
                 0.058, 0.036) +
            _starts(0.165, (-0.440, -0.010))),
    },
    # ----------------------------------------------------- Marvel vs Capcom
    "marvel-vs-capcom": {
        "width_ft": 2.30, "depth_ft": 0.92,
        "note": "8 per player -- RED x3 over GREEN x3 over BLUE x2 -- read "
                "off g1_mvc_deck.png, which is the clearest control-panel "
                "photograph in the set.  Widest deck of the four.",
        "sticks": [_stk(-0.392, 0.560, base_r=0.082),
                   _stk(0.036, 0.560, base_r=0.082)],
        "buttons": (
            _row(0.330, (-0.252, -0.180, -0.108), (_RED, _RED, _RED),
                 0.060, 0.038) +
            _row(0.520, (-0.244, -0.172, -0.100), (_GRN, _GRN, _GRN),
                 0.060, 0.038) +
            _row(0.710, (-0.208, -0.136), (_BLU, _BLU), 0.052, 0.032) +
            _row(0.330, (0.176, 0.248, 0.320), (_RED, _RED, _RED),
                 0.060, 0.038) +
            _row(0.520, (0.184, 0.256, 0.328), (_GRN, _GRN, _GRN),
                 0.060, 0.038) +
            _row(0.710, (0.220, 0.292), (_BLU, _BLU), 0.052, 0.032) +
            _starts(0.155, (-0.428, -0.006), r=0.036)),
    },
    # -------------------------------------------------------- Mortal Kombat
    "mortal-kombat": {
        "width_ft": 2.04, "depth_ft": 0.92,
        "note": "THE FIVE-BUTTON MK ARC -- 3 back / 2 front offset into the "
                "gaps -- not a 3-over-3 grid, plus the two blue auxiliaries "
                "g1_mk_deck.png shows at the back of the station.  Biggest "
                "caps of the three fighting cabinets.",
        "sticks": [_stk(-0.398, 0.600, base_r=0.076),
                   _stk(0.036, 0.600, base_r=0.076)],
        "buttons": (
            _row(0.330, (-0.268, -0.182, -0.096), (_YEL, _RED, _WHT),
                 0.064, 0.040) +
            _row(0.548, (-0.225, -0.139), (_RED, _BLU), 0.064, 0.040) +
            _row(0.150, (-0.318, -0.256), (_BLU, _BLU), 0.046, 0.030) +
            _row(0.330, (0.166, 0.252, 0.338), (_YEL, _RED, _WHT),
                 0.064, 0.040) +
            _row(0.548, (0.209, 0.295), (_RED, _BLU), 0.064, 0.040) +
            _row(0.150, (0.116, 0.178), (_BLU, _BLU), 0.046, 0.030) +
            _starts(0.150, (-0.408, 0.026))),
    },
    # ------------------------------------------------------------ NFL Blitz
    "nfl-blitz": {
        "width_ft": 2.06, "depth_ft": 0.92,
        "note": "3 big in a row + 1 turbo -- the sports layout, the fewest "
                "and largest caps in the room.  v3 1 shows one row of large "
                "caps across this deck, not a fighting cluster.  The stick "
                "TOP does not resolve in any frame; it is built as a ball to "
                "match its neighbours and that is a declared choice.",
        "sticks": [_stk(-0.406, 0.560, base_r=0.086),
                   _stk(0.064, 0.560, base_r=0.086)],
        "buttons": (
            _row(0.420, (-0.290, -0.192, -0.094), (_BLU, _GRN, _RED),
                 0.068, 0.040) +
            _row(0.690, (-0.192,), (_AMB,), 0.072, 0.042) +
            _row(0.420, (0.180, 0.278, 0.376), (_BLU, _GRN, _RED),
                 0.068, 0.040) +
            _row(0.690, (0.278,), (_AMB,), 0.072, 0.042) +
            _starts(0.205, (-0.446, 0.024), r=0.036)),
    },
}

# The material classes the "finish" keys above ask for, spelled out so the
# engine agent does not have to guess a number.  These are requests against
# a2kit, not something this module can set.
CONTROL_FINISH = {
    "gloss_col": "roughness 0.28, metallic 0.0, emissive = the cap colour at "
                 "0.35 (round 6 uses 0.75, which is why a red cap reads as a "
                 "flat red disc with no shading at all).  For every coloured "
                 "button cap.",
    "gloss_dark": "roughness 0.26, metallic 0.0, NO emissive.  For the black "
                  "ball tops.  This is the one that fixes the flagged "
                  "blowout: at a2hw's 0.42 a ball top gathers the ceiling "
                  "cans over its whole crown; at 0.26 it takes one small "
                  "specular and stays black, which is what v4 6 shows.",
    "gloss_white": "roughness 0.30, metallic 0.0, NO emissive, albedo "
                   "#d8dade rather than #e6e9ef.  For the white start caps "
                   "and any white plunger -- a white cap must not be "
                   "emissive or it blooms, and decks5 already knows that "
                   "(its luma-190 split), but the albedo also wants pulling "
                   "down half a stop under these cans.",
    "chrome": "roughness 0.34, metallic 0.80.  Joystick shafts only.",
}
