# -*- coding: utf-8 -*-
"""Record round 8 in tools/roomkit/rooms/2.json."""
import collections
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", ".."))
P = os.path.join(ROOT, "tools", "roomkit", "rooms", "2.json")
d = json.load(io.open(P, encoding="utf-8"),
              object_pairs_hook=collections.OrderedDict)

d["_payload_kb"] = 1527.1
d["pieces"]["Arcade Cabinets East"]["kb"] = 203.3
d["pieces"]["Arcade Cabinets South"]["kb"] = 217.6
d["pieces"]["Arcade Cabinets North"]["kb"] = 183.2

d["_round8_tmolding"] = collections.OrderedDict([
    ("date", "2026-08-31"),
    ("scope",
     "Round 8 integration pass. Rebuilt and re-placed ONLY Arcade Cabinets "
     "East / South / North. No room geometry, no footprint, no other room, no "
     "frontend/js, no backend, no poses.json, no Flask restart."),
    ("headline",
     "THE CARCASE IS BLACK AND THE COLOUR IS A BEAD. Rounds 4-7 handed each "
     "machine's accent hue to a2kit.sweep()'s BODY material, which paints the "
     "whole perimeter -- top, back, head front, apron, deck skirt and the strip "
     "of front face either side of the printed panel -- so the Turtles cabinet "
     "was flood-fill green and NBA Jam flood-fill maroon. Two round-7 critics "
     "named it, the photographs agree, and so does this room's own roster, "
     "which said 'Black carcase with BRIGHT GRASS-GREEN T-molding' in round 4 "
     "and was read wrongly. The hues did NOT move: a2kit.CARCASE is renamed "
     "a2kit.TMOLD verbatim and is now the colour of a real bead of geometry "
     "running the seam between each flank and the perimeter face."),
    ("evidence", [
        "docs/photos-jpg/Arcade Room v4 7.jpg px (390,160)-(470,300) at 8x "
        "LANCZOS -> scratchpad/arc4/shots/_ph_tmnt_bead.png: a bright green "
        "bead runs the whole front edge of the Turtles cabinet with black "
        "carcase either side of it, NBA Jam's dark-red bead beside it. The "
        "bead peaks (176,222,177) where the same machine's body meters 41-56 "
        "luma -- it is glossy plastic catching the ceiling cans.",
        "docs/photos-jpg/Arcade Room v3 4.jpg px (100,520)-(520,700) at 3x -> "
        "scratchpad/arc4/shots/_ph_v34_tops.png: the whole east run is five "
        "BLACK carcases each outlined by its own bright bead -- gold, maroon, "
        "maroon, green -- and every cabinet TOP is black.",
        "docs/photos-jpg/Arcade Room v4 7.jpg px (40,105)-(200,180) at 7x -> "
        "scratchpad/arc4/shots/_ph_tops.png: NFL Blitz and Golden Tee heads "
        "flat black to the top edge; no pale cap strip anywhere.",
    ]),
    ("geometry", collections.OrderedDict([
        ("what",
         "ar2.tmold(): a 3-point section -- a landing 0.006 ft off the flank, "
         "a crown 0.030 ft proud, a landing 0.006 ft off the perimeter face -- "
         "swept as ONE smooth strip per flank along the machine's own profile. "
         "0.062 ft across the corner = 0.74 in, real T-molding."),
        ("where",
         "The seam IS the swept profile's outline at x0 and x1, so one strip "
         "per flank carries all three runs at once: the perimeter of the front "
         "face, the deck's front edge and the side panel's edge. Two profile "
         "edges are skipped -- the floor edge and the back edge -- which are "
         "never in frame and are ~20% of the strip."),
        ("material",
         "a2tm, ONE vertex-coloured material per run (so zero extra glTF "
         "primitives for sixteen hues) at roughness 0.30 against the body's "
         "0.55 -- glossy plastic against painted melamine. That is what gives "
         "it the specular line the photographs show; the crown's averaged "
         "smooth normal turns across the section so it reads as a line, not "
         "two flat facets."),
        ("z_fighting",
         "Neither landing is coplanar with the surface it sits on: 0.006 ft "
         "off the flank plane and 0.006 ft off the perimeter face, proud of "
         "both in between. Inspected at 5x on the grazing mq_east pose "
         "(scratchpad/arc4/shots/_diag_graze1.png) -- continuous, no shimmer."),
        ("bug_found_and_fixed",
         "The first build ran the section OUTWARD from both flanks (sgn -1 at "
         "x0, +1 at x1), which put the whole bead outside the cabinet and left "
         "a 3-pixel carcase reveal between the printed panel and the bead. "
         "sgn now points INWARD (+1 at x0, -1 at x1) and only BEAD_A's lip "
         "stands proud of the flank."),
        ("cost",
         "a2tm geometry: east 13.80 KB / 402 v / 480 t, south 9.68 / 282 / "
         "336, north 7.83 / 228 / 272 = 31.3 KB and 1088 triangles gross for "
         "the room's sixteen machines (~2.0 KB and 68 tris per cabinet). Paid "
         "for by three things, none of which is artwork: one shared black body "
         "material per run instead of sixteen per-machine carcase materials "
         "(-9 glTF primitives, ~-5.0 KB), the pale cap deletion (-14.6 KB, see "
         "below) and per-class atlas quantisation (-4.6 KB). NET on the three "
         "GLBs +6.2 KB against the same art without the bead; the room lands "
         "at 1527.1 KB, 8.9 KB under the 1536 cap."),
    ])),
    ("carcase_value", collections.OrderedDict([
        ("method",
         "PROBED, not chosen. Each run was rendered twice with ONLY the body "
         "colour changed and the pixels that moved kept, so the sample is the "
         "carcase by construction (ROOM-BRIEF's probe2 technique); two-point "
         "log-linear fit per run in scratchpad/arc4/r8fit.py."),
        ("target",
         "docs/photos-jpg/Arcade Room v4 6.jpg is the least colour-cast frame "
         "in the set (its floor meters neutral #a4a39f). Its two clean black "
         "carcases -- Golden Tee's lower front px (362,238)-(392,248) and "
         "(364,254)-(392,262), NFL Blitz's body -- meter median 39-48 against "
         "that frame's floor at median 200: a carcase/floor ratio of "
         "0.195-0.24. This room is judged on ratios (its photographs are an "
         "RGB-lit night set), so 0.215 is the target."),
        ("why_per_run",
         "One albedo cannot serve three orientations in a scene with one "
         "directional sun and no bounce. MEASURED: #474954 renders 39.1 on "
         "east, 112.1 on north and 24.7 on south. ROOM-BRIEF says exactly this "
         "-- 'do not apply a single factor, probe the specific wall you need "
         "to match, on the orientation you need it on'."),
        ("shipped", {"east": "#454754", "south": "#545967",
                     "north": "#141519"}),
        ("result",
         "east carcase median 37.6 / floor 173.5 = 0.216 (n=82470 probed px); "
         "north 36.3 / 175.5 = 0.207 (n=98259); south 35.6 / 167.5 = 0.212 "
         "(n=28950). Photo band 0.195-0.24. Round 7 was 0.070 on east."),
        ("hue",
         "Held at the cool blue-grey of the roster's own photo samples "
         "(#282737, #313234, #353745, #2b2e38, #1c161e); only the value "
         "moves."),
        ("coloured_bodies",
         "FOUR machines really do have a coloured carcase and the roster says "
         "so: star-wars-atari (golden yellow), pac-man (yellow body, maroon "
         "molding 'in deep shadow in every frame; do not trust any hex'), "
         "time-crisis (cream/gold head over a RED body), ridge-racer (red). "
         "They keep their body hue and their bead takes the same colour rather "
         "than a guessed second one."),
    ])),
    ("pale_cap_removed",
     "The #787c82 strip round 3 ran across every cabinet top -- 'end-on from "
     "the dollhouse quadrant an all-black run merges into one mass, and this "
     "line breaks it into machines' -- is DELETED. It is a correction, not a "
     "saving: v4 7 and v3 4 both show black cabinet tops and no pale strip, "
     "and the T-molding bead does the job it was standing in for, correctly "
     "and from every camera rather than only from above. It was 14.6 KB across "
     "the three GLBs."),
    ("full_bleed",
     "decks5.front_rect's default was (-bw/2+0.08, bw/2-0.08, plinth+0.16, "
     "dy-0.62) and both art agents deleted their own painted edge trim this "
     "round expecting a real bead to take that strip. It is now "
     "(-bw/2+0.045, bw/2-0.045, plinth+0.05, dy-0.57): the bead occupies "
     "x0-0.006..x0+0.056 of the front face, so the last 0.011 ft of vinyl runs "
     "UNDER it -- full bleed into a T-molding -- and the panel now stops 0.02 "
     "ft short of where the flat front face ends instead of 0.07. Panel "
     "ASPECTS follow automatically through ar2._aspects() -> "
     "atlas4.set_aspects(), so every module's art re-renders to the new shape "
     "rather than stretching into it."),
    ("marquee_uvs", collections.OrderedDict([
        ("finding",
         "THERE IS NO UV OVERSCAN ANYWHERE IN THE ROOM, and the round-7 'ORTAL "
         "KOMBAT' had two other causes. Checked with scratchpad/arc4/r8marq.py: "
         "every one of the sixteen marquee quads takes its own packed rect at a "
         "UV span of 99.4-99.5% of the tile -- the half-texel inset and nothing "
         "else."),
        ("cause_1",
         "The art was authored INTO the bleed. Rounds 4-7 set MORTAL and "
         "KOMBAT with their outer stems ~1% of the tile width from the edge. "
         "art_g1 fixed that in round 8 (12% safe margin, verified in the tile: "
         "scratchpad/arc4/shots/_diag_mkmq_r7.png vs _diag_mkmq_r8.png)."),
        ("cause_2",
         "OCCLUSION, not clipping. Mortal Kombat is a 'step' profile whose "
         "marquee sits at ft-0.37, and its neighbour Marvel vs Capcom is a "
         "'riser' whose marquee sits at ft+0.13 -- half a foot proud. From "
         "mq_east, which looks along the run, MvC's head covers the left ~8% "
         "of MK's marquee. That is real geometry doing what real geometry "
         "does; the fix is the safe margin, not a UV change."),
        ("verified_r8",
         "All five east marquees read complete in r8_mq_east (MARVEL SUPER "
         "HEROES / MORTAL KOMBAT / NBA JAM / TURTLES, plus the two art-panel "
         "marquees); all four north read complete in r8_mq_north (PAC-MAN / "
         "NFL BLITZ / GOLDEN TEE 3D GOLF!). In r8_mq_south_w, TIME CRISIS and "
         "CHAMPION STREET FIGHTER EDITION read complete; LEGENDS ULTIMATE and "
         "RIDGE RACER are each partly hidden by the other's cabinet round the "
         "SW corner -- occlusion from that camera, not a mapping defect."),
    ])),
    ("art_consumed", collections.OrderedDict([
        ("art_g0_g1",
         "Consumed as delivered. Both modules import, all 34 of their panels "
         "render through atlas4, and no two modules claim the same key "
         "(atlas4 raises on that and did not). Their deleted edge trim is now "
         "real bead geometry and their full-bleed grounds reach the tile "
         "edge."),
        ("art_g2",
         "Consumed, including its BLOCKING hand-off: a2kit.DECK_MAT now "
         "carries street-fighter-2-champion-edition and terminator-2 as 'D'. "
         "Its diagnosis was right -- ART_DK's #4c4c4c is 0.0723 linear against "
         "ART_D's 0.584, and with art_g2's own 3.05 pre-division on top the "
         "diffuse term sat under the scene's ambient floor. Both south decks "
         "now print in r8_full_south; round 7's frame showed them as flat "
         "plates."),
        ("front_rect_inset",
         "art_g2's FRONT_RECT already asked for inset_ft 0.06 on its four; the "
         "other twelve now get 0.045 from the new default, which is the number "
         "that actually puts vinyl under this bead."),
    ])),
    ("atlas_quant",
     "atlas4.QUANT is now per panel class: marquee/front/riser stay at 20, "
     "everything else goes to 28 (QUANT_CLS / QUANT_REST). Round 4's 'banding "
     "begins at 24' was measured on a MARQUEE -- the one class with a large "
     "soft ground behind big letterforms. A flank at 42 px, a deck at 52, a "
     "bezel and a screen are small dense panels where a coarser step is "
     "invisible. MEASURED all three runs packed: 141.00 KB everything at 20, "
     "126.54 everything at 24 (marquees band), 136.42 as shipped. No artwork "
     "removed to reach it."),
    ("payload", {"Arcade Cabinets East": 203.3, "Arcade Cabinets South": 217.6,
                 "Arcade Cabinets North": 183.2, "room_total_kb": 1527.1,
                 "cap_kb": 1536.0, "headroom_kb": 8.9,
                 "triangles": {"east": 3390, "south": 3590, "north": 3106}}),
    ("shots", ["scratchpad/arc4/shots/r8_full_east.png",
               "scratchpad/arc4/shots/r8_full_north.png",
               "scratchpad/arc4/shots/r8_full_south.png",
               "scratchpad/arc4/shots/r8_mq_east.png",
               "scratchpad/arc4/shots/r8_mq_north.png",
               "scratchpad/arc4/shots/r8_mq_south_w.png",
               "diagnostics: _diag_graze1.png (bead at a grazing angle, 5x), "
               "_diag_bead_tmnt.png, _diag_sw_end.png, "
               "_diag_r8_marq_east.png"]),
    ("still_open", [
        "THE APRON IS NOT PRINTED. The sloped face between the printed front "
        "and the control deck (profile edge P2->P3, ~0.3 ft tall on every "
        "machine) is bare carcase. In the photographs it carries the machine's "
        "artwork -- the Turtles brick riser runs onto it. The fix is one extra "
        "quad per machine (~0.15 KB each) mapped to the top k of the front "
        "tile, and it needs each art module to declare its own riser fraction; "
        "guessing k would cut a title in half.",
        "Legends Ultimate and Ridge Racer occlude each other's marquee from "
        "mq_south_w. Neither is fully legible in any judged frame. That is the "
        "room's real layout round the SW corner, not a mapping bug, and fixing "
        "it means moving a cabinet.",
        "The carcase renders as flat colour (sd 13-20 across the probe mask, "
        "which is shading not texture) against photographed black melamine at "
        "sd 16-25. Painted melamine really is flat, but a critic cropping in "
        "will find no grain.",
        "art_g0 leaves the title stamped twice on marvel-super-heroes, tmnt and "
        "nba-jam -- once on the kick panel and once on the riser -- because the "
        "photographs show two. It declared this and I did not overrule it.",
        "mortal-kombat.side and nfl-blitz.side still carry round-5 ghost title "
        "watermarks on flanks the roster calls featureless. Invisible in every "
        "judged frame (run gaps 0.00-0.16 ft) but a critic who crops a flank "
        "can count a third occurrence.",
    ]),
])

io.open(P, "w", encoding="utf-8").write(json.dumps(d, indent=1,
                                                   ensure_ascii=False))
print("written %d bytes" % os.path.getsize(P))
