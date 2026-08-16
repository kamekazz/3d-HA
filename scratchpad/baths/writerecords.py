"""Write tools/roomkit/rooms/{16,26,23}.json from the live DB + this round's notes."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOMS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools\roomkit\rooms"
ST = json.load(open(os.path.join(HERE, "state.json")))

NOTE = (
    "FURNISHING PASS (round 4, bathrooms). Build scripts live in "
    "scratchpad/baths/ -- bkit.py holds every shared helper (it imports "
    "scratchpad/shellpass/kit.py wholesale), b16/b26/b23.py are idempotent by "
    "piece name so re-running replaces rather than duplicates, probe2.py solves "
    "the four wall-skin albedos from real renders, meterwalls.py reports the "
    "finished per-wall numbers, shootpose.py shoots a photo-matched camera "
    "without touching poses.json.")

SHADOW = (
    "CONTACT SHADOWS were the unfinished item this round inherited, and they "
    "needed four things at once. (1) HEIGHT y=0.05: the room slab is drawn with "
    "polygonOffsetFactor -1, so a decal at 0.005-0.018 z-fights into faint "
    "crescents. (2) ALPHA-BLENDED, not an opaque colour mix: the opaque version "
    "painted mix(floor_color, tone) over the slab, which killed the plank "
    "texture and -- because the authored floor_color is lighter than the "
    "textured render -- left a PALE disc round every piece. (3) ONE coplanar "
    "layer of non-overlapping annuli on a smooth ramp, so there is no bullseye "
    "and no outer outline. (4) The ramp has to run OUTSIDE the footprint: the "
    "first rebuild ran 0->1 across the piece's own half-extent, which buried "
    "every dark ring under the piece and left ~3% alpha where it actually "
    "showed -- it metered as no shadow at all. Final form: a solid core over "
    "the footprint, alpha falling (1-t)^1.15 over an extra 0.72-0.85 ft. "
    "Metered in the doll render: 82 against a clean floor of 124, i.e. 34% "
    "darkening at the contact edge easing to zero over ~25 px at dollhouse "
    "distance.")

FLOOR = (
    "FLOOR: I agree with the shell pass and with the previous round. Every "
    "photo of all three bathrooms shows the same grey wood-look PLANK as the "
    "rest of the house running unbroken under the vanities and up to the shower "
    "curbs -- no tile field and no threshold strip anywhere outside the pans. "
    "Tile appears only INSIDE the enclosures (grey hexagon mosaic in room 26's "
    "pan, charcoal pan in room 23, marble slab in room 16) and on the enclosure "
    "walls. floor_texture stays 'wood' in all three.")

SKINS = (
    "Per-wall NON-emissive albedo skins on all four walls, solved by "
    "probe2.py: it renders the room twice with only ONE wall's skin changed "
    "(grey 250 -> grey 120) and keeps the pixels that moved. There is no bounce "
    "light in this scene, so those pixels are that wall's skin and nothing "
    "else -- no hand-drawn box can swallow a towel bar or a mirror rim. Each "
    "skin then carries a gentle vertical value ramp about the solved albedo "
    "(mean preserved by construction), because one flat quad metered sd ~3 "
    "against the photographs' 8-15. Measured on the finished room: ")

META = {
    "16": dict(
        cam="doll_nw",
        why=("doll_nw culls the N and W walls and leaves the SOUTH wall (double "
             "vanity, two oval mirrors, sconces, toilet) and the EAST wall "
             "(window, towel bar and bath sheet, framed print, tub filler) "
             "standing -- the two walls that carry this room's content. Cost of "
             "the choice: the west-wall console and the bedroom door leaf are "
             "left with no wall behind them. doll_ne would save those but would "
             "strand the EAST window unit in mid-air, which reads worse."),
        room_note=("Master Bath. -- 'Master Bath. 1.jpg'. WEST borders the "
                   "master bedroom (local z 0..6.3) and the 2F hallway (z "
                   "6.6..12.7), SOUTH the master closet, NORTH and EAST are "
                   "exterior. Shower NW behind a solid west return, "
                   "freestanding oval tub NE under the two windows, 72in double "
                   "vanity on the SOUTH wall, toilet in the SE corner, "
                   "glass-door console on the WEST wall under the "
                   "almond-blossom canvas, four white bath rugs on the floor."),
        walls=("n 172.9 / w 190.1 / s 167.6 / e 181.2, spread 22.5, mean 178.0 "
               "(photo's four clean wall fields 150.2 / 203.7 / 175.4 / 171.3, "
               "mean 175.2). Render sd 5.7-10.2 against the photo's 9.6-15.0; "
               "sample sizes 37k-365k px at native resolution."),
        gaps=[
            "Density is still below the photo: the real vanity counter is crowded end to end and the console top is a jumble; the render carries 16 counter items and 19 on the console and still reads tidier.",
            "The shower's marble back is veined with thin wandering lines but nowhere near the photo's bold grey drama. The previous round's version was worse (0.25 ft axis-aligned blocks that read as static); this one is too quiet.",
            "|d1|/sd on the walls is 0.017-0.116 against the photo's 0.039-0.214. The render has no sensor grain and no bounce light, so fine-scale wall variation is genuinely absent; the vertical albedo ramp closed the sd gap (2.7 -> 5.7-6.8) but not the fine-scale one.",
            "Openings are `door`/`window` types, not cut passages: the master bedroom, hallway and closet are other agents' rooms and an un-paired hole would look through at their solid wall (ROOM-BRIEF: cut BOTH sides).",
        ]),
    "26": dict(
        cam="doll_ne",
        why=("doll_ne culls the N and E walls and leaves the WEST wall (vanity, "
             "round black mirror, towel ring) and the SOUTH wall (window, "
             "toilet, framed print, towel bar) standing. The shower sits on the "
             "EAST wall but is built as a placed object with its own tiled "
             "walls, so culling the room's east wall costs nothing. The only "
             "stranded item is the north door leaf."),
        room_note=("bath (2F) -- 'Second floor bathroom.jpg'. NORTH is the 2F "
                   "hallway (door at local x 0.42..3.22, the WEST end), WEST is "
                   "the Rios Room party wall (vanity + round mirror), EAST and "
                   "SOUTH are exterior. Subway-tiled shower with a black "
                   "barn-rail slider and a grey hex mosaic pan fills the EAST "
                   "side x 4.45..8.02, z 0.10..5.30; window on the SOUTH wall x "
                   "2.55..5.65; toilet EAST of it, tank on the south wall."),
        walls=("n 177.9 / w 192.9 / s 165.1, spread 27.8, mean 178.6 (photo's "
               "clean wall fields 176.0 / 170.8 / 159.7 / 191.6, mean 174.5). "
               "Sample sizes 100k-151k px. The EAST wall could not be metered: "
               "the shower alcove covers all but a sliver of it and the probe "
               "moved 0 pixels, so its skin is left at #fafafa and reported "
               "rather than guessed."),
        gaps=[
            "The east wall's skin is unsolved (0 px of it are visible anywhere in the room) -- reported rather than invented.",
            "One bath mat, one plant and six counter items: the photographs are a little busier than this.",
            "The barn rail reads as a heavy black band from a camera standing right under it in the doorway; it is correct in plan but foreshortens badly at 3 ft.",
            "Corrected the shell pass twice here: it had the door at the EAST end of the north wall (standing there you would be inside the shower alcove, which no photo shows) and the toilet WEST of the window instead of east.",
        ]),
    "23": dict(
        cam="doll_se",
        why=("doll_se culls the S and E walls and leaves the NORTH wall "
             "standing -- which carries everything: grey shaker vanity, round "
             "black mirror, black three-light bar, toilet, paper holder. The "
             "shower on the EAST is a placed object with its own tile, so it "
             "survives the cull; the stranded item is the south door leaf."),
        room_note=("Bathroom (1F) -- 'Bathroom.jpg'. WEST is the Living Room "
                   "party wall, EAST is the Office party wall, NORTH is "
                   "exterior, SOUTH faces the untraced circulation strip "
                   "between this room and the pantry -- and the plan's only "
                   "wall gap is there, at local x 1.30..4.15, so that is the "
                   "door. Grey shaker vanity + toilet on the NORTH wall, "
                   "white-tiled shower with a black-framed slider and a "
                   "charcoal pan on the EAST, two striped mats. There is no "
                   "window in this room and the plan gives it nowhere to be."),
        walls=("n 176.0 / w 189.4 / s 166.7, spread 22.7, mean 177.4 (photo's "
               "four clean wall fields 198.6 / 168.8 / 201.7 / 159.1, mean "
               "182.1). Sample sizes 87k-203k px. The EAST wall is behind the "
               "shower and moved 9 px in the probe, so its skin is left at "
               "#fafafa."),
        gaps=[
            "The east wall's skin is unsolved (9 px visible).",
            "The south wall caps at 166.7 with a pure-white skin -- it is the wall the sun never reaches, and the ROOM-BRIEF already records that residual as the renderer's limit rather than a defect.",
            "Floor meters 163.7 / sd 12.0 / |d1| 2.18 against the photo's 146.4 / 14.4 / 8.02: value and sd are close, the fine-scale plank grain is about 4x weaker, because the floor texture is the app's tiled wood map which this pass does not own.",
            "Corrected the shell pass: it recorded 'door on the west wall', which is the Living Room party wall.",
            "The vanity and the mirror were both re-solved from photo RATIOS, not hex codes: the photo meters the vanity front at 140.8 and the mirror at 146.3 against a 198.6 wall (0.71 and 0.74). A GLB piece collects ~1.7-2x what a room wall of the same albedo does, so the first 'grey' cabinet rendered BRIGHTER than the wall and the value step inverted.",
        ]),
}

for rid, meta in META.items():
    st = ST[rid]
    path = os.path.join(ROOMS, rid + ".json")
    old = json.load(open(path))
    doc = {
        "_note": NOTE,
        "_room_note": meta["room_note"],
        "_room": old.get("_room"),
        "_surfaces": st["surfaces"],
        "_camera": {"judge_from": meta["cam"], "why": meta["why"]},
        "_openings": st["openings"],
        "pieces": st["pieces"],
        "_photo_vs_brief": FLOOR,
        "_contact_shadows": SHADOW,
        "_wall_skins": SKINS + meta["walls"],
        "_gaps": meta["gaps"],
    }
    with open(path, "w") as fh:
        json.dump(doc, fh, indent=1)
    print("wrote", path, len(st["pieces"]), "pieces")
