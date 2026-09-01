# -*- coding: utf-8 -*-
"""Append the round-7 payload accounting to the geometry-spec block."""
import io
import os

Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_r7_spec.py")
s = io.open(Q, encoding="utf-8").read()
if "SIZE_KEY_REQUEST" in s:
    raise SystemExit("already applied")

ANCH = "# Which photograph each DECK graphic was read off"
assert ANCH in s

BLOCK = '''# ----------------------------------------------------------------- payload
# WHAT ROUND 7 COSTS, AND WHAT PAYS FOR IT.  ROOM-BRIEF forbids deleting
# content to hit a number, and nothing here is deleted, so the cost is real and
# it needs a lever.  Measured with `_r7_bytes.py` and `_r7_levers.py`, packing
# MY panels alone so the number is not entangled with the other three modules.
#
#   the four .deck panels alone         round 6  2.21 KB -> round 7  4.33 KB
#   my 16 core panels                   round 6 28.11 KB -> round 7 30.37 KB
#   my 20 panels incl. .screen          round 6 28.87 KB -> round 7 31.14 KB
#                                                            = +2.28 KB
#
# Per machine, decks only: legends-ultimate +1.32, champion edition +0.92,
# time-crisis +0.27, terminator-2 -0.37 (T2's deck got CHEAPER: flat blocks
# beat round 5's full-field _field() gradient, and it also reads better).
#
# TWO LEVERS I OWN, both measured, both fidelity dials on surfaces no camera
# reaches -- take them and the cost falls to +1.71 KB:
SIZE_KEY_REQUEST = {
    # the three INNER south flanks.  ar2's run spacings leave 0.10-0.22 ft
    # between these cabinets; the roster says so and round 5 already cut them
    # to 44 for the same reason.  44 -> 38 measures -0.44 KB on my run.
    # legends-ultimate is NOT in this list: it stands at the west end and its
    # west flank is the one south flank a camera can see.
    "street-fighter-2-champion-edition.side": 38,
    "time-crisis.side": 38,
    "terminator-2.side": 38,
    # my four .screen panels.  All four of these CRTs are dark glass with a
    # reflection and one instruction card; there is not a letterform in any of
    # them at any size.  28 -> 24 measures -0.13 KB.
    "legends-ultimate.screen": 24,
    "street-fighter-2-champion-edition.screen": 24,
    "time-crisis.screen": 24,
    "terminator-2.screen": 24,
}

# THE REMAINING ~1.7 KB NEEDS A ROOM-WIDE LEVER, and rooms/2.json names two as
# untaken.  Re-measured just now across all three packed wall atlases with this
# module in place (`scratchpad/arc4/levers_r5.py`, shipping = 144.6 KB):
#
#   SIZE[front] 92 -> 84    139.3 KB   -5.3 KB      <- recommended, at 86
#   SIZE[deck]  52 -> 46    141.2 KB   -3.4 KB      <- REFUSED, see below
#   SIZE[marquee] 104 -> 96 140.9 KB   -3.7 KB
#   QUANT 20 -> 24          129.8 KB  -14.8 KB      <- refused in round 5
#
# I RECOMMEND SIZE[front] 92 -> 86 and I flag the cost honestly rather than
# selling it: the roster's own conclusion is that "THE LOWER FRONT PANELS ARE
# WHERE THE TITLES LIVE IN THIS ROOM" -- six of sixteen machines are identified
# from their front, not their marquee -- so this is not a free surface.  At 86
# it is a 12% pixel cut on a 1.3:1 panel, which costs about 5 columns across a
# wordmark that currently gets 105.  It is the smallest real cost available.
#
# I REFUSE SIZE[deck] 52 -> 46.  The deck is the surface this round exists to
# fix and the one all four round-6 critics named; paying for deck artwork by
# cutting deck resolution is the round-2 mistake ROOM-BRIEF records.
PAYLOAD_R7 = {
    "my_20_panels_kb": {"round6": 28.87, "round7": 31.14, "delta": +2.28},
    "decks_only_kb": {"round6": 2.21, "round7": 4.33, "delta": +2.12},
    "per_machine_deck_delta_kb": {
        "legends-ultimate": +1.32,
        "street-fighter-2-champion-edition": +0.92,
        "time-crisis": +0.27,
        "terminator-2": -0.37,
    },
    "levers_taken": [
        "flat blocks instead of full-field _field() gradients on every deck: "
        "T2's panel got 0.37 KB CHEAPER while reading better",
        "opaque nebula masses and 1-texel hard stars on legends-ultimate "
        "instead of alpha-blended soft discs: -0.05 KB, and at 30 output rows "
        "the box filter destroyed the softness anyway",
        "SIZE_KEY_REQUEST above: -0.57 KB",
    ],
    "lever_recommended_room_wide": "SIZE[front] 92 -> 86",
    "levers_refused": [
        "SIZE[deck] 52 -> 46 (-3.4 KB): the deck is what this round is judged "
        "on",
        "QUANT 20 -> 24 (-14.8 KB): round 4 measured 24 as where banding "
        "starts on a marquee",
        "cutting any machine's artwork: ROOM-BRIEF forbids it and it was not "
        "needed",
    ],
}

'''
s = s.replace(ANCH, BLOCK + ANCH, 1)
io.open(Q, "w", encoding="utf-8").write(s)
print("patched", Q)
