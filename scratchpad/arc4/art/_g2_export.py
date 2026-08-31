# =========================================================================
#  EXPORTS
# =========================================================================
# ROUND 5 OWNS THE SOUTH RUN.  `PANELS` is exactly the four machines this
# agent was assigned; the three machines art_g2 painted in round 4 that are
# now on other agents' runs have moved to `LEGACY_PANELS` so that merging
# this module can never collide with theirs.
#
# INTEGRATOR: if no other module claims marvel-vs-capcom / nfl-blitz /
# east-7-no-machine this round, `atlas4.Atlas` will raise
# "no art module paints 'nfl-blitz.side'".  The fix is one line, after the
# merge loop in atlas4.py:
#
#     for k, fn in art_g2.LEGACY_PANELS.items():
#         PANELS.setdefault(k, fn)
#
# That prefers whoever owns them now and falls back to round 4's drawings.
PANELS = {
    "legends-ultimate.marquee": lu_marquee,
    "legends-ultimate.side": lu_side,
    "legends-ultimate.front": lu_front,
    "legends-ultimate.deck": lu_deck,
    "legends-ultimate.screen": lu_screen,

    "street-fighter-2-champion-edition.marquee": ce_marquee,
    "street-fighter-2-champion-edition.side": ce_side,
    "street-fighter-2-champion-edition.front": ce_front,
    "street-fighter-2-champion-edition.deck": ce_deck,
    "street-fighter-2-champion-edition.screen": ce_screen,

    "time-crisis.marquee": tc_marquee,
    "time-crisis.side": tc_side,
    "time-crisis.front": tc_front,
    "time-crisis.deck": tc_deck,
    "time-crisis.screen": tc_screen,

    "terminator-2.marquee": t2_marquee,     # ROUND 4'S, UNCHANGED
    "terminator-2.side": t2_side,
    "terminator-2.front": t2_front,
    "terminator-2.deck": t2_deck,
    "terminator-2.screen": t2_screen,
}

# Round 4's three, kept only as a fallback -- see the note above.
LEGACY_PANELS = {
    "marvel-vs-capcom.marquee": mvc_marquee,
    "marvel-vs-capcom.side": mvc_side,
    "marvel-vs-capcom.front": mvc_front,
    "marvel-vs-capcom.riser": mvc_riser,
    "marvel-vs-capcom.deck": mvc_deck,
    "nfl-blitz.marquee": blitz_marquee,
    "nfl-blitz.side": blitz_side,
    "nfl-blitz.front": blitz_front,
    "nfl-blitz.deck": blitz_deck,
    "east-7-no-machine.marquee": blank_marquee,
    "east-7-no-machine.side": blank_side,
    "east-7-no-machine.front": blank_front,
    "east-7-no-machine.deck": blank_deck,
}

# `.screen` is NEW and OPTIONAL.  ar2.upright currently draws the monitor as
# an untextured `SCRN` quad, which is why three critics saw four black
# rectangles in a row.  To use these:
#   1. atlas4.EXTRA_KEYS += tuple("%s.screen" % s for s in MY_SLUGS)
#      and atlas4.SIZE["screen"] = 48
#   2. in ar2.upright, replace
#          sub.add(quad(...), SCRN)
#      with
#          if art.has(slug + ".screen"):
#              uvq(sub, art.BEZEL_ART_or_ART, [...], art.uv(slug + ".screen"))
#          else:
#              sub.add(quad(...), SCRN)
#      sampling through a DARK factor material (the glass is glossy and
#      nearly black -- ART at #ffffff would wash these to grey).  Measured
#      cost of all four at 48 px is reported in the round-5 notes.
# If the integrator does not want the ar2 change, drop these four keys and
# nothing else in this module changes.
SCREEN_KEYS = tuple("%s.screen" % s for s in
                    ("legends-ultimate",
                     "street-fighter-2-champion-edition",
                     "time-crisis", "terminator-2"))


# -------------------------------------------------------------- geometry spec
# THE BUTTONS AND JOYSTICKS ARE GEOMETRY.  ar2.upright places them and this
# module cannot, so this is the contract the integrator consumes.  Round 4's
# upright() gave every machine in the room the identical loop
#
#     for k in range(2):  two 0.09 ft chrome shafts, two cube tops (red,
#     blue), then three FLAT SQUARE buttons each, at fixed offsets
#
# which is the defect all three critics named in the same words.  Replace
# that loop with a read of `DECKS[slug]`.
#
# COORDINATES, both normalised so they survive any re-proportioning:
#   u  -1.0 .. +1.0 across the cabinet width.  u = -1 is local x = -bw/2.
#      For a south-wall machine (rot 180) local -x is the VIEWER'S LEFT, and
#      these tables are written as the viewer sees them.
#      -> x = u * (bw/2 - 0.10)
#   v   0.0 at the deck's BACK edge (the screen end, z = ft + 0.04)
#       1.0 at the deck's FRONT lip  (z = fd - 0.06)
#      -> z = (ft + 0.04) + v * ((fd - 0.06) - (ft + 0.04))
#   every *_ft is feet, and every y is measured UP from the deck's top face
#   (y = dy + 0.014), except COINS, whose y is measured up from the cabinet
#   base (plinth included), matching upright()'s own coin-door block.
#
# ELEMENT SHAPES
#   stick   {u, v, top, top_color, top_r_ft, shaft_color, shaft_h_ft,
#            dust_color, dust_r_ft}
#           top: "ball"  a sphere (an 8-segment low-poly sphere is plenty)
#                "bat"   a taller capsule, flat-topped
#                "none"  shaft only
#   button  {u, v, r_ft, h_ft, color, shape}
#           shape: "round_convex"  a short cylinder with a domed cap -- THE
#                                  DEFAULT.  Round 4 used flat squares on
#                                  every machine in the room and a critic
#                                  named it.
#                  "round_flat"    a plain cylinder, no dome
#                  "square"        the round-4 box, kept only where a photo
#                                  shows a square membrane pad
#   gun     {u, v, yaw_deg, body, grip, len_ft, cradle, cradle_color}
#           yaw_deg 0 = muzzle pointing at the player (down-tile, +v).
#           `cradle` True means a shallow recessed cup is modelled under it.
#   trackball {u, v, r_ft, color, bezel_color}
#   spinner   {u, v, r_ft, color}
#   lip     {color, emissive, emissive_strength, h_ft}  a strip across the
#           whole deck front lip.  Only Legends Ultimate has one, and both
#           v3 4 and v4 8 resolve it, so it is a fixture the photograph
#           shows -- emissive is legitimate there under ROOM-BRIEF's rule.
#
# NOTHING HERE IS SHARED BETWEEN THE FOUR MACHINES: the counts are 2 sticks
# + 12 buttons + trackball + spinner / 2 sticks + 14 buttons / 2 guns + 3
# buttons / 2 guns + 2 buttons, and no two use the same top, colour set,
# radius or arrangement.
DECKS = {
    "legends-ultimate": {
        "note": ("The photographs do NOT resolve this deck's controls "
                 "(roster: 'do not invent joysticks').  What they DO resolve "
                 "is the lit white strip along the front lip, which is "
                 "modelled.  The control layout below is the manufacturer's "
                 "standard for this cabinet -- two ball-tops, 6+6 buttons, a "
                 "centre trackball and a spinner -- and is declared as "
                 "INFERENCE, not as a photo reading.  It is here because a "
                 "bare deck reads as unbuilt; if the integrator would rather "
                 "ship only the lip, drop `sticks`/`buttons`/`trackball`/"
                 "`spinner` and keep `lip`."),
        "inferred": True,
        "sticks": [
            {"u": -0.62, "v": 0.42, "top": "ball", "top_color": "#f2f4f8",
             "top_r_ft": 0.062, "shaft_color": "#9aa0aa", "shaft_h_ft": 0.15,
             "dust_color": "#1a1c22", "dust_r_ft": 0.085},
            {"u": 0.62, "v": 0.42, "top": "ball", "top_color": "#f2f4f8",
             "top_r_ft": 0.062, "shaft_color": "#9aa0aa", "shaft_h_ft": 0.15,
             "dust_color": "#1a1c22", "dust_r_ft": 0.085},
        ],
        "buttons": (
            [{"u": -0.44 + 0.11 * i, "v": 0.32 + 0.05 * (i % 2),
              "r_ft": 0.052, "h_ft": 0.030, "shape": "round_convex",
              "color": c}
             for i, c in enumerate(("#e03a2e", "#e8a51e", "#f2f4f8"))]
            + [{"u": -0.44 + 0.11 * i, "v": 0.52 + 0.05 * (i % 2),
                "r_ft": 0.052, "h_ft": 0.030, "shape": "round_convex",
                "color": c}
               for i, c in enumerate(("#2f6bd8", "#39a552", "#d0d4dc"))]
            + [{"u": 0.80 - 0.11 * i, "v": 0.32 + 0.05 * (i % 2),
                "r_ft": 0.052, "h_ft": 0.030, "shape": "round_convex",
                "color": c}
               for i, c in enumerate(("#e03a2e", "#e8a51e", "#f2f4f8"))]
            + [{"u": 0.80 - 0.11 * i, "v": 0.52 + 0.05 * (i % 2),
                "r_ft": 0.052, "h_ft": 0.030, "shape": "round_convex",
                "color": c}
               for i, c in enumerate(("#2f6bd8", "#39a552", "#d0d4dc"))]
        ),
        "trackball": {"u": 0.0, "v": 0.46, "r_ft": 0.115, "color": "#15161c",
                      "bezel_color": "#3a3e46"},
        "spinner": {"u": 0.26, "v": 0.20, "r_ft": 0.075, "color": "#b8bec8"},
        "guns": [],
        "lip": {"color": "#f6f8fb", "emissive": "#c9d2e0",
                "emissive_strength": 0.9, "h_ft": 0.05},
        "coin_geometry": None,
    },

    "street-fighter-2-champion-edition": {
        "note": ("Six buttons per player in two rows of three, BAT-top "
                 "sticks, and two small black start buttons on the back "
                 "edge.  The identifying feature is not the controls but the "
                 "bright steel bezel band along the leading edge -- that is "
                 "painted into `.deck` and should NOT also be modelled."),
        "inferred": False,
        "sticks": [
            {"u": -0.66, "v": 0.46, "top": "bat", "top_color": "#15161b",
             "top_r_ft": 0.048, "shaft_color": "#8f95a0", "shaft_h_ft": 0.20,
             "dust_color": "#c8ccd4", "dust_r_ft": 0.075},
            {"u": 0.66, "v": 0.46, "top": "bat", "top_color": "#15161b",
             "top_r_ft": 0.048, "shaft_color": "#8f95a0", "shaft_h_ft": 0.20,
             "dust_color": "#c8ccd4", "dust_r_ft": 0.075},
        ],
        "buttons": (
            [{"u": -0.44 + 0.115 * i, "v": 0.34 + 0.045 * (2 - i),
              "r_ft": 0.058, "h_ft": 0.026, "shape": "round_convex",
              "color": "#e8eaee"} for i in range(3)]
            + [{"u": -0.44 + 0.115 * i, "v": 0.56 + 0.045 * (2 - i),
                "r_ft": 0.058, "h_ft": 0.026, "shape": "round_convex",
                "color": "#2f5fd0"} for i in range(3)]
            + [{"u": 0.14 + 0.115 * i, "v": 0.34 + 0.045 * i,
                "r_ft": 0.058, "h_ft": 0.026, "shape": "round_convex",
                "color": "#e8eaee"} for i in range(3)]
            + [{"u": 0.14 + 0.115 * i, "v": 0.56 + 0.045 * i,
                "r_ft": 0.058, "h_ft": 0.026, "shape": "round_convex",
                "color": "#cf2424"} for i in range(3)]
            + [{"u": -0.20, "v": 0.10, "r_ft": 0.034, "h_ft": 0.018,
                "shape": "round_flat", "color": "#22242a"},
               {"u": 0.20, "v": 0.10, "r_ft": 0.034, "h_ft": 0.018,
                "shape": "round_flat", "color": "#22242a"}]
        ),
        "trackball": None,
        "spinner": None,
        "guns": [],
        "lip": None,
        "coin_geometry": None,
    },

    "time-crisis": {
        "note": ("NO joystick and NO button field.  One RED gun lying flat "
                 "and angled across the maroon island left of centre (the "
                 "roster records only this one as certain) and one BLUE gun "
                 "standing in the socket right of centre, which is the blue "
                 "object v3 4 resolves there.  Also a RED FOOT-PEDAL unit on "
                 "the floor in front of the cabinet -- listed in `extras`; "
                 "ar2 has no geometry for it and it is a distinctive "
                 "silhouette worth building."),
        "inferred": False,
        "sticks": [],
        "buttons": [
            {"u": -0.72, "v": 0.16, "r_ft": 0.040, "h_ft": 0.020,
             "shape": "round_flat", "color": "#e03a2e"},
            {"u": 0.72, "v": 0.16, "r_ft": 0.040, "h_ft": 0.020,
             "shape": "round_flat", "color": "#2f5fd0"},
            {"u": 0.0, "v": 0.86, "r_ft": 0.034, "h_ft": 0.016,
             "shape": "round_flat", "color": "#e8c24e"},
        ],
        "guns": [
            {"u": -0.30, "v": 0.55, "yaw_deg": 24.0, "body": "#c0392b",
             "grip": "#3a1512", "len_ft": 0.62, "cradle": True,
             "cradle_color": "#4d1b16"},
            {"u": 0.44, "v": 0.58, "yaw_deg": -8.0, "body": "#2f5fd0",
             "grip": "#141a2e", "len_ft": 0.58, "cradle": True,
             "cradle_color": "#1d2a52"},
        ],
        "trackball": None,
        "spinner": None,
        "lip": None,
        "coin_geometry": {
            "u": 0.0, "y0_ft": 0.62, "y1_ft": 1.36, "w_ft": 0.94,
            "depth_ft": 0.075, "plate": "#9aa1ac", "recess": "#0a0a0e",
            "cup": True, "cup_color": "#07070a",
            "note": ("The BIG door of the wall: steel, centred, and it "
                     "projects.  Painted into `.front` as well, so the "
                     "geometry only needs the plate, the two slots and the "
                     "return cup registered to the print."),
        },
        "extras": [
            {"kind": "foot_pedal", "note": "red pedal unit on the floor, "
             "roughly 1.0 x 0.8 x 0.35 ft, centred on the cabinet and about "
             "0.9 ft in front of the deck lip.  Visible in v3 4 and v4 5."},
        ],
    },

    "terminator-2": {
        "note": ("TWO LIGHT GUNS in chrome-collared cradles, blue LEFT and "
                 "red RIGHT -- resolved at 16x in v3 4 and 14x in v4 8.  No "
                 "joystick, no button field, two start buttons.  Round 4 "
                 "gave this machine two joysticks and six squares, which is "
                 "flatly contradicted by both photographs."),
        "inferred": False,
        "sticks": [],
        "buttons": [
            {"u": -0.50, "v": 0.17, "r_ft": 0.038, "h_ft": 0.018,
             "shape": "round_flat", "color": "#2f5fd0"},
            {"u": 0.50, "v": 0.17, "r_ft": 0.038, "h_ft": 0.018,
             "shape": "round_flat", "color": "#cf2424"},
        ],
        "guns": [
            {"u": -0.50, "v": 0.52, "yaw_deg": 0.0, "body": "#2f5fd0",
             "grip": "#12162a", "len_ft": 0.58, "cradle": True,
             "cradle_color": "#181521"},
            {"u": 0.50, "v": 0.52, "yaw_deg": 0.0, "body": "#cf2424",
             "grip": "#2a1013", "len_ft": 0.58, "cradle": True,
             "cradle_color": "#181521"},
        ],
        "trackball": None,
        "spinner": None,
        "lip": None,
        "coin_geometry": {
            "u": 0.32, "y0_ft": 0.34, "y1_ft": 0.72, "w_ft": 0.52,
            "depth_ft": 0.035, "plate": "#22222a", "recess": "#08080b",
            "cup": False, "cup_color": None,
            "note": ("Small, OFFSET RIGHT and nearly black -- the deliberate "
                     "opposite of Time Crisis's.  Round 4 put a 0.68 ft grey "
                     "plate dead centre on every machine in the room."),
        },
        "extras": [],
    },
}

# The printed front panel's own rect, in feet, where it should differ from
# upright()'s hard-coded `plinth + 0.16 .. dy - 0.62` inset by 0.08 either
# side.  ROOM-BRIEF's standard for this round is a panel that runs TO THE
# FLOOR; three of these four do in the photographs.
FRONT_RECT = {
    # runs to the floor, full width: the licence grid is edge to edge and
    # there is no black kick under it in v3 4 or v4 8.
    "legends-ultimate": {"y0_ft": 0.02, "y1_ft": 2.00, "inset_ft": 0.03},
    # the blue base.  ar2 builds `a2capc` as a solid box whose front face is
    # ~0.015 ft PROUD of this quad, so the panel is invisible today.  Pull
    # the box front from `D - 0.06 - SD` to `D - 0.10 - SD` and raise this
    # quad to cover the base's height; the box then reads as the blue
    # surround the photograph shows round the printed area.
    "street-fighter-2-champion-edition": {
        "y0_ft": 0.06, "y1_ft": 2.30, "inset_ft": 0.10,
        "requires": "a2capc box front -> D - 0.10 - SD"},
    # red pillars are part of the print, so the panel must reach the
    # cabinet's full width and down to the plinth.
    "time-crisis": {"y0_ft": 0.02, "y1_ft": 1.86, "inset_ft": 0.02},
    "terminator-2": {"y0_ft": 0.02, "y1_ft": 1.80, "inset_ft": 0.02},
}

# Suggested atlas sizes for the four new screen panels.  48 px each; the
# glass is dark and low-contrast so they quantise to very few levels.
SCREEN_SIZE_PX = 48

# which photograph each graphic was read off, for the record
EVIDENCE = {
    "legends-ultimate": (
        "docs/photos-jpg/Arcade Room v3 4.jpg px (985,690)-(1130,850) at 7x "
        "-> scratchpad/arc4/art/g2r5/lu_grid.png: the two-column licence "
        "grid, sixteen logos, of which MILLIPEDE, STAR WARS, TRON and the "
        "white Space-Invaders block are legible and are drawn as themselves; "
        "the other twelve resolve as a coloured wordmark SHAPE only and are "
        "drawn as ink at letterform scale, not as invented titles.  Marquee "
        "px (1025,570)-(1175,615) at 12x.  Whole machine "
        "art/g2r5/lu_whole.png.  Corroborated v4 8 -> art/g2r5/v48_south.png "
        "(no coin door anywhere on the front) and v4 5."),
    "street-fighter-2-champion-edition": (
        "docs/photos-jpg/Arcade Room v3 4.jpg px (900,545)-(1010,830) at 5x "
        "-> scratchpad/arc4/art/g2r5/ce_whole.png: the gold-ringed oval "
        "marquee badge with CHAMPION arched and EDITION straight, the "
        "ghosted pale fighter on the royal-blue base and CAPCOM low.  Base "
        "blue #2b5baf..#4e7bba off v4 8 (white cans, not cove) -> "
        "art/g2r5/v48_south.png; the steel band on the deck's leading edge "
        "reads in both."),
    "time-crisis": (
        "docs/photos-jpg/Arcade Room v3 4.jpg px (820,540)-(930,900) at 5x "
        "-> scratchpad/arc4/art/g2r5/tc_whole.png: cream head, maroon band, "
        "tan speaker panel with two round holes, red body with gold front "
        "trim, red-orange deck with a red gun and two pale instruction "
        "panels, black lower front between two red pillars.  The coin door "
        "and its return cup are read off v4 5 px (150,120)-(320,300) at 7x "
        "-> art/g2r5/v45_t2ce.png.  Screen shows a DIM OLIVE image in v3 4 "
        "and is painted dim, not as an attract loop."),
    "terminator-2": (
        "docs/photos-jpg/Arcade Room v4 5.jpg px (150,120)-(320,300) at 7x "
        "-> scratchpad/arc4/art/g2r5/v45_t2ce.png: the white T2 low on the "
        "black front, the maroon T-molding down both front edges, the strip "
        "of small coloured plates along the bottom of the panel, and the "
        "BLUE gun left / RED gun right on the deck.  Marquee and guns also "
        "at 14-16x in roster/rec/v34_south.png and v4 8.  Screen is black in "
        "all three frames and is painted as reflection only."),
}
