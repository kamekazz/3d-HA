# Room 17 — Hallway (2F) — v2 rebuild brief

Read `tools/roomkit/ROOM-BRIEF.md` and `tools/roomkit/STYLE-BAR.md` first. This file
records only what is NEW or CHANGED since the CIRCULATION round, and it overrides
`tools/roomkit/rooms/17.json` and `scratchpad/circ/r17.py` wherever they disagree.

## Scope

Room 17 only. You may also add/correct the PAIRED opening on a neighbour's wall
(rooms 13, 14, 15, 26) where room 17 already has one — nothing else in those rooms.
No furniture, colours or geometry anywhere else in the house.

## The bar

`docs/v2 Hallway-jpg/*.jpg` — six photos, converted from the owner's HEICs.

| file | what it shows |
|---|---|
| `hallway_looking_towards_stairs` | south end of the walking strip looking NORTH: closed white door at the far (north) end, knee wall running away on the right, runner down the middle, sculpture on the west wall |
| `hallway_with_white_runner_rug` | north end looking SOUTH: knee wall on the left, runner, closed white door at the south end, purple night-light on the west wall |
| `staircase_looking_down` | standing at the head of the flight looking down: grey plank treads, WHITE risers, black handrail on black brackets, white capped knee wall, 1F entry at the bottom |
| `staircase_looking_up` | from the 1F: white square-baluster balustrade with a BLACK newel post and BLACK handrail on the open (west) side, white skirt board on the closed (east) side, grey stair runner over grey treads |
| `two_closed_white_doors_1/2` | the dead end: closed white **6-panel** doors, matte-white, **matte black lever handles and black hinges**, flat white casing, white baseboard |

**These photos are 450×600.** That is small enough that sd measured off them is
scale-inflated — the same trap that produced two wrong Kitchen reports. Use them for
CONTENT, LAYOUT and COLOUR only. For fine-scale metering (`sd`, `mean|Δ|`, `|d1|/sd`)
use the 1200×1600 `docs/photos-jpg/Second-floor hallway.jpg`.

## Owner's ground truth — do not re-derive this

- The three doors at the dead end are **Rios Room, a closet, and the Guest Room**.
- The **Master Bedroom** is at the opposite (NORTH) end, with **one** door.
- The **bathroom** door is at the south end, is **different from the three**, and is
  the one **closest to them**.

## What changed structurally (already applied — do not redo)

Room 17's footprint is no longer a rectangle. It is an L that notches the stairwell
out of the SE corner, so the slab has a REAL VOID and the flight below shows through
from both levels. This is the owner's second complaint and it is now fixed.

    points (room-local ft) = [[0,0],[8.1,0],[8.1,7.7],[3.95,7.7],[3.95,16.7],[0,16.7]]
    anchor x=10.5 z=6.6, width 8.1, depth 16.7, height 8.0   (world Y of this slab = 18.0)

Edge numbering follows consecutive point pairs:

| edge | from → to (local) | what it is |
|---|---|---|
| 0 | (0,0) → (8.1,0) | NORTH wall — Master Bedroom door |
| 1 | (8.1,0) → (8.1,7.7) | EAST wall, north landing only |
| 2 | (8.1,7.7) → (3.95,7.7) | head of the stairwell — cut away, opening 133 |
| 3 | (3.95,7.7) → (3.95,16.7) | the knee-wall line — cut away, opening 134 |
| 4 | (3.95,16.7) → (0,16.7) | SOUTH wall (west part only) — bathroom door |
| 5 | (0,16.7) → (0,0) | WEST wall, full length — Guest / closet / Rios doors |

Current openings: 124 (e0, off 4.05, w 2.90 — master bed), 127 (e4, off 0.25,
w 2.80 — bath), 125 (e5, off 6.02, w 2.73 — guest), 126 (e5, off 2.10, w 2.70 —
closet), 133 (e2, full length, cut away), 134 (e3, full length, cut away).

`Hall2F Floor Stairwell` (the old fake dark panel) has been DELETED. Do not re-place it.

## Traps specific to this room

- **`ckit.openings(17, want)` deletes anything not in `want`.** Openings 133 and 134
  are what make the stairwell a hole. If you call it, include them.
- **`ckit.blit`, `ckit.wall_skin` and `kit.baseboards` assume a RECTANGLE.** The east
  wall now exists only over z 0..7.7 and the south wall only over x 0..3.95. Anything
  authored "edge to edge" on those two walls will hang in mid-air over the void.
- **`Hall2F Floor Planks` still spans the whole 8.1 × 16.7 rect** and therefore floats
  across the void, hiding it. It must be recut to the L.
- **Do NOT run `scratchpad/circ/r17.py`.** It is written against the old rectangle and
  will re-place the fake well panel. Write new scripts in `scratchpad/hall2/`.
- `objects.js SURFACE_RE` makes a piece unpickable if its name contains
  floor / ceiling / wall wash / baseboard / crown. Names are global — keep `Hall2F `.
- Author in FEET with `roomkit.glb`; place with `roomkit.place` / `ckit.save_and_place`
  (idempotent by piece name). Never write the DB directly. Never touch the footprint,
  `poses.json`, or another room's geometry.

## Shooting

The app is already running on http://127.0.0.1:5000 — **do not restart it**.

    cd tools
    PY=../backend/.venv/Scripts/python.exe
    $PY -m roomkit.shot --pose-json '<pose>' --level 2 --day --no-cutaway --out <png>

`--no-cutaway` is NEW and required for any photo-matched interior pose: cutaway.js
always fades ceilings out and drops the two near walls, which is right for the
dollhouse pose and wrong when the bar is a photo taken standing in the room.
Keep the cutaway ON for `doll_se` (the dollhouse judging pose for this room).

`python scratchpad/hall2/shots.py [names...]` wraps this and already carries poses
matched to the photos: `v2_north`, `v2_south`, `v2_down`, `v2_doors`, plus every
generated pose. `TAG=<prefix>` prefixes the output filenames.

Blind pairing for a critic:

    $PY -m roomkit.sbs <render.png> <out.jpg> --ref "docs/v2 Hallway-jpg/<photo>.jpg" --blind

## Budget

≤1.5 MB for the room, ≤300 KB for any one piece. Room 17 was 400.9 KB over 9 pieces
before this round, so there is room — but tone fields are the usual culprit, so prefer
tiled/vertex tone over rasterised cells.

## The second-floor plan is NOT reliable (owner, 22 Aug 2026)

`docs/floor plan/Second Floor Plan App.png` is a **phone screenshot of the Home Assistant
app**, not an architectural drawing: faint outlines, no dimensions, and app UI chips
sitting on top of the geometry — a light-button chip covers the stairwell, and the
"Guess room" chip and "Closet." label sit exactly where the three doors are. The 2F room
rectangles in the DB were traced from it and inherit its errors. Room 15 (Rios) sharing
only 0.6 ft of wall with the hallway is almost certainly a trace artefact, not real.

Use it as a rough sanity check only. Priority of sources for this room:

1. `docs/v2 Hallway-jpg/*.jpg` — the photos.
2. The owner's statement (three doors = Rios / closet / Guest; master bedroom alone at
   the north end; bathroom door at the south end, different, closest to the three).
3. The plan, for gross layout only.

The one thing the plan does support, and it agrees with the owner: reading down the WEST
side of the hallway from the south end northward the rooms run **Rios Room, Closet,
Guest room, Closet**. Existing west openings are 126 (world z 18.50..21.20 = the
unmodelled closet) and 125 (world z 14.55..17.28 = Guest), so the missing **Rios door
sits SOUTH of 126**, at the dead end where both door photos were taken.

Do not fudge another room's geometry to make a pairing work. If a paired cut cannot be
made against a real shared wall, leave the neighbour uncut and report the exact
parameters that would be needed.

## Door count: FIVE, confirmed by the owner (22 Aug 2026)

The hallway has **exactly five doors** — no more, no fewer:

| # | wall | opening | room behind |
|---|---|---|---|
| 1 | north, edge 0 | 124 (off 4.05, w 2.90) | Master Bedroom — the single door at the far end |
| 2 | west, edge 5 | 125 (off 6.02, w 2.73) | Guest Room |
| 3 | west, edge 5 | 126 (off 2.10, w 2.70) | the closet |
| 4 | west, edge 5 | **MISSING — must be added** | Rios Room, south of 126 at the dead end |
| 5 | south, edge 4 | 127 (off 0.25, w 2.80) | the 2F bathroom |

Doors 2, 3 and 4 are the three the owner photographed at the dead end. Door 1 is alone at
the north end. Door 5 is different from the three and is the closest to them.

This independently confirms the plan's west-side order (Rios, Closet, Guest room, Closet)
and settles the count: the second "Closet." the plan draws further north does NOT open
onto the hallway. Do not invent a sixth opening, and do not leave any of the five as a
bare `passage` — every one carries a closed white 6-panel leaf.

## Neighbour wall-wash holes — owner-approved (22 Aug 2026)

Room 13's `Guest Wall Wash` and room 26's `Bath2F Wall Wash` span their whole walls with
no hole where the hallway's doorway already is, so they render as a flat slab across the
opening and hide the leaf. The owner has approved cutting **those two holes only**.

Scope stays tight: punch the hole, change nothing else in rooms 13 or 26 — no furniture,
no colours, no geometry, no other piece. Once cut, revert the temporary workaround in
`scratchpad/hall2/doors.py piece_doors()`: set the guest and bathroom leaves back to
`REV` (0.155) from `rev=0.004` / `rev=0.100` so they regain the full 2 in reveal.

## Duplicate neighbour door panels — owner-approved (22 Aug 2026)

Cutting the wall-wash holes was necessary but not sufficient. Room 13's `Guest Baseboards`
and room 26's `Bath2F Baseboards` each carry their OWN flat painted door panel on the wall
shared with the hallway, 0.145 ft deep, sitting in front of room 17's modelled leaf:

- `scratchpad/guest13/g1_shell.py:106` — `door_unit(m, "e", W, D, DOOR[0], DOOR[1])`,
  world x 10.355–10.500.
- `scratchpad/baths/b26.py build_trim()` — `door_unit(m, "n", W, D, *DOOR_N)`,
  world z 23.400–23.545, x 10.92–13.72 — which is 0.48 ft out of register with opening
  128 and shows doubled panel outlines from inside room 26.

The owner has approved DROPPING BOTH LEAVES, keeping each piece's casing and skirting.
Room 17's leaves are `both_faces=True`, so they serve both sides — which is already how
room 13's doorway behaves seen from room 13. This also fixes room 26's ghost door.

Nothing else in rooms 13 or 26 changes.

## `house.js` now skips a wall an opening fully spans (22 Aug 2026)

`buildRoom` extends each wall run one `WALL_THICKNESS` past both ends so corners
overlap, and an opening's offset is clamped to `[0, len]`. So an opening meaning "there
is no wall here" could never reach the overshoot: it always left a floor-to-ceiling post
at each end, and two of them met in a solid column at the stairwell notch corner.
Widening the opening instead makes `ExtrudeGeometry` triangulate garbage walls.

`buildRoom` now skips the wall entirely when an opening on that edge satisfies
`offset <= 0 && offset + width >= len && elevation <= 0.01 && elevation + height >=
room.height - 0.02`. Audited against all 62 openings in the house: exactly two match,
openings 133 and 134, both in room 17. The plinth skirt and accent rim are children of
the wall, so they go with it — which also removed the saturated accent stripes that were
ringing the void.

Consequences: `Hall2F Stair Pier` is deleted and dropped from `stairs.py`'s default piece
set. The "well rim reveal" inside `Hall2F Stairwell Floor Lining` is now redundant but
harmless.

Unrelated pre-existing bug found while auditing, NOT fixed: room 14 opening 79 has
`edge_index` 7 on a 7-edge room (valid indices 0-6), so that window has never rendered.
