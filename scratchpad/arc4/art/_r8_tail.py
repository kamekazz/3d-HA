# -*- coding: utf-8 -*-
"""Append ROUND8 to art_g2.py.  Idempotent: re-running replaces the block."""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "art_g2.py")
MARK = "\n\n# =========================================================================\n#  ROUND 8, machine-readable."

TAIL = '''

# =========================================================================
#  ROUND 8, machine-readable.  Everything here is measured; the scripts that
#  produced each number are named so a critic can re-run them.
# =========================================================================
ROUND8 = {
    "scope": ("art_g2.py only.  No other art module, no atlas4, no a2kit, "
              "no ar2, no decks5, no room geometry, no rebuild, no shot."),
    "root_cause": {
        "claim": ("street-fighter-2-champion-edition.deck and "
                  "terminator-2.deck were drawn, packed and UV-mapped "
                  "correctly in round 7 and still rendered as flat plates.  "
                  "The material factor, not the drawing, is the defect."),
        "proof": [
            "backend/uploads/models/model_285.glb: the embedded atlas "
            "carries both panels drawn, at 79x33 and 81x33 texels, and "
            "primitive 19 (a2artk_south) maps the two deck quads onto their "
            "full rects with no flip and no degenerate UV.",
            "terminator-2.deck texture row 9 swings 0-80 across the panel; "
            "the same row of the same deck in scratchpad/arc4/shots/"
            "r7_full_south.png swings 73-80.  The texture does not reach "
            "the frame.",
            "a2kit.ART_D baseColor #c9c9c9 = 0.584 linear; a2kit.ART_DK "
            "#4c4c4c = 0.0723 linear.  8.1x, on top of this module own "
            "3.05 pre-division: ~24x under an ART_D deck at the same true "
            "colour, which is under the scene ambient/specular floor.",
            "6/6 correlation room-wide: every deck called bare or black by "
            "a critic (pac-man, star-wars-atari, east-7, ridge-racer, and "
            "these two) is ART_DK; every deck that prints (legends-"
            "ultimate, time-crisis, tmnt, nba-jam, mortal-kombat, "
            "golden-tee) is ART_D or ART_DM.",
        ],
        "why_round_5_missed_it": (
            "round 5 fitted 'an ART_DK deck renders ~3x its authored value' "
            "through two ground-level samples.  The relationship is an "
            "ADDITIVE floor, not a multiplier, so the fit predicted the "
            "ground level correctly and the contrast not at all."),
    },
    "blocking_handoff": INTEGRATOR_MUST,
    "levels": {
        "method": ("clean deck medians, photo and panel, ratioed against "
                   "time-crisis.deck -- the one south deck a critic has "
                   "accepted, and whose authored median (86.2) sits within "
                   "12% of its own photographed median (96-101).  Absolute "
                   "luma is not comparable: these are the owner's frames at "
                   "the owner's exposure, so ROOM-BRIEF's rule for this "
                   "room applies and it is judged on ratios."),
        "script": "scratchpad/arc4/art/_r8_meter.py",
        "terminator-2": {"photo": [0.386, 0.511], "round7": 0.568,
                         "round8": 0.465},
        "street-fighter-2-champion-edition": {"photo": [1.26],
                                              "round7": 1.582,
                                              "round8": 1.297},
    },
    "front_bleed": {
        "what": ("FRONT_RECT inset_ft 0.02-0.10 -> 0.06 ft on all four.  "
                 "decks5.front_rect turns the inset into the printed quad's "
                 "half-width, so the inset IS the strip of sweep() perimeter "
                 "face left showing either side -- the surface the carcase "
                 "agent is colouring as the T-molding bead.  0.06 ft is "
                 "3/4 in, real T-molding.  Round 7's 0.02 was a 7 mm reveal "
                 "and invisible at every camera in this room."),
        "deleted": [
            "lu_front's hairline silver reveal on all four edges -- v4 8 px "
            "(438,175)-(490,220) at 20x shows the licence grid running to "
            "the cabinet edge on black with no reveal, and the grid is "
            "widened (columns 63/193 half-width 56, was 66/188 at 48) so "
            "the ink now bleeds into the bead.",
            "t2_front's painted maroon T-molding stripes at x 0-11 and "
            "245-256 plus their two dark hairlines -- the bead is real "
            "geometry now and a painted one beside it doubles it.  v4 8 px "
            "(355,145)-(392,200) at 22x shows a flat black panel edge to "
            "edge with the white T2 on it.",
        ],
        "kept": ("tc_front's two red pillars.  v4 4 and v4 5 both show ~0.4 "
                 "ft of printed red either side of the black centre on that "
                 "machine: printed vinyl, not a 0.06 ft bead."),
        "also": ("ce_front's CAPCOM moves from CENTRED WHITE over a darker "
                 "band to LOW LEFT in warm red on continuous blue, which is "
                 "what v4 8 px (404,155)-(442,215) at 22x shows."),
    },
    "repeated_wordmark_sweep": {
        "within_one_panel": "none found in this module's 16 panels",
        "across_one_machine": {
            "time-crisis": ("carried TIME CRISIS on marquee + lower front + "
                            "deck lip.  The deck one is REMOVED: "
                            "DECK_EVIDENCE's own reads list for that panel "
                            "never mentioned a legend, and v4 4 px "
                            "(36,166)-(110,200) at 20x shows the lip plain "
                            "red under the gold band."),
            "legends-ultimate": ("KEPT.  Its deck wordmark is photo-read in "
                                 "chartreuse at 10x in v4 3, and the front "
                                 "carries a licence grid, not a title."),
        },
    },
    "payload": {
        "my_20_panels_kb": {"round7": 30.92, "round8": 32.11, "delta": 1.19},
        "per_panel_kb": {
            "street-fighter-2-champion-edition.deck": {"r7": 1.29, "r8": 1.89},
            "terminator-2.deck": {"r7": 0.48, "r8": 0.77},
            "time-crisis.deck": {"r7": 1.09, "r8": 0.90},
            "legends-ultimate.front": {"r7": 3.58, "r8": 4.01},
            "terminator-2.front": {"r7": 1.81, "r8": 1.84},
            "street-fighter-2-champion-edition.front": {"r7": 2.14,
                                                        "r8": 2.18},
        },
        "script": "scratchpad/arc4/art/_r8_bytes.py  (and _r8_bytes.py old)",
        "lever_available": ("SIZE_KEY_REQUEST above is still untaken and "
                            "returns 0.57 KB of the 1.19."),
        "note": ("the south atlas is packed once and lands in one GLB, so "
                 "this is +1.2 KB on the room, not +3.6."),
    },
    "still_open": [
        "THE FIX IS NOT COMPLETE INSIDE THIS FILE.  Until a2kit.DECK_MAT "
        "carries both machines as 'D', both decks render exactly as they do "
        "today, only 3.05x less crushed.",
        "terminator-2.deck's chrome shard and its two player bars remain "
        "DECLARED EXTRAPOLATION -- see DECK_EVIDENCE.  The photographs show "
        "this deck near-black with the blue/red split carried by the two gun "
        "bodies; the bars print that split and nothing else was added.",
        "street-fighter-2-champion-edition's control LAYOUT is still class "
        "inference: no frame in the set resolves a single control on that "
        "machine.  Only the PANEL is photo-read.",
        "the 0.06 ft bead assumes the carcase agent colours sweep()'s "
        "perimeter strip either side of the printed front quad.  If the bead "
        "is built as separate proud geometry instead, inset_ft should go "
        "back down so the print is not held off the cabinet edge twice.",
        "nothing here was seen in the 3D render: round 8 forbade rebuilding "
        "or re-placing models, so this module is verified against the packed "
        "atlas and the photographs only (r8_south-decks.png).",
    ],
    "sheets": [
        "scratchpad/arc4/art/r8_south-decks.png  -- photo | round 7 packed | "
        "round 8 packed | round 8 + DECKS geometry, for all four decks, plus "
        "the four fronts with the bead drawn at true width",
        "scratchpad/arc4/art/_r8_panels.png  -- all 16 panels at true aspect",
    ],
    "scripts": [
        "scratchpad/arc4/art/_r8_dump.py     packed panels, new and old",
        "scratchpad/arc4/art/_r8_preview.py  the sheet",
        "scratchpad/arc4/art/_r8_meter.py    panel medians and photo ratios",
        "scratchpad/arc4/art/_r8_bytes.py    my 20 panels, new and old",
        "backup: scratchpad/arc4/art/art_g2_r7.bak.py "
        "(and _r8old/art_g2.py, the copy the A/B scripts import)",
    ],
}
'''

with io.open(TARGET, encoding="utf-8") as f:
    src = f.read()
i = src.find(MARK)
if i >= 0:
    src = src[:i]
with io.open(TARGET, "w", encoding="utf-8") as f:
    f.write(src.rstrip("\n") + "\n" + TAIL)
print("appended ROUND8 to", TARGET)
