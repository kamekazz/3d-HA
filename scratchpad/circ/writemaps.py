"""Rewrite tools/roomkit/rooms/{12,17,27}.json from the live house."""
import json
import urllib.request
import os
import glob
import math

H = json.loads(urllib.request.urlopen('http://127.0.0.1:5000/api/house', timeout=30).read())
UP = r'C:\Users\Manuel\Desktop\Pro\3d HA\backend\uploads\models'
ROOT = r'C:\Users\Manuel\Desktop\Pro\3d HA\tools\roomkit\rooms'

NOTES = {
 12: dict(
  camera=("doll_ne",
          "Walls are FrontSide with inward normals, so the two nearest the camera are culled. "
          "Room 12 content is its WEST wall (three doorways) and its SOUTH wall (front door + two "
          "sidelights); doll_ne is the only quadrant that leaves BOTH of those standing. The shell "
          "pass chose doll_sw, which culls both of them."),
  room_note=(
   "First floor hallway + entry. VERIFIED this round, not rebuilt: the seven real openings were "
   "re-checked against the registered Main Floor Plan (scratchpad/circ/wallscan.py) and against the "
   "neighbours own cuts -- north == room 5 opening 32 exactly, west-kitchen == room 6 opening 8 "
   "exactly. The stair is the app own level-1 stairs row (world x 14.6..18.4, z 14.3..24.5, "
   "ascending north) dressed with treads/risers/runner plus a raked balustrade. CHANGED this round: "
   "every contact shadow moved from y=0.008-0.010 (which loses the depth fight to the room slab "
   "polygonOffsetFactor -1) to y=0.078, and from strength 0.12-0.26 to 0.44-0.48; the plank palette "
   "and floor_color darkened x0.80 so the floor meters 106.5 / sd 12.4 against the photo 109.2 / "
   "sd 13.6."),
  gaps=[
   "Room 4 (Dining) does NOT register with this room dining passage. Ours is world z 24.90..31.15 "
   "(the plan gap is 25.05..32.20); room 4 own cut (opening id 85, its edge 7) is z 22.70..28.30, so "
   "the two overlap only over 24.90..28.30. Room 4 is another agent room and was not touched. The "
   "fix on their side: opening 85 -> edge_index 7, offset 3.20, width 6.25.",
   "Walls meter n 197.1 / e 191.9 / w 191.9 / s 168.7 -- spread 28.4, inside the ~30 a real room "
   "sits in, against the photo 182.2 (west) and 217.1 (east; that photo patch includes the stair "
   "white trim).",
   "Every wall skin meters sd 0.00 and mean|d1| 0.00 -- flat paint with no fine-scale grain at all, "
   "against the photo sd 3.55 / |d1| 0.42. Floor |d1| 0.10 native (0.27 downsampled to the photo "
   "ft/px) against the photo 2.96. This is the biggest remaining accuracy gap in all three rooms.",
  ]),
 17: dict(
  camera=("doll_se",
          "Content is the WEST wall (metal sculpture, return-air grille, two doorways) and the NORTH "
          "wall (the master-bedroom cased opening the primary photo looks straight at). doll_se culls "
          "south + east and leaves exactly that pair standing -- and the east wall it culls is the "
          "only blank one in the room. The shell pass chose doll_nw, which culls the west wall and "
          "would leave the sculpture hanging in mid-air."),
  room_note=(
   "Hallway (2F). Orientation: the primary photo has the stairwell knee wall running away on the "
   "RIGHT and the master-bedroom opening at the far end, so it is shot from the SOUTH looking NORTH. "
   "Confirmed independently by the level-1 stairs row (world x 14.6..18.4, z 14.3..24.5) landing on "
   "the plan drawn treads, and by the plan showing the knee-wall line at world x ~14.4 running "
   "z 13.7..23.5. NO crown in this room -- every shot shows a clean drywall corner. CHANGED this "
   "round: per-wall albedo skins re-fitted from real two-point render probes (the previous skins "
   "were ONE flat colour on all four walls and metered a 121.2-byte spread; now 9.1); runner and "
   "plant contact shadows moved to y=0.078 and strength 0.42-0.46; plank palette and floor_color "
   "re-fitted to the photo."),
  gaps=[
   "Room 14 (Master Bed) does NOT register with this room north opening. Ours is world x "
   "14.55..17.45 at z=6.60, matching the plan gap 14.56..17.43 to 0.02 ft; room 14 south wall on "
   "that leg (its edge 1, from (18.62,6.30) to (13.84,6.30)) has no opening at all. It reads through "
   "in practice only because room walls are FrontSide, so a neighbour uncut wall is back-face culled "
   "from our side. The fix on their side: a passage on edge_index 1, offset 1.17, width 2.90, "
   "height 7.00, elevation 0.",
   "The second west doorway (world z 18.50..21.20) is a real gap in the plan but the layout has NO "
   "room behind it -- world x 6.70..10.50, z 17.30..22.70 is unmodelled space between room 25 and "
   "this hallway. It is cut with an opaque leaf in it so it does not open onto nothing.",
   "Room 26 (2F bath) does NOT register with this room south opening (world x 11.40..14.20 at "
   "z=23.30); room 26 has no openings at all. It belongs to the bathroom agent and was not touched. "
   "The fix on their side: a passage on room 26 edge_index 0 (z=23.40), offset 0.90, width 2.80.",
   "Room 17 footprint has no void in it and the app draws one opaque slab across the whole rect, so "
   "the real stairwell opening down to the first floor cannot be shown -- it is a dark inset panel "
   "with a white nosing board, which reads as a well from the dollhouse pose but is not a hole.",
   "Wall skins meter sd 0.00 / mean|d1| 0.00 against the photo 13.60-26.40 / 0.37-1.19.",
  ]),
 27: dict(
  camera=("doll_nw",
          "The hero surface is the black raked accent wall on the SOUTH; only a camera to the north "
          "leaves it standing, and doll_nw keeps SOUTH + EAST, which is the pair the primary photo "
          "looks at. The north wall it culls carries only freestanding wire racks, which do not read "
          "as floating without a wall behind them."),
  room_note=(
   "Master Closet. ORIENTATION CORRECTED THIS ROUND: the shell pass put the ceiling rake and the "
   "black accent wall on the EAST wall. Raycasting the house-shell GLB straight down over the "
   "footprint gives a roof underside that is CONSTANT in x (x = 22 / 25 / 28 / 31.5 all identical) "
   "and falls in z: z=13 -> 21.54, z=15 -> 20.58, z=17 -> 19.61, z=19 -> 18.65, z=20.5 -> 17.93 "
   "world ft, slope 0.481 = a 6:12 pitch. So the roof falls SOUTH. Two independent checks agree: the "
   "plan makes z=20.80 the outer edge of the 2F with the garage roof beyond, and in both photos the "
   "black raked wall is a LONG expanse (south is 13.6 ft, east only 8.4). The single door is on the "
   "NORTH wall from the Master Bath, cut to room 16 own span exactly and as a passage so room 16 "
   "painted leaf fills it instead of two coplanar panels z-fighting."),
  gaps=[
   "The white STEPPED form along the base of the black wall is INFERRED. It is unmistakable in the "
   "primary photo -- five or six white treads with a shoe and folded towels standing on them -- but "
   "nothing in the layout explains it: there is no stair within 4 ft of this room. Built as what it "
   "looks like, a white tiered platform / shoe bench (local x 3.60..9.30, 2.62 ft down to 0.46 ft), "
   "with the plain white skirting carrying on either side of it exactly as the photo shows.",
   "The rake break point (local z 2.60) and its low height (4.70 ft at the south wall) are inferred: "
   "the shell own roof numbers put the deck BELOW this room slab, so the shell gives the direction "
   "and the slope but not the height. Read off the photos against the 6.5 ft wire rack beside it.",
   "The east wall caps at 191.9 even with a pure-white (#ffffff) skin -- it is the wall the sun "
   "never reaches and cannot be brought to the 205 the other two hit. Residual white-wall spread "
   "15.2 (n 207.0 / w 207.1 / e 191.9) against the photo 211.",
   "Carpet meters 107.0 / sd 13.3 / mean|d1| 1.13 against the photo 99.3 / 19.3 / 16.35. The nap "
   "decal is deliberately PARTIAL (~60% coverage, jittered 0.13-0.30 ft patches at y=0.055) so the "
   "app tiled carpet texture still shows through; a full-coverage plane painted the texture out and "
   "metered sd 2.6.",
   "Wall skins meter sd 0.00 / mean|d1| 0.00 against the photo 9.47-21.68 / 0.71-10.26.",
  ]),
}

for rid, note in NOTES.items():
    for f in H['floors']:
        for r in f['rooms']:
            if r['id'] != rid:
                continue
            fp = r['footprint']
            pieces, kb = {}, 0.0
            for o in sorted(r['objects'], key=lambda o: o['name']):
                g = glob.glob(os.path.join(UP, 'model_%d.*' % o['model_id']))
                sz = os.path.getsize(g[0]) / 1024.0 if g else 0.0
                kb += sz
                pieces[o['name']] = {
                    "pos_room_local_ft": [round(o['position']['x'], 3),
                                          round(o['position']['y'], 3),
                                          round(o['position']['z'], 3)],
                    "rot_y": round(o['rot_y'], 4), "scale": o['scale'],
                    "kb": round(sz, 1)}
            pts = [[0, 0], [fp['width'], 0], [fp['width'], fp['depth']], [0, fp['depth']]]
            ops = []
            for op in sorted(r['openings'], key=lambda o: (o['edge_index'], o['offset'])):
                i = op['edge_index']
                ax, az = pts[i]
                bx_, bz = pts[(i + 1) % 4]
                dx, dz = bx_ - ax, bz - az
                L = math.hypot(dx, dz)
                ux, uz = dx / L, dz / L
                ops.append({"type": op['type'], "edge_index": i, "wall": "nesw"[i],
                            "offset": op['offset'], "width": op['width'],
                            "elevation": op['elevation'], "height": op['height'],
                            "world_span": [
                                [round(fp['x'] + ax + ux * op['offset'], 2),
                                 round(fp['z'] + az + uz * op['offset'], 2)],
                                [round(fp['x'] + ax + ux * (op['offset'] + op['width']), 2),
                                 round(fp['z'] + az + uz * (op['offset'] + op['width']), 2)]]})
            doc = {
                "_note": ("CIRCULATION round. Build scripts live in scratchpad/circ/ -- ckit.py holds "
                          "the shared helpers (idempotent openings reconcile, per-wall albedo skins "
                          "with holes punched round every cut, stair dressing) and r12.py / r17.py / "
                          "r27.py are idempotent by piece name, so re-running rebuilds and re-places "
                          "without duplicating. Wall/floor probes: scratchpad/circ/probe.py (12, 17) "
                          "and probe27.py (27); the fine-scale mean|d1| metric is d1.py."),
                "_room_note": note["room_note"],
                "_room": {"id": rid, "name": r['name'],
                          "floor": {"id": f['id'], "name": f['name'], "level": f['level']},
                          "rect_world": {"x": [round(fp['x'], 2), round(fp['x'] + fp['width'], 2)],
                                         "z": [round(fp['z'], 2), round(fp['z'] + fp['depth'], 2)]},
                          "size_ft": [fp['width'], fp['depth']], "wall_height": r['height']},
                "_surfaces": {k: r.get(k) for k in
                              ("wall_color", "floor_color", "floor_texture", "wall_texture")},
                "_camera": {"judge_from": note["camera"][0], "why": note["camera"][1]},
                "_openings": ops,
                "_payload_kb": round(kb, 1),
                "pieces": pieces,
                "_gaps": note["gaps"],
            }
            path = os.path.join(ROOT, "%d.json" % rid)
            with open(path, "w") as fh:
                json.dump(doc, fh, indent=2)
            print("wrote %s  %.0f KB payload, %d pieces, %d openings"
                  % (path, kb, len(pieces), len(ops)))
