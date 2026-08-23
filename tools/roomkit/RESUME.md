# Where the dollhouse build stands — resume here

## 2026-08-23 — the v3 run. FOUR SPACES BUILT, NO CRITIC HAS SEEN THEM.

**Resume here.** The owner dropped new reference photography in `docs/v3/` for
five spaces and asked for a last gauntlet run over those, and only those:
**Movie Room (1), Arcade Room (2), Garage (7), Frontyard (11), Backyard (3)**.
All five are built. **All four critics died on a session limit before
reporting**, so nothing below has been judged. Running them is the next job —
see "Next actions".

The 27 photos are converted and registered in `photos.json`, with per-room notes
recording which are 450x600 (layout only — their sd is scale-inflated), which
two back-yard PNGs are duplicate downscales, and that both exteriors were shot
at dusk. `scripts/heic_to_jpg.py` takes `--src`/`--name` now.

**The owner's standing instruction for the exterior: build NO lights.** The
eave, porch and garden string lights are lit in the photographs and are
deliberately a future job. Daytime geometry only, no emissive fixtures, front
or back.

### Three structural findings, each of which invalidated something we believed

1. **Walls are extruded OUTWARD from their own footprint line** (`house.js`,
   `WALL_THICKNESS 0.35`, `geo.translate(0, 0, -t)`), so on a shared wall **each
   room's wall mass lands inside its neighbour**. Two builders found this
   independently this run. Consequences already paid for:
   - The Movie Room's north wall "clipping at 238" was the **Arcade's wall
     face**, not tone-curve saturation. Open item 3 below used to say an albedo
     skin could not fix it; a skin authored at local z 0.39 fixed it outright,
     238 -> 161.9, with a 26-point chair-rail step that had never rendered.
   - The Garage's round-1 per-wall fit was **void**: its probe had been reading
     the Pantry's and Laundry's paint, which push 0.35 ft through into it.

   **So: author anything on a shared wall at depth >= 0.36, and re-probe a wall
   before trusting any value you did not measure yourself this round.**
2. **The Arcade Room was 180 degrees out on X.** The cabinet run is on the
   **east** wall. That is the **seventh** room in this project to ship a
   structural orientation error. The verification step in `ROOM-BRIEF.md` is not
   optional.
3. **`kit.contact_shadow` does not work in this scene.** Its stacked coincident
   translucent layers meter **0.5-9% darkening** where the brief calls for 34% —
   coincident transparent triangles inside one primitive do not accumulate here.
   This is very likely why several rooms have shipped shadows that meter as no
   shadow at all. Both basement builders replaced it with **one coplanar layer
   of non-overlapping annuli**, each with its own alpha, running the ramp from
   ~0.55x the piece's half-extents out past the footprint, and hit 30-33%.
   **`shellpass/kit.py` still has the broken version — fix it for everyone.**

### Toolchain changes this run

- `glb.py` now supports **tiled textures**: `Material(tex=...)`, `Part(uv=...)`,
  `uv_quad`, `uv_floor`, `png_gray`, `png_rgb`, and `_weld(parts,
  with_uv=True)`. Purely additive — the legacy call path is unchanged and was
  re-verified while three agents were still using it. This closes the
  "`Material` has no texture-map support" blocker three rooms have now hit.
  Caveat found in the same run: **`puff`/`slab`/`cylinder` emit no UVs**, so a
  `tex=` on them samples texel (0,0) and renders as flat paint. The Movie Room
  worked around it with a planar UV projection in a post-pass.
- `shot.py` takes **`--sun-azimuth`** and `--sun-elevation`. `--day` hardcoded
  azimuth 155, which is the **front** of this house, so every back-yard
  comparison shot rendered the rear elevation a flat unlit grey. The default is
  unchanged at 155; **use `--sun-azimuth 335` for anything facing the rear**,
  and say which you used — a critic comparing a differently-lit shot is not
  looking at what you built.
- **`--no-cutaway` is mandatory for any eye-level photo-matched interior pose.**
  Without it the ceiling is culled and the shot shows the night sky. Not
  currently mentioned in `ROOM-BRIEF.md` section 3.
- **`kit._blit` drops `Part.uv` and `Part.colors`**, turning textured panels
  into flat paint. And **its wall frame runs backwards on the south and west
  walls** (s: `world x = W - a`; w: `world z = D - a`) while `wall_band`'s does
  not — feeding room coordinates straight into `cased_opening` draws the casing
  several feet from the hole. `scratchpad/bsmt/ar2.py` has `SA()`/`WA()`
  converters. The same trap is live in every other room script.
- **`check_pick` is not a meaningful test for an outdoor room.** It samples the
  room slab at world y 8 and every yard piece sits below that, so it always
  passes and proves nothing.

### App changes (frontend) — do not undo these

- **The Frontyard and Backyard no longer isolate when tapped.** They are the
  outside of the house, and focusing one used to drop the level selector onto
  the first floor, leave House mode, and blank the shell, the lawn, the trees
  and every other room. `focus.js` has an outdoor branch that hides nothing,
  stays on level `'all'`, and flies to an exterior three-quarter view; the
  stand-off snaps to the cardinal axis the yard sits on, so the front frames the
  facade rather than a corner.
- `house.js` owns **`isOutdoorRoom()`** (three modules need it) and
  **`getBuildingBox()`**, which isolates the building mass from the shell GLB —
  the shell's own bbox is the whole **lot**, 113 x 152 ft, and centres nowhere
  near the house.
- **Objects in an outdoor room survive the House-mode sweep** (`objects.js`),
  and the **focused yard's device markers** survive it too (`devices.js`).
  Without the first, a deck is invisible on the only view the exterior is ever
  seen from. `cutaway.js` skips outdoor rooms — a yard has nothing to cut away.
- `house.js` **`maskShellProps()`** cuts the shell's baked **open cantilever
  parasol** by world box — 5,631 triangles merged into `Root_Node`, the
  79k-triangle catch-all, so the object could not be hidden without taking the
  siding with it. They separate cleanly by height: below y 5.5 in that footprint
  is terrace slab and boundary fence, above it there is nothing but parasol. It
  must run **after** `applyShellTransform`: `SHELL_CUTS` is in world feet and the
  shell's `matrixWorld` is the identity until it is placed. Deleting the faces
  then left the **SketchUp edge overlay** drawing the ribs as bare white lines in
  mid-air, so the whole `LineSegments` overlay is hidden too. Add a box to
  `SHELL_CUTS` for any other baked prop that has to go.

### Open items from this run

- **An unpaired opening.** The 3.2 ft opening at the SE corner of the Arcade's
  south wall, to the stair landing, is real in the plan and **is not cut**.
  Cutting one side only leaves the neighbour's wall standing in the hole. Spec:
  Arcade `edge_index 2, offset 0.0, width 3.2`; Movie Room `edge_index 0,
  offset 17.3, width 3.2`.
- **The deck cannot sit at the photographed height.** The photos show 4-5 risers
  down to the lawn; the shell puts its rear grade flush with its own ground
  floor and the rear ground-floor sill measures y 5.5, so a deck at photo height
  would run its rail across those windows. Built at 3.95/3.30. Matching the
  photo means dropping the shell's rear grade.
- **River rock is ~3x too smooth** (mean|d1| 5.5 against the photo's 15.8). The
  right next fix is a cobble normal map on the beds material, not more geometry.
- **The shell has a SketchUp scale figure** baked into `Root_Node` at about
  x -16.5, z 44.7, standing on the front lawn. A `SHELL_CUTS` box would remove
  it now; currently a tree is planted over it.
- All 69 device markers in the two yards are flagged **hidden by the user**, so
  tapping a yard shows no devices even though the code path now allows it. That
  is the owner's own setting, not a bug.
- House payload is **22.5 MB / 285 models**, up from 18.9. Only ~0.36 MB of that
  is the yards.

### The emissive-ceiling finding — house-wide, and NOT this run's doing

The Arcade's round-3 critic found a **482 sq ft emissive ceiling plane** in room 2
(`model_171`, material `ceil`, `emissiveFactor 0.434`) and called it the thing
ROOM-BRIEF forbids by name. It measured the night frame: **ceiling 198.1 while
the south upper wall reads 13.7** — the walls fall 12x and every object goes
black, the ceiling drops 5%.

The finding is real. **Charging it to this run's builder is not.** I audited the
whole house rather than take it on trust — `python -m roomkit.emissive_audit`,
which is now a permanent tool. It measures the **area of the geometry actually
carrying each emissive material** (in sq ft, after the glTF metre->foot
conversion), because a recessed can lens and a 480 sq ft ceiling plane are both
"emissive material on an object called Ceiling" and only one of them is
forbidden. Results:

- **136 room-scale emissive surfaces across 21 rooms.** 39 of them are ceilings.
- The biggest: Arcade 482.3 sq ft @ 0.434, Movie 479.4 @ 0.089, Garage 442.7 @
  0.202, Living Room 335.4 @ **0.552**, Kitchen 225.9 @ 0.445, Rios 146.3 @
  0.503. A dozen more ceilings sit at exactly 0.434.
- `git log --diff-filter=A` on the GLBs: the Arcade's ceiling was added
  **2026-08-16** and the Living Room's **2026-08-15**. This run's first commit is
  **2026-08-22**. They predate it by six and seven days.

So **lighting a ceiling with emissive is long-standing house-wide practice in
this project**, inherited by every room that has one. What was genuinely wrong in
room 2 was the *declaration*: `rooms/2.json _gaps` stated "there is deliberately
NO room-filling emissive box and no emissive on any room-scale trim run" and
enumerated the emissive inventory, and the ceiling was not on that list. That
sentence was false about the room as it stood, whoever authored the plane.

**Do not quietly strip 39 ceilings.** That is a whole-house decision with a
whole-house look attached to it, and it is outside the five rooms the owner
scoped this run to. What it needs is an owner call, and then one pass. The
question to put to them: **the rooms currently read as lit at night when their
lights are off**, because the ceiling keeps emitting while everything else goes
dark. Two honest options — drop the ceiling emissive and accept darker night
rooms, or drive it from HA light state the way `roomlights.js` already drives the
slab glow, which is the fix that actually matches the app's premise.

Note the distinction the audit exists to enforce, because it is the whole point:
**a can lens, an LED strip, a marquee, a monitor — fixtures the photograph shows,
at the size it shows them — are legitimate and must stay.** The Arcade is lit by
RGB strips in real life and its emissive inventory is almost entirely correct.
It is the 482 sq ft *plane* that is not a fixture.

### Next actions for this run, in order

1. **Run the four blind critics** — Garage, Movie Room, Arcade, and the exterior
   (front and back judged separately). Each must be a **fresh-context** agent
   that opens the actual images, compares against `docs/photos-jpg/` and
   `docs/ref-sims4/`, answers "which of these is the photograph" and "which
   reads as finished", and names **one** biggest gap. Renders are in
   `scratchpad/shots/v3_garage/`, `v3_movie/`, `v3_arcade/`, `v3_ext/`.
2. Feed each verdict back to a builder and loop until the critic picks ours.
3. **Do not touch any room outside those five** — the owner scoped this run to
   them explicitly.

---

Last session ended **2026-08-16** at a clean stopping point: the Living Room and
Kitchen rounds below were carried further, everything was verified in the
running app and committed. Health check at close: **423 device markers, 241
furniture objects across 21 rooms**, house payload **18.9 MB**, `house.db`
integrity ok, no dangling model references, no orphan or missing model files,
the shell and both rebuilt rooms render with no broken geometry, and no console
errors. Nothing needs repairing — the rounds below are simply unfinished.

(The level selector shows a fourth floor named **"error"** at level 10 holding
one room, "House", with 25 device markers. That is not our bug: Home Assistant
itself has a floor literally named `error` with an area `house`, and the app is
mirroring it. Rename or re-home it in HA and run "Sync with HA" if it bothers
you.)

## Read these first
- `ROOM-BRIEF.md` — the toolchain and every lesson twelve critic reports have
  produced. The sections that cost other agents a rebuild round: orientation
  verification, **sd is scale-blind**, **never delete content to improve a
  number**, honest metering, per-wall albedo, payload, opening registration.
- `STYLE-BAR.md` — the dollhouse bar and choosing the camera quadrant
- `rooms/<id>.json` — per-room piece maps, each recording its own evidence

## Unfinished rounds — resume these first

| room | where it stands |
|---|---|
| 5 Living Room | **round 5, three sub-passes done, not yet shot for a critic.** 31 objects, **1.64 MB** (was 1.98). (a) `b5_soft.py`: upholstery cells coarsened ~30% now the fine gradient comes from the tile not the mesh — metrics re-measured after the change, not assumed. (b) `b5_shadows.py` (new): contact shadows now read **live object positions out of the app** instead of hand-copied constants, so they cannot drift again — this is the round-4 critic's "no contact shadow under the east sofas or armchair"; pieces standing on the rug draw at y 0.115, on bare plank at 0.050. (c) `b5_view.py` (new): the three outdoor boards re-cut to sit 0.30 ft behind their openings (they were 1.7 ft outside the shell and visible from the dollhouse quadrant) and roughly halved to ~105 KB total. **Next: the per-wall albedo skins — still the unpulled lever, wall spread 114.4 — then shoot `doll_se` + the photo views and send to a critic.** |
| 6 Kitchen | **round 4, two fixes done, not yet shot for a critic.** 15 objects, **1.66 MB** — the round-3 payload failure (5.88 MB, 27% of the house) is **fixed**. (a) `p_extras.py` rug weave calibrated rather than guessed: render = 0.89·albedo + 55.3 measured, so the weave is re-based to 72.8 mean / sd 45 to land on photo F's 120.1 / 38.1. (b) `p_floor.py` island contact shadow moved onto the **counter** footprint, not the box. **Next: the counter stone — still the round-3 fail, hf/tot 0.25 against the photo's 0.40-0.48, to be rebuilt as a tiled texture or vertex colours, NOT raster cells — then the fridge side face and counter clutter.** |
| 16 Master Bath + 26, 23 | Bathrooms round 1. Was at "contact shadows render but are far too faint and z-fight — rebuild as an opaque radial colour ramp". 16 has 10 objects; 26 has 4; 23 has 4. **Check the shadow rebuild landed sanely before adding to it.** |
| 12, 17, 27 hallways/closet | Was at "room 12 is in good shape, now room 17". 12 has 10 objects and 7 openings; 17 has 9 objects; 27 has 4. **Room 17's footprint and all five of its doors were re-traced 2026-08-22** (see below) — the furniture in it predates the new shape, so check nothing is now standing in the east arm or in the stairwell wall. |

## 2026-08-22 — second-floor hallway + doors re-traced

`fix_2f_hallway.py` (idempotent, re-runnable) rebuilt room 17's footprint and
placed the five doors the owner marked in
`docs/floor plan/Gemini_Generated_Image_i28ml3i28ml3i28m.jpg`. What changed:

- **Room 17 Hallway** is now a 10-vertex L. The old polygon was missing the
  whole east arm (plan px 684..790, the stretch fronting the Rios closet and the
  guest room), so two of the five doors had no wall to sit on.
- **Room 28 Stairwell** is new — the north half of the strip the partition at
  px 580 walls off. It exists because that strip as a bare notch had no west
  wall, leaving an exterior gap above the master closet. It is only the north
  half because a room slab covers its whole footprint (`house.js:431`) and a
  full-strip slab floors the staircase over; the plan's tread hatching
  (py 915..990) is left as an open cut so the stairs still read on the 2F.
- **Five doors**, `type: door`, each cut on **both** sides (rooms 13, 14, 15,
  24, 25, 26). Rooms 25 and 24 were sealed boxes before this.
- Deleted: opening 111 (cut the hallway stem's east wall, which the plan shows
  solid — it was traced from a region a UI card covers in the screenshot) and
  opening 79 (targeted `edge_index 7` on a 7-vertex polygon, so it never
  rendered).
- Stairs 7 trimmed to `z 13.5, depth 9.8`; it ran 1.06 ft into the 2F bathroom.
- **Room 17's anchor moved 3.80 ft west** when the arm was added. Objects and
  placements are stored relative to the footprint anchor (`objects.js:128`), so
  the script compensates all 18 pieces by the anchor delta. If you re-shape this
  room again, do the same or the whole room slides.
- **`Hall2F Doors` deleted.** The circulation round hand-built it to stand
  leaves in the four openings room 17 had then; against the corrected footprint
  two of them coincide with the engine's own door panels, one stands free in the
  middle of the new east arm, and one is buried in the solid stem wall. Its
  casings went with it — re-cut them against the new edges next roomkit round.
  This closes three of the four `_gaps` recorded in `rooms/17.json`: room 14 and
  room 26 now register with this room's openings, and the "unmodelled space
  between room 25 and …" is the east arm, now built. `rooms/17.json`'s
  `_room.rect_world` (10.5–18.6 × 6.6–23.3) is stale — the room is now the
  10-vertex L at 6.70–18.62 × 6.55–23.44.

`plan_retrace.py`'s `ROOMS[17]`, `ROOMS[14]` and the new `ROOMS[28]` were
updated to match, so its `raster_check()` reproduces the live layout
(L2: 1229 sq ft, no overlaps).

**Still open here:** which end of the stairwell strip is the top landing. The
plan hatches only 2.7 ft of treads, and stairs 7 is `direction: 'n'` (from the
*main*-floor plan), which puts its head under the new landing slab. It renders
fine, but if the owner says you come up facing south, the Stairwell room should
move to the south end of the strip instead.

## The two open critic verdicts

**Living Room round 4 — FAIL.** Biggest gap: everything is plastic. Every fabric
and masonry surface matches the photo's sd and is 3-7× too smooth at the scale a
human sees (upholstery mean|Δ| 1.62 vs 11.84; `|d1|/sd` 0.070 vs 0.324-0.394).
Root cause found in source: `kit4.py`'s `plate()`, `mottle()` and `puff()` all
split every cell on a fixed diagonal, and `rings=7/seg=14` gives ~0.2 ft facets
against the 1-2 inch cells needed. Fix by alternating split direction per cell
and driving displacement from a fine-cell noise field.
Three regressions to undo: the east canvas was re-toned to a **blank slab (sd
0.0** against the photo's 43.2) — restore round 3's marks on round 4's ground and
do NOT move `CANVAS_E` toward `#b8b5af`; stone relief was deleted chasing sd —
restore a shallower bevel; and `doll_nw` drops the room's whole identity — return
to `doll_se` and fix the occlusion as a framing problem (the mid-air-object half
of this is fixed: mounted pieces fade with their wall now).
Wall spread 114.4 is the unpulled lever (office 85→23, garage 91→12, laundry
90→18). Verified from the photos: both east sofas are the same cream as the
sectional; the TV is a hard matte-black rectangle; the wreath is soft matte
lavender; **photo f shows the chaise ottoman clean, so removing its throw is
deleting a fabrication, not documented content.**

**Kitchen round 3 — FAIL.** Biggest gap: the counter stone is still marks, not a
field — high-pass energy hf/tot 0.25 against the photo's 0.40-0.48. Rebuild at
3-5× line density and ⅓ the width and contrast, **as a tiled texture or vertex
colours, not raster cells.** ~~Payload is a hard failure: **5.88 MB in one
room**~~ — **fixed in round 4: 1.66 MB, the largest piece now 253 KB, nothing
over the cap.** The stone is what is left. Regressions: rug
hue went warm (R−B −1.9 → +6.9) and its sd chased photo A's scale-inflated 51.5
instead of photo F's honest 39.0. **Meter only from `Kitchen F.jpg`** — A and C
are 450×600 and their sd is inflated.
Both of round 3's disagreements were adjudicated **in the builder's favour**: the
photo genuinely has the backsplash ~29 points below the counter, and the black
fridge face genuinely was albedo, not a winding bug.

## Tooling corrections — still in force

`roomkit.meter` **only works on an EMPTY room.** Its centre patch lands on
cabinetry and islands in a furnished one — that is how "wall spread 54" reached
two Kitchen reports when the true bare-wall spread is ~16. It now prints each
patch's sd and warns when a patch cannot be wall. Meter furnished rooms by hand
with verified clean boxes; `scratchpad/lr5/m5.py` reports sd, mean|Δ| and
`|d1|/sd` together at native resolution with a visual overlay of every box.

`roomkit.rooms` offers `doll_se/sw/ne/nw`. The two walls nearest the camera fade
out (`frontend/js/cutaway.js`), which is what makes the cutaway — so shoot the
diagonal opposite the content, and say which quadrant you used. Mounted pieces
now fade with their wall, so a dropped wall no longer leaves its art floating;
`shot.py` calls `window.__cutaway.settle()` so a screenshot cannot catch a wall
mid-fade.

`roomkit.dollhouse` renders the whole house with every floor visible and the
shell hidden — a view the app itself does not have.

`glb.py cylinder()` had all three surfaces wound inward; fixed and verified.
Existing GLBs are baked with the old winding, so rebuild a piece to pick it up.

## Known open items

1. **Payload**: 18.9 MB house over 241 pieces (measured 2026-08-16). Budget
   ≤1.5 MB/room, ≤300 KB/piece. Tone fields are the usual culprit — prefer
   tiled textures. Rooms still over budget: **Dining 2.27, Master Bed 1.82,
   Kitchen 1.66, Living Room 1.64, Rios 1.58 MB**. Pieces still over the 300 KB
   cap: **Dining Floor 1239 KB** (by far the worst in the house), Rios Floor
   421, Rios Birdcage 371, Bed 350, Wall Art 325. Kitchen and Living Room came
   down from 5.88 and 1.98 without the critic's content changing — the same
   trick (gradient from the tile, coarser mesh cells) is what Dining needs.
   Housekeeping: 15 model rows (1.4 MB of files) are uploaded but unused by any
   object; harmless, left in place so undo history stays intact.
2. The plans put part of the 2F over the garage footprint, disagreeing with the
   exterior photo reading as a single-storey garage wing. The re-trace trusted
   the plans. Worth an owner check.
3. The Movie Room's real footprint is L-shaped around the stairwell; ours is a
   rectangle. Its north wall clips at 238 — tone-curve saturation, not colour, so
   an albedo skin cannot fix it.
4. The Office cut a passage into the printer nook but room 22's wall is still
   solid — **openings on shared walls must be cut on both sides**.
5. `poses.json` is master-bedroom-specific and predates the re-trace; prefer
   `roomkit.rooms <id> --poses-only`.

## Next actions, in order

1. Finish the unfinished rounds above. The two nearest a verdict: **Living Room
   round 5** needs per-wall albedo skins then a shoot, and **Kitchen round 4**
   needs the counter stone rebuilt as a tiled texture then a shoot. Both are
   otherwise done and in the app.
2. Critics on the rooms never judged: Dining r2, Rios r2, Master Bed r5, Office,
   Guest Room, Movie, Arcade, Garage.
3. Furnish what is still shell-only: 22, 24, 25, and finish 23/26/27.
4. Whole-floor dollhouse pass against `docs/ref-sims4/`.
