import json
import os
import subprocess

PY = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\.venv\Scripts\python.exe"
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"

NOTES = {
    7: dict(cam="doll_ne", why=(
        "Walls are FrontSide with inward normals, so the two nearest the camera are culled. "
        "doll_ne culls NORTH+EAST and leaves SOUTH (the 16.5 ft sectional door -- this room's "
        "defining feature) and WEST (the workbench / pegboard / cabinet / shelving run the floor "
        "plan draws there) standing. The shell pass recorded doll_nw, which keeps the sectional "
        "door but culls the west storage wall and would leave that whole run floating. The north "
        "wall is culled in both, but the laundry's own south wall stands right behind it, so the "
        "person door still reads as a door in a doorway. Everything on the culled east wall is "
        "floor-standing (water heater, freezer, mower, bins) -- nothing is wall-hung there."),
        note=("FURNISHING PASS on top of the shell. NO INTERIOR PHOTO OF THIS GARAGE EXISTS -- see "
              "_evidence for what is measured and what is inferred. Build scripts: "
              "scratchpad/util/{gkit,g_west,g_east,g_main,g_bay,g_skin}.py, idempotent by piece "
              "name.")),
    9: dict(cam="doll_sw", why=(
        "doll_sw culls SOUTH+WEST and leaves NORTH (the appliance wall: washer, dryer, ledge, "
        "uppers, floating shelf, framed print) and EAST standing -- the north wall carries this "
        "room's entire content."),
        note=("FURNISHING PASS. ORIENTATION CORRECTION: the washer/dryer run moved from the WEST "
              "end of the north wall to the EAST end -- see _evidence. Build script: "
              "scratchpad/util/l_main.py.")),
    10: dict(cam="doll_nw", why=(
        "The shelf run is on the EAST wall -- the wall you face through the double doors. doll_nw "
        "culls NORTH+WEST, so the east wall stands behind the shelving and you look in over the "
        "doorway wall. The shell pass recorded 'doll' (= doll_se), which culls the east wall and "
        "would leave every shelf hanging in mid-air."),
        note=("FURNISHING PASS. Both pantry photos show the doors CLOSED, so the entire interior "
              "is inference. Build script: scratchpad/util/p_main.py.")),
}

EVID = {
    7: [
        "MEASURED (docs/floor plan/Main Floor Plan App.png): 16.5 ft sectional door on the SOUTH "
        "(street/driveway) wall; person door to the laundry on the NORTH wall at local x 2.9-5.8; a "
        "step just inside that door (the plan's hatch at world x 21.8-26.5, z 13.0-14.7); a ~2.4 ft "
        "deep x 8.5 ft long storage run against the WEST wall (world x 19.2-21.6, z 20.5-29.0 = "
        "local x 0.3-2.7, z 7.5-16.0); two blobs hard against the EAST wall at local z 3.4-5.6 and "
        "z 16.2-18.6.",
        "MEASURED (exterior photos): the sectional door is a single wide cream raised-panel door; a "
        "black BMW X5 is parked on the driveway -- environment.js already builds that SUV outside.",
        "INFERRED (normal construction sense, no interior photo): WHAT the west run is (workbench "
        "with butcher-block top, pegboard and tools, red rolling tool chest, tall graphite "
        "cabinets, steel shelving); WHAT the two east blobs are (water heater north, wheelie bins "
        "south); the chest freezer, mower, ladders, shop vac, bike, scooter; the whole opener "
        "assembly (rail, motor head, torsion tube and springs, tracks, safety eyes, wall button); "
        "and the car.",
        "The car is a LIGHT SILVER SALOON, deliberately NOT a second black SUV -- the household SUV "
        "is the one environment.js parks outside. The west bay is the 'stuff bay' (totes, soil "
        "bags, cooler, wheelbarrow, wagon, sports bin) because the 2.5 ft west storage run leaves "
        "only one comfortable parking bay in a 20.4 ft wide garage.",
    ],
    9: [
        "MEASURED (floor plan): the plan's appliance icon sits at world x 29.4-31.9, z 7.7-10.5 = "
        "local x 7.5-10.0, z 0.4-3.2 -- against the NORTH wall at the EAST end, with a partition "
        "drawn at local x 7.5. The 'Indoor garage door' hatch is at world x 21.8-26.5 = local "
        "x 0-4.6, i.e. the WEST end. The shell pass had the appliances at local x 0.05-6.0, sitting "
        "on top of the garage doorway.",
        "MEASURED (Laundry.jpg + 'Laundry room and garage door right next to it.jpg'): top-load "
        "Samsung washer LEFT, front-load dryer RIGHT with a rose-gold facia band and a dark glass "
        "door; white shaker uppers with BLACK BAR PULLS and crown; a full-width white ledge under "
        "them carrying two woven baskets and a white box; a floating white shelf with three dark "
        "bottles under a framed print between the two cabinets; a woven box on the dryer top; a "
        "white floor register; tall white baseboard; grey wood-look plank floor.",
        "NOT RECONCILABLE: no camera position inside an 11.0 x 5.7 ft rectangle reproduces the "
        "photo's geometry. The photo shows the appliance wall and the garage-door wall meeting at a "
        "corner immediately right of the dryer; the traced footprint merges the real mudroom and "
        "the laundry alcove and has no such corner. The floor plan was used as the tie-breaker for "
        "WHICH END each element sits on.",
    ],
    10: [
        "MEASURED ('pantry door.jpg', 'Pantry and garage door.jpg'): a pair of white six-panel "
        "leaves on the 5.7 ft WEST wall, facing the first-floor hallway. Both photos show them "
        "CLOSED, so there is no photograph of the inside of this room.",
        "INFERRED (everything inside): five-tier white shelving on the east wall with steel "
        "standards, four short tiers on each 3.1 ft end wall, and ordinary dry-store stock -- "
        "boxes, cans, jars, woven baskets, paper towels, bottles -- plus a case of water, a sack "
        "and a folding step stool on the floor.",
    ],
}

SURF = {
    7: dict(wall_color="#dad7d0", floor_color="#686764", floor_texture="concrete",
            per_wall_skin={"n": "#797873", "w": "#b2afaa", "e": "#e8e5dd", "s": "#fffcf3"}),
    9: dict(wall_color="#dbdbda", floor_color="#6b6967", floor_texture="wood",
            per_wall_skin={"n": "#7f7f7e", "w": "#b3b3b2", "e": "#f2f2f1", "s": "#fffffe"}),
    10: dict(wall_color="#dcdcdb", floor_color="#6b6967", floor_texture="wood",
             per_wall_skin={"n": "#848483", "w": "#babab9", "e": "#fbfbfa", "s": "#fffffe"}),
}

METER = {
    7: {"_target": "NO PHOTO of this room exists, so there is no photo mean to aim at. Values are "
                   "reported for audit and for wall-to-wall consistency only.",
        "walls_before_skin": {"north": "233.1 (n=175000, sd 0.0)",
                              "west": "200.3 (n=245000, sd 0.2)",
                              "east": "167.9 (n=245000, sd 0.0)",
                              "south": "141.6 (n=15840, sd 0.5)", "spread": 91.5},
        "walls_after_skin": {"north": "179.8 (n=127500, sd 0.0)",
                             "east": "176.9 (n=59800, sd 0.0)",
                             "west": "173.6 (n=31200, sd 0.4)",
                             "south": "167.5 (n=4800, sd 0.0)", "spread": 12.3},
        "floor": "141.8 (n=31500, sd 3.3) after floor_color #8e8d89 -> #686764; was 184.3 (sd 2.8)"},
    9: {"_target": "photo 'Laundry room and garage door right next to it.jpg': wall 192.9 "
                   "(n=99900, sd 12.9) and 186.1 (n=88000, sd 12.8) -> aim 189; floor 138.7 "
                   "(n=89300, sd 13.4); ceiling 180.0 (n=85500, sd 4.4)",
        "walls_before_skin": {"north": "234.0 (n=64800)", "west": "209.7 (n=155000)",
                              "east": "168.0 (n=103600)", "south": "144.4 (n=162000)",
                              "spread": 89.6},
        "walls_after_skin": {"north": "186.9 (n=100000, sd 0.0)",
                             "east": "183.3 (n=103600, sd 4.4)",
                             "west": "175.7 (n=53340, sd 3.3)",
                             "south": "168.7 (n=162000, sd 0.0)",
                             "spread": 18.2, "avg": 178.7},
        "floor": "143.0 (n=57500, sd 3.0) against the photo's 138.7 (sd 13.4): mean within 4.3, but "
                 "the plank texture is much flatter than the real LVP (sd 3.0 vs 13.4)"},
    10: {"_target": "no interior photo; the laundry photo's 189 was used -- same paint, adjacent "
                    "room",
         "walls_after_skin": {"west": "182.1 (n=144000, sd 0.0)"},
         "_note": "The west wall is the only one that yields a clean field -- the shelving covers "
                  "the other three. The bare west wall metered 203.1 against the laundry's 209.7 on "
                  "the same wall and the same paint (3% agreement), so the laundry's four-wall set "
                  "was scaled by 203.1/209.7 to size these skins."},
}

GAPS = {
    7: ["No interior photo exists, so nothing in this room is photo-verified except the sectional "
        "door and the plan-derived layout. A critic cannot fail it against a photo, and should not "
        "be told it matches one.",
        "The two east-wall floor-plan blobs are identified by inference only (water heater / "
        "wheelie bins).",
        "Floor sd is 3.3 -- the concrete texture is flat. No photo target exists to aim the spread "
        "at, so it was left alone rather than guessed at.",
        "The south wall cannot be lifted above ~168 even with a pure-white skin (measured), so it "
        "sits 12 below the other three."],
    9: ["The traced 11.0 x 5.7 ft footprint is not the shape of the real room (see _evidence), so "
        "the side-by-side is a content match, not a geometry match. No camera reproduces the "
        "photo.",
        "The framed 'Wash Dry Fold' print and the left upper cabinet are hidden behind the alcove "
        "end panel from the reference camera; they are visible from doll_sw.",
        "Woven baskets are modelled as banded boxes -- at close range they read as boxes, not "
        "wicker.",
        "Floor sd 3.0 vs the photo's 13.4: the plank texture has far less variation than real LVP."],
    10: ["Entirely inferred interior -- both photos show the doors closed.",
         "Only the west wall gives a clean metering field; the other three are behind shelving."],
}


def main():
    for rid in (7, 9, 10):
        facts = json.loads(subprocess.check_output(
            [PY, "-m", "roomkit.rooms", str(rid)], cwd=TOOLS))["facts"]
        n = NOTES[rid]
        out = {
            "_note": n["note"],
            "_room": {"id": rid, "name": facts["name"], "floor": facts["floor"],
                      "rect_world": {"x": facts["world"]["x"], "z": facts["world"]["z"]},
                      "size_ft": [round(facts["local"]["x"][1], 1),
                                  round(facts["local"]["z"][1], 1)],
                      "wall_height": facts["wall_height"]},
            "_evidence": EVID[rid],
            "_surfaces": SURF[rid],
            "_camera": {"judge_from": n["cam"], "why": n["why"]},
            "_metered_srgb_luma": METER[rid],
            "pieces": {o["name"]: {
                "pos_room_local_ft": [round(o["x"], 3), round(o["y"], 3), round(o["z"], 3)],
                "rot_y": o["rot_y_deg"], "scale": o["scale"]}
                for o in sorted(facts["objects"], key=lambda o: o["name"])},
            "_gaps": GAPS[rid],
        }
        p = os.path.join(TOOLS, "roomkit", "rooms", "%d.json" % rid)
        with open(p, "w") as fh:
            json.dump(out, fh, indent=2)
        print("wrote", p, len(out["pieces"]), "pieces")


if __name__ == "__main__":
    main()
