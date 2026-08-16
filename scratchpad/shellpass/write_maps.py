"""Write tools/roomkit/rooms/<id>.json for every room this shell pass touched."""
import json, os, urllib.request

BASE = "http://127.0.0.1:5000"
DEST = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools\roomkit\rooms"

COMMON = ("SHELL PASS (not a furnishing round). Build scripts live in "
          "scratchpad/shellpass/ -- kit.py holds every shared helper and each "
          "r*.py is idempotent by piece name, so re-running rebuilds and "
          "re-places without duplicating. Every room got: a ONE-SIDED ceiling "
          "plane wound to face into the room (solid at eye level, invisible "
          "from the plan pose), a three-step crown where the photo shows one, "
          "recessed cans / fixtures / supply registers off the photo, a tall "
          "white baseboard run gapped at every doorway, door leaves and "
          "casings, and photo-derived wall/floor surfaces via "
          "PATCH /api/house/room/<id>. The '<Room> Ceiling' and "
          "'<Room> Baseboards' names match objects.js SURFACE_RE so they stay "
          "pickable:false; furniture names deliberately avoid it. NO EMISSIVE "
          "on any trim run -- only the downward ceiling plane carries emissive, "
          "because it collects almost no light in this renderer.")

NOTES = {
 13: ("Guest Room -- primary photo 'Guest Room.jpg'. WEST is exterior and "
      "carries the window (the floor plan draws it pale blue at local z 1.3..4.9); "
      "EAST is the 2F hallway (entry door); NORTH has the closet double doors "
      "with room 24 behind them; SOUTH is the headboard wall with room 25 "
      "behind. Chair rail at 3.32 ft, matching the photo. Defining pieces: the "
      "black platform bed and the black dresser. Judge from doll_nw or doll_sw "
      "-- doll_ne culls the window wall.", "doll_sw"),
 16: ("Master Bath. -- 'Master Bath. 1.jpg'. WEST borders the master bedroom "
      "(local z 0..6.6) and the hallway (z 6.9..12.7), SOUTH the master closet, "
      "NORTH and EAST are exterior. Layout follows photo 2: shower NW, "
      "freestanding tub against the east window, double vanity on the south "
      "wall, toilet in the SW corner. FLOOR IS PLANK, NOT TILE -- see _photo_vs_brief. "
      "Judge from doll_nw: it leaves the vanity/mirror wall and the window wall "
      "standing.", "doll_nw"),
 17: ("Hallway (2F) -- 'Second-floor hallway.jpg'. NO CROWN in this room; every "
      "shot shows a clean drywall corner at the ceiling. The stairwell is the "
      "level-1 stair (world x 14.6..18.4 / z 14.3..24.5) = local x 4.1..7.9 / "
      "z 7.7..16.7, and the defining piece is the white capped KNEE WALL round "
      "it (solid half wall, no spindles -- that is what the photo shows on this "
      "floor). Four door units: guest room and room 25 west, master bath and "
      "master closet east.", "doll_nw"),
 26: ("bath (2F) -- 'Second floor bathroom.jpg'. Enter from the hallway on the "
      "NORTH. Standing in that doorway looking south, screen-left is EAST, so "
      "the subway-tiled shower with the black sliding rail is on the east side, "
      "the white vanity on the west, and the window + toilet on the south "
      "(exterior) wall. FLOOR IS PLANK, NOT TILE.", "doll_nw"),
 27: ("Master Closet -- 'Walking Closet for the Master bedroom.jpg'. The only "
      "SLOPED ceiling in the pass: flat to local x 6.8, then raking down to "
      "4.55 ft at the east wall, which is 1.2 ft short of the house's east edge "
      "so that is where the roof falls. Grey CARPET, not plank. The dark accent "
      "wall under the rake is named 'Master Closet Wall Wash Dark' PURELY so "
      "objects.js keeps it unpickable -- it is a flat matte panel, NOT the "
      "emissive wall wash two critics rejected. Chrome wire shelving + a "
      "hanging rail run.", "doll_nw"),
 24: ("Bathroom closet -- no photo. Ceiling + baseboards + surfaces only, per "
      "the brief. NOTE: this room's footprint OVERLAPS Master Bed (14)'s rect "
      "in the layout data (x -1.9..5.9 / z 0.9..6.3 is inside both). Nothing in "
      "room 14 was touched; a later round should re-trace one of the two.",
      "doll"),
 25: ("Room 7 -- Rios Room's closet, no photo. Ceiling + baseboards + surfaces "
      "only. The skirting is gapped on the SOUTH wall where Rios Room's own "
      "'Rios Closet Doors' piece already stands.", "doll"),
 8:  ("Office -- 'Office A.jpg'. The signature is the TWO-TONE wall: greige "
      "above a chair rail at 3.30 ft, charcoal #3e4145 wainscot below it, both "
      "built into 'Office Baseboards'. Tall window on the east (exterior) wall, "
      "a plain door and the glazed 15-lite french door photo B shows on the "
      "west, a cased opening south into the printer nook (room 22). Defining "
      "piece: the L desk with the ultrawide monitor, the mesh task chair and "
      "the second desk on the east wall.", "doll_sw"),
 12: ("First floor hallway -- 'First floor hallway.jpg'. The defining piece is "
      "the STAIR BALUSTRADE: square white newel, turned white balusters and the "
      "BLACK handrail, raked along the west edge of the level-1 stair (local "
      "x 3.90, bottom of the flight at local z 19.90 because the stair's "
      "direction is 'n'). The ceiling is CUT round the stairwell (hole "
      "x 3.78..7.6 / z 9.55..20.05) so the flight is open to the floor above. "
      "The skirting is gapped -- with no leaf -- at local z 11.69..15.09 on the "
      "west wall, where room 6 has already cut a real passage through to the "
      "kitchen.", "doll_sw"),
 23: ("Bathroom (1F) -- 'Bathroom.jpg'. Grey shaker vanity with a white top, "
      "black faucet, round black-rimmed mirror and the black three-light bar, "
      "plus the toilet, all in one piece; white subway shower with a "
      "black-framed slider at the east end. Door on the west wall. FLOOR IS "
      "PLANK, NOT TILE.", "doll_sw"),
 9:  ("Laundry -- 'Laundry.jpg'. Top-load washer + front-load dryer against the "
      "north wall under white upper cabinets with a floating shelf and two "
      "woven baskets between them. Doors west (to the pantry/hall) and south "
      "(to the garage).", "doll_sw"),
 10: ("Pantry -- 'pantry door.jpg'. 3.1 x 5.7 ft. Ceiling + baseboards + "
      "surfaces, plus five open shelves on the east wall; the double doors "
      "themselves belong to hallway 12's 'Hall1F Baseboards' piece, so the "
      "skirting here is only gapped.", "doll"),
 22: ("Office printers -- no photo of its own, but 'First-floor bathroom.jpg' "
      "is in fact this nook shot from the office (the office's charcoal "
      "wainscot frames the doorway). Ceiling + baseboards + surfaces + the "
      "cased opening north into the office.", "doll"),
 7:  ("Garage -- no photo. Ceiling with four flush fixtures and NO crown, a "
      "poured concrete curb instead of skirting (named '... Baseboards' so it "
      "stays unpickable), concrete floor texture, a 16 ft sectional garage door "
      "with a row of lites on the SOUTH (street) wall and a person door north "
      "to the laundry. Deliberately empty otherwise -- it is the last room on "
      "the priority list.", "doll_nw"),
 1:  ("Movie Room -- 'Movie room.jpg'. Chair rail at 3.35 ft with a slightly "
      "deeper grey below, white crown, ten cans and four flush in-ceiling "
      "speaker grilles, the high basement window on the west wall. Defining "
      "pieces: the big black screen with its grey media console and two black "
      "sub boxes on the north wall, and the large cream rug. The rug is named "
      "'Movie Floor Rug' so objects.js keeps it unpickable -- it covers most of "
      "the footprint and would otherwise swallow every click.", "doll_sw"),
 2:  ("Arcade Room -- 'Arcade Room.jpg'. Ten cans + four speaker grilles, white "
      "crown, tall skirting, the pale grey rug. Defining piece: twelve upright "
      "arcade cabinets in two runs (west wall facing east, east wall facing "
      "west) with colour-blocked marquees -- the only thing that makes this "
      "room read as an arcade from 50 degrees up. Marquee emissive is 1.1 on "
      "small cabinet panels only, never on a room-scale run.", "doll_nw"),
}

PHOTO_VS_BRIEF = (
 "The task brief said 'bathrooms are tile'. Rooms 16, 23 and 26 were built with "
 "floor_texture 'wood' instead, because every bathroom photo in docs/photos-jpg "
 "shows the same grey wood-look PLANK as the rest of the house running "
 "unbroken under the vanity and up to the shower curb ('Master Bath. 1/2.jpg', "
 "'Bathroom.jpg', 'Second floor bathroom.jpg'). Tile appears only inside the "
 "shower pans and surrounds, which are modelled as tile. Recording the "
 "disagreement rather than building against the photo, per ROOM-BRIEF round-2 "
 "lesson 1.")

house = json.load(urllib.request.urlopen(BASE + "/api/house"))
byroom = {}
for f in house["floors"]:
    for r in f["rooms"]:
        byroom[r["id"]] = (r, f)

for rid, (note, doll) in NOTES.items():
    r, f = byroom[rid]
    doc = {
        "_note": COMMON,
        "_room_note": note,
        "_room": {
            "id": rid, "name": r["name"],
            "floor": {"id": f["id"], "name": f["name"], "level": f["level"]},
            "rect_world": {"x": [r["x"], round(r["x"] + r["width"], 2)],
                           "z": [r["z"], round(r["z"] + r["depth"], 2)]},
            "size_ft": [r["width"], r["depth"]],
            "wall_height": r.get("height"),
        },
        "_surfaces": {"wall_color": r.get("wall_color"),
                      "floor_color": r.get("floor_color"),
                      "floor_texture": r.get("floor_texture"),
                      "wall_texture": r.get("wall_texture")},
        "_camera": {"judge_from": doll,
                    "why": "roomkit.rooms <id> --poses-only; walls are FrontSide "
                           "with inward normals so the two nearest the camera "
                           "are culled -- this quadrant leaves the walls that "
                           "carry this room's content standing."},
        "pieces": {o["name"]: {"pos_room_local_ft": [round(o["position"]["x"], 3),
                                                     round(o["position"]["y"], 3),
                                                     round(o["position"]["z"], 3)],
                               "rot_y": o.get("rot_y", 0.0),
                               "scale": o.get("scale", 1.0)}
                   for o in sorted(r.get("objects", []), key=lambda o: o["name"])},
        "_photo_vs_brief": PHOTO_VS_BRIEF if rid in (16, 23, 26) else None,
        "_gaps": [
            "This is a SHELL pass: the room has its lid, trim, surfaces, lights "
            "and one or two defining pieces, not a furnished set. Density is "
            "well below the photo everywhere.",
            "Contact shadows are only under the defining pieces, as smooth "
            "superellipse falloffs (12 stacked translucent rings, alpha chosen "
            "so the centre reads 0.2-0.3 and the outer edge disappears).",
            "No real cut openings were added; door leaves and cased trim sit "
            "flush on the wall. Room 12's west wall does carry room 6's "
            "existing cut passage and the skirting is gapped for it.",
        ],
    }
    doc = {k: v for k, v in doc.items() if v is not None}
    path = os.path.join(DEST, f"{rid}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    print("wrote", path, len(doc["pieces"]), "pieces")
