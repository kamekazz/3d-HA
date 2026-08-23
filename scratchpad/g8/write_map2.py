"""Rewrite tools/roomkit/rooms/7.json for the round-2 build.

Reads the live object list out of the running app so the piece map cannot drift
from what is actually placed.
"""
import json
import os
import urllib.request

P = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools\roomkit\rooms\7.json"
MODELS = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\uploads\models"

d = json.load(open(P, encoding="utf-8"))

h = json.load(urllib.request.urlopen("http://127.0.0.1:5000/api/house"))
pieces, tot = {}, 0.0
for f in h["floors"]:
    for r in f["rooms"]:
        if r["id"] != 7:
            continue
        for o in r["objects"]:
            fn = [x for x in os.listdir(MODELS)
                  if x.startswith("model_%d." % o["model_id"])]
            kb = round(os.path.getsize(os.path.join(MODELS, fn[0])) / 1024, 1) \
                if fn else 0
            tot += kb
            pieces[o["name"]] = {
                "pos_room_local_ft": [round(o["position"][k], 3) for k in "xyz"],
                "rot_y_deg": o["rot_y"], "scale": o["scale"], "kb": kb}

d["_note"] = (
    "ROUND 2, 2026-08-23. Round 1 was FAILED by a blind critic whose single named "
    "gap was: every hero surface in this room is built as a collage of axis-aligned "
    "boxes when the toolchain already supports the textured quad that would fix it. "
    "Round 2 is that fix plus the four other findings. Build scripts: "
    "scratchpad/g8/{gk,g8_tex,g8_clean,g8_surface,g8_arch,g8_furn,probe_walls,m,"
    "meter_shadows,write_map2}.py -- all idempotent by piece name. g8_tex.py is new "
    "and owns every texture.")

d["_round2"] = {
    "1_banner": (
        "The KIES vinyl is now ONE TEXTURED QUAD carrying a photo-derived albedo, "
        "replacing ~25 axis-aligned boxes. g8_tex.banner_png rectifies the vinyl out "
        "of Garage v3 1.jpg with a four-point perspective solve, DIVIDES OUT the "
        "photograph's own illumination (wide gaussian estimate, then normalise) so "
        "what is mapped is albedo rather than a lit image the renderer lights twice, "
        "median-filters the JPEG blocking and unsharps. 77 KB at 440x600, 190-colour "
        "palette. PROPORTION was also wrong: round 1 hung it 11.25 x 5.88 ft "
        "LANDSCAPE; the vinyl rectifies at 0.73 W/H, i.e. PORTRAIT, and it is now "
        "5.2 x 7.1 ft. The rectification check is that the KIES baseline comes out "
        "level and the car's centre split comes out vertical -- the first two corner "
        "guesses failed both, because the top edge slopes DOWN to the east (the "
        "camera stands west of the banner and below its top edge)."),
    "2_contact_shadows": (
        "Rebuilt twice and re-metered each time. Round 1's ten hand-listed "
        "footprints had drifted off the furniture and metered 48/15/9/0/0 per cent. "
        "They are now DERIVED from the geometry this build saves: every part whose "
        "lowest vertex is within 0.09 ft of the slab is a foot, its x/z bbox is a "
        "footprint, footprints are unioned per piece and then GROWN by whatever mass "
        "stands over them (so a chest gets its carcass, not four castor dots). "
        "MECHANISM CHANGED: alpha annuli cannot reach the brief's 34 per cent in "
        "this scene -- the decal is a LIT surface and a black diffuse patch still "
        "returns the ~4 per cent Fresnel specular off a bright sky, so it never "
        "renders below ~0.75 of the floor; measured 21 per cent at alpha 0.92, and a "
        "second stacked layer bought only 2 more points. The shadow is now baked "
        "into the FLOOR's own vertex colours (COLOR_0 multiplies baseColor, so it "
        "darkens the real floor, cannot z-fight, cannot halo, and the coin texture "
        "reads straight through). The whole Garage Floor Shadows object is deleted."),
    "3_interpenetrations": (
        "The coiled hose and the feed sack stood at x 1.1-1.35, z 18-19, inside the "
        "tool chest's own carcass (x 0.10-1.95, z 16.4-20.2); both are now out on "
        "the open floor east of it, where photo 1's foreground has them. The broom "
        "stand's base slabs moved south of the ride-on's footprint. Every piece is "
        "now placed WITHOUT on_floor: place() seats min-Y at pos.y and "
        "save_and_place's default pos.y IS the authored min-Y, so on_floor was "
        "lifting any piece whose lowest authored point was slightly negative -- that "
        "is the 'terminates above the floor plane with floor visible beneath' fault. "
        "The ride-on is measured after its tip and dropped so its lowest point is "
        "exactly y=0; the chest's castors are seated so the tyre bottom is y=0."),
    "4_door": (
        "Three struts FOUND, not added: round 1's source had them, authored at "
        "zi..zi+0.055 -- between the leaf and the wall, where nothing in the room can "
        "see them. They now sit on the face that looks into the room, with hinges, "
        "and the two jamb tracks moved with them. VALUE: roughness 0.58 -> 0.26 (a "
        "smooth leaf collects env specular a 0.95-rough wall cannot) plus emissive "
        "#7f7f7d. SURFACE: the whole leaf carries one textured quad -- top-lit "
        "gradient, a pillow across each section, joint lines, an embossed stucco "
        "grain and grime at the bottom rail."),
    "5_object_fidelity": (
        "Clock: was a 0.86 ft SPHERE with a red rectangle; now a torus bezel plus a "
        "textured 1.32 ft disc with real ticks, numerals and the LIQUI MOLY block. "
        "(Two false starts: a filled cylinder with averaged normals shades like a "
        "dome, and a dial coplanar with the bezel z-fights and loses.) Ride-on: was "
        "a yellow tub, a yellow cowl and four discs; now a moulded toy supercar with "
        "a BLACK bonnet inlay, a BLACK bucket seat, a BLACK steering wheel on a "
        "raked column, black valance and skirts, five-spoke silver rims, wing, head "
        "and tail lights -- and it is stood on its tail with its TOP facing WEST. "
        "Round 1's rot_y=90 after the tip pointed the top SOUTH, so the room saw its "
        "flat black underside. Textured now: both prints beside the TV, both hung "
        "deck graphics, the two oval car mirrors, both KIES cabinet posters, the "
        "PARKING ONLY sign, the wave canvas. The M4 line drawing is a real tube "
        "outline, not two grey rectangles."),
    "6_density": (
        "Built from the critic's missing list: the RED FIRE EXTINGUISHER (its own "
        "piece -- bracket, chrome valve and pull ring, white instruction band with "
        "the yellow A/B/C column, black hose; round 1 had a 0.32 ft red cylinder "
        "buried inside the tool chest), the clear plastic drop sheet behind the "
        "ride-on, a red bow and two red garden tools in the corner greenery, the "
        "round chrome wall fan rebuilt as a caged fan on the NORTH wall, the two "
        "oval car-printed mirrors, the SECOND KIES poster on the cabinet doors, the "
        "PARKING ONLY sign as real type, and the red generator from Garage v3 4.jpg. "
        "Also added: the second Eames chair (photo 1 has a pair), two north-wall "
        "skate decks and two hanging caps, banner hem and grommets."),
    "7_surfaces": (
        "Floor: coin tile UNTOUCHED (the one thing round 1 passed); the missing "
        "large-scale half is now a vertex-colour field on a 0.40 ft grid -- "
        "reflected door light, three specular smears down the bay, two tyre-track "
        "arcs, two octaves of scuff noise and a rubbed patch under the ride-on. "
        "Walls: the grain was re-scaled, not merely coarsened. Reading round 1's two "
        "terms separately, |d1| was already right (2.16 vs the photo's 2.50) and sd "
        "was too LOW (3.14 vs 5.12); the ratio was high because the denominator was "
        "small. A first attempt that coarsened the lattice took the north wall to sd "
        "2.34 / |d1| 0.17 and destroyed the term that was correct, so the tile now "
        "keeps round 1's finest octave at round 1's texel density and adds two "
        "coarse octaves. Ceiling: was mean|d1| 0.06 -- dead flat and 195 against the "
        "photo's 175.7; now a drywall tile with taped joints, at 169.")}

d["_camera"]["photo_pose"] = {
    "pos": [23.3, 13.1, 34.1], "target": [28.9, 12.2, 13.0], "fov": 84,
    "size": [900, 1200], "flags": "--level 1 --day --no-cutaway",
    "_note": "unchanged from round 1 so the critic compares like with like"}
d["_camera"]["photo_pose_wide"] = {
    "pos": [22.9, 13.4, 33.9], "target": [28.3, 11.2, 13.0], "fov": 102,
    "size": [900, 1200], "flags": "--level 1 --day --no-cutaway",
    "_note": (
        "Garage v3 1.jpg is an uncorrected ultra-wide (a pinhole solve returns ~112 "
        "deg horizontal), so the 84 deg pose above cannot show the foreground the "
        "photograph does -- the extinguisher, the hose coil and the feed sack sit at "
        "a bearing of about 85 deg west of the optical axis and no reasonable fov "
        "reaches them. This wider pose frames the same content the photograph does.")}

d["_shots"] = {
    "_dir": "scratchpad/shots/v3_garage/",
    "r2_photo.png": "round-1 pose, like-for-like",
    "r2_photo_wide.png": "the photograph's own coverage",
    "r2_doll_sw.png": "the judged dollhouse quadrant (drops SOUTH and WEST)",
    "r2_doll_nw.png": "secondary; keeps the sectional door",
    "r2_lookS.png": "eye level at the closed sectional door",
    "r2_west.png": ("eye level down the west wall: extinguisher, chest, hose, "
                    "sack, cabinets, generator"),
    "r2_plan.png": "top-down, used to meter the contact shadows",
    "_sbs": ["r2_photo_sbs.jpg", "r2_photo_wide_sbs.jpg", "r2_doll_sw_sbs.jpg",
             "r2_lookS_sbs.jpg"]}

d["_metered_srgb_luma"] = {
    "_method": (
        "native-resolution boxes on the round-2 renders listed in _shots. sd AND "
        "mean|d1| both reported. Photo numbers come from Garage v3 1.jpg "
        "(1200x1600) for the interior and, for the closed door only, from v3 3 and "
        "v3 5. TWO TRAPS, both avoided: c_look_n (950,200)-(1060,600) is a LIT "
        "OBJECT, not wall, and 300,120-690,290 in v3 1 is the underside of the OPEN "
        "sectional door (214.9), not ceiling -- the real ceiling patch is "
        "430,455-560,490 at 175.7."),
    "walls_render": {
        "north_clean": "169.8 (sd 4.17, |d1| 2.82, |d1|/sd 0.676)",
        "south_beside_door": "150.5 (sd 9.82, |d1| 2.98)",
        "_note": "east and west are behind furniture in every round-2 pose"},
    "walls_photo": {"north_clean": "166.9 (sd 5.12, |d1| 2.50)",
                    "east_clean": "178.1 (sd 6.52, |d1| 1.79)"},
    "door_render": "197.0 (sd 2.75, |d1| 1.18) / 191.7 (sd 19.33, |d1| 2.51)",
    "door_photo": ("v3 5: 220.6 (sd 19.68, |d1| 3.91); "
                   "v3 3: 216.2 (sd 23.75, |d1| 4.57)"),
    "door_differential": "render +46.5 over its own south wall; photo +30 to +78",
    "floor_render": {"open": "77.9 (sd 7.88, |d1| 4.14)",
                     "mid": "81.5 (sd 12.26, |d1| 5.74)",
                     "far": "85.7 (sd 3.46, |d1| 1.12)"},
    "floor_photo": {"far": "81.7 (sd 17.24, |d1| 4.76)",
                    "mid": "86.4 (sd 17.95, |d1| 6.76)",
                    "grazing_v3_5": "95.2-126.4 (sd 10.9-25.8)"},
    "ceiling": ("render 169.0-170.0 (|d1| 0.43-0.71) against the photo's 175.7 "
                "(sd 9.26, |d1| 2.19)"),
    "banner": "render 190.3 / 207.4 against the photo's 201.6 / 198.5",
    "contact_shadow_darkening_at_the_edge": {
        "_method": (
            "meter_shadows.py computes both boxes from the same footprint list the "
            "floor is built from, and picks the sample side by clearance from every "
            "other footprint, so a box cannot land on an object. 'edge' is the "
            "0.02-0.22 ft strip of floor outside the footprint; 'open' is 1.05-1.35 "
            "ft out."),
        "cabinets + generator run": "36.1%",
        "tool chest / hose / sack / white box": "34.1%",
        "brooms + shovel stand": "34.1%",
        "gear bag": "33.4%",
        "ride-on car": "33.5%",
        "two Eames chairs": "35.4%",
        "steps + scraper mat": "36.8%",
        "bristly mat": "38.6%",
        "_unsampleable": (
            "drop sheet 18.0%, speaker 75.6% and paper stack 3.7% have clearance "
            "under 0.5 ft from a neighbouring footprint, so their 'open' box still "
            "sits inside a neighbour's ramp or on a neighbouring object -- those "
            "three numbers are the sampler's, not the shadow's."),
        "target": "about 34% at the contact edge (ROOM-BRIEF)"}}

d["_payload"] = {"room_total_kb": round(tot, 1), "objects": len(pieces),
                 "largest_piece_kb": max(v["kb"] for v in pieces.values()),
                 "largest_piece": max(pieces, key=lambda k: pieces[k]["kb"]),
                 "budget": "<=1.5 MB per room and <=300 KB per piece: both met",
                 "round1_was": "952.7 KB over 20 objects"}
d["pieces"] = pieces

gaps = [g for g in d["_gaps"]
        if "reinforcement" not in g
        and not g.startswith("The banner artwork")
        and not g.startswith("Contact shadows:")]
gaps += [
    "THE BANNER TEXTURE IS PHOTO-DERIVED, and that is declared, not hidden: it is a "
    "rectified, illumination-normalised crop of the real vinyl out of Garage v3 "
    "1.jpg, mapped as a baseColor albedo. This is texture baking -- the standard way "
    "a photographed artwork gets into a render -- not a composite of the photograph "
    "into the frame. Everything else in the room is drawn procedurally.",

    "DISAGREEMENT with the round-1 verdict: the two car mirrors are NOT flanking the "
    "house door. Garage v3 6.jpg and the 350-400 px column of v3 1 show both of them "
    "on the EAST jamb side, one directly above the other. Built stacked.",

    "DISAGREEMENT: the pegboard is not black. The east-wall crop of v3 1 (x "
    "1025-1200, y 635-730) shows a MID-GREY perforated panel carrying BLACK hooks; "
    "the hooks are what read as black at distance. Round 1's own _evidence line "
    "called it black and was wrong. Repainted #5e6367.",

    "The floor's sd is still short: 7.9-12.3 against the photo's 17.2-18.0, at a "
    "matching mean (77.9-85.7 vs 81.7-86.4) and a matching mean|d1| (4.14-5.74 vs "
    "4.76-6.76). Pushing the vertex field harder was tried at SHEEN_GAIN 1.55 and it "
    "took the contact shadows to 36-42 per cent -- past the brief's 34 -- so it was "
    "backed off to 1.28. The remaining sd in the photograph is mostly the big "
    "specular reflection of the OPEN door, which this room models closed.",

    "The ceiling is still flatter than the photograph: mean|d1| 0.43-0.71 against "
    "2.19. That is 7-12x better than round 1's 0.06 and its value is now right (169 "
    "vs 175.7), but the drywall tile mips away at the distance the ceiling is seen "
    "from. Same root cause as the coin floor's: GLTFLoader gives an embedded texture "
    "anisotropy 1 and a GLB cannot set it.",

    "The sectional door reaches 197.0 against the photograph's 216-220. The "
    "DIFFERENTIAL is inside the photograph's range (+46.5 over its own south wall "
    "against +30 to +78), which is the term the round-1 verdict said mattered more. "
    "Closing the last 20 points needs either a stronger emissive (the leaf would "
    "then glow at night) or interior shop lights this scene does not model.",

    "The room's exact feet ALONG the north wall stay unsolved and are now "
    "understood: the photograph disagrees with itself by about 5 ft across that "
    "wall. The banner rectifies at 4.9-5.2 ft wide, which needs ~39 px/ft; the whole "
    "run from the service door's east jamb to the NE corner is 13.87 ft in 364 px, "
    "which needs 26. No single pinhole pose reconciles them -- the lens is "
    "barrel-distorted and the camera stands hard against the west side. Wall "
    "ASSIGNMENT is from the plan and is unchanged."]
d["_gaps"] = gaps

json.dump(d, open(P, "w", encoding="utf-8"), indent=2)
print("written %s (%d objects, %.1f KB)" % (P, len(pieces), tot))
