"""Write the round-7 record into tools/roomkit/rooms/2.json."""
import collections
import io
import json

P = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools\roomkit\rooms\2.json"
d = json.load(io.open(P, encoding="utf-8"),
              object_pairs_hook=collections.OrderedDict)

d["_round7_controls"] = collections.OrderedDict([
    ("date", "2026-08-31"),
    ("scope",
     "Round 7 engine pass. Rebuilt ONLY Arcade Cabinets East / South / North. "
     "No room geometry, no footprint, no other piece, no poses.json, no "
     "frontend/js, no backend/, no Flask restart, and no art module edited."),
    ("defect_it_answers",
     "Round 6 was rejected 0 of 4 and all four critics named the same "
     "surface: 'the pushbuttons are painted into the control-deck texture "
     "rather than modelled: flat 2-3px coloured lozenges with no dome, no rim "
     "shadow and no specular, and the identical six-dot cluster repeats on "
     "all six machines'."),
    ("root_cause",
     "TWO causes, both found by reading the code rather than the render. "
     "(1) The buttons WERE geometry, and the geometry was a lozenge: "
     "art_g1.button_cap is a domed n-gon FAN and nothing else -- an apex, one "
     "ring at y = h*(1-dome), seg triangles, NO SIDE WALL. It never touches "
     "the deck, so every cap floated 0.015 ft above the artwork with open air "
     "under its rim, and rose 13 degrees off flat. (2) decks5._btn defaulted "
     "`emis` to True for any colour under luma 190, so 128 of the room's 152 "
     "caps rendered through cmat(col, 0.34, 0, col, 0.75) -- emissive at "
     "strength 0.75 in their own hue. An emissive surface takes no highlight "
     "and no shading, so whatever geometry stood under it rendered as a flat "
     "disc of pure colour. art_g1's CONTROL_FINISH asked for exactly this to "
     "be removed, in writing, and round 6 did not read the key."),
    ("built", collections.OrderedDict([
        ("button",
         "ar2.btn_geo(r, cap_r, h, rise, seg=6) -- ring 0 at y=0 radius r (the "
         "flange where it meets the deck), ring 1 at y = h-rise radius cap_r "
         "(the shoulder), apex at y=h. One smooth part: 13 verts / 18 tris. "
         "The truncated cone between rings 0 and 1 faces sideways and "
         "down-and-out, so under this room's overhead sun it renders darker "
         "than both the deck it stands on and the cap it carries -- the rim "
         "the critics asked for, as real geometry that moves with the camera "
         "and vanishes in a plan view."),
        ("emissive",
         "removed from every cap in the room except art_g3's two Ridge Racer "
         "whites, which that module flags as lit. 128 -> 2."),
        ("materials",
         "new a2btn at roughness 0.70 carries every UP-FACING cap (button "
         "crowns, ball tops, bat tops, trackballs). a2hw stays at 0.42 for "
         "gun bodies, holster channels, coin plates, the Star Wars yoke and "
         "Ridge Racer's wheel, which meter correctly and were never flagged. "
         "Cost: exactly one extra glTF primitive per cabinet GLB."),
        ("trackball",
         "rings 3 -> 4, routed through a2btn, authored albedo capped at "
         "_TB_CEIL 0.78 (#f2f2ec -> #bdbdb8)."),
        ("dark_hardware",
         "_HW_FLOOR 44 -- vertex colours on a2btn parts are lifted so their "
         "brightest channel is at least 44/255, hue preserved. DECLARED: this "
         "is the same kind of exposure correction a2kit already applies to "
         "printed artwork through ART_D / ART_DK / ART_DM, applied to "
         "hardware. It does not overwrite any art module's authored hex."),
    ])),
    ("specs_consumed", collections.OrderedDict([
        ("art_g0",
         "cap_r and dome_rise now reach the render; round 6 discarded both and "
         "drew h*(1-0.45). pad_r correctly stays printed, not built."),
        ("art_g1",
         "`emissive` (False on all 58 caps) and `profile` now read. base_r "
         "stays printed. CONTROL_FINISH is answered by a2btn."),
        ("art_g2",
         "unchanged in shape; r_ft / h_ft / dust_* / round_flat all still "
         "arrive. `inferred` now flows per machine instead of decks5's stale "
         "hard-coded tuple -- art_g2 promoted legends-ultimate to READ this "
         "round and declared champion-edition inferred instead."),
        ("art_g3",
         "`emissive` per button; the only route to an emissive cap left."),
        ("totals",
         "152 buttons, 21 sticks, 2 trackballs, 4 guns, 1 yoke, 1 wheel across "
         "16 machines. Per-machine counts: $PY scratchpad/arc4/decks5.py"),
        ("declared_not_readings",
         ["street-fighter-2-champion-edition -- art_g2 inferred: True",
          "marvel-super-heroes -- art_g1's own 'DECLARED CHOICE, not a "
          "reading'"]),
    ])),
    ("proof_layouts_differ",
     "scratchpad/arc4/r7eng/shots/sbs_sheet.png -- four machines' decks shot "
     "at one scale (each camera 3.35 ft off its own deck centre, 1.75 ft "
     "above it, fov 38): tmnt 2 sticks / 13 buttons, nba-jam ball + BAT top / "
     "8 buttons, mortal-kombat 2 sticks / 16 buttons, golden-tee no stick / "
     "trackball / 2 buttons. Nothing about those four frames is shared."),
    ("roughness_metered", collections.OrderedDict([
        ("method",
         "a2btn swept 0.42 / 0.62 / 0.72, room rebuilt and re-shot at each "
         "value, sampled on scratchpad/arc4/r7eng/shots/p0*_msh.png."),
        ("white_cap", "234.3 / 234.3 / 234.3 -- roughness does not move a pale "
                      "cap here at all"),
        ("blue_cap", "121.9 / 120.4 / 118.2"),
        ("black_ball_top", "3.7 / 5.8 / 7.4  (max 25.1 / 45.6 / 58.9)"),
        ("finding",
         "a2hw's 0.42 was NOT the blowout the round-6 note blamed it for. The "
         "blowout was the emissive. Roughness only moves the DARK hardware, "
         "and it moves it UPWARD, so 0.70 was chosen: it matches art_g0's "
         "a2ball request, sits just above art_g2's 0.62, and costs the "
         "coloured caps nothing. art_g1's 0.26 request is refused ON "
         "MEASUREMENT -- it is the value that makes the black ball tops "
         "darkest, which is the opposite of what its note predicts."),
        ("photo_reference",
         "docs/photos-jpg/Arcade Room v4 6.jpg px (460,360)-(600,440) at 10x: "
         "deck 185.4, white cap 223.9, red cap 91.7, blue cap 110.2, black "
         "ball top 48.8."),
        ("render_final",
         "deck 177.2 (within 5% of the photo), white cap 234.3, red 139.1, "
         "blue 118.7, black ball top 12.8 (max 74.3)."),
        ("unreachable",
         "the black ball tops. Photo 0.264 of their own deck; round 6 0.033; "
         "round 7 0.072 -- 2.2x better and still 3.7x short. The "
         "photograph's 48.8 is mostly sheen off curved black plastic and this "
         "scene has one sun and no bounce, the limit ROOM-BRIEF documents. "
         "Reaching 48.8 by albedo alone needs an authored ~#82828a, which is "
         "mid grey, not black, and would be wrong in the dollhouse view and "
         "on the night ramp."),
        ("trackball",
         "crown/fairway ratio -- photo 1.217, round 6 1.255, round 7 1.287. "
         "Value was never the defect: neither round clipped, and the "
         "photograph's own trackball is 93% clipped to white. What changed is "
         "that the crown now carries a dome gradient and a dark bezel ring "
         "instead of reading as a featureless white cap."),
    ])),
    ("payload", collections.OrderedDict([
        ("room_total_kb", 1523.9),
        ("cap_kb", 1536.0),
        ("headroom_kb", 12.1),
        ("was_kb", 1535.6),
        ("pieces_kb", {"Arcade Cabinets South": 213.7,
                       "Arcade Cabinets East": 205.5,
                       "Arcade Cabinets North": 181.7}),
        ("triangles", {"Arcade Cabinets East": 2994,
                       "Arcade Cabinets South": 3314,
                       "Arcade Cabinets North": 2882,
                       "total": 9190, "round6_total": 7334}),
        ("chain_measured_on_the_three_cabinet_glbs", [
            "round-7 art on round-6 geometry            625.9 KB   7334 tris",
            "  - emissive off every cap (26 prims)      605.1 KB   7334 tris  -20.8",
            "  + btn_geo flange + dome                  644.0 KB   8819 tris  +38.9",
            "  + uint16 glTF indices (LOSSLESS)         592.1 KB   8819 tris  -51.9",
            "  + trackball rings 3->4, a2btn routing    592.7 KB   8851 tris   +0.6",
            "  + seg 6 on every cap                     600.9 KB   9190 tris   +8.2",
            "round-6 shipping, for comparison           612.6 KB   7334 tris",
        ]),
        ("marginal_button_cost_in_a_saved_glb", [
            "round 6  domed fan, smooth            232 B/button    6 tris",
            "round 7  flange+dome, SMOOTH          472 B/button   18 tris",
            "round 7  flange+dome, FLAT SHADED    1620 B/button   18 tris",
            "The round-6 gun agent's finding holds and then some: the same 18 "
            "triangles cost 3.4x more flat-shaded, because a flat face "
            "duplicates its vertices to carry its normal. 152 buttons flat "
            "would have been +211 KB. Script: scratchpad/arc4/r7eng/btncost.py",
        ]),
        ("the_lever",
         "tools/roomkit/glb.py now writes UNSIGNED_SHORT indices whenever a "
         "primitive fits in 65535 vertices, which is every primitive this "
         "project has ever exported. It was writing UNSIGNED_INT "
         "unconditionally and spending 6 bytes a triangle on zeros. -51.9 KB "
         "on these three GLBs for byte-identical geometry, and every room in "
         "the house gets the same on its next rebuild. Existing files are "
         "untouched, bufferView offsets are already 4-aligned so the 2-byte "
         "element alignment is satisfied, and the guard keeps the old path "
         "for anything over 65535 vertices."),
        ("levers_declined", [
            "art_g0.SIZE_KEY_REQUEST      measured -0.4 KB -- NOT TAKEN",
            "art_g2.SIZE_KEY_REQUEST      measured -0.8 KB -- NOT TAKEN",
            "art_g1's QUANT 20 -> 22      measured -6.8 KB -- NOT TAKEN",
            "art_g2's SIZE[front] 92->86  measured -3.8 KB -- NOT TAKEN",
            "All four cut artwork resolution on surfaces this room is judged "
            "on -- marquees, lower fronts, two decks, the four south screens. "
            "The uint16 lever pays for the whole round without them, so "
            "nothing was cut. Measured with scratchpad/arc4/r7eng/levers7.py, "
            "which builds the real GLBs rather than summing atlas PNGs.",
        ]),
    ])),
    ("still_open_not_fixed", [
        "pac-man's deck is a plain black overlay -- art_g0 declares this "
        "rather than inventing artwork the photographs deny. The round-6 "
        "'AC-MAN' clipping IS gone: art_g0 removed the invented legend and "
        "added _text_fit.",
        "terminator-2's and marvel-vs-capcom's decks carry no game artwork. "
        "Both art modules declare it against the photographs.",
        "the four south screens at 3.5-8.6 grey against the north run's 60-66 "
        "-- ROOM-BRIEF's documented one-sun-no-bounce limit, untouched.",
        "black ball tops at 0.072 of their own deck against the photo's 0.264 "
        "-- see roughness_metered.unreachable.",
    ]),
    ("files_touched", [
        "scratchpad/bsmt/ar2.py       btn_geo, a2btn, _hw, _tb_col, controls()",
        "scratchpad/arc4/decks5.py    _btn (emis defaults False, cap_r, rise), "
        "_from_g0, _from_g1, INFERRED derived from the modules",
        "tools/roomkit/glb.py         uint16 indices when they fit",
        "scratchpad/arc4/r7eng/       measure.py, levers7.py, probe.py, "
        "decks_sbs.py, btncost.py, meter.py, record.py",
        "backups: scratchpad/bsmt/ar2_r6.bak.py, a2kit_r6.bak.py, "
        "scratchpad/arc4/decks5_r6.bak.py",
    ]),
    ("shots", ["scratchpad/arc4/shots/r7_full_east.png",
               "scratchpad/arc4/shots/r7_full_north.png",
               "scratchpad/arc4/shots/r7_full_south.png",
               "scratchpad/arc4/shots/r7_mq_east.png",
               "scratchpad/arc4/shots/r7_mq_north.png",
               "scratchpad/arc4/shots/r7_mq_south_w.png",
               "scratchpad/arc4/r7eng/shots/sbs_sheet.png  (layouts-differ "
               "proof)"]),
    ("freshness",
     "newest room-2 GLB 2026-08-31 06:34:09 (Arcade Cabinets North); oldest "
     "judged PNG 2026-08-31 06:34:20 (r7_full_east). Every judged frame "
     "postdates every room-2 GLB by 11.8 s or more. The previous r7_*.png "
     "were deleted before shooting."),
    ("black_slab_check",
     "all six judged frames looked at; no pure-black surface, so no inverted "
     "normals."),
    ("check_pick", "OK -- 22/49 floor samples resolve to room 2, 0 off-room."),
    ("rebuild",
     "cd tools; then in python: sys.path gets ..\\tools, ..\\scratchpad\\bsmt, "
     "..\\scratchpad\\arc4, ..\\scratchpad\\arc4\\art; import ar2; "
     "[ar2.BUILDERS[k]() for k in ('east', 'south', 'ncab')]"),
])
d["_payload_kb"] = 1523.9

io.open(P, "w", encoding="utf-8").write(json.dumps(d, indent=2))
print("rooms/2.json updated;", len(d), "top-level keys")
