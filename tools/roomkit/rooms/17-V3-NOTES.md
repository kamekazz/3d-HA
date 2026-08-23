# Room 17 (2F Hallway) — where V3 stopped

Stopped by the owner during round 2 wave A. The room is in a clean, consistent
state; all six poses in `scratchpad/hall2/shots/done_*.png` were shot and checked
after the in-flight builders were killed and their partial work reverted.

## Structural changes that are now part of the app — keep these

- **`rooms.is_void`** (new column, `house/store.py` SCHEMA + ALTER + `ROOM_FIELDS`).
  A room with `is_void=1` gets its walls but **no floor slab and no plinth cap**
  (`frontend/js/house.js buildRoom`). Room 28 "Stairwell" is the only one set.
  This is what makes a stairwell read as an open well: the app draws one opaque
  slab per footprint and a polygon cannot carry an interior hole, so a shaft has
  to be its own room and that room has to be floorless.
- **Openings 143 (room 17 edge 1) and 144 (room 28 edge 3)** are full-span,
  floor-to-ceiling passages. That makes `buildRoom` skip those walls outright, so
  the boundary between the hallway strip and the stairwell is carried by the
  `Hall2F Knee Wall` GLB alone. This was the owner's "a half wall that you made
  into a whole wall".
- **Room 17's five door openings are `passage`, not `door`.** The engine draws its
  own flat panel for every `door`, and so does the neighbouring room for its copy
  of the same doorway — so every hallway doorway used to carry two coincident
  white slabs a wall-thickness apart. That was almost certainly the owner's "one
  extra door". `Hall2F Doors` supplies the real leaves instead.

## The floor plan is correct and signed off — do not move it

Room 17's polygon, its anchor, and all five door positions are as the owner
approved. All five openings were checked against the photographs and the plan and
all five are supported. The weakest is **opening 125** (room 25, the alcove's west
wall): the plan symbol there spans ~4.1 ft, which reads as a bypass closet rather
than a 2.9 ft swing door, and both alcove photos are titled "two closed white
doors". Left alone deliberately. That is an owner question, not a bug.

## Open verdicts — the spec for a next round

`scratchpad/hall2/VERDICTS-R1.md` holds nine blind critic verdicts in full. All
nine correctly identified the photograph, all nine "certain". Four themes ran
through every one: no texture anywhere, nothing touches the ground, every white is
the same white, no light falloff. In priority order the critics gave:

1. **Floor planks** — five critics' opening tell, three of them judging something
   else. Value too dark and too cool; no plank joints, no butt joints, no
   board-to-board variation, no sheen running down the hall.
2. **Wall skins** — DELETED, needs building from nothing. `walls3.py` is on disk,
   unfinished. Two successive attempts left broken geometry in the scene.
3. **Stair dressing** — the runner must be a narrow centre band over exposed plank
   treads with a white raking skirt, not wall-to-wall carpet; rail needs shaped
   brackets; the shaft wants a raked soffit; the bottom landing wants daylight.
4. **Doors** — cove sticking with rounded corners and far less bevel contrast.
   `doors2.py` has the better panel research but renders swirl artefacts; treat it
   as a draft to finish, not working code.
5. **Baseboards** — moulded cove cap, standing proud, butting into the casing.
6. **Runner and decor** — the runner reads as a lumpy blob, the plants as extruded
   cactus proxies, the sculpture is oversized.

## Two process lessons, both paid for

- **Never leave a probe piece placed.** Killed agents left the knee wall in R/G/B
  mask colours, the baseboards magenta and the ceiling as a calibration fan.
  `kwprobe.py` and `ccal.py` both overwrite real pieces. Re-place the real piece in
  the same script run.
- **A critic told to judge one subject will not see a hole in the room.** Two pure
  black voids sat in the hallway across nine verdicts and nobody mentioned them.
  Always run at least one critic whose subject is the whole frame.

Tooling added this round, all re-runnable: `scratchpad/hall2/v3.py` (the six
photo-matched poses — do not edit them, parallel agents compare through them),
`blind.py` (builds a labels-stripped, order-shuffled A/B pair), `progress_v3.py`
+ `state_v3.json` (the progress page).
