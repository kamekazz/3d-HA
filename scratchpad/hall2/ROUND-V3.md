# Room 17 (2F Hallway) — round V3 brief

**The bar is the six photographs in `docs/v2 Hallway-jpg/`. Open the actual JPGs.
Never work from a description of them.**

| photo | what it shows | our pose |
|---|---|---|
| `hallway_looking_towards_stairs.jpg` | south end looking N; knee wall on the RIGHT, master-bed door far end, two snake plants | `p_stairs` |
| `hallway_with_white_runner_rug.jpg` | north end looking S; knee wall on the LEFT, bath door dead ahead, metal sculpture near right | `p_runner` |
| `staircase_looking_down.jpg` | head of the flight looking down to the 1F front door | `p_down` |
| `staircase_looking_up.jpg` | 1F hall at the foot looking up the flight | `p_up` (level 1) |
| `two_closed_white_doors_1.jpg` | close on the west alcove corner | `p_doors1` |
| `two_closed_white_doors_2.jpg` | a step back, the alcove's doors | `p_doors2` |

Shoot with:

    cd "C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2"
    TAG=myinitials_ ../../backend/.venv/Scripts/python.exe v3.py p_runner p_stairs

Output lands in `scratchpad/hall2/shots/<TAG><pose>.png`. **Do not edit `v3.py`'s
poses** — every agent this round compares from the same viewpoints. Add your own
extra poses in your own file if you need them.

## Hard scope rules for this round

1. **Do not touch any room other than 17.** Not room 28 (the shaft), not 13, 14,
   15, 24, 25, 26. Room 28 is already set `is_void=1` and has its north+west
   walls opened; leave it alone.
2. **Do not move the floor plan.** Room 17's polygon, its anchor, and the
   position/width of all five door openings are CORRECT and signed off by the
   owner. Do not PATCH `points`, `x`, `z`, `width`, `depth`, or any opening's
   `edge_index` / `offset` / `width`. You may change an opening's `type` if your
   piece needs the engine to stop drawing its own flat panel.
3. **Do not delete a door.** The owner said "you have every door where it's
   supposed to be".
4. Piece names are global — every piece you write must start `Hall2F `.
   `roomkit.place` is idempotent by name, so re-running your script rebuilds in
   place instead of stacking duplicates.
5. Budgets still apply: **≤300 KB per piece**, and the room's total was 1.32 MB.
   Fine gradients come from a tiled tone field, not from mesh cells.

## The footprint, in room-local feet (anchor = world 6.70, 18.00, 6.55)

Room 17 is a 10-vertex L. `polygon_local`:

    (11.92,6.81) (7.61,6.81) (7.61,16.89) (3.86,16.89) (3.86,16.15)
    (0,16.15) (0,10.77) (3.86,10.77) (3.86,0) (11.92,0)

Three parts:
- **North block** local x 3.86..11.92, z 0..6.81 — the master-bedroom end.
- **Walking strip** local x 3.86..7.61, z 6.81..16.89 — the runner runs here.
- **West alcove** local x 0..3.86, z 10.77..16.15 — the three-door dead end.

Edges (edge i runs vertex i -> vertex i+1), with the opening on each:

| edge | run | opening |
|---|---|---|
| 0 | z=6.81, x 7.61..11.92 | passage 124, full-span: **no wall**, this is the open stairwell cut |
| 1 | x=7.61, z 6.81..16.89 | passage 143, full-span: **no wall** — the KNEE WALL stands here instead |
| 2 | z=16.89, x 7.61..3.86 | door 133 -> bathroom (room 26) |
| 3 | x=3.86, z 16.89..16.15 | short jog, solid |
| 4 | z=16.15, x 3.86..0 | door 127 -> Rios Room (room 15) |
| 5 | x=0, z 16.15..10.77 | door 125 -> room 25 |
| 6 | z=10.77, x 0..3.86 | door 136 -> Guest Room (room 13) |
| 7 | x=3.86, z 10.77..0 | solid |
| 8 | z=0, x 3.86..11.92 | door 137 -> Master Bed (room 14) |
| 9 | x=11.92, z 0..6.81 | solid |

Wall height 8.0 ft. Slab world Y = 18.0. Level 2.

## What this round already fixed — do not undo it

- `rooms.is_void` (new column) makes house.js skip a room's slab and plinth cap.
  Room 28 "Stairwell" is now `is_void=1`, so the stairwell reads as an open well
  instead of being floored over. That was the owner's "I don't want to see the
  bottom of the stairs" — the well is open now and `p_down` sees all the way to
  the 1F front door.
- The full-height wall between the strip and the stairwell is gone (openings 143
  on room 17 edge 1 and 144 on room 28 edge 3, both full-span floor-to-ceiling,
  which makes `buildRoom` skip the wall outright). That was the owner's "a half
  wall that you created as a whole wall". **The knee wall GLB is now the only
  thing standing on that line — it has to carry the whole boundary.**

## What is still wrong, from the current renders

Every one of these is visible in `shots/a_*.png` / `shots/b_*.png`:

- The **ceiling piece and the baseboards were built for the OLD footprint** and
  stop short of the west alcove — `p_doors2` looks straight up into open sky.
  Same for the wall skins and the floor planks.
- **Door leaves are flat featureless slabs.** The photos show 6-panel colonial
  doors: two small top panels, two long bottom panels, deep coves, white; black
  lever handles with a rose; black butt hinges; a white casing about 3.5 in wide
  with a square edge; a visible reveal shadow at the leaf-to-frame line.
- **Floor planks are hard alternating light/dark stripes.** The photos are a
  cool mid-grey wood-look plank, low contrast plank-to-plank, with a soft sheen
  running down the hall that is most of what makes the hall read as long.
- **Ceiling lights are protruding white saucers plus one enormous dome.** The
  photos show flush recessed cans, small, warm.
- The **knee wall cap is far too thick** and its near end is a stepped notch.
  The photos show a flat white cap board that overhangs both faces slightly,
  with a square post at the open end.
- The **metal wall sculpture is oversized and too dense**, and it runs to the
  floor. The **snake plants are three fat blades**, not a dense fan.
- The **stair runner is a lighter quad painted on the tread tops** — it must
  wrap over each nosing and down each riser as a continuous band inset from the
  sides. The **handrail is a chunky faceted bar with no brackets**. The photos
  show a black rail on black brackets on the shaft wall (`staircase_looking_down`)
  and a black newel + black rail over white square balusters at the foot
  (`staircase_looking_up`).
- **No contact shadow** under the runner, the plant stands, or the door bottoms.

## Engine limits — do not chase these

`roomkit.glb` has **no image-texture API**: "tiled texture" here means per-cell or
vertex tone authored into the geometry. The app renders **no shadow maps for
generated geometry**, so cast shadows and AO are unavailable — bake a contact
shadow decal under every piece instead. The levers you do have: material
roughness/metalness for sheen, vertex/cell tone for grain and gradients, baked
contact-shadow decals, baked light falloff in the wall skins, differentiated
albedo per trim element, and better geometry.

Read `tools/roomkit/ROOM-BRIEF.md` for the toolchain and
`scratchpad/hall2/CRITICS-R2.md` for the five themes four blind critics
converged on last round.

## Round 2 was killed mid-flight — rules that came out of it

Every agent in the first round-2 attempt was terminated by a session limit while
still iterating. Three pieces were left **placed in a debug/calibration state** and
the room rendered as a neon test card: the knee wall in per-part R/G/B mask colours
(`kwprobe.py`), the baseboards in magenta, and the ceiling as an 8-tone calibration
fan (`ccal.py`). A fourth, `Hall2F Wall Wash Skins`, was left holding a
**near-black (#2b2b2b) panel** that punched two pure-black voids into the hallway —
above the far door and beside it — which is what the black holes in
`shots/r2a_*.png` and `shots/fix_*.png` are.

So, three rules, and they are not optional:

1. **Never finish a step with a probe piece placed.** If you place a debug,
   calibration or mask version of your piece to measure it, re-place the REAL piece
   in the same breath — same script run, not "next time". Assume you will be killed
   between one tool call and the next.
2. **Place from `glb/<your_piece>.glb`.** The skins builder uploaded an
   in-progress mesh whose source was never written to `glb/`, so the file on disk
   and the model in the app disagreed and the only way to find that out was to
   raycast the running scene. Keep the two in sync.
3. **Look at the whole frame before you report, not just your piece.** Two rounds
   of critics missed those black voids because each was told to judge one subject.

`Hall2F Wall Wash Skins` (object 282) has been DELETED for exactly this reason.
The room currently renders on the engine's own wall colour `#cfd1d2`. Whoever owns
the wall skins this round is building that piece from nothing — do not look for an
existing one to patch.

`Hall2F Doors` / `Hall2F Door Casings` were reverted to the round-1 build
(`doorsv3.py`), because the round-2 rewrite (`doors2.py`) was killed with swirl
artefacts inside every panel. `doors2.py` is on disk and has the better panel
research in it; treat it as a draft to finish, not as working code.
