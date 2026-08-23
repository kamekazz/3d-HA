# -*- coding: utf-8 -*-
"""Write tools/roomkit/rooms/2.json for round 3."""
import json
import os

P = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools\roomkit\rooms\2.json"
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(P, encoding="utf-8"))
pieces = json.load(open(os.path.join(HERE, "_pieces.json")))

d["_note"] = (
    "ROUND 3, 2026-08-23, after a FAIL verdict on round 2. Built by "
    "scratchpad/bsmt/ar2.py + scratchpad/bsmt/a2kit.py (idempotent, re-runnable). "
    "Round 1's ar.py is superseded and must NOT be re-run: it is 180 degrees out on X.")

d["_round3"] = {
    "verdict_closed": [
        "Tell 1 -- 'the hero cabinet run is the same box seven times with the hue swapped'. "
        "The upright is now a SWEPT SIDE PROFILE (a2kit.sweep), not a stack of boxes: four "
        "silhouettes (straight / slope / step / riser), per-machine width 2.04-2.95 ft, height "
        "5.78-6.36 ft, deck height 2.40-2.62 ft, marquee band 0.52-0.80 ft and an optional "
        "plinth 0.06-0.14 ft, and a CONTROL DECK THAT PROJECTS 0.70 ft past the carcase front "
        "(round 2: 0.06 ft, ar2.py:303). Every visible zone carries PRINTED ARTWORK sampled from "
        "a shared 256x256 RGB atlas through the new glb.py texture path: both flanks, the lower "
        "front panel, the control deck, the screen bezel and the marquee title band each take "
        "their own tile. The sweep is also ~5x cheaper per machine than the box stack, which is "
        "what paid for the north wall.",

        "Tell 2 -- 'a quarter of the room is unbuilt'. NEW piece 'Arcade Cabinets North': four "
        "frontal uprights at local x 6.55 / 9.00 / 11.30 / 13.55 facing south, a 2.55 x 1.30 x "
        "5.55 ft glass-fronted lit Funko display cabinet in the NE corner (5 lit shelves x 6 "
        "printed box fronts), the large plush in its net bag hung at x 16.3 y 4.35, and the black "
        "speaker on a stand at x 15.1. The NW alcove that was bare floor now carries the RGB floor "
        "lamp, a green vase, a large leafy plant, a low storage cube and a second Y fixture. The "
        "NW utility closet has skirting on all four faces, a two-step cap and two framed prints on "
        "a picture rail on its north face -- the face the dollhouse quadrant puts in the "
        "foreground.",

        "Tell 3 -- 'the two recessed gaming booths are missing'. NEW piece 'Arcade Booths': two "
        "2.80 ft openings at local z 7.55-10.35 and 10.95-13.75, 6.70 ft high, in a 1.55 ft deep "
        "stud bay on the west wall, each with a dark lining, RGB strips down both reveals, a wall "
        "monitor at y 3.10-5.30, a white worktop at 2.35 with a keyboard, two headset hooks and a "
        "Razer chair. The desk run moved south to z 14.30-20.90 to make room and gained its L "
        "return arm; the TV moved with it to z 14.40-20.70.",

        "Smaller: collectible shelf 24 -> 40 packed figures with a real under-shelf glow strip AND "
        "a lit back panel; the chevron band is now two facets at different values plus a cast "
        "shadow line instead of one panel at the wall's own value; the black/iridescent hexes "
        "above the T2 group on the south wall are built; both Y fixtures use a 6.0-strength "
        "emissive; the desk no longer sinks into the slab (its bbox min y was -0.11 because the "
        "chair casters were cylinders rotated about X at y=0 -- they now sit at y 0.11); plants "
        "are a real plant() helper at 0.75-1.45 scale instead of 4-inch tufts, and the large leafy "
        "plant is built at the west wall's south end."
    ],

    "withdrawn_gap": (
        "Round 2 recorded 'the ceiling is invisible in every render because cutaway.js fades any "
        "object whose name ends in ceiling'. That was WRONG and it is deleted: with --no-cutaway "
        "the ceiling, its recessed cans, its supply grille and all four near walls render in full. "
        "Every eye-level pose below was re-shot with --no-cutaway."),

    "bug_found_and_fixed": (
        "THE ENTIRE SOUTH WALL OF ROUND 2 WAS INVISIBLE. house.js extrudes each wall OUTWARD from "
        "its own footprint line (WALL_THICKNESS 0.35, geo.translate(0,0,-t)), so on the party wall "
        "with the Movie Room the NEIGHBOUR's wall mass lands 0.35 ft inside this room. Round 2 "
        "authored the south skin at depth 0.035, the Movie Room door leaf and casing at 0-0.145, "
        "the black diagonal-rib acoustic panel at 0-0.10 and the RGB hex light bar at 0-0.07 -- "
        "every one of them behind that face. What a round-2 render shows at the south end is the "
        "Movie Room's paint, not ours. ar2.py now carries SD = 0.40: the south skin, the hexes, "
        "the acoustic panel, the RGB bar, the south skirting, the wall-hung mini cabinet and the "
        "Connect-4 console are authored at depth >= 0.40, the four south uprights moved 0.40 ft "
        "north, and the Movie Room door is rebuilt as a real 0.40 ft reveal (lining back to z = D, "
        "leaf and casing on the room side)."),

    "neighbour_regression": (
        "Movie Room opening 3 is now edge_index 0, offset 17.3, width 3.10 = world x 15.4-18.5. "
        "That is the STAIR-LANDING opening from RESUME's open-items list, not the party-wall door. "
        "It no longer registers with our opening 103 (world x 11.4-14.1), so the Movie Room's "
        "north wall is solid behind our door and our proud leaf is what makes the doorway read at "
        "all. Room 1 belongs to another agent and was not touched. Re-pair spec: Arcade 103 is "
        "edge 2, offset 4.5, width 2.7."),
}

d["_walls"] = {
    "east x=20.7": (
        "THE ROOM. 7 uprights facing west (z 2.85..16.41, moved 1.2 ft south of round 2 to clear "
        "the NE Funko cabinet), the lit Funko shelf over them at y 6.34 with 40 packed figures and "
        "an under-shelf glow, the two-facet chevron acoustic band at y ~7.0, the cove LED at 7.62, "
        "the Y-shaped RGB fixture at z 20.55, the pinball at z 19.05 and a low glass collectible "
        "case at z 20.3..22.1."),
    "south z=23.3": (
        "Legends Ultimate / Capcom Champion (on its blue CAPCOM base) / Time Crisis / T2 across "
        "x 0.5..11.3, black/iridescent hexes above them, the black diagonal-rib acoustic panel "
        "x 11.6..13.2, the Movie Room door x 13.5..16.2 (opening 103) in a 0.40 ft reveal, a "
        "vertical RGB hex bar on the 1.2 ft stub at x 16.85, a wall-hung mini cabinet and the "
        "Connect-4 game on a low white console. EVERYTHING here is authored at depth >= SD = "
        "0.40."),
    "west x=0": (
        "the two gaming booths z 7.21..14.09 in a 1.55 ft bay, the white sit-stand desk run "
        "z 14.30..20.90 with its L return, monitors, a retro-console shelf, two plants and five "
        "RGB floor uplights; the very large TV z 14.40..20.70 at y 3.25..6.55 with an RGB bias "
        "strip; hex panels; the large leafy floor plant at z 18.6; Ridge Racer round the corner "
        "at z 21.55."),
    "north z=0": (
        "FOUR frontal arcade cabinets at x 6.55 / 9.00 / 11.30 / 13.55, the black speaker on a "
        "stand at x 15.1, the plush in its net bag at x 16.3, the lit glass Funko display cabinet "
        "at x 17.45..20.00 in the NE corner, hex panels and three small mounted screens at "
        "y 6.9..7.5 above them, and the NW alcove (x 0..5.3, z 0..3.4) with a floor lamp, a vase, "
        "a large plant and a storage cube."),
}

d["_camera"]["poses_world"] = {
    "photo_v3_4_match": {"pos": [14.4, 5.4, -9.5], "target": [6.6, 2.9, 11.4], "fov": 80,
                         "size": [900, 1200], "_flags": "--no-cutaway"},
    "photo_v3_1_match": {"pos": [4.5, 5.4, 7.7], "target": [9.4, 2.2, -10.9], "fov": 100,
                         "size": [900, 1200], "_flags": "--no-cutaway"},
    "booths": {"pos": [8.4, 4.6, -1.2], "target": [-2.1, 3.2, 0.6], "fov": 72,
               "size": [1100, 850], "_flags": "--no-cutaway"},
    "doll_nw": {"pos": [-7.156, 40.009, -22.252], "target": [8.25, 2.24, -0.25], "fov": 42,
                "size": [1200, 900]},
    "plan": {"pos": [8.25, 37.0, -0.25], "target": [8.25, 0.0, -0.25], "fov": 45,
             "size": [900, 900]},
}

m = d["_metered"]
m["_how"] = (
    "Photo boxes are hand-placed on clean single-material patches at NATIVE 1200x1600 "
    "(scratchpad/bsmt/m2.py reports mean, sd, mean|d1| between adjacent pixels and |d1|/sd "
    "together). Render walls are metered by the DIFF-MASK method (scratchpad/bsmt/probe2.py): the "
    "room is rendered with one wall's skin changed and the pixels that moved ARE that wall, so no "
    "sample box can swallow a cabinet. Render floor/rug numbers come from the top-down plan pose. "
    "NOTE the photos are a NIGHT shot under RGB cove/hex fixtures -- every surface is colour-cast "
    "and the absolute luminances are NOT comparable to a daylight render; ratios and texture "
    "statistics are. ALSO note round 2's four wall numbers are void: the south 'wall' it metered "
    "was the Movie Room's wall face (see _round3.bug_found_and_fixed), and all four skins have "
    "been re-solved from scratch this round.")
m["render_wall_north"] = "167.6  n=51039  sd=13.64  |d1|=2.81  ratio 0.206"
m["render_wall_east"] = "170.7  n=50774  sd=12.40  |d1|=1.01  ratio 0.082"
m["render_wall_south"] = "162.6  n=70342  sd=15.64  |d1|=1.56  ratio 0.100"
m["render_wall_west"] = "170.8  n=27067  sd= 8.91  |d1|=0.86  ratio 0.096"
m["render_wall_SPREAD"] = (
    "8.2  (round 2 claimed 11.0 but its south figure was the neighbour's wall; this is the "
    "tightest honestly-measured spread in the house -- garage 12.3, laundry 18.2, office 22.9)")
m["render_rug_clean"] = (
    "172.2  n=29900  sd=6.58  |d1|=2.72  ratio 0.414   (photo clean single-lit patch 159.7 "
    "sd 6.76 |d1| 2.68 ratio 0.397 -- round 2 was sd 8.25 |d1| 0.59 ratio 0.072, i.e. the right "
    "amount of variation four times too coarse. The nap is now a 64 px directional-streak tile "
    "repeating every 3.2 ft, and the piece went 126.9 -> 21.1 KB.)")
m["render_rug_over_plank"] = "1.22  (photo 1.19)"
m["render_contact_shadow"] = (
    "horizontal profile across the lounge in the plan pose: free rug 172, contact edge 113.5 west "
    "/ 119.0 east = 34.0% / 30.8% darkening, easing to zero over 24 px = 0.82 ft. Target 34% over "
    "~25 px. The annuli are unchanged from round 2 except seg 20 -> 16 and smooth=True welding (a "
    "coplanar fan then shares vertices instead of emitting three per triangle -- a 3x saving on "
    "every shadow in the room).")

d["_wall_skins"] = {
    "_how": (
        "probe2.py, RE-SOLVED 2026-08-23 against the TEXTURED skin and the corrected south plane. "
        "At #fafafa the four walls render N 235.3 / E 185.8 / S 160.2 / W 213.5; at #6e6e6e they "
        "render N 165.2 / E 73.2 / S 50.6 / W 105.3. Two-point power fits (gamma N 0.431, E 1.135, "
        "S 1.403, W 0.861) inverted for a common target of 170 gave albedos 118 / 231 / 255 / 192, "
        "which rendered 173.1 / 173.9 / 162.6 / 182.9; one measured nudge plus a 1.5% warm shift "
        "gives the values below."),
    "final": {"n": "#71706e", "e": "#e2e0dc", "s": "#fffefb", "w": "#b0aeaa"},
    "note": (
        "Each skin is now ONE textured quad (a 64 px grey tile at 2.6 ft, mean 250 sd 6 |d1| 4) "
        "rather than ~24 tone-banded boxes: 7.2 KB against 101.5, and the grain is at texel scale "
        "instead of 1.85 ft bands -- measured |d1| 0.86-2.81 against round 2's 0.52-1.28. The "
        "south skin sits at z = D - 0.41, in front of the Movie Room's wall mass. The south wall "
        "is the one the sun never reaches: it reaches only 165 at pure white, so it is left white "
        "and lands ~8 under the others."),
}

d["_shadows"] = (
    "kit.contact_shadow's stacked-layer shape metered as a 0.5-2% darkening in this scene -- "
    "coincident translucent triangles inside one primitive do not accumulate here. ar2.py's "
    "cshadow() replaces it with ONE coplanar layer of NON-OVERLAPPING annuli, each carrying its "
    "own alpha, full darkness AT the footprint feathering out over 0.7-0.85 ft, at y=0.050 on "
    "plank and y=0.115 on the rug. Measured 30.8-34.0% at the contact edge over 0.82 ft.")

d["_gaps"] = [
    "The photos are lit almost entirely by RGB cove strips, Nanoleaf hexes, marquees and floor "
    "uplights; the app renders daylight. Only the fixtures the photo actually shows are emissive "
    "here (marquees, the shelf strip and its lit back panel, the cove, a third of the hexes, the "
    "two Y fixtures, the RGB bar, the booth reveal strips, the uplight lenses, the TV bias strip). "
    "There is deliberately NO room-filling emissive box and no emissive on any room-scale trim "
    "run.",

    "The 3.2 ft opening from the SE corner of the south wall (local x 17.5..20.7) to the stair "
    "landing is real in the plan and is NOT cut on our side. Spec: Arcade edge_index 2, offset "
    "0.0, width 3.2. The Movie Room's opening 3 now sits exactly there, so ours is the missing "
    "half.",

    "Opening 103 (the party-wall door) is no longer paired: the Movie Room's opening 3 moved to "
    "the stair-landing span this run, so its north wall is solid behind our door and our leaf "
    "standing 0.40 ft proud is what makes the doorway read. See _round3.neighbour_regression.",

    "THE TWO GAMING BOOTHS ARE AN INTERPRETATION OF THE PHOTOGRAPHS, NOT OF THE PLAN. 'v3 1' "
    "(crop 0,430-560,850) and 'v3 2' both show them left of the six-panel door with a continuous "
    "ceiling and skirting line running past them, which puts them on the WEST wall between the "
    "closet and the desk. That wall is the exterior foundation on the basement plan, so they "
    "cannot be recesses cut into it; they are built as a 1.55 ft stud bay standing proud of it, "
    "which is what the photo's ~1 ft white reveals read as anyway. If the owner says the reveals "
    "are deeper, the bay depth is one constant (BOOTH_D).",

    "The room is really L-shaped: the plan puts a 5.2 x 3.7 ft utility closet at local x 0..5.2, "
    "z 3.4..7.1 (registered off the basement plan at 36.1 px/ft). It is built here as a solid "
    "block (inside 'Arcade Baseboards' so it stays unpickable) with skirting, a two-step cap, a "
    "picture rail and two prints, and its south face carries the six-panel door. The footprint is "
    "a rectangle and does not know about it, so the slab and skirting still run underneath.",

    "ONE cabinet builder is reused sixteen times. The silhouette (four profiles), width, height, "
    "deck height, marquee depth and plinth all vary per machine and the artwork comes from 16 "
    "atlas tiles, but the atlas graphics are procedural shapes -- they read as printed vinyl at "
    "3 ft, not as Pac-Man and Marvel Super Heroes.",

    "Cabinet count is 16 uprights plus the pinball against the photos' ~17: east 7, south 4 plus "
    "Ridge Racer, north 4. The Capcom Champion base is modelled; Time Crisis's gun holsters are "
    "not.",

    "Not modelled: the pinball's side art, the desk's second monitor arm, the Funkos are printed "
    "box fronts rather than sculpted Pops, and the plush is a puff blob rather than the photo's "
    "character.",
]

d["pieces"] = pieces["pieces"]
d["_payload_kb"] = pieces["total"]
d["_shots"] = [
    "scratchpad/shots/v3_arcade/r2_a_look_s.png  + _sbs.jpg   (photo v3 4 match, --no-cutaway)",
    "scratchpad/shots/v3_arcade/r2_b_look_n.png  + _sbs.jpg   (photo v3 1 match, --no-cutaway)",
    "scratchpad/shots/v3_arcade/r2_e_booths.png  + _sbs.jpg   (west-wall gaming booths, "
    "--no-cutaway)",
    "scratchpad/shots/v3_arcade/r2_c_doll_nw.png + _sbs.jpg   (dollhouse, doll_nw, cutaway ON)",
    "scratchpad/shots/v3_arcade/r2_d_plan.png                 (plan pose, used for metering)",
]
d["_build_script"] = (
    "scratchpad/bsmt/ar2.py + scratchpad/bsmt/a2kit.py  (probe: scratchpad/bsmt/probe2.py, "
    "meter: scratchpad/bsmt/m2.py)")

json.dump(d, open(P, "w", encoding="utf-8"), indent=1)
print("written", os.path.getsize(P), "bytes")
