# Where the dollhouse build stands — resume here

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
| 12, 17, 27 hallways/closet | Was at "room 12 is in good shape, now room 17". 12 has 10 objects and 7 openings; 17 has 9 and 4; 27 has 4. |

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
