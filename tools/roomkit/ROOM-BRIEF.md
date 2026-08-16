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
