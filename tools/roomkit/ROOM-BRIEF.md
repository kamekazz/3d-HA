# Room build — shared brief (any room)

Goal: make one room of the live house render like its real photo, and read as a
Sims-4-style dollhouse room from above. `BRIEF.md` is the master-bedroom version
of this document — read it too for worked examples of how far the detail goes.

Everything below is built and proven. Do not rebuild it.

## Run everything from `tools/`

```
cd "C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY="../backend/.venv/Scripts/python.exe"
```

The app is already running at http://127.0.0.1:5000. **Do not restart it** — the
DB is live and other agents are working in it. If it is genuinely down, say so in
your result instead of starting a second copy.

## 0. Get your room's brief

```
$PY -m roomkit.rooms 6            # facts + every camera pose, as JSON
$PY -m roomkit.rooms --list       # all rooms, one line each
```

That prints the room's local/world extents, slab Y, wall height, polygon (if
any), existing objects, and a set of ready-made poses: `corner_se/sw/ne/nw`,
`look_n/s/e/w`, `plan`, `doll`. Feed any of them straight to `shot --pose-json`.

Your reference photos are in `tools/roomkit/photos.json`, under
`docs/photos-jpg/`. **Look at the actual images, never a description of them.**
The first photo listed is the primary — the one the critic judges from.

## 1. Author a piece — `roomkit.glb`

Author in **feet**; the exporter converts to metres on save (glTF is metres and
the app scales loaded models by 3.28084). Every primitive is centred on X/Z with
its base at y=0, so a piece built "sitting on the floor at the origin" is exactly
what the app wants.

```python
import sys; sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import Model, Material, box, rounded_box, cylinder, prism, quad, sag_plane, torus

OAK = Material("oak", "#6f6a66", roughness=0.75)
m = Model()
m.add(box(6.5, 0.6, 7.0), OAK, at=(0, 0.5, 0))      # at = (x, y, z) in feet
m.add(box(6.6, 3.4, 0.4), OAK, at=(0, 0, -3.5), rot_y=0)   # rot_* are RADIANS
m.save(r"...\piece.glb")
print(m.bounds())   # (lo, hi) in feet — check the piece is the size you meant
```

Available: `box(w,h,d,anchor)`, `rounded_box(w,h,d,r,seg,anchor)`,
`cylinder(radius,h,seg,anchor,r_top)`, `prism(points,h)` (extrude a CCW `[(x,z)]`
polygon), `quad(p0,p1,p2,p3)`, `sag_plane(w,d,sag,nx,nz,y,edge_drop)` (bedding,
rugs, throws), `torus(radius,tube)`. `Material(name, color, roughness, metallic,
emissive, emissive_strength, opacity, double_sided)` — `color` is an sRGB hex
picked straight off the photo.

Reuse one `Material` instance across parts: parts are grouped by material into
one primitive each, so fewer materials means a smaller file.

## 2. Place it — `roomkit.place`

```python
from roomkit.place import place
place("Kitchen Island", r"...\island.glb", 6, pos=(9.0, 0, 3.6), rot_y_deg=0, scale=1.0)
```

Idempotent **by name**: re-running with the same name replaces that model's file
and moves its existing object instead of stacking duplicates. Names are global
across the house — **prefix yours with the room** (`"Kitchen Island"`, not
`"Island"`) or you will overwrite another agent's piece.

`pos` is **room-relative feet** from the room footprint's min corner, `y` up from
the floor slab. `rot_y_deg` is degrees CCW seen from above. The app seats a model
by its bounding box: X/Z centred on `pos`, **min-Y sitting at `pos.y`**. So a
wall-hung piece (art, cabinets, blinds) needs an explicit `y`.

Author every piece facing **+z (south)**; `rot` then aims it: 0 = back to the
NORTH wall, 90 = back to the WEST wall, 180 = back to the SOUTH wall, 270 = back
to the EAST wall.

## 3. Look at it — `roomkit.shot`

```
$PY -m roomkit.shot --pose-json "$($PY -m roomkit.rooms 6 --poses-only | jq -c .corner_se)" --level 1 --day --out ../scratchpad/shots/k1.png
$PY -m roomkit.sbs ../scratchpad/shots/k1.png ../scratchpad/shots/k1_sbs.jpg --room 6
```

`--level` **must** match your room's floor level (`facts.floor.level` — 0
basement, 1 first, 2 second). `--day` forces bright sunny daylight; most of the
photos are daytime shots. Device markers are hidden by default; `--markers`
shows them.

**Never edit `poses.json`** — it is the master bedroom's and parallel agents race
on it. Use `--pose-json` with what `roomkit.rooms` gives you.

## Verify the room's ORIENTATION against the floor plan before you build anything

**Six rooms in a row have had a structural error that the photographs alone
could not catch**, and every one cost a full rebuild round:

| room | error |
|---|---|
| Rios Room | the whole room was 180° out; windows on the wrong wall |
| Guest Room | 180° out on Z; headboard, closet and dresser all on wrong walls |
| Living Room | fireplace read as being on the north wall; it is on the chamfer |
| Master Bed | dresser read as on the headboard wall; it is on the west wall |
| Office | one window built where the plan shows two; a door invented on a party wall |
| Arcade | door leaf drawn 2.4 ft from where the opening was actually cut |

Photographs establish *detail* — colour, material, clutter, proportion. The plan
establishes *which wall things are on*, and a wide phone lens flattens corners
badly enough to fool a careful reader. Pin the room with adjacencies before you
model anything: `roomkit.rooms --list` gives every room's world rect, and the
plans are in `docs/floor plan/`. State your derivation in your report.

Techniques that have worked: registering the plan image to world coordinates
from three rooms whose rects are known and then sampling it as ASCII; a camera
solve from identifiable points (one room got rms 1.16° and tested the rival
hypotheses, which scored 18.3°); and reading a mirror — **a mirror cannot
reflect the wall it hangs on**, which settled two rooms outright.

## What round 1 got wrong — read this before you build

Five rooms were built and judged. Two independent critics failed both rooms they
judged, and these are the mistakes they found. Do not repeat them.

1. **Nothing had a contact shadow, so everything floated.** The app renders no
   shadows for generated geometry. Every piece that meets the floor needs a soft
   dark decal baked under its footprint — see how the master bedroom's `Rug`
   bakes the bed's contact shadow into the floor (`layout.json` → Rug). Both
   critics named this; it was applied to exactly one piece in the whole house.
2. **Do not build a room-filling emissive box to fake wall brightness.** Four
   builders did this independently. It reads as hard-edged rectangular panels on
   the wall, not as light — the Rios critic called it "a mis-mapped plane". The
   underlying problem (walls facing away from the sun rendering dark) has now
   been **fixed at the app level** in `daylight.js`: the hemisphere ground
   colour and the daytime IBL intensity were raised, measured with
   `roomkit.meter`. An empty room's four walls went from 222/185/158/125 to a
   much tighter spread. **Re-meter before compensating for anything** — tone
   values metered before this change are now too bright.
3. **Cut real openings.** Earlier builders believed the app draws "a hardcoded
   teal slab" over an opening and so faked every window as a flush decal.
   That was half wrong: `house.js buildRoom` cuts a genuine hole in the wall
   shape (`shape.holes.push`), and only the placeholder panel was ugly. That
   panel is now proper glass / a painted door. Use real openings — a flush decal
   window is invisible from outside the room and breaks the dollhouse view.
4. **Do not leave dead floor.** If the footprint is bigger than the room in the
   photo, say so in your report — do not stand a fake wall across the room and
   leave the remainder bare. A critic called that "a room someone stopped
   furnishing". (Footprints are being re-traced to the floor plans to remove the
   need for this.)
5. **Keep wall values consistent within a room.** Two walls of one painted room
   rendering at different values was flagged in both rooms.
6. **Density.** The real rooms are lived in. Renders came back tidier and
   emptier than the photos in every case.

## What round 2 got wrong — the newer lessons

1. **A critic's finding is not automatically right. Verify it against the photo
   before you act on it.** Round 1's critic said the kitchen's upper cabinets
   should have round knobs; round 2 dutifully changed all ~30 doors, and round
   2's critic found photo F unambiguously shows **bar pulls on every upper door**
   and knobs only on base doors. A wrong finding got built because nobody
   re-checked the photo. If you disagree with a finding, say so in your report
   with the evidence — that is a valid outcome.
2. **Contact shadows must be a smooth gradient, not nested rings.** Round 2 baked
   them as five hard-edged concentric outlines, which read as bullseye decals
   painted on the floor — the critic called it worse than no shadow at close
   range. Use a radial-falloff texture on a single quad; `environment.js` has a
   working `makeShadowTexture()` to copy the idea from.
3. **Match the photo's spread, don't just beat the old number.** Round 1's floor
   measured sigma 9.5 against the photo's 16.2 and read plastic; round 2 "fixed"
   it to 23.7 and reads as a random light/dark patchwork. Overshooting is not
   closer. Meter the photo, then meter yours, then aim at the photo's value.
4. **Pure black surfaces mean inverted normals.** A one-sided face turned away
   from every light renders solid black and reads as a hole in the room. If you
   see a black slab in a render, check the winding of the piece you just placed.

## Wall-to-wall brightness spread: a known limit, not your bug

Every critic so far has flagged that the walls of one painted room render at
different values (Living Room measured north 212 / west 158 / east 119; a real
room's walls sit within ~30). Understand what this is before you try to fix it:

The scene has **one directional sun and no bounce light**. A wall facing away
from it gets only hemisphere + IBL. `daylight.js` was already raised once to
close the gap, and raising it further was measured and rejected — at IBL 1.9 an
empty room's spread improved only 80 → 71 bytes while the exterior roof and
siding visibly flattened. So a residual 50–80 byte spread is the renderer's
limit, not a defect in your room.

**Do not fight it with emissive.** Two rounds of builders did, and both were
rejected: room-filling emissive boxes read as hard-edged rectangles, and
emissive on room-scale *runs* (crown, baseboards) makes them glow as bright fins
against the darker walls — which is a large part of why a room reads as
partitions rather than a room. The "no emissive box" rule covers trim runs too.

**UPDATE — this is now largely solved. Use per-wall albedo skins (option 2).**
The Office (room 8) took its four walls from **N 234 / W 210 / E 171 / S 149,
spread 85.5**, down to a **spread of 22.9** that way — real rooms sit within ~30,
so that is the problem closed, not merely improved. Skin colours were solved from
two-point log-linear fits measured off real renders, not from a formula. The
residue is the one wall the sun never reaches (it capped ~20 below the others
even with a pure-white skin); that part really is the renderer.

What you CAN legitimately do, in increasing order of effort:

1. Pick a `wall_color` that lands the room's **average** near the photo rather
   than tuning to one wall, and let the spread sit. Know the cost: a builder
   doing exactly this got the four-wall average to 157.5 against the photo's
   160.3, but its north wall then sat at 218 — brighter than the photo's
   ceiling. With one colour and a 112-byte spread you cannot win everywhere.
2. **Give each wall its own albedo — all four of them.** Results so far, all
   with non-emissive skins fitted from two-point probes: **garage 91.5 → 12.3**,
   **laundry 89.6 → 18.2**, **office 85.5 → 22.9**, and the Guest Room, which
   skinned only its two dark walls, **91 → 59**. Skin them all, including the
   bright one — it usually needs bringing *down*, and that is most of the gain.
   Fit each from a probe, never by eye. One `wall_color` serves all of them, but
   nothing stops you skinning a wall with a full-height, edge-to-edge GLB plane
   in a different colour, so a wall the sun never reaches is simply painted
   lighter. This is NOT the rejected "wall wash": that failed because it was
   **emissive** (so it glowed at night and read as light rather than paint) and
   because it covered only part of the wall, showing hard rectangular edges.
   A plain non-emissive skin covering a whole wall face is just a painted
   surface, and it is the only way to bring all four walls near the photo.
   If you do it: no emissive, cover the wall corner to corner, and match the
   `roughness` of the room wall (0.95) or the seam will show — see the note
   above about pieces and walls not rendering alike.

## A GLB piece and a room wall do NOT render the same at the same albedo

Measured on the master bedroom: an object's material collects roughly **1.7×**
what a room wall of the same authored colour does. Solving a ceiling gable on the
wall's number left a visible seam across the room.

**Correction — that 1.7 is not a constant, it is orientation-dependent.** It was
measured on one wall and generalised here in error. The garage measured the
piece/wall response ratio on all four: **north 2.08, west 1.24, east 1.03, south
1.02.** A surface facing the sun sees a big difference; one facing away sees
almost none. So do not apply a single factor — probe the specific wall you need
to match, on the orientation you need it on.

`models.js` and `scene.js` set the same `envMapIntensity`, so this is not an app
bug — it is material authoring. Room walls are built at `roughness 0.95`;
`roomkit.glb`'s `Material` defaults to `0.85`, and a smoother surface picks up
more environment specular. Metalness matters even more (glTF's own default
`metallicFactor` is 1.0 — always set it explicitly).

**So: never assume equal albedo gives equal render.** When a piece has to match a
room surface — a ceiling meeting a wall, baseboards meeting a floor — render both
and meter them against each other, and match `roughness` as well as colour.

Related, from the same build: the analytic tone inverse in `build/room14/tone.py`
no longer predicts the render after the lighting change. Two-point log-linear
fits measured off real renders are what work now.

## Payload budget — this loads on a tablet, all at once

`buildHouse` loads **every** room's models on every rebuild. There is no
per-floor lazy loading. So a room's GLB payload is not a local cost, it is a
whole-app cost.

Current: **20 MB across 109 models.** The Kitchen alone reached 6.2 MB in round 3
(its floor 1.29 MB, its island 1.47 MB) chasing surface texture through
rasterised tone fields. Seventeen rooms at that weight would be ~100 MB and the
dashboard would stop being usable — which counts as breaking the app.

**Budget: aim for ≤1.5 MB per room and ≤300 KB per piece.** If a surface needs
tone variation, prefer a coarser cell size, a tiled texture, or vertex colours
over more geometry. Merge parts that share a material — `Model.add` already
groups by material, so fewer `Material` instances means fewer primitives.

**Tone fields are the usual culprit.** Rasterising a gradient into cells buys
surface variation at brutal cost — the Kitchen went 4.5 → 5.88 MB doing it, and
a critic then judged the result a *perceptual regression* on the hero surface, so
the megabytes bought nothing. Prefer a tiled texture or vertex colours; they also
give finer spatial detail, which is what the eye actually reads (see the
scale-blind section above).

Check yourself before reporting done:
```
ls -S backend/uploads/models/*.glb | head
du -ch backend/uploads/models/*.glb | tail -1
```

## sd is SCALE-BLIND. Measure fine-scale gradient too, or you will build plastic

This is the most important measurement lesson in the project, and it explains why
rooms kept passing their numbers and failing their critics.

**Standard deviation does not know what scale the variation is at.** A surface
with a few big soft patches and a surface with real fabric grain can meter the
same sd. Every fabric and masonry surface in the Living Room was tuned until its
sd matched the photograph, and the critic still called the whole room plastic —
correctly. Measured as **mean |Δ| between adjacent pixels**:

| surface | render | photo |
|---|---|---|
| upholstery | 1.62 | 11.84 |
| stone | 0.47 | 1.77 |
| rug | 2.76 | 8.56 |

Normalised as `|d1| / sd`, the render sat at **0.070** where the photo is
**0.324–0.394**. Same sd, 7× less texture at the scale a human actually sees.

**So report both**: the sd AND `mean|Δ|` (or the ratio `|d1|/sd`, target ≈0.3 for
fabric). Sample at NATIVE render resolution — measuring an upsampled crop
inflates sd and will flatter you (one report's rug sd of 20.5 was really 10.9).

## Never delete content to improve a number

The same round produced two regressions, both from optimising a metric:

- The east canvas was re-toned until its value ratio to the wall was "right",
  and ended up **sd 0.0 — a blank slab**. The previous round's canvas had sd 47.4
  against the photo's 43.2. The earlier critic's "reads as a panel" complaint was
  never about value; it was about the canvas being a featureless rectangle. The
  fix made the actual defect total.
- The stone's chamfer was deleted because restoring it pushed sd from 6 to 13-18.
  But the photo meters sd 9.6 *while carrying heavy relief*, because its relief
  is large-scale with soft gradients. The right move was a shallower bevel, not
  no bevel.

If hitting a number requires removing detail, the number is the wrong target.
Say so in your report and propose the metric you think is right — the brief
already tells you a critic's finding is not automatically correct, and that
applies to the metric a critic names as much as to the defect it names.

## How to meter honestly — this has now gone wrong twice

Numbers in build reports have been misleading, not because anyone faked them but
because of two sampling mistakes. Both were caught by a critic re-measuring.

1. **Sample a CLEAN field, not a region with objects in it.** A round-3 builder
   reported the fireplace stone at a stone/wall ratio of 0.98 and concluded it
   matched the photo. The critic re-measured clean lit stone only and got
   1.10–1.15 — the builder's photo sample had swallowed the wreath and the
   firebox shadow. Same error made a stone field look like sd 31 when clean
   stone in the render is sd 34 against the photo's 8.
2. **Report EVERY wall, not the favourable ones.** The same builder re-toned the
   walls and reported "average 169, against the photo's 155–171". The critic
   found that averaged only the two brightest walls: the east wall actually
   meters 95–98 and the south 92–135 against the photo's 156–161. The re-tone
   made the two dark walls *worse* while the headline number improved.

So: when you report a value, say which surface, how big the sample was, and give
the range across all four walls — not one number. And when you pick a single
`wall_color` for a room whose walls are lit very differently, choose it so the
**average across all of them** lands near the photo; optimising the bright walls
pushes the dark ones further away.

## An opening between two rooms must be cut in BOTH rooms' walls

Each room owns its own walls, so cutting a doorway in yours leaves the
neighbour's wall standing in the hole — you look through your opening at their
blank wall face, or at their jamb lining.

Two rooms have hit this. The Dining room got it right: it set its kitchen
doorway to the **exact world span room 6 had already cut on its own side**, so
the two holes register. The Office got it wrong: it cut a passage into the
printer nook but left room 22's north wall solid, so the hole shows the nook's
wall rather than the nook.

So: before cutting an opening on a shared wall, check whether the neighbour has
one there (`roomkit.rooms <neighbour id>` reports its opening count; the DB has
the spans). Match the world span exactly. If the neighbour is another agent's
room and you must not touch it, say so in your report so it gets paired up.

## Room-scale surfaces must be named so they stay unclickable

A floor plane over the slab, a ceiling, an emissive wall wash, a baseboard run —
these span the whole room, and `pick()` raycasts objects *before* rooms. Left
clickable they swallow every click in that room and the room editor can never be
opened again.

`objects.js` marks an object unpickable when its name contains **floor**,
**ceiling**, **wall wash**, **baseboard(s)** or **crown** (`SURFACE_RE`). So name
them `"Kitchen Floor"`, `"Kitchen Ceiling"`, `"Kitchen Baseboards"` — never
`"Kitchen Slab"` or `"Kitchen Underlay"`. Real furniture must NOT match that
pattern (a piece genuinely called "Floor Lamp" would wrongly go unpickable —
call it "Kitchen Lamp Tall").

Verify it after you place them:

```
$PY -m roomkit.check_pick <room id> --level <level>
```

It fails loudly if anything you placed would steal the room's clicks.

## Room geometry is ground truth

Footprints are traced from the real floor plans in `docs/floor plan/`. **Never
edit a room's footprint, polygon, or height.** Match the photo with what you put
inside it. If the geometry genuinely cannot hold what the photo shows, say so in
your result — do not silently resize the room.

Wall and floor *surfaces* are yours: set them with
`PATCH /api/house/room/<id>` (`wall_color`, `floor_color`, `wall_texture`,
`floor_texture`; texture keys in `frontend/js/textures.js`).

## Rules

- Match the photo. Proportions and placement first, then colour and material.
- Keep it low-poly and clean — this renders live on a tablet dashboard.
- Don't touch other agents' pieces, `poses.json`, other rooms' footprints, or the
  DB directly. Place through `roomkit.place` only.
- Do not break the Home Assistant app: no changes to `frontend/js/*` behaviour,
  device markers, controls, realtime, planner, or undo. You are adding content,
  not changing the app.
- Record what you built in `tools/roomkit/rooms/<id>.json` (your room's own
  layout map — one file per room, so no two agents write the same file).
