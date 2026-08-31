# -*- coding: utf-8 -*-
"""Round-7 tail block for art_g0.py (spliced by _g0r7_splice.py)."""

TAIL = r'''

# =========================================================================
#  ROUND 7 -- what changed, what it cost, and what the integrator has to do
# =========================================================================
# SCOPE.  Four `.deck` panels and the DECKS spec.  Nothing else in this module
# moved: the marquees, flanks, fronts, Golden Tee's bezel, DOORS,
# DECK_MAT_REQUEST and the whole of NOTES are round 5's and are untouched.

ROUND7 = {
    "why": "0 of 4 in round 6, and all four critics named the SAME surface: "
           "the buttons were painted, every deck wore the same layout, and "
           "the decks read as empty planes with a faint round ghost decal.",

    "root_cause_found":
        "atlas4.SIZE['deck'] = 52 packs a 2.35:1 deck at 80 x 34 TEXELS, i.e. "
        "37 texels/ft. Round 5 drew its collars as cv.ring(r 0.096, stroke "
        "0.018, alpha 0.45) -- a 0.6-TEXEL stroke at 45%. atlas4 supersamples, "
        "box-averages and re-quantises at QUANT 20, so that ring lands on the "
        "same output level as the field and ceases to exist. The critics were "
        "not describing a weak decal, they were describing NO decal. Every "
        "collar this round is a filled mark >= 4 texels across at full alpha.",

    "deck_art": {
        "nba-jam": "REBUILT. Hardwood with white court lines, both keys, "
                   "three-point arcs, centre circle, and the NBA JAM burst "
                   "wordmark lying on the boards at the LEFT END clear of the "
                   "controls (round 5 put it dead centre, where the sticks "
                   "are). Court lines 0.052 (1.8 texels) instead of 0.030.",
        "tmnt-turtles-in-time": "REBUILT, and the biggest correction in the "
                                "round: round 5 drew a DARK brick wall. v4 7 "
                                "shows a BRIGHT TAN street with a brick block "
                                "standing in it, a violet night sky over the "
                                "far end, TURTLES wordmarks cascading across "
                                "it, a magenta splash, three portrait decals "
                                "along the player's edge and a pale label at "
                                "the back.",
        "golden-tee-3d-golf": "REBUILT full-bleed. The yellow three-panel "
                              "legend is REMOVED from the deck -- it is on "
                              "the bezel, which is where the geometry and the "
                              "photograph both put it, and round 5 shipped it "
                              "twice. Its five rows are now fairway.",
        "pac-man": "REBUILT, and it is still a black plane -- because the "
                   "object is. See NOTES['pac-man.deck']. The invented yellow "
                   "legend is gone; the clipping the brief named is gone with "
                   "it, and _text_fit now makes that class of bug impossible.",
    },

    "no_two_alike":
        "PAC-MAN one stick and ONE ROW of eight small buttons. NBA JAM two "
        "stations, a BALL top and a BAT top, eight large buttons scattered at "
        "eight different (u, v) with no two sharing a row. TURTLES two ball "
        "tops, seven JUMBO domes in two triads plus a red, and a back-edge row "
        "of six small violet admin buttons. GOLDEN TEE a trackball, two "
        "buttons and NO stick. Four different counts, four different sizes, "
        "four different topologies, all four from the photographs.",

    "self_assessment":
        "Of the four, PAC-MAN would still read as a tinted slab to a critic, "
        "and I am not going to pretend otherwise: v3 1, v4 3 and v4 7 all show "
        "a plain black overlay with a maroon lip, a pale label and small "
        "buttons, and inventing artwork for it would be exactly the thing "
        "ROOM-BRIEF forbids. What carries that machine is the saturated yellow "
        "carcase, the front panel's ghost-and-Pac group and the marquee -- all "
        "round-5 work, all untouched. The other three are printed edge to edge "
        "and none of them shares a composition with any other.",

    "bugs_fixed": (
        "PAC-MAN LEGEND CLIPPING. Round 5 set 'PAC-MAN' at h 0.215 / aspect "
        "0.68 centred at u 0.170; its advance width is 0.488 in u, so it "
        "spanned -0.074..0.414 and the render read 'AC-MAN'. The legend is "
        "removed as unsupported by the photographs, and all deck type now goes "
        "through _text_fit, which shrinks and clamps.",
        "TWO-STAGE QUANTISER SPLITTING NEAR-NEUTRAL GREYS. The paint quantises "
        "to multiples of 8 and atlas4 re-quantises to multiples of QUANT 20, "
        "so a grey authored two levels off neutral -- (124,124,126) -- lands "
        "on (120,120,140) and the surface goes lilac. Pac-Man's deck did "
        "exactly this in the first round-7 preview. Every grey on that panel "
        "is now EXACTLY neutral. Anyone authoring a near-neutral surface into "
        "this atlas needs to know that.",
        "GOLDEN TEE'S DOUBLED LEGEND STRIP (see deck_art above).",
    ),

    "open_defect_not_mine_to_fix":
        "a2kit's a2hw is roughness 0.42 and every up-facing cap blows out. "
        "That is a2kit's file. BUTTON_MAT_REQUEST above names the three "
        "materials and the values, with the reason for each.",
}


# ---- payload.  MEASURED, and measured the hard way ----------------------
# The three wall-run atlases are NOT a usable baseline while the other three
# art agents are working: the SOUTH atlas holds no art_g0 panel at all and it
# moved 34.4 -> 37.0 KB between two consecutive runs of the meter.  So the
# attributable number is art_g0's own four deck panels, packed alone, with the
# round-6 backup and the round-7 module built in the SAME process --
# `art/bytes_g0_r7.py` does that, and `art/levers_g0_r7.py` measures the dials.
PAYLOAD_R7 = {
    "four decks, round 6": 5.30,
    "four decks, round 7": 5.50,
    "delta": +0.21,
    "levers_owned_by_this_module": {
        "SIZE_KEY['pac-man.deck'] = 44": -0.07,
        "SIZE_KEY['golden-tee-3d-golf.deck'] = 48": -0.09,
        "both of the above": -0.16,
        "SIZE_KEY['nba-jam.side'] and ['pac-man.side'] 46 -> 40": -0.18,
    },
    "net_with_the_two_deck_levers": +0.05,
    "net_with_all_four_levers": -0.13,
    "recommendation":
        "Take all four and this round is NET NEGATIVE on a room sitting 0.4 KB "
        "under its cap.  The two deck levers cost nothing visible: Pac-Man's "
        "deck is a black overlay carrying one pale label, and Golden Tee's is "
        "grass with no letterform on it since the legend moved to the bezel. "
        "The two side levers are the flanks round 5 already cut to 46 because "
        "they stand in 0.1-0.2 ft gaps and appear in none of the judged "
        "frames; 40 is the same judgement one step further, and it is a "
        "fidelity dial, not a content one -- both tiles are still drawn in "
        "full.  If the integrator would rather not touch the flanks, the two "
        "deck levers alone leave this round at +0.05 KB, which is inside the "
        "room's 0.4 KB of headroom on its own.",
}

# Round 5 asked for 48 on the two flanks and atlas4 ships 46.  Round 7 re-asks
# at 40 and adds two deck keys; see PAYLOAD_R7 for what each one is worth.
SIZE_KEY_REQUEST = {
    "nba-jam.side": 40,
    "pac-man.side": 40,
    "pac-man.deck": 44,
    "golden-tee-3d-golf.deck": 48,
}


# ---- the four .deck notes, replacing round 5's -------------------------
NOTES.update({
    "nba-jam.deck":
        "v4 7 (288,248)-(370,330) at 14x -- art/r7/nba_deck_zoom.png, the "
        "clearest control deck in the whole photo set.  Hardwood boards, thick "
        "white court lines, the NBA JAM burst wordmark at the LEFT end, deep "
        "red T-molding, and eight large buttons in orange / white / red / cyan "
        "SCATTERED across the lines.  Scale solved on that crop with the "
        "T-molding as the ruler (0.75 in = 2.5 px -> 0.30 in/px, which returns "
        "the deck width as 24.6 in and checks out): the buttons are 2.25 IN.",
    "tmnt-turtles-in-time.deck":
        "v4 7 (330,290)-(470,400) at 10x -- art/r7/tm_deck_far.png.  BRIGHT "
        "TAN street, brick block, violet night sky at the far end, TURTLES "
        "wordmarks in green and blue, magenta splash, three square portrait "
        "decals along the player's edge, a pale instruction label at the back, "
        "green T-molding all round.  Two ball tops, CYAN and BLACK -- not "
        "yellow.  Seven JUMBO domes and a row of six small VIOLET admin "
        "buttons across the back edge, both of which are in that crop.",
    "golden-tee-3d-golf.deck":
        "v4 7 (112,180)-(175,205) at 20x and v4 6 (360,190)-(440,230) at 16x "
        "-- art/r7/gt_deck_zoom.png, gt_deck_v46.png.  Full-bleed grass "
        "fairway with pale mown highlights, a bunker each side, a putting "
        "green and flag, and the trackball as its brightest mark.  DEPARTURE "
        "FROM THE ROSTER, declared: the roster calls the deck 'two printed "
        "bands' with the yellow legend as the upper one.  Both frames put that "
        "strip on the DARK VERTICAL FACE ABOVE the deck, separated by a hard "
        "step, and the bezel panel already draws it there -- round 5 drew it "
        "in both places, so the render carried two.",
    "pac-man.deck":
        "v3 1 (590,620)-(700,700) at 10x, v4 3 (70,150)-(130,220) at 14x (very "
        "nearly a plan view of this deck) and v4 7 (0,175)-(45,235) at 18x -- "
        "art/r7/pac_deck_v31.png, pac_v43.png, pac_deck_v47.png.  There is NO "
        "printed graphic on this deck in any of the three: a plain black "
        "overlay, a maroon T-molding lip, one pale rectangular instruction "
        "label at the right, one red ball-top stick and a row of small round "
        "white / red / blue buttons.  The roster agrees.  Round 5's big yellow "
        "PAC-MAN legend was invented and is removed.  THIS IS THE ONE DECK OF "
        "THE FOUR THAT WILL STILL READ AS A TINTED SLAB, and it reads that way "
        "because the object does.",
})
'''
