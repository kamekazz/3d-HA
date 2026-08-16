# Where the dollhouse build stands — resume here

Work stopped mid-flight when the API session limit hit. Four agents were killed
before they wrote anything (Kitchen critic, Master Bedroom re-place, Dining
round 2, Rios round 2), so **nothing is half-applied** — the DB and the repo are
consistent. Pick up from the list at the bottom.

## Read these first
- `ROOM-BRIEF.md` — the toolchain, plus "What round 1 got wrong" (the critic
  findings that apply to every room)
- `STYLE-BAR.md` — the Sims 4 dollhouse half of the bar
- `BRIEF.md` + `layout.json` — the master bedroom, the deepest-built room
- `rooms/<id>.json` — per-room piece maps

## State of each room

| id | room | state | notes |
|---|---|---|---|
| 6 | Kitchen | **round 2 built, NOT yet judged** | fake wall gone, real cut openings, contact shadows, wall spread 93→56. A critic was queued and never ran. |
| 5 | Living Room | **round 2 built, NOT yet judged** | fireplace moved to the NW chamfer (chimney chase in the plan). Two cased openings were converted to type `passage` after it finished. |
| 4 | Dining | round 1 built, geometry re-traced under it | **needs re-place.** Now 14.6 × 13.1 polygon with a real east bay — round 1's faked flat bay can become real. |
| 15 | Rios Room | round 1 FAILED by critic, geometry re-traced under it | **needs re-place + the critic's 12-item list.** Windows are the big one: built 6.15 ft tall, measured ~4.8. Delete `Rios Wall Wash`. |
| 14 | Master Bed | **round 4 re-placed into the rotated footprint, NOT yet judged** | Dresser moved to the WEST wall (the plan + Master Bed 2 prove it) and the long-standing headboard-wall collision is gone; vault re-derived (ridge N–S at x 10.50, peak 14.6, 32.2°/33.4°); 7 REAL openings cut (4 windows, 2 doors, 1 passage); contact shadows added; every tone re-metered — wall 239→225, floor 199→140 so rug/floor is 1.68 like the photo. Build/re-place with `build/room14/r4_place.py`. `poses.json`'s `ref` is still for the OLD room — use the pose in `layout.json._room._camera_warning`. |
| 8, 13, 16, 26, 23, 12, 17, 27, 9, 10, 1, 2 | everything else | **never built** | photos mapped in `photos.json` |

## What changed app-wide (and why re-metering matters)

`daylight.js` — interior walls facing away from the sun rendered far too dark
(an empty room metered 222/185/158/125 on one paint colour), so every builder
faked it with emissive panels that critics then flagged. Hemisphere ground and
daytime IBL were raised; measure with `roomkit.meter <room> --level <n>`.
**Every tone value metered before this is now too bright.**

`house.js` — opening panels were a saddle-brown slab and a flat teal one. Glass
and painted doors now, and **type `passage` renders as a true hole with no
panel** (types: `door`, `window`, `passage`). Builders no longer need to fake
windows as flush decals.

`objects.js` + `main.js` — room-scale surface objects (names matching
`floor|ceiling|wall wash|baseboards|crown`) are `pickable:false`. Without this a
room-wide floor plane swallows every click and the room editor can never be
opened. Guarded by `roomkit.check_pick <room> --level <n>` — run it after placing.

`environment.js` — front yard (beds, car, bin, planters, path lights) and the
foliage palette moved to explicit sRGB (`setHSL` defaults to the LINEAR working
space in three r160, which rendered the treeline pale mint).

The house-shell GLB (`backend/uploads/models/model_3.glb`) had its roof texture
renormalised and its front door darkened; backups are beside it.

## Geometry corrected after the re-trace

**Room 14's entry vestibule was ~7.9 ft too far west** and has been moved. Two
independent derivations (a critic and the round-5 builder, both using
`plan_retrace.py`'s own transform — the one that reproduces all four blue window
marks within 0.05 ft) put it at local **x 15.73–20.51, hard against the east
wall**, where the re-trace had it at x 7.86–15.58, centred. Applied via PATCH;
level 2 re-verified with zero overlapping cells, and the vestibule now meets the
2F hallway across its full width instead of over 3.2 ft.

The anchor and bounding box did not change, so furniture in the main area was
unaffected. Round 5's own notes flag that `r5_shadows.FEET`, the TV x position
and `r4_room.POLY` edge indices were derived against the OLD leg and need
re-checking.

**A library bug was fixed in `glb.py`:** `cylinder()` wound all three surfaces
inward — the side wall faced the axis and both end caps were inverted. It never
showed because `Material` defaults to double-sided, but it put a bright emissive
disc per recessed can shining up through a one-sided ceiling. Fixed and verified
(0 wrongly-facing triangles). Existing GLBs are baked with the old winding;
rebuild a piece to pick up the fix.

## Known open items

1. **The shell no longer matches the rooms.** Rooms shrank ~28% linearly in the
   re-trace; the shell was not rescaled. Invisible in practice — House mode shows
   only the shell, single-floor mode shows only the rooms, and they are never
   drawn together — but it will matter if anything ever shows both.
2. **`poses.json` was authored for the old, larger rooms** and frames loosely
   now. It is master-bedroom-specific; prefer `roomkit.rooms <id> --poses-only`.
3. **Room `height` is flat 8 ft** on the second floor, but the master bedroom
   photo shows a vault. The Ceiling piece expresses it, not the room height.
4. The re-trace put part of the 2F over the 1F garage footprint, which disagrees
   with the exterior photo reading as a single-storey garage wing. It trusted the
   plans (three wall matches, sub-0.5 ft residual). Worth an owner check.
5. Master Closet (27) was traced on the wrong side of the house and was moved to
   the plan position — worth confirming against how the real closet opens.

## Next actions, in order

1. Critic on Kitchen round 2 and Living Room round 2 (both built, unjudged).
2. Re-place Master Bedroom (rotated), Dining (new bay), Rios (+ its critic list).
3. Then the twelve unbuilt rooms — Office, Guest Room, Master Bath, both other
   bathrooms, both hallways, Master Closet, Laundry, Pantry, Movie, Arcade.
4. Whole-floor dollhouse pass against `docs/ref-sims4/` once rooms are furnished.
