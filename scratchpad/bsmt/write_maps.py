"""Write tools/roomkit/rooms/1.json and 2.json from the live house."""
import json
import os
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.rooms import fetch_house, room_facts

OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools\roomkit\rooms"
MODELS = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\uploads\models"

NOTES = {
    1: {
        "_note": "FURNISHING ROUND (follows the shell pass). Build scripts live in "
                 "scratchpad/bsmt/ -- bkit.py holds the shared helpers (it imports "
                 "scratchpad/shellpass/kit.py and adds puff/slab/barrel/nailheads), "
                 "mv.py is this room and ar.py is room 2. Both are idempotent by "
                 "piece name, so re-running rebuilds and re-places without "
                 "duplicating. Run them from scratchpad/bsmt/.",
        "_room_note":
            "Movie Room -- 'Movie room.jpg'. ORIENTATION, derived from "
            "docs/floor plan/Basement Floor Plan App.png (thresholded to an ASCII "
            "wall map; plan LEFT = world +X = EAST, plan TOP = world +Z, confirmed "
            "against the Garage/Frontyard footprints on the main floor) and "
            "cross-checked against the live `stairs` row: "
            "NORTH wall (local z=0, world z=11.4) is shared with the Arcade Room "
            "and carries the ~7.6 ft black screen, the grey/white media console, "
            "two black subs and the door to the Arcade at local x 13.35-16.05 "
            "(the plan's wall gap is world x 11.4-14.1); "
            "WEST wall (local x=0, world x=-1.9) is exterior and carries the "
            "L-sectional, the five-panel print and the high basement window; "
            "EAST wall is solid over z 0-16.6 -- the stair (DB row: world x "
            "15.1-18.4, z 15.2-27.6 = local z 3.8-16.2, direction 'n') runs behind "
            "it -- and is OPEN over z 16.6-23.5, which is the foot of that stair "
            "and is exactly the black newel post in the photo's bottom-right; "
            "SOUTH wall is the exterior front wall, behind the camera. "
            "The shell pass drew its door leaf at 13.4-16.1 but the DB hole was at "
            "11.03-14.03; the plan says the leaf was right, so the opening moved. "
            "Furniture positions (console, ottoman, both swivel chairs, the "
            "sectional's two legs) are the plan's own LiDAR blobs, not eyeballed.",
        "_camera": {
            "judge_from": "doll_se",
            "why": "walls are FrontSide with inward normals, so the two nearest "
                   "the camera are culled. This room's content is on the NORTH "
                   "(screen) and WEST (sofa/art/window) walls, and doll_se is the "
                   "only quadrant that leaves both standing. The shell pass said "
                   "doll_sw, which culls the west wall and leaves the art and the "
                   "window hanging in mid-air. doll_se also matches the level-0 "
                   "whole-floor pose (roomkit.rooms --floor-doll 0, az 35).",
            "reference_pose": {"pos": [13.5, 5.5, 33.7], "target": [3.6, 3.2, 12.0],
                               "fov": 80, "size": [900, 1200]},
        },
        "_metered": {
            "_how": "Rec.709 luminance of CLEAN plateaus in --day renders at level 0, "
                    "read off vertical profiles (scratchpad/bsmt/prof.py) so every "
                    "quoted band has sd<=1 unless noted. Photo values from "
                    "scratchpad/bsmt/m.py, which writes a _boxes overlay of every sample.",
            "render_ceiling": "207.9  n=15600 sd=0.0",
            "render_wall_upper_north": "238.3  n=15600 sd=0.4   (CLIPPED - see gaps)",
            "render_wall_upper_west": "202.9  n=25600 sd=0.0",
            "render_wall_upper_east": "170.3  n=27200 sd=0.3",
            "render_wall_upper_south": "144.6  n=46000 sd=0.0",
            "render_wall_upper_AVERAGE_4": "189.0",
            "render_wainscot_north": "238.3 (no separation, clipped)",
            "render_wainscot_east": "132.7  n=13600 sd=0.1",
            "render_wainscot_south": "107.8  n=18400 sd=8.4",
            "render_wainscot_west": "not measurable - sofa and side table occlude it",
            "render_floor_plank": "141.8  n>20000 sd=1.2-2.4",
            "render_rug": "212.7  n=24700 sd=6.6",
            "photo_ceiling": "188.9  n=40000 sd=3.8",
            "photo_wall_upper": "175.3 n=18750 sd=6.6 (west, above the art) / "
                                "197.7 n=11900 sd=8.9 (west, mid) / "
                                "179.3 n=3528 sd=5.2 (north, above the screen) / "
                                "209.0 n=3420 sd=6.6 (north, right of it) -> mean 190.3",
            "photo_wall_lower": "166.7 n=6600 sd=25.9 (west) / 172.1 n=2860 sd=23.9 (north)",
            "photo_floor_plank": "152.1  n=4500 sd=3.7",
            "photo_rug": "208.0  n=100000 sd=6.8",
            "photo_screen_black": "11.9 n=11700 sd=4.8",
            "photo_chair_ivory": "204.8 n=4800 sd=25.0",
            "photo_ottoman_top": "206.9 n=13200 sd=5.1"
        },
        "_gaps": [
            "The four upper walls run 238 / 203 / 170 / 145 -- a 93-byte spread "
            "against the photo's 175-209. The AVERAGE (189.0) lands on the photo's "
            "(190.3), which is what ROOM-BRIEF asks for, but the north wall (the one "
            "the sun at azimuth 155 faces) is CLIPPED: the wall and the "
            "authored-darker wainscot both meter 238, so the chair rail has no value "
            "step on that wall at all. Two authored values 45 apart (#dcdbd8 wall vs "
            "#b0aeaa wainscot) come out identical there, so no albedo skin fixes it "
            "either -- it is the tone curve saturating, not a colour choice.",
            "The footprint is a rectangle but the real room is L-shaped: the plan "
            "shows it wrapping the top of the stairwell over world x 15.1-18.4, "
            "z 28.0-34.9 (local x 17-20.3, z 16.6-23.5). About 21 sq ft of real room "
            "is outside the footprint. Nothing was resized; the stairwell opening was "
            "cut on the east wall where that wrap begins.",
            "The sectional's shape is the plan's LiDAR blob (a west leg at local "
            "z 11.7-19.2 and a south leg at x 2.1-12.7), not the photo -- the photo "
            "only shows the west leg and the near end of the south one.",
            "The five-panel print is a blocked-out seascape, not the photo's artwork; "
            "same for the console doors and the pillow weave.",
            "Not modelled: the white electrical panel and thermostat on the west wall, "
            "and the console's exact hardware."
        ],
    },
    2: {
        "_note": "FURNISHING ROUND (follows the shell pass). See scratchpad/bsmt/ar.py.",
        "_room_note":
            "Arcade Room -- 'Arcade Room.jpg'. ORIENTATION: the photo is taken "
            "from the SOUTH looking NORTH, standing in the doorway from the Movie "
            "Room. Derivation: the basement plan's only wall gap between the two "
            "rooms is world x 11.4-14.1 on z=11.4, i.e. this room's SOUTH wall at "
            "local x 13.5-16.2 -- the same door the Movie Room photo shows from "
            "the other side, so the camera stands in it. The photo's far wall "
            "carries a white six-panel door with a wall cabinet beside it and "
            "measures ~5.3 ft; the plan puts a 5.3 x 6.5 ft utility room inside "
            "this footprint's NW corner (world x -2.3..3.2, z -9.0..-5.3), and its "
            "south face is exactly that wall. That fixes left = WEST (the "
            "Arcade1Up run, the collectible shelf, the duct bulkhead, the "
            "pinball) and right = EAST (the five full-size uprights under the hex "
            "panels).",
        "_camera": {
            "judge_from": "doll_se",
            "why": "doll_se leaves the NORTH and WEST walls standing, which is "
                   "where this room's content is (the pier + hex panels, and the "
                   "west cabinet run + shelf + bulkhead), and it matches the "
                   "level-0 whole-floor dollhouse pose. The cost is that the EAST "
                   "run has no wall behind it from that quadrant; its cabinets "
                   "were given pale caps and plinths and a wider pitch so the run "
                   "reads as a row of machines rather than one black wall.",
            "reference_pose": {"pos": [3.6, 5.3, 10.0], "target": [4.9, 3.3, -11.4],
                               "fov": 84, "size": [900, 1200]},
        },
        "_metered": {
            "_how": "same method as room 1. NOTE the photo is a night shot under RGB "
                    "LEDs -- its ceiling meters rgb=(144,152,218), so its absolute "
                    "luminances are NOT comparable to a daylight render and are quoted "
                    "for ratio only.",
            "render_ceiling": "207.9  n=25600 sd=0.0",
            "render_wall_north": "234.1  n=25600 sd=0.0",
            "render_wall_east": "170.6  n=51000 sd=0.0-0.3",
            "render_wall_south": "147.6  n=32000 sd=9.8 (door casing in the band)",
            "render_wall_west": "not measurable - the cabinet run, the shelf and the "
                                "bulkhead occlude z 6.5-21.6 and the leaning posters "
                                "cover the rest. Proxy 202.9 (room 1's west wall: same "
                                "albedo #dcdbd8, same normal, same level, n=25600).",
            "render_wall_AVERAGE_4": "188.8 using that proxy",
            "render_floor_plank": "142.0  n=6400 sd=1.2",
            "render_rug": "205.3  n=24000 sd=13.8",
            "photo_ceiling": "155.4  n=71500 sd=2.6  rgb=(144,152,218)",
            "photo_walls": "166.0 n=4000 sd=9.0 (north) / 156.0 n=2400 sd=10.1 (east) / "
                           "173.9 n=9600 sd=24.5 (west soffit)",
            "photo_rug": "169.4 n=80000 sd=6.6 (centre) / 179.8 n=15000 sd=8.0 (right)",
            "photo_floor_plank": "142.2 n=67500 sd=21.0",
            "photo_lounge_black": "17.7 n=17600 sd=7.7",
            "photo_pouf_grey": "171.0 n=3300 sd=7.7",
            "rug_over_floor_ratio": "photo 1.19, render 1.45 -- the render's rug still "
                                    "has more contrast against the plank than the photo"
        },
        "_gaps": [
            "The photo is lit by RGB LED strips, Nanoleaf hexes and marquees; the app "
            "renders daylight. Only the marquees, the shelf strip, a third of the hex "
            "panels, the pinball playfield and the floor lamp are emissive here, so "
            "the room reads neutral where the photo reads purple/cyan. That is "
            "deliberate -- the alternative is emissive on room-scale runs, which two "
            "rounds of critics rejected.",
            "The 5.3 x 6.5 ft utility room in the footprint's NW corner is built as a "
            "solid white pier (inside 'Arcade Baseboards' so it stays unpickable). It "
            "is real -- it is in the plan and it is the wall the photo's door sits in "
            "-- but the footprint does not know about it, so the room's slab and "
            "skirting still run underneath it.",
            "ONE cabinet model is reused eleven times (six mini uprights + five "
            "full-size) with only the marquee/side-art hue varying, to stay inside the "
            "payload budget. The photo's eleven machines are all different.",
            "From doll_se the EAST wall is culled, so the east run stands with no wall "
            "behind it. Pale caps, pale plinths and a 2.52 ft pitch keep it reading as "
            "a row of machines rather than one black wall, but it is still the weakest "
            "thing in the dollhouse shot.",
            "The black lounge is five wedge-backed modules on a common base; the real "
            "one is a single sculptural piece and reads softer.",
            "Not modelled: the posters' artwork, the shelf figures are coloured blocks "
            "rather than Funko Pops, and the pinball has no side art."
        ],
    },
}


def main():
    house = fetch_house()
    for rid, notes in NOTES.items():
        f = room_facts(house, rid)
        doc = dict(notes)
        doc["_room"] = {"id": rid, "name": f["name"], "floor": f["floor"],
                        "rect_world": {"x": f["world"]["x"], "z": f["world"]["z"]},
                        "size_ft": [f["local"]["x"][1], f["local"]["z"][1]],
                        "wall_height": f["wall_height"]}
        doc["_surfaces"] = f["surfaces"]
        doc["_openings"] = house and [
            o for fl in house["floors"] for rm in fl["rooms"] if rm["id"] == rid
            for o in rm.get("openings", [])]
        with urllib.request.urlopen("http://127.0.0.1:5000/api/house/models") as r:
            lib = {m["name"]: m["filename"] for m in json.loads(r.read().decode())}
        pieces = {}
        for o in sorted(f["objects"], key=lambda o: o["name"]):
            fn = lib.get(o["name"])
            kb = (os.path.getsize(os.path.join(MODELS, fn)) / 1024.0) if fn else 0
            pieces[o["name"]] = {"pos_room_local_ft": [round(o["x"], 3),
                                                       round(o["y"], 3),
                                                       round(o["z"], 3)],
                                 "rot_y": o["rot_y_deg"], "scale": o["scale"],
                                 "kb": round(kb, 1)}
        doc["pieces"] = pieces
        doc["_payload_kb"] = round(sum(p["kb"] for p in pieces.values()), 1)
        with open(os.path.join(OUT, f"{rid}.json"), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        print(rid, doc["_payload_kb"], "KB", len(pieces), "pieces")


if __name__ == "__main__":
    main()
