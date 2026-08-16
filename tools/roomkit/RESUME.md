# Where the dollhouse build stands — resume here

Four agents were killed **mid-work** by an API session limit. Unlike the earlier
interruption, partial work IS in the DB. It was verified afterwards: the app is
healthy, **423 device markers intact, 230 furniture objects across 21 rooms**,
every interrupted room still selectable, payload 20 MB, and the second floor
renders with no broken geometry. Nothing needs repairing — the rounds below are
simply unfinished.

## Read these first
- `ROOM-BRIEF.md` — the toolchain and every lesson twelve critic reports have
  produced. The sections that cost other agents a rebuild round: orientation
  verification, **sd is scale-blind**, **never delete content to improve a
  number**, honest metering, per-wall albedo, payload, opening registration.
- `STYLE-BAR.md` — the dollhouse bar and choosing the camera quadrant
- `rooms/<id>.json` — per-room piece maps, each recording its own evidence

## Interrupted mid-round — resume these first

| room | state at interruption |
|---|---|
| 5 Living Room | **round 5**, fresh agent. Had run `m5.py`, was at "per-wall albedo skins — first a two-point probe". 31 objects placed. Its predecessor's full analysis is in the round-5 brief below. |
| 6 Kitchen | **round 4**. Was at "the fridge side face and the counter clutter". 15 objects. |
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
restore a shallower bevel; and `doll_nw` culls the room's whole identity — return
to `doll_se` and fix the occlusion as a framing problem.
Wall spread 114.4 is the unpulled lever (office 85→23, garage 91→12, laundry
90→18). Verified from the photos: both east sofas are the same cream as the
sectional; the TV is a hard matte-black rectangle; the wreath is soft matte
lavender; **photo f shows the chaise ottoman clean, so removing its throw is
deleting a fabrication, not documented content.**

**Kitchen round 3 — FAIL.** Biggest gap: the counter stone is still marks, not a
field — high-pass energy hf/tot 0.25 against the photo's 0.40-0.48. Rebuild at
3-5× line density and ⅓ the width and contrast, **as a tiled texture or vertex
colours, not raster cells.** Payload is a hard failure: **5.88 MB in one room**,
27% of the house, five pieces over the 300 KB cap, grown from 4.5 MB during a
round whose result the critic judged a perceptual regression. Regressions: rug
hue went warm (R−B −1.9 → +6.9) and its sd chased photo A's scale-inflated 51.5
instead of photo F's honest 39.0. **Meter only from `Kitchen F.jpg`** — A and C
are 450×600 and their sd is inflated.
Both of round 3's disagreements were adjudicated **in the builder's favour**: the
photo genuinely has the backsplash ~29 points below the counter, and the black
fridge face genuinely was albedo, not a winding bug.

## Tooling corrected this session

`roomkit.meter` **only works on an EMPTY room.** Its centre patch lands on
cabinetry and islands in a furnished one — that is how "wall spread 54" reached
two Kitchen reports when the true bare-wall spread is ~16. It now prints each
patch's sd and warns when a patch cannot be wall. Meter furnished rooms by hand
with verified clean boxes; `scratchpad/lr5/m5.py` reports sd, mean|Δ| and
`|d1|/sd` together at native resolution with a visual overlay of every box.

`roomkit.rooms` offers `doll_se/sw/ne/nw`. The two walls nearest the camera cull,
which is what makes the cutaway — so shoot the diagonal opposite the content, and
say which quadrant you used.

`roomkit.dollhouse` renders the whole house with every floor visible and the
shell hidden — a view the app itself does not have.

`glb.py cylinder()` had all three surfaces wound inward; fixed and verified.
Existing GLBs are baked with the old winding, so rebuild a piece to pick it up.

## Known open items

1. **Payload**: 20 MB house, Kitchen 5.88 MB of it. Budget ≤1.5 MB/room,
   ≤300 KB/piece. Tone fields are the usual culprit — prefer tiled textures.
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

1. Finish the four interrupted rounds above.
2. Critics on the rooms never judged: Dining r2, Rios r2, Master Bed r5, Office,
   Guest Room, Movie, Arcade, Garage.
3. Furnish what is still shell-only: 22, 24, 25, and finish 23/26/27.
4. Whole-floor dollhouse pass against `docs/ref-sims4/`.
