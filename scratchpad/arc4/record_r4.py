# -*- coding: utf-8 -*-
"""Record round 4 (cabinet artwork) in tools/roomkit/rooms/2.json."""
import io
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
J = os.path.join(ROOT, "tools", "roomkit", "rooms", "2.json")
d = json.load(io.open(J, encoding="utf-8"))

db = sqlite3.connect(os.path.join(ROOT, "backend", "house.db"))
rows = db.execute("select o.name, m.filename from objects o "
                  "join models m on o.model_id = m.id where o.room_id = 2").fetchall()
tot = 0
for name, fn in rows:
    p = os.path.join(ROOT, "backend", "uploads", "models", fn)
    kb = os.path.getsize(p) / 1024.0 if os.path.exists(p) else 0.0
    tot += kb
    if name in d["pieces"] and isinstance(d["pieces"][name], dict):
        d["pieces"][name]["kb"] = round(kb, 1)
d["_payload_kb"] = round(tot, 1)

d["_round4"] = {
    "scope": "CABINET ARTWORK ONLY.  No room geometry, no footprints, no app "
             "code, no other room, no poses.json.  Every z/x position, width, "
             "height, deck height, marquee depth, plinth and profile style in "
             "ar2.py's three run tables is round 3's, unchanged.",
    "the_defect": "Round 3's critic: 'the cabinet artwork is one machine "
                  "repeated sixteen times in different hues, where the "
                  "photograph shows four unrelated printed graphics.'  Correct. "
                  "a2kit._art_atlas() painted 16 tiles of which 0-11 were the "
                  "SAME motif (ground gradient + header strip + one off-centre "
                  "blob) in twelve hues and 12-15 were sine-wash bands with "
                  "rectangles standing in for lettering.  upright() then fed "
                  "ONE of those tiles to the front panel AND the control deck "
                  "AND the screen bezel.",
    "the_fix": "16 machines identified from the owner's photographs and drawn "
               "individually by four art modules (scratchpad/arc4/art/art_g0..3"
               ".py), packed by scratchpad/arc4/atlas4.py into one atlas PER "
               "WALL RUN, and wired by slug in ar2.py.  Each machine now has "
               "its own .marquee / .side / .front / .deck, its own marquee "
               "emissive tint, and its own carcase / T-molding colour.",
    "roster": {
        "east_wall_north_to_south": [
            "star-wars-atari", "marvel-super-heroes", "marvel-vs-capcom",
            "mortal-kombat", "nba-jam", "tmnt-turtles-in-time",
            "east-7-no-machine"],
        "south_wall_west_to_east": [
            "legends-ultimate", "street-fighter-2-champion-edition",
            "time-crisis", "terminator-2"],
        "sw_corner": ["ridge-racer"],
        "north_wall_west_to_east": [
            "north-1-graffiti-multicade", "pac-man", "nfl-blitz",
            "golden-tee-3d-golf"],
    },
    "atlas": {
        "builder": "scratchpad/arc4/atlas4.py",
        "why_three": "glb.py shares an image by byte identity INSIDE one file, "
                     "but Cabinets East / North / South are three GLBs, so one "
                     "room-wide atlas is paid for three times.",
        "east_px": "1024x280, 28 panels, 73.8 KB",
        "south_px": "512x384, 20 panels, 47.8 KB",
        "north_px": "512x280, 17 panels, 41.5 KB",
        "total_kb": 163.1,
        "panel_px": {"marquee": 120, "front": 96, "side": 64,
                     "side_star_wars_and_multicade": 96, "deck": 48,
                     "bezel_golden_tee_only": 48},
        "supersample": "every panel painted at 2x and box-averaged down; "
                       "art_g2 paints into a fixed 256 buffer and point-samples "
                       "on the way out, which shreds letterforms at any smaller "
                       "tile.",
        "quantisation": "16 levels/channel after the average.  The modules "
                        "quantise to 8 and lean on a fixed 4x4 Bayer pattern; "
                        "box-averaging destroys both and cost 0.86 bytes/px "
                        "against their own 0.13-0.47.  Re-quantising put it "
                        "back: 243.2 KB at 8 levels, 174.9 at 16, for the same "
                        "panel sizes.  Re-dithering at quantise time cost 40 KB "
                        "and was rejected.",
    },
    "marquee_emissive": "A marquee IS a backlit lamp in the photographs, so it "
                        "stays emissive -- a fixture the photograph shows, at "
                        "the size it shows it, which is the exception "
                        "ROOM-BRIEF allows.  Round 3 shared four pastels across "
                        "sixteen machines at strength 1.7.  Now per-machine "
                        "(a2kit.MARQUEE): hue from that band, value LOW, "
                        "strength ~1.  glTF emissive is a flat factor with no "
                        "texture, so the first pass at the band's own light hue "
                        "washed NBA Jam's crimson caps pink and bleached the "
                        "Turtles marquee; the shipped tints sit at luma 60-85 "
                        "for the bands the photos show LIT (Pac-Man, NBA Jam, "
                        "Time Crisis, Golden Tee, Ridge Racer) and 22-30 for "
                        "the ones they show dark (Star Wars, NFL Blitz, the "
                        "graffiti multicade, east-7).",
    "carcase_colour": "New this round (a2kit.CARCASE).  sweep()'s perimeter "
                      "quads are the cabinet's top, back and the strip of front "
                      "face either side of the printed panel -- i.e. the "
                      "T-molding.  Round 3 painted all sixteen black.  Now: "
                      "Star Wars and Pac-Man yellow carcases, Turtles bright "
                      "grass-green molding, Time Crisis and Ridge Racer red "
                      "bodies, MK / NBA Jam / T2 maroon molding, Marvel Super "
                      "Heroes gold-tan.  Material colour only, no geometry.",
    "declared": [
        "EAST_RUN[6] is kept because this round changed artwork, not layout, "
        "and the geometry was explicitly out of scope.  The roster counted FIVE "
        "uprights on the east wall in four independent frames, not seven, so "
        "the slot is dressed as an honest unbranded black upright with a blank "
        "marquee and no licensed graphic.  It should be DELETED and the run "
        "re-spaced in a geometry round.",
        "No riser quads were added.  art_g1 and art_g2 painted separate .riser "
        "panels for Marvel Super Heroes, Turtles and Marvel vs Capcom, but the "
        "cabinet has no riser geometry and splitting the front quad would "
        "squash those machines' front artwork ~20% vertically.  Marvel vs "
        "Capcom therefore carries its wordmark on the printed base band of its "
        "front panel rather than on a separate riser; the roster says that "
        "machine's own lower front is 'essentially no printed graphic'.",
        "time-crisis.speaker was painted by art_g1 and is NOT packed -- the "
        "cabinet has no separate speaker quad.",
        "Three of art_g3's four bezels are dropped (its own assessment: they "
        "'carry no identity').  Golden Tee's is kept because its lit yellow "
        "three-panel instruction strip is a real feature.  The other fifteen "
        "bezels are a plain untextured #15151a material, per art_g0's "
        "recommendation -- round 3 reused the front tile there, which smeared "
        "NBA Jam's flaming ball round its monitor.",
        "sweep() maps ONE side rect to both flanks, so a machine's side art is "
        "correctly anchored to the cabinet on both sides but reads mirrored on "
        "the +x flank.  Not fixed: fixing it needs a second, mirrored tile per "
        "machine, and only Star Wars and the graffiti multicade have side art "
        "with any directional content.",
        "The display case's 30 collectible boxes (NE corner) take a rotation of "
        "the NORTH run's own panels (ar2.BOX_ART).  They are 0.35 x 0.58 ft "
        "boxes seen from across the room, so what they need is varied printed "
        "colour, not identity -- but a critic is entitled to know they are "
        "cabinet artwork re-used at box scale.",
        "flip=True was removed from the control-deck quad.  It mirrored the "
        "tile left-right, which was harmless on an abstract motif and is not "
        "now: NBA Jam's logo lies on its boards, Golden Tee's deck legend is "
        "three words, Mortal Kombat's carries its wordmark.",
        "The four judged poses in shoot4.py all aim DOWN and crop every machine "
        "at the screen bezel, so not one marquee was in shot.  Four level "
        "frames at marquee height were ADDED (mq_east, mq_north, mq_south, "
        "mq_south_w); the original four are unchanged so the A/B against "
        "base_*.png still holds.",
    ],
    "payload": {
        "room_kb": round(tot, 1),
        "budget_kb": 1536,
        "atlas_kb": 163.1,
        "round3_atlas_kb": 29.3,
        "note": "Round 3's whole art atlas was 29.3 KB because it was twelve "
                "hues of one drawing.  Sixteen machines' worth of real artwork "
                "at 256 px would be ~1.2 MB per copy and ~3.6 MB across the "
                "three GLBs.  Per-run atlases, per-panel-class sizes and "
                "16-level re-quantisation land it at 163.1 KB total.",
    },
    "shots": ["scratchpad/arc4/shots/r4_a_look_s.png",
              "scratchpad/arc4/shots/r4_b_look_n.png",
              "scratchpad/arc4/shots/r4_cab_east.png",
              "scratchpad/arc4/shots/r4_cab_north.png",
              "scratchpad/arc4/shots/r4_mq_east.png",
              "scratchpad/arc4/shots/r4_mq_north.png",
              "scratchpad/arc4/shots/r4_mq_south.png",
              "scratchpad/arc4/shots/r4_mq_south_w.png"],
    "art_sheets": ["scratchpad/arc4/sheet_east.png",
                   "scratchpad/arc4/sheet_south.png",
                   "scratchpad/arc4/sheet_north.png"],
    "build": "cd scratchpad/bsmt && python ar2.py east south ncab",
}

io.open(J, "w", encoding="utf-8").write(
    json.dumps(d, indent=1, ensure_ascii=False))
print("recorded; room payload %.1f KB" % tot)
