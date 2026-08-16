"""Rewrite tools/roomkit/rooms/6.json with the round-3 record."""
import json

P = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools\roomkit\rooms\6.json"
d = json.load(open(P, encoding="utf-8"))

d["_round3"] = (
    "Round 2 was FAILED by a critic on surfaces, hardware and artifacts; the geometry was confirmed "
    "correct and was NOT touched (footprint, aisles 3.10/3.57 ft, fridge run tight to the real south "
    "wall, pass-through open to the living room, black dishwasher west of the sink, six cans, nothing "
    "intersecting the bay). Round 3 rebuilt the surface program. The one new shared module is "
    "scratchpad/kbuild/kraster.py: a tone-field RASTERISER. Round 2 drew every texture as discrete "
    "marks -- veins as little boxes walking across the slab, contact shadows as five nested "
    "rectangles, the rug as flecks -- where the photograph has a continuous FIELD. kraster samples "
    "field(u,w) -> t in [0,1], quantises it onto a palette, and merges equal-tone cells into one quad "
    "per run, so a surface gets a real gradient at close to a plain plane's triangle count and the "
    "quantisation contours are irregular: no rings, no bands, no stripes. Every quad's winding is "
    "checked against the face normal it is supposed to carry.")

d["_metering_r3"] = {
    "_how": "photo patches cropped with scratchpad/kbuild/crop.py; render patches from the same "
            "region of the matching pose, --level 1 --day; luminance 0.2126/0.7152/0.0722.",
    "island top": {"photo_F": "205.0 / sd 24.9", "round2": "222.6 / sd 18.2",
                   "round3": "204.4 / sd 20.2"},
    "backsplash": {"photo_F": "173.4 / sd 19.0", "round2": "163.0 / sd 5.1",
                   "round3": "173.1 / sd 12.0"},
    "upper door": {"photo_F": "205.8 / sd 10.9", "round3": "207.0 / sd 6.8"},
    "counter": {"round3": "208.8 / sd 8.8"},
    "floor": {"photo_A": "116.4 / sd 23.5", "round2": "127.7 / sd 23.7",
              "round3": "117.3 / sd 32.1; open floor clear of any contact shadow 113.6 / sd 7.8"},
    "rug": {"photo_A": "121.4 / sd 51.5", "photo_F": "123.7 / sd 36.7",
            "round3": "116.6 / sd 54.4"},
    "fridge side, corner_se pose": {"photo_A fridge door": "54.7", "round2": "0, pure black",
                                    "round3": "41.9"},
    "wall spread, roomkit.meter": "54 bytes against round 2's 55 -- no emissive wall wash added",
}

d["_critic_fixes_r3"] = {
    "1 stone program": (
        "REBUILT. veins() is deleted. top_stone()/splash_stone() in kcommon.py drive "
        "kraster.stone_field: a low-frequency cloud (the mottling), fine grain (stops large flats "
        "reading as paint), and a kraster.Veins distance field -- a branching NET of soft strokes "
        "with a short step and high meander so they curve instead of running as straight diagonals. "
        "The palettes TOPS/SPLASH are 16-step ramps calibrated on this renderer's measured response "
        "(albedo 74 lands on 110, 192 on 215, 205 on 222.6; slope about 0.89 low and 0.58 in the "
        "highlights), so the field albedo and the vein-core albedo are each solved for the rendered "
        "value the photo wants."),
    "2 island too bright": (
        "222.6 -> 204.4 against the photo's 205.0, sd 18.2 -> 20.2 against 24.9. Done with albedo, "
        "not exposure: the TOPS ramp tops out at #b9b9b6."),
    "3 upper hardware REGRESSION": (
        "FIXED, after re-cropping photo F at 2x rather than trusting the finding. Every upper door "
        "carries a black vertical bar pull low on the meeting stile; base doors have small round "
        "knobs and drawers horizontal bars. two_door() takes kind= and every upper call site passes "
        "'v'."),
    "4 contact shadows REGRESSION": (
        "REBUILT as kraster.Shadows: one exponential distance field over the whole floor covering "
        "all nine occluders at once, rasterised at 0.062 ft cells onto 15 TRANSLUCENT steps. The "
        "translucency is the point -- an opaque decal paints one flat tone over planks that are "
        "themselves varying, so its outline shows as a tone discontinuity however fine the falloff "
        "is, which is why the first round-3 attempt still read as a stepped patch. Alpha darkens "
        "what is underneath instead. Measured 102 under the island against 116 on open floor with "
        "no visible boundary."),
    "5 floor contrast REGRESSION": (
        "127.7 / sd 23.7 -> 117.3 / sd 32.1 against the photo's 116.4 / sd 23.5; on open floor away "
        "from any contact shadow 113.6. The palette is narrower (six greys spanning 1.64x, was "
        "1.94x) and plank tone is drawn by a RANDOM WALK across it so no board sits five steps from "
        "its neighbour, which is what made round 2 a patchwork. GAIN 0.635 -> 0.560."),
    "6 pure black surface": (
        "DIAGNOSED AND FIXED, but the critic's diagnosis was wrong. probe.py raycast that pixel: it "
        "is the FRIDGE's east side face 1.6 ft from the stock corner_se camera, material side = "
        "DoubleSide. Not an inverted normal -- every roomkit Material defaults to "
        "double_sided=True. The cause is albedo: #141517 with no emissive is linear 0.006 and a face "
        "turned away from this scene's single sun lands on literally 0. BLACK and GLASSBLK now carry "
        "an emissive floor and appliances use APPL/APPL_LO/APPL_HI with sheen bands. That face "
        "meters 41.9 against photo A's fridge door at 54.7."),
    "7 cased openings": (
        "cased_opening() builds each one with jamb linings and a head lining running AWAY from the "
        "room into the wall cavity, so the casing stays flush with the wall plane and in the same "
        "plane as the baseboard; the linings are drawn in SHADOWLN a few steps below the casing "
        "white, because this renderer has no shadow to sell a reveal. Applied to the hallway "
        "opening, the Dining opening and the living-room walk-through; the pass-through over the "
        "peninsula gets painted drywall returns instead, which is what photo F shows. What is "
        "visible THROUGH the Dining opening is another agent's Dining-room wall panel 17.5 ft away, "
        "not our geometry."),
    "8 range rug": (
        "REBUILT from a 2.5x crop of photo F: a cream/taupe woven ground (rasterised) carrying about "
        "1200 individually rotated near-black loop quads on a 0.85 in lattice, plus the bound dark "
        "edge and a short fringe on both ends. 116.6 / sd 54.4 against photo A's 121.4 / sd 51.5. "
        "The loops are real geometry, not raster cells -- a 3 px mark cannot survive quantisation "
        "onto a grid, and the first attempt read as digital camouflage."),
    "9 cooktop and towels": (
        "The five crossed-bar 'stars' are replaced by two continuous rectangular grate sections plus "
        "a centre one, each a perimeter frame with parallel ribs over recessed burner caps. The "
        "towels are mid-grey terry (albedo #6f7274, was #9b9e9f) folded over the handle with the "
        "front panel hanging lower than the back, a crease and a pale hem band."),
    "10 crown": (
        "crown_run(): five members projecting 0.30 ft past the door faces over a 0.62 ft height, "
        "sitting on a dark SHADOWLN reveal. Applied to both the east and south upper runs."),
    "11 wall value split": "NOT FIXED -- see _disagreements_r3.",
}

d["_disagreements_r3"] = [
    "The critic diagnosed the black slab as 'a one-sided face turned away from every light -- fix "
    "its winding'. It is not a winding bug: every Material in roomkit/glb.py defaults to "
    "double_sided=True and the raycast confirms side = DoubleSide on the hit face. It is an albedo "
    "problem and is fixed as one. The rasteriser does still verify winding per quad, because that "
    "class of bug is easy to introduce.",
    "'Lighten the backsplash to counter value.' Photo F does not put them at the same value: a "
    "clean backsplash patch under the uppers measures 173.4 while the island top in open light "
    "measures 205.0 and an upper door 205.8. It is the same stone at the same albedo, sitting in "
    "the cabinets' shade. Ours lands at 173.1 against a counter at 208.8 -- the same 35-point gap "
    "the photo has. Lifting it to counter value would have been wrong; what was wrong was the sd, "
    "and that is fixed (5.1 -> 12.0).",
    "Item 11, the wall behind the fridge reading grey against the bay wall. roomkit.meter still "
    "puts the room's wall spread at 54 bytes (round 2: 55). The residue is physical: the app has "
    "one sun, so an interior face turned toward it renders brighter than one turned away, and the "
    "photos do the same thing (photo F's near wall 220 against photo A's far wall 138). Photo A "
    "also shows a grey wall return to the right of the fridge. The only lever left is an emissive "
    "wall wash, which the brief told me to keep out, so it is reported rather than papered over.",
]

d["_known_gaps"] = [
    "The three cased openings are real holes with no panel, but what shows through the Dining one "
    "is the neighbouring room's flat wall panel, which still reads as a pale slab at that angle. "
    "That is another room's geometry.",
    "Backsplash sd is 12.0 against the photo's 19.0. The rest would need either clipping the cloud "
    "field at the white end or veining hard enough to read as camouflage at close range, which is "
    "what an earlier round-3 pass did before it was pulled back.",
    "The stone is quantised onto 0.034-0.052 ft cells, so closer than about 3 ft the vein edges "
    "step. The island top, the hero surface, is the finest at 0.034 ft.",
    "The room's GLB payload is 6.2 MB across 15 pieces, up from 4.5 MB; the floor (1.29 MB) and the "
    "island (1.47 MB) are the bulk. That is the price of the tone fields, and the cell sizes are "
    "single constants if it has to come down.",
    "Stool sled is black; photo F's reads as bright chrome while photos A and C read black.",
]

d["_camera_note"] += (
    " Round 3 added a close east-wall pose for metering the backsplash and cooktop: "
    "pos [4.81, 12.0, 10.24] target [10.68, 11.6, 10.24] fov 52 size 900x700.")

R3 = {
    "Kitchen Floor":
        "ROUND 3: contact shadows rebuilt as one kraster.Shadows field covering all nine occluders, "
        "rasterised at 0.062 ft onto 15 TRANSLUCENT steps (alpha 0 -> 0.44) so the boundary cannot "
        "show as a tone step. Plank palette narrowed and plank tone drawn by a random walk; "
        "GAIN 0.635 -> 0.560.",
    "Kitchen Rug":
        "ROUND 3: rebuilt as a cream/taupe woven ground with ~1200 individually rotated near-black "
        "loop quads, a bound dark edge and a fringe on both ends.",
    "Kitchen Island":
        "ROUND 3: the top is a rasterised stone field at 0.034 ft cells, metering 204.4 / sd 20.2.",
    "Kitchen Cabinets East":
        "ROUND 3: bar pulls restored on every upper door; built-up crown_run; the hallway opening is "
        "a cased_opening with real jamb linings; backsplash and counters are rasterised stone.",
    "Kitchen Cabinets South":
        "ROUND 3: same crown and stone changes; the Dining opening is a cased_opening.",
    "Kitchen Cabinets North":
        "ROUND 3: stone fields on the peninsula top and the corner backsplash; the living-room "
        "walk-through is a cased_opening and the pass-through has painted drywall returns; the "
        "dishwasher uses the APPL blacks.",
    "Kitchen Range":
        "ROUND 3: continuous grate sections instead of crossed-bar stars, grey terry towels with a "
        "fold and a hem band, APPL body, and a blinds reflection in the microwave door.",
    "Kitchen Fridge":
        "ROUND 3: APPL charcoal with sheen bands. This piece was the critic's 'pure black surface'.",
}
for k, v in R3.items():
    d["pieces"][k]["note_r3"] = v

json.dump(d, open(P, "w", encoding="utf-8"), indent=2)
print("wrote", P)
