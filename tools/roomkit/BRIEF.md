# Master bedroom build — shared brief

Goal: make room 14 ("Master Bed") render like the real photo,
`docs/Master bedroom.heic` (it is a JPEG despite the extension — copy it to
`.jpg` and open it; **look at the actual image, never a description of it**).

Everything below is already built and proven working. Do not rebuild it.

## Run everything from `tools/`

```
cd "C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY="../backend/.venv/Scripts/python.exe"
```

The app is already running at http://127.0.0.1:5000. Do not restart it — the DB
is live and other agents are working in it.

## 1. Author a piece — `roomkit.glb`

Author in **feet**; the exporter converts to metres on save (glTF is metres and
the app scales loaded models by 3.28084). Every primitive is centred on X/Z with
its base at y=0, so a piece built "sitting on the floor at the origin" is exactly
what the app wants.

```python
import sys; sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import Model, Material, box, rounded_box, cylinder, prism, quad, sag_plane, torus

OAK = Material("oak", "#6f6a66", roughness=0.75)
LINEN = Material("linen", "#efece6", roughness=0.95)

m = Model()
m.add(box(6.5, 0.6, 7.0), OAK, at=(0, 0.5, 0))          # at = (x, y, z) in feet
m.add(sag_plane(6.4, 6.0, edge_drop=0.5), LINEN, at=(0, 1.9, 0.4))
m.add(box(6.6, 3.4, 0.4), OAK, at=(0, 0, -3.5), rot_y=0)  # rot_* are RADIANS
m.save(r"...\bed.glb")
print(m.bounds())   # (lo, hi) in feet — check your piece is the size you meant
```

Available: `box(w,h,d,anchor)`, `rounded_box(w,h,d,r,seg,anchor)`,
`cylinder(radius,h,seg,anchor,r_top)`, `prism(points,h)` (extrude a CCW `[(x,z)]`
polygon), `quad(p0,p1,p2,p3)`, `sag_plane(w,d,sag,nx,nz,y,edge_drop)` (bedding,
rugs, throws), `torus(radius,tube)`. `Material(name, color, roughness, metallic,
emissive, emissive_strength, opacity, double_sided)` — `color` is an sRGB hex
string picked straight off the photo.

`Model.add(part, mat, at=(x,y,z), rot_y=, rot_x=, rot_z=, scale=)` bakes the
transform in. Reuse one `Material` instance across parts — parts are grouped by
material into one primitive each, so fewer materials means a smaller file.

## 2. Place it — `roomkit.place`

```python
from roomkit.place import place
place("Bed", r"...\bed.glb", 14, pos=(9.0, 0, 3.6), rot_y_deg=0, scale=1.0)
```

Idempotent **by name**: re-running with the same name replaces that model's file
and moves its existing object instead of stacking duplicates. Always reuse your
piece's name from `layout.json`.

`pos` is **room-relative feet** from the room footprint's min corner, `y` up from
the floor slab. `rot_y_deg` is degrees CCW seen from above. The app seats a model
by its bounding box: X/Z centred on `pos`, **min-Y sitting at `pos.y`**. So a
wall-hung piece (art, blinds) needs an explicit `y`.

## 3. Look at it — `roomkit.shot`

```
$PY -m roomkit.shot --pose ref --day --out ../scratchpad/shots/mine.png
$PY -m roomkit.shot --pose-json '{"pos":[16,23.5,-8],"target":[6,22,-18],"fov":60,"size":[900,1200]}' --day --out close.png
```

`--pose ref` is **the** comparison viewpoint — it reproduces the photo's vantage
(standing in the south-east doorway looking north-west) and is the only pose the
final judgement is made from. Use `--pose-json` for your own close-ups;
**never edit `poses.json`** — other agents are running in parallel and would race
on it.

`--day` forces bright sunny daylight (the photo is a bright daytime shot).
Device markers are hidden by default; pass `--markers` to see them.

## Room geometry — this is ground truth, do not change it

Room 14 is traced from the real floor plan. **Never edit the room footprint,
its polygon, or the floor/room heights.** Match the photo with what you place
inside it.

Room-local coordinates (what `place()` takes), origin at the footprint min corner:

```
local x: 0 .. 26.5 ft        world x = local x - 5.5
local z: 0 .. 23.5 ft        world z = local z - 20.5
floor slab: world y = 18.0   wall top: world y = 26.0 (room height 8 ft)

main bedroom area   local x 0..26.5,    z 0..16      (26.5 x 16 ft)
entry leg (doorway) local x 20.5..26.5, z 16..23.5

z = 0     NORTH wall  <- the bed's headboard wall (far wall in the photo)
z = 16    SOUTH wall  <- camera side
x = 0     WEST wall   <- left in the photo
x = 26.5  EAST wall   <- right in the photo (desk + big window)
```

The `ref` camera stands at local (24.0, z 15.0), eye 5.6 ft above the slab.

## What the photo shows

Grey wood-plank floor, white walls, **vaulted/cathedral ceiling** (the room
currently has no ceiling at all — you see sky). Grey panel-headboard king bed
with a white duvet and grey + white pillows and a storage drawer at the foot;
large coral/red abstract poppy canvas above it; grey nightstand with a lamp;
grey dresser with a mirror and a taller narrow chest on the left; white desk with
a black mesh office chair under the right-hand window; a big cream textured area
rug under the bed; white horizontal blinds on three windows; a white five-blade
ceiling fan with a light kit; white baseboards; a dark chest in the near-right
foreground.

## Rules

- Match the photo. Proportions and placement first, then colour and material.
- Keep it low-poly and clean — this renders live on a tablet dashboard.
- Don't touch other agents' pieces, `poses.json`, the room footprint, or the DB
  directly. Place through `roomkit.place` only.
- `layout.json` is the shared placement map. Read it. If your piece needs to
  move, say so in your result rather than editing another piece's entry.
