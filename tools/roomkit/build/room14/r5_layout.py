"""Write round 5's facts back into tools/roomkit/layout.json and rooms/14.json."""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RK = os.path.abspath(os.path.join(HERE, "..", ".."))
P = os.path.join(RK, "layout.json")
d = json.load(open(P, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)

d["_round5"] = (
    "ROUND 5 - the bed, the textures and the density. (1) THE BED IS A KING. Round 3 'proved' a "
    "queen off the photo and rounds 3-4 carried it, while THIS FILE contradicted itself: "
    "_wall_derivation records the plan's bed icon at x 6.85..13.95 (7.10 ft) and _north_wall_budget "
    "then built a 5.35 ft queen inside it. The queen reading was a camera artifact - the photo is "
    "shot from the room's EAST side, so the headboard is ~25 deg off square and foreshortens by a "
    "quarter. Re-measured against things at the SAME depth: the two shams span 235 px where the "
    "headboard cap spans 283 px for 7.10 ft (39.9 px/ft), so each sham is 2.95 ft - a 36 in KING "
    "pillow. (2) EVERY SOFT SURFACE IS NOW A TONE FIELD (build/room14/r5_raster.py), not a height "
    "field. Round 4 metered rug sigma 3.6 / duvet 2.8 against the photo's ~18 local / ~12; this "
    "scene has one sun and a large isotropic hemisphere term, so a 20 deg normal tilt buys nothing "
    "- contrast has to be ALBEDO. Round 5 meters rug 15.3, duvet 6.3..8.5 local / 17.1 broad, "
    "shams 5.7..6.5 local / 14.0 broad. (3) The invented white Tall Chest is DELETED and the "
    "photo's pale ARMCHAIR + LEANING MATTRESS PANELS stand there instead. (4) Density: bags + "
    "folded laundry on the dresser, a plant, a second lamp, a bin, tablet/bottle/speaker on the "
    "nightstand, a sill cushion, two floor vents, a laundry hamper. (5) The wall TV from "
    "Master Bed 2 is built. (6) The dresser is rebuilt with FOUR drawers (two over one over one) "
    "and real plank grain. (8) BUG FIXED: the recessed cans rendered as white blobs on the FLOOR "
    "from the dollhouse poses - roomkit.glb.cylinder winds BOTH end caps the same way, so with "
    "double_sided=False the up-facing cap survived the ceiling's back-face cull. They are single "
    "down-facing discs now. PAYLOAD: the room went 3.41 MB -> 1.74 MB (rug 1.13 -> 0.14, wall art "
    "1.43 -> 0.32). Build scripts: build/room14/r5_*.py; run r5_place.py.")

d["_vestibule_finding"] = (
    "INVESTIGATED, NOT CHANGED. The round-4 critic claimed the entry vestibule is ~8 ft off the "
    "plan. Re-derived independently from docs/floor plan/Second Floor Plan App.png through "
    "plan_retrace.py's own transform (local x = 20.513 + (461-px)/27.592, local z = "
    "(1720.5-py)/27.592 - the same transform that reproduces all four blue window marks to within "
    "0.05 ft). Wall-pixel scans: the far-south wall at py 1196..1204 runs px 456..494, then a GAP "
    "px 494..575, then wall px 575..1032. That gap is the door to the 2F hallway and it sits at "
    "local x 16.38..19.32. The alcove containing it is bounded by the east wall (px 456..465 = "
    "local x 20.37..20.69) and a partition at px 593..601 (local x 15.44..15.73), i.e. local x "
    "15.73..20.37, 4.64 ft wide, HARD AGAINST THE EAST WALL. The critic's 15.73..20.33 is right. "
    "The model puts the leg at x 7.86..15.58 (7.72 ft, centred) - about 7.9 ft too far west. What "
    "actually occupies x 7.86..15.73 in the plan is a separate walled nook that opens into the "
    "bedroom over only x 11.67..15.44 and has no hallway door. Corroboration from the photos: from "
    "an east alcove looking north the dark Foreground Chest on the east wall is immediately to the "
    "camera's right, which is exactly what Master Bed 1 shows, and the near-left wall return in "
    "the primary photo is the x=15.6 partition. GEOMETRY WAS NOT TOUCHED - moving it is out of a "
    "builder's remit and would leave an unassigned gap in the floor.")

pieces = d["pieces"]
pieces["Bed"].update({
    "size_ft": [7.10, 4.42, 7.60], "pos": [10.40, 0.0, 3.875], "rot": 0,
    "note": ("REBUILT AS A KING (r5_bed.py). Mattress 6.33 x 6.67, frame 6.75, headboard 7.10 "
             "spanning the plan's own bed icon x 6.85..13.95, overall length 7.55, headboard "
             "4.42 (measured against the nightstand at 64.5 px/ft). The photo's headboard is a "
             "horizontal PLANK field between two end stiles under a top cap that OVERHANGS both "
             "sides and projects forward. TWO storage drawers in the foot plinth, not one. The "
             "knit coverlet, the quilted grey-piped shams and the sleeping pillows are TONE "
             "FIELDS. pos.z 3.875 lands the headboard's back face at local z 0.075.")})
pieces["Rug"].update({
    "size_ft": [8.90, 0.062, 9.80], "pos": [9.75, 0.045, 7.45], "rot": 0,
    "note": ("REBUILT as a tone field (r5_rug.py): 1.13 MB -> 0.14 MB and sigma 3.6 -> 15.3. Pile "
             "x 5.30..14.20, z 2.55..12.35, re-sized for the king (~1 ft past the west rail, "
             "level with the nightstand on the east, 4.7 ft past the foot). Banded flat/looped/"
             "chevron pile with a per-band pitch jitter - a fixed repeat renders as a venetian "
             "blind. The bed's contact shadow is baked into the field. pos.y 0.045 keeps the "
             "backing clear of the slab's polygonOffset.")})
pieces["Wall Art"].update({
    "size_ft": [5.95, 5.45, 0.062], "pos": [10.40, 5.76, 0.06], "rot": 0,
    "note": ("RE-SAMPLED FROM THE PHOTOGRAPH (r5_art.py): the canvas's four corners in "
             "Master bedroom.jpg are un-keystoned, area-averaged into a 69 x 109 grid, quantised "
             "to 10 tones and merged into runs - 1.43 MB -> 0.32 MB for the same painting. The "
             "photo ratios round 2 measured still hold (canvas/headboard 0.83, gap 0.19 of the "
             "headboard width); the headboard changed 5.30 -> 7.10, so the canvas goes 4.44 -> "
             "5.95 wide and the gap 1.00 -> 1.34, i.e. pos.y 5.76. Palette solved backwards "
             "through tone.radiance_for_byte off a measured render: metered 161.5 +/- 30.1 "
             "against a 221 wall = 0.730 (photo 0.742 +/- 37.3). TRAP: the stretcher box's front "
             "face must NOT be coplanar with the paint plane - at 0.055 they z-fought and the "
             "canvas metered 191 flat.")})
pieces["Nightstand"].update({
    "pos": [15.05, 0.0, 1.50],
    "note": ("Unchanged GLB, moved east to x 13.95..16.15 now the king's rail is at 13.95. It "
             "overlaps Window North East's x band (15.83) by 0.32 ft, but its top is 2.10 and the "
             "sill is 2.20, so nothing collides.")})
pieces["Dresser"].update({
    "size_ft": [1.595, 6.44, 5.00], "pos": [0.873, 0.0, 5.91], "rot": 90,
    "note": ("REBUILT (r5_dresser.py). WEST WALL CONFIRMED by the round-4 critic with a better "
             "argument than the builder's: the dresser mirror reflects the north window, the red "
             "canvas AND the bed headboard, and a mirror cannot reflect the wall it hangs on. "
             "Round 4's GLB had SIX drawers where the photo has FOUR - two over one over one - "
             "and read as flat plastic grey. Now four drawers, dark bar pulls, tapered legs and a "
             "weathered plank-grain TONE FIELD (metered sd 52 across the piece). Case 4.90 x 2.62 "
             "x 1.45 off the plan icon (x 0.21..1.66, z 3.32..8.50); near-square mirror 3.55 x "
             "3.30 painted in layers with the reflected window, canvas and headboard.")})
pieces.pop("Tall Chest", None)
pieces["Master Armchair"] = {
    "size_ft": [2.72, 2.83, 2.80], "pos": [3.30, 0.0, 1.85], "rot": 18,
    "note": ("NEW. Replaces the invented white Tall Chest, which round 4's own note admitted was "
             "inference and which stood exactly where the photo has this chair. The plan's "
             "armchair icon is x 1.05..4.93, z 0.24..4.08 - in front of Window North - and the "
             "photo shows a pale cream chair there with a rounded back and tapered wooden legs. "
             "Photo patch 196.6 / wall 176.2 = 1.116; the fabric field is parked a little under "
             "that so the weave has somewhere to go before it clips.")}
pieces["Master Lean Panels"] = {
    "size_ft": [1.10, 3.55, 2.02], "pos": [0.62, 0.0, 1.70], "rot": 90,
    "note": ("NEW. Three pale slabs leaning on the west wall in the NW corner - the stack of "
             "mattress/headboard panels the photo shows beside the dresser, and the other half of "
             "what the Tall Chest was standing in for.")}
pieces["Master TV"] = {
    "size_ft": [4.62, 3.14, 0.23], "pos": [5.20, 2.825, 13.151], "rot": 180,
    "note": ("NEW, from Master Bed 2.jpg - the largest object on that wall and, in a Home "
             "Assistant house, a controllable device. Sized off the two doors flanking it in that "
             "photo (6.67 ft leaves at 178 px and 97 px -> 26.7 and 14.5 px/ft): panel ~3.9 ft "
             "tall x ~5.1 ft along the wall, i.e. a 65-70 in set, bottom ~3.3 ft off the floor, "
             "over a white soundbar. PLACEMENT CAVEAT: centred at x 5.20 so it sits inside "
             "x 2.55..7.86, which the FLOOR PLAN draws as solid wall. It overlaps the model's "
             "second door opening (edge 4, x 4.93..7.86), which the plan does not have - the "
             "plan's only door on this wall is at x 0.72..3.59, matching the model's other "
             "opening. Openings were confirmed in round 4 and were left alone.")}
for n, sz, pos, rot, note in [
    ("Master Dresser Clutter", [2.16, 1.56, 0.62], [0.95, 3.04, 5.20], 90,
     "Kraft shopping bag, a heap of folded dark/mid/pale laundry and a second cloth pile - what "
     "the photo has all over this dresser top."),
    ("Master Plant", [0.90, 1.03, 0.68], [0.85, 3.04, 3.95], 0,
     "The potted plant on the dresser's north end."),
    ("Master Lamp Small", [0.84, 1.36, 0.83], [0.88, 3.04, 8.00], 0,
     "Second lamp, dresser south end."),
    ("Master Bin", [1.02, 1.04, 1.00], [0.65, 0.0, 9.11], 0,
     "The white bin on the floor by the dresser."),
    ("Master Nightstand Props", [1.34, 0.96, 0.73], [14.80, 2.10, 1.62], 6,
     "Tablet on a stand, water bottle, puck speaker."),
    ("Master Sill Cushion", [1.32, 1.00, 0.34], [20.10, 2.52, 3.90], 270,
     "The zigzag cushion on the east window sill."),
    ("Master Floor Vent A", [0.98, 0.03, 0.42], [17.30, 0.012, 1.10], 0,
     "Floor grille by the nightstand. Named with 'floor' so objects.js keeps it unpickable."),
    ("Master Floor Vent B", [0.42, 0.03, 0.98], [1.10, 0.012, 11.40], 90,
     "Floor grille on the west side."),
    ("Master Laundry", [1.40, 1.90, 1.12], [1.10, 0.0, 12.51], 8,
     "Hamper with a stack of folded laundry."),
]:
    pieces[n] = {"size_ft": sz, "pos": pos, "rot": rot, "note": note}

pieces["Ceiling"]["note"] = (
    "ROUND 5 rebuilt from r4_ceiling as r5_ceiling.py for ONE bug fix and nothing else: the six "
    "recessed cans rendered as white blobs on the FLOOR from the dollhouse poses. "
    "roomkit.glb.cylinder() winds both end caps the same way, so its bottom cap faces UP; with "
    "double_sided=False (which the ceiling needs so its slopes cull from above) that left one "
    "bright emissive disc per can facing up through the culled ceiling, and at a 50 deg dollhouse "
    "elevation a disc 14 ft up projects onto the floor. Each can is now a single "
    "explicitly-wound DOWN-facing disc. ") + pieces["Ceiling"]["note"]

d["_metered_round5"] = collections.OrderedDict([
    ("_pose", "the round-4 comparison pose in _room._camera_warning, --day, level 2"),
    ("north wall", 221.3),
    ("wall art", "161.5 sd 30.1"),
    ("duvet/coverlet", "228 broad, sd 17.1 broad / 6.3..8.5 on 56 px patches"),
    ("shams", "237.5, sd 5.7..6.5 on 40 px patches / 14.0 broad"),
    ("rug", "230, sd 15.3 broad / 12..19 on 56 px patches"),
    ("floor", 139.5),
    ("dresser", "130.5 sd 52.0"),
    ("_photo", "wall 176.2 sd 2.2; coverlet 192.9 sd 12.3 local; shams 193.0 sd 22.0; rug "
               "142..204 with local sd 9..33; floor ~104; dresser drawer fronts 124..136; canvas "
               "130.7 sd 37.3"),
    ("_read", "Round 4's rug 3.6 / duvet 2.8 are gone: the rug's 15.3 is on the photo's number "
              "and the coverlet is 2.3x better but still short locally. The binding constraint is "
              "HEADROOM, not method - the photo's wall sits at 176/255 and ours at 221/255, so a "
              "coverlet at the photo's 1.095 of the wall would be byte 242 with 13 bytes of room "
              "above it. The coverlet mean is deliberately parked at 1.03 to buy the spread."),
])

d["_still_wrong"] = [
    "THE ENTRY VESTIBULE IS ABOUT 7.9 FT OFF THE PLAN - see _vestibule_finding. Moving it is out "
    "of a builder's remit; until it moves, no pose can reproduce the primary photo's vantage.",
    "The model's second door on edge 4 (x 4.93..7.86) is not in the floor plan, which draws that "
    "wall solid; the TV is centred on plan-solid wall and overlaps it. Openings were confirmed in "
    "round 4 and were left alone.",
    "Chair is still a black mesh task chair; the photo shows a tall upholstered nailhead chair. "
    "181 KB, the third-largest piece in the room.",
    "The coverlet meters sigma 6.3..8.5 on small patches against the photo's ~10..14 - better than "
    "round 4's 2.8 but not there. See _metered_round5._read for why.",
    "Nightstand, Desk and Foreground Chest are still round-2 GLBs at ~0.78 of the wall against the "
    "photo's 0.67..0.72.",
    "The room is 1.74 MB against the 1.5 MB aim (was 3.41 MB). Bed 342 KB and Wall Art 318 KB are "
    "both over the 300 KB per-piece cap; Chair 181 KB is a round-2 piece.",
    "The comparison pose is 88 deg vertical where the photo is an ultrawide, so the render always "
    "reads further away and tidier.",
]

json.dump(d, open(P, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("layout.json updated,", len(pieces), "pieces")

# ---- the per-room map ------------------------------------------------------
os.makedirs(os.path.join(RK, "rooms"), exist_ok=True)
room = collections.OrderedDict([
    ("_note", "Room 14 (Master Bed), round 5. The full placement map with every derivation lives "
              "in tools/roomkit/layout.json, which is this room's own file - this is a pointer "
              "plus the round-5 headline so `rooms/` is complete."),
    ("room_id", 14), ("level", 2),
    ("map", "tools/roomkit/layout.json"),
    ("build", "tools/roomkit/build/room14/r5_place.py (idempotent: builds + re-places everything)"),
    ("payload_mb", 1.74),
    ("round5", d["_round5"]),
    ("vestibule_finding", d["_vestibule_finding"]),
    ("still_wrong", d["_still_wrong"]),
])
json.dump(room, open(os.path.join(RK, "rooms", "14.json"), "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)
print("rooms/14.json written")
