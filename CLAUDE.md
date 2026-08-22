# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Reads a Home Assistant instance and renders the house as an interactive 3D model (Three.js), split by
floor, with each device shown live and controllable from the 3D view. Flask backend, vanilla JS
(ES modules, no bundler/build step) frontend. The HA long-lived access token never reaches the
browser — the browser only talks to Flask; Flask talks to Home Assistant.

## Running it

```
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env          # then edit .env:
#   HA_BASE_URL = https://<your-instance>.ui.nabu.casa
#   HA_TOKEN    = <a FRESH long-lived access token>
#   APP_SECRET  = <anything random>

python app.py
```

Open http://127.0.0.1:5000. There is no `.env.example` requirement to boot — the app starts without
`.env` too (you can build rooms, but there's no HA data or live states until it's configured).

There is no test suite, linter, or build step in this repo (no `package.json`, no Python test
files). Verify changes by running the app and exercising the flow in a browser (see the `run` and
`verify` skills).

`app.py` runs with the Werkzeug reloader **off** on purpose (`debug=False`) — the HA websocket
background thread must only start once per process; enabling the reloader would double-start it.

## Architecture

```
Browser (Three.js + vanilla JS, ES modules via importmap, no build step)
     │ HTTP + SocketIO (no HA token here)
     ▼
Flask backend
  ├── ha/client.py     REST → HA (states, call_service) — holds the token
  ├── ha/ws_client.py  WebSocket → HA (registries + state_changed, auto-reconnect)
  ├── ha/cache.py      in-memory floors/areas/devices/entities + states
  ├── house/           our 3D layout (SQLite: backend/house.db)
  └── realtime/        SocketIO relay of state changes to browsers
```

**Two separate data models that get merged client-side:**
- *HA's own registries* (floors/areas/devices/entities/states) — read-only, fetched over HA's
  WebSocket API by `ha/ws_client.py` (`HARealtime`, a background thread since Flask is sync) and
  held in `ha/cache.py` (`HACache`, thread-safe in-memory). `HACache.structure()` joins the four
  registries into a floors → areas → devices/entities tree.
- *Our own 3D layout* (floors, rooms/footprints, per-entity 3D placements) — this app's own
  data, persisted in SQLite via `house/store.py` (`HouseStore`). Linked to HA by `ha_floor_id`
  (floor), `ha_area_id` (room), and `entity_id` (placement), but geometry (x/y/z, width/depth/height,
  color) lives only here.

**Auto-generation is idempotent by design** (`HouseStore.generate_from_ha`): on first load with HA
configured, it seeds a room per HA area (grid-laid-out) and places that area's entities inside it,
but only for areas/entities not already linked/placed. It never touches existing rooms or
placements, so user edits in the room editor always survive a re-run or a "Refresh HA". Related:
`sync_floors_from_ha` (adds floor rows for new HA floors) and `prune_unlinked_empty_floors` (drops
the placeholder floor seeded before HA was configured, once a real HA-linked floor exists).

**Full reconcile on demand** (`HouseStore.sync_from_ha`, exposed as `POST /api/house/sync` and the
"Sync with HA" topbar button): pulls HA changes into the layout in one shot — adds new HA floors,
**re-levels HA-linked floors to their HA floor's level** (`reconcile_floor_levels_from_ha` — HA is
the source of truth for floor ordering; floors not HA-linked or whose HA floor has no level keep
their level, only shifted to dodge a collision; the `level` column is UNIQUE so all floors are
parked at temp negative levels before finals are written), **re-parents rooms to the floor their HA
area now lives on** (`reconcile_rooms_to_ha_floors`, keyed by `ha_area_id`), generates rooms/devices
for new areas, and drops HA-linked floors that no longer exist in HA *and* hold no rooms
(`prune_stale_ha_floors`). Still never deletes a room or moves its geometry — it only ever follows
an explicit HA area→floor assignment; rooms whose area is unassigned/deleted in HA, or that aren't
linked to an area, stay put. Note `sync_floors_from_ha` only sets a level when it *creates* a floor
row; re-leveling an existing floor happens solely through `reconcile_floor_levels_from_ha` on sync.
The frontend button issues a `refreshHA()` first, waits ~1.5s for the registry refresh to land, then
calls sync.

**Undo/redo** covers every layout edit app-wide (planner gestures, panel field changes, 3D drags,
deletes, generate/sync). Backend-owned, session-only: `@undoable` on each mutating route in
`house/routes.py` snapshots the five layout tables (`HISTORY_TABLES` in `house/store.py` — models
excluded, they're file-lifecycle) via `HouseStore.export_snapshot` before the call and records it in
`house/history.py` (`HouseHistory`, in-memory two-stack, cap 100) only if the call succeeded and
changed data (no-op PATCHes burn no step). `POST /api/house/undo|redo` restore a snapshot verbatim
with **original row ids** (`restore_snapshot`: delete-all child→parent, insert parent→child — so
undoing a room delete restores its cascade-deleted placements/objects, and `floors.level UNIQUE`
never trips), returning `{ok, can_undo, can_redo}`; `GET /api/house/history` returns counts.
Dangling `model_id` on restore: placements → NULL, objects → row dropped. `delete_floor_plan` only
nulls the DB column now (file kept on disk) so undoing a plan delete re-shows the image; file
*contents* aren't versioned. Frontend: `js/undo.js` owns the topbar + planner buttons and
Ctrl+Z / Ctrl+Y / Ctrl+Shift+Z (skipped while typing in inputs — native text undo wins); `api.js`
notifies it after every mutating `/api/house` call so buttons stay fresh. After undo/redo the
current context re-fetches: `reloadHouse` in the 3D view, or the planner's `rehydrate()` (swapped in
via `setUndoHandler` on open/close — keeps floor/selection/zoom, unlike `setActiveFloor`).

**Realtime path:** HA's `state_changed` events arrive on the `HARealtime` background thread, update
`HACache`, and are relayed to all connected browsers via `realtime/socketio.py` (SocketIO event
`state_changed`). The frontend (`js/socket.js`) falls back to 5s polling if the socket drops.
`js/state.js` owns the live entity-state map and re-styles 3D markers (color/emissive/scale) when a
state changes.

**Control path:** browser → `POST /api/control` (`api/control_routes.py`) → `HAClient.call_service`
→ HA. `domain` defaults to the entity_id's prefix and `service` defaults to `toggle` if not given.

**Key endpoints:** `GET /api/ha/structure` (HA tree), `GET /api/ha/states`, `GET /api/ha/status`,
`POST /api/ha/refresh` (re-fetch HA registries) — `GET/POST/PATCH/DELETE /api/house*` (floor/room/
device-placement CRUD, backed by `HouseStore`), `POST /api/house/generate` (add missing rooms),
`POST /api/house/sync` (full reconcile — see above) — `POST/GET/DELETE /api/house/floor/<id>/plan`
+ `GET /api/house/plan/<id>` (floor-plan tracing images, saved under `backend/uploads/` — tracked
in git for now so clones ship the demo data, to be re-ignored later;
png/jpg/webp only, never SVG — files are served back verbatim) — `POST /api/control` — SocketIO
event `state_changed`.

**Units are FEET everywhere** (world unit = 1 ft; grid cells are 1 ft). Databases from before the
feet switch stored meters and are converted ×3.28084 once on boot, gated by `PRAGMA user_version`
(0 = meters, 1 = feet) in `HouseStore._migrate_meters_to_feet`.

**Room footprints can be rectilinear polygons**, not just rectangles: `rooms.points` (TEXT, JSON
`[[dx,dz],…]`, nullable) holds vertices **relative to the room's `x/z` anchor**, which always stays
the polygon's bbox min corner (so device positions, `generate_from_ha`'s layout math, and whole-room
moves keep working). `normalize_points` in `house/store.py` validates (≥3 points, no
self-intersection, non-zero area), forces CCW winding, and folds the bbox shift into the anchor on
every write; invalid polygons → HTTP 400. `points: null` reverts a room to its bbox rectangle.
`points` is NULL for all generated rooms. In 3D, `house.js buildRoom` extrudes polygon rooms with
`THREE.Shape`/`ExtrudeGeometry` (map `(x,z) → (x,-z)` then `rotateX(-π/2)`); rect rooms keep the
centered-BoxGeometry path. `focus.js` frames rooms via world-space `Box3`, never
`geometry.parameters` (BoxGeometry-only API).

**3D model library** ("Models" topbar button): uploaded `.glb`/`.gltf` files live in a `models`
table + `backend/uploads/models/model_<id>.<ext>` (same deterministic-filename pattern as
floor plans; `MODEL_EXTENSIONS` whitelist). Note: `backend/house.db` and `backend/uploads/` are
currently **tracked in git** on purpose (teammates clone the demo house); re-ignore when that ends. A model can (a) **replace a device marker** —
`placements.model_id` (FK, `ON DELETE SET NULL` so deleting a model reverts the primitive), plus
`rot_y` (radians) and `scale` — or (b) be placed as **standalone furniture**: an `objects` row
(room-anchored like placements, `model_id ON DELETE CASCADE`). `frontend/js/models.js` owns the
GLTFLoader (+ DRACO decoder **vendored** at `frontend/vendor/draco/gltf/`, served off our own static
root — not the CDN, since the house-shell GLB is DRACO-compressed and a CDN-blocked deploy would then
render the whole scene *except* the house; re-copy it from the matching
`three@<ver>/examples/jsm/libs/draco/gltf/` if three is bumped) and a per-model cache; instances are `scene.clone(true)`
with **cloned materials** (originals stashed in `child.userData.__orig`) inside a pivot scaled
×3.28084 (glTF is meters, world is feet) — device models are bbox-centered, furniture bottom-seated.
`state.js applyStyle` restyles model groups by emissive glow/grey-lerp (never repaints authored
colors) and composes `scale = userScale × stateScale`. `objects.js` builds furniture into floor
groups (`userData.kind: 'object'`); `main.js pick()` raycasts markers+objects first (recursive,
walks up to the `userData.kind` owner) so they win over translucent walls. `drag.js` drags the
**selected** marker/object (selection = open device/object panel) on the horizontal plane through
its own height, one PATCH on release, no rebuild. Endpoints: `POST /api/house/model` (multipart),
`GET /api/house/models` (with usage counts), `GET /api/house/model/<id>/file`, `PATCH/DELETE
/api/house/model/<id>`, `POST /api/house/room/<id>/object`, `PATCH/DELETE /api/house/object/<id>`.
Max upload 64 MB (`app.py MAX_CONTENT_LENGTH`; api.js maps the bodyless 413 to a friendly error).

**Stairs** connect two floors: a `stairs` row (rect footprint + `direction` of ascent, n/s/e/w)
belongs to the LOWER floor (`floor_id`) and rises that floor's full `floor_height`. In 3D they're
stepped meshes added to the house root (not a floor group) so `setLevel` can show them on **both**
levels they connect (`userData.levels`). In the planner they appear on both floors' tabs ("▲ up" /
"▼ down"), drawn with "+ Stairs" (they connect the active floor down to the one below), moved/
resized as rects, direction set in the side panel. Endpoints: `POST/PATCH/DELETE /api/house/stairs*`.

**The 2D floor-plan editor** (`frontend/js/planner.js`, "Floor plan" topbar button) is a full-screen
canvas overlay: per-floor tabs, draw rooms as rectangles, drag vertices/edge-midpoints (edges stay
rectilinear), Alt+click an edge to insert a vertex, drag whole rooms, snap in ft (Shift bypasses),
assign HA area/name/color/height, and trace over an uploaded floor-plan image (per-floor
`plan_image`/`plan_scale` (ft/px)/`plan_x`/`plan_z` columns). It edits its own fetched copy of the
house, PATCHes per gesture through the normal room endpoints, and triggers exactly one 3D rebuild
when closed. `demo/seed_demo.py` + `demo/demo_layout.json` seed this instance's real layout (traced
from the screenshots in `demo/`) — idempotent keyed upserts, re-runnable.

**Dynamic lighting** follows Home Assistant's sun and weather — frontend-only, no backend changes.
`frontend/js/daylight.js` reads `sun.sun` (`elevation`/`azimuth`) and the first `weather.*` entity
(via `state.js findEntities`), maps elevation through a keyframe ramp (night/dusk/golden/day) and
the weather condition through a dim/desaturate table, and eases `scene.js`'s exported
`sunLight`/`hemiLight` plus background+fog color toward the target each frame (~1s settle;
`onFrame(fn)` tick registry in scene.js — fog near must stay > controls.maxDistance 300; HA azimuth
0=N maps to scene north = −Z). Renderer uses ACESFilmic tone mapping; shadows stay off (translucent
walls). Topbar `☀ auto` button cycles auto/day/night (persisted in `localStorage['3dha.lightMode']`);
`window.__daylight.simulate({elevation, azimuth, condition})` fakes states for testing,
`simulate(null)` reverts. `frontend/js/roomlights.js` makes rooms glow at night when their HA
`light.*` entities are on (placed devices ∪ the linked HA area's lights): slab emissive tint per lit
room, plus a **fixed pool of 6 PointLights** (never added/removed — changing the scene's light count
recompiles every MeshStandard shader; only intensities animate, scaled by `getNightFactor()`).
When >6 rooms are lit, the ones nearest `controls.target` on visible levels win.
`setRoomLightsData({house, structure})` must be re-called after every house rebuild
(`main.js reloadHouse`) because slabs get fresh materials.

**Outdoor environment & weather** (frontend-only): `frontend/js/environment.js` builds the yard —
a grass disc reaching past fog-far, merged low-poly trees/bushes (two draw calls, vertex-colored
foliage, seeded RNG so the yard never reshuffles) laid out to mirror the real property's satellite
view (dense west treeline, treeline across the back, open east lawn, shrubs flanking the driveway
entrance), plus a fake-AO contact shadow. Plants anchor to the house-shell GLB's **measured**
footprint when one is loaded — re-measured on `levelChanged` since the shell loads async, with flat
hardscape meshes (<3 ft tall, e.g. the driveway) excluded from the bounds — and never grow on a
room rect (`onPad`). `setEnvironmentData(house)` re-runs on every `reloadHouse`.
`frontend/js/weather.js` renders the HA weather condition: rain streaks (LineSegments) + snow
(Points) from fixed max-size pools throttled with `setDrawRange`, ~9 drifting cloud meshes,
lightning as `renderer.toneMappingExposure` flashes (never add/remove lights — shader recompile),
and eased wet/whitened lawn tinting via `setGroundWet/Snow`. It follows daylight.js's resolved
sun+weather through `onDaylightChanged`, so the mode button and `__daylight.simulate({condition})`
drive it too; `window.__weather.step(secs)` advances the easing manually for testing (rAF pauses in
hidden tabs, so nothing eases while the tab is backgrounded). Both hide in edit mode
(`appModeChanged`), where the grid/dark ground shows instead, and in single-floor view (below).

**The dollhouse cutaway** (`frontend/js/cutaway.js`): the walls between you and a room fade out, so
every room reads like a Sims-4 build-mode shot — two far walls, no near walls, no ceiling. This used
to be free: walls were zero-thickness `ShapeGeometry` fins wound with inward normals and drawn
`side: THREE.FrontSide`, so the GPU backface-culled whichever ones the camera stood behind. That
popped at exactly 90 degrees, and it only ever hid the wall *surface* — the art and windows mounted
on it are separate GLB objects and were left hanging in mid-air.

Walls now have a body (`house.js WALL_THICKNESS`, 0.35 ft, extruded **outward** so the inner face
stays on the old plane — every one of the hand-placed furniture pieces is flush against it, and an
inward extrusion would embed them). Each polygon edge is its own child `Mesh` of the room mesh with
its own **cloned** material and `userData { part:'wall', edgeIndex, nx, nz (inward normal), fade,
hx, hz }`; the room mesh itself now carries empty geometry and is just the identity + parent
(`roomMeshes`, picking, `userData.kind`). Each wall's shape runs from `u = -t` to `len + t` so
neighbours overlap in a `t x t` block at every corner instead of leaving a notch. Each wall also
carries its own `part:'plinth'` skirt and `part:'edges'` accent rim as children, so both fade with
it — a room-wide version of either left a colored kerb and a bright outline tracing walls that had
dissolved. The skirt is a bare quad on the wall's **outer** face, not a solid: the outer face is the
only part of a kerb you can ever see, and a solid's end cap points along its wall, so at a corner
whose neighbour had faded it jutted into the open side as a colored nub. One `part:'plinthCap'`
(the polygon at `-PLINTH_DEPTH`, **BackSide**) closes the underside; BackSide is load-bearing —
faced up, its projection slides out past the slab's along the near edges and repaints the kerb.

One `onFrame` tick scores every wall by `dot(inward normal, horizontal direction to the camera)` and
eases opacity across a **wide** band (`FADE_LO 0.02 .. FADE_HI 0.55` — these are cosines, so that is
~33 degrees of orbit; the first attempt at 0.05..0.30 spanned barely 15 and still read as the pop it
replaced). The score is horizontal-only: folding in camera height would fade every wall at once from
overhead. `house.js applyWallOpacity` is the single writer, multiplying `userData.fade` by the room's
`baseOpacity` so focus-mode ghosting composes; `setRoomOpacity`/`setRoomEmissive`/`paintRoomEmissive`
fan out over the wall children (`paintRoomEmissive` deliberately does *not* touch `baseEmissive` —
hover needs to add a boost and put the stored level back).

It runs in **every** view that draws rooms, not just room focus: a solid wall does not backface-cull,
so a focus-only fade would turn the single-floor view into a row of sealed boxes.

Things mounted on a wall go with it. Door/window hinges carry `edgeIndex`. Furniture binds whole-object
when it is within 2 ft of a wall **and** its anchor is above 1.2 ft — the height gate is what keeps a
sofa pushed against a wall in place while the art above it leaves. **Architecture** (`WALL_ARCH_RE`:
wall/wainscot/baseboard/crown/moulding/trim, plus the openings through it — window, door, opening,
casing, jamb, lining, slider, panel; every noun takes an optional plural, since the pieces that
exposed this were named "Dining Openings"/"Dining Windows"/"Rios Closet Doors") takes a different
route from furniture in two ways that are the whole point of the split list: it **skips the 1.2 ft
height gate** (a door lining or a garage door starts at the floor and still has to leave with its
wall) and it is measured **by geometry, not by its anchor** ("Dining Windows" is five units on four
walls in one model, anchored near none of them). `floor` is deliberately absent — a floor plane in a
narrow room measures within `SURFACE_MAX_DIST` of every wall and would be shredded across all of
them. Not objects.js's `SURFACE_RE`, which is about pickability and also matches "Ceiling Fan".
Architecture is one GLB per room and binds **per wall**: by sub-mesh
where the GLB happens to have one per wall, and otherwise by `splitMerged`, which sorts the merged
run's triangles by nearest wall and rebuilds it as one child mesh per wall (buckets share the source
attribute buffers, differ only in their index, and each needs its **own** material clone, since
`fadeSubtree` tracks the transparent flag per material). That split is what the whole thing turns
on: `glb.py` groups primitives **by material, never by wall**, so a `for w in "nswe"` trim run lands
in a single primitive whose bbox centre is mid-room — it bound to nothing and kept full opacity
forever, leaving skirting, wainscot, casings and door leaves standing in the gap. Fixing it here and
not in the GLBs means every already-uploaded room is covered with no rebuild. The bind is lazy (GLBs
resolve late) and must `root.updateWorldMatrix(true, true)` first, because `Box3.setFromObject`
refreshes only the object's own matrix and a stale parent chain makes every panel measure to the
room origin; collect the sub-meshes before splitting, or `traverse` walks into the buckets it just
made. Ceilings (`CEILING_RE`, name *ending* in "Ceiling") always fade to 0 — crown authored inside
a `* Ceiling` piece therefore goes with it even on walls still shown.
Anything faded gets `transparent: true` set once (flipping that flag is what recompiles a shader).
`objects.js` stays the single writer of object *visibility*; the fade goes through its `wallFade` map.
`window.__cutaway` exposes `settle()` (jump every fade to its target — roomkit's `shot.py` and
`dollhouse.py` call it before grabbing the canvas), `setEnabled(b)` and `debug()`. Snapshot cards
render from their own camera, so `snapshots.js` brackets its render with `scoreForCamera(snapCam)`.
Room focus also hides stairs, which live on the house root and would otherwise hang in the backdrop.

**Single-floor presentation mode** (`frontend/js/floorview.js`): picking a floor in the level
selector shouldn't leave one slab hovering over the lawn, so on `levelChanged` to a floor it swaps
the sky for a dark studio-gradient backdrop (a radial CanvasTexture as `scene.background`, fog
nulled — daylight.js guards its background/fog writes behind `scene.background.isColor`/`scene.fog`
and exposes `repaintSky()` for the restore, since its tick early-returns once converged), flies the
camera to a centered ~50°-elevation dollhouse shot of that floor's rooms (keeps the current
azimuth), locks zoom-out just past that framing shot (`scene.js setMaxZoom` retunes the live
`MAX_ZOOM` cap), and disables pan so the floor stays centered; environment.js and weather.js hide
their roots on the same event. Selecting House ('all') restores the daylight sky, the house zoom
cap, and the pose you left from (focus-mode exits then override with their own saved pose — both
were captured at the same moment). Same-level re-fires (rebuilds) only re-center the orbit target
— buildHouse's `focusOn` points it at the whole-house center otherwise — without moving the camera.

**Frontend module layout** (`frontend/js/`, loaded as native ES modules, Three.js via CDN
importmap — no npm/bundler):
- `main.js` — bootstraps: loads HA structure + house layout, builds the scene, wires picking
  (raycasting for click/hover on rooms and device markers) and realtime.
- `scene.js` — Three.js scene/camera/renderer/controls setup.
- `house.js` — builds room geometry (floors, per-edge thick walls, slab, plinth) from `/api/house`
  data. Also loads the whole-house shell GLB; when that fetch/parse fails it dispatches
  `shellLoadFailed` and `ui.js`
  raises a persistent banner — a silently missing house reads as a render bug rather than the deploy
  problem it usually is (see `docs/TROUBLESHOOTING-house-shell.md`).
- `devices.js` — builds device markers from placements; owns the `markers` map (entity_id → mesh)
  and per-domain base colors.
- `state.js` — live entity-state store; restyles markers on state change (color/emissive/scale
  encode on/off/unavailable).
- `socket.js` — SocketIO client wrapper with polling fallback.
- `daylight.js` — sun/weather-driven scene lighting (see Dynamic lighting above).
- `cutaway.js` — camera-aware per-wall fade + wall-mounted furniture (see The dollhouse cutaway
  above). Owns `window.__cutaway`.
- `floorview.js` — single-floor presentation mode: dark backdrop, centered floor framing,
  zoom-out lock (see Single-floor presentation mode above).
- `roomlights.js` — per-room night glow for HA lights that are on.
- `environment.js` — grass/trees/bushes yard + contact shadow (see Outdoor environment above).
- `weather.js` — rain/snow/clouds/lightning + lawn tint from the HA weather condition.
- `ui.js` — room editor panel, device detail/control panel, level selector, connection banner.
- `planner.js` — the 2D per-floor floor-plan editor (canvas overlay, feet grid, polygon editing,
  plan-image tracing).
- `api.js` — thin fetch wrapper for the Flask endpoints above; notifies layout-mutation listeners
  (`onLayoutMutation`) after each mutating `/api/house` call.
- `undo.js` — app-wide undo/redo buttons + Ctrl+Z/Y shortcuts (see Undo/redo above).

## The room build ("roomkit") — how the house gets furnished

Every room is being rebuilt as procedural geometry until a critic can't tell the render from the
photograph of the real room. **Start any room work by reading `tools/roomkit/RESUME.md`** — it
carries the current state, the open critic verdicts and what to do next; then `ROOM-BRIEF.md`
(toolchain + every lesson the critic reports have produced) and `STYLE-BAR.md` (the Sims 4
dollhouse bar). Per-room piece maps live in `tools/roomkit/rooms/<id>.json`; whole-house state in
`house_status.json`, rendered to a shareable page by `python -m roomkit.house_progress` (run from
`tools/`).

`tools/roomkit/` is the toolchain: `glb.py` writes GLBs by hand (no Blender), `place.py` uploads
and positions them through the normal `/api/house/model` + `/api/house/room/<id>/object` endpoints,
`rooms.py` shoots a room from the reference photo's viewpoint or from a `doll_se/sw/ne/nw`
cutaway quadrant, `dollhouse.py` shoots the whole house with every floor visible, `meter.py`
compares render against photo. Per-room build scripts live in `scratchpad/<room>/` (e.g.
`scratchpad/lr5/`, `scratchpad/kbuild/`) and are idempotent and re-runnable, keyed by piece name.

The loop is build → shoot → **blind** critic verdict → next round. Two rules that have each cost a
round: `roomkit.meter` only measures an *empty* room (its centre patch lands on furniture
otherwise — meter furnished rooms by hand), and standard deviation is scale-blind, so match
mean|Δ| between adjacent pixels too, at native resolution. Budgets: **≤1.5 MB per room, ≤300 KB
per piece** — take fine gradients from a tiled texture, not from mesh cells.

## Conventions worth knowing

- Backend modules are organized as Flask blueprints under `api/`, `house/`, `ha/`, `realtime/`,
  each independent and registered in `app.py`'s `create_app()`.
- `config.py` is the only place that reads `.env`; the HA token only ever lives in `config.py` and
  `ha/client.py`/`ha/ws_client.py` — never send it to the frontend.
- Windows dev environment (PowerShell). Default port is 5000; if that's in use, an alternate
  `3d-ha-5001` launch config exists (see `.claude/launch.json`).
- UI-chrome design language: the app's own glassy-dark tokens live at `:root` in
  `frontend/css/style.css`. A vendored Apple.com design spec (full token set + do's/don'ts)
  sits in the `apple-design` skill (`.claude/skills/apple-design/`) as a reference for
  restyling that chrome — it is not what the app currently ships.
- Not yet implemented (see `3d-home-assistant-house-spec.md` phases 8-9): drag-to-position for
  *devices* in the 2D planner (rooms drag there already; devices drag in the 3D view once their
  panel is open, or via numeric inputs), app-level login (needed before hosting this anywhere
  public).
