# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Reads a Home Assistant instance and renders the house as an interactive 3D model (Three.js), split by
floor, with each device shown live and controllable from the 3D view. Flask backend, vanilla JS
(ES modules, no bundler/build step) frontend. The HA long-lived access token never reaches the
browser — the browser only talks to Flask; Flask talks to Home Assistant.

## Running it

`cd backend` then `python app.py` (create the venv and `pip install -r requirements.txt` first).
Opens on http://127.0.0.1:5000.

`backend/config.py` is the only reader of `.env` (`HA_BASE_URL`, `HA_TOKEN`, `APP_SECRET`). There is
no `.env.example` in the repo, and the app boots without `.env` at all — you can build rooms, but
there's no HA data or live states until it's configured.

There is no test suite, linter, or build step in this repo. Verify changes by running the app and
exercising the flow in a browser (see the `run` and `verify` skills).

`app.py` runs with the Werkzeug reloader **off** on purpose (`debug=False`) — the HA websocket
background thread must only start once per process; enabling the reloader would double-start it.

## Architecture

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

**Endpoints** are declared as `@bp.<verb>("/path")` in `house/routes.py` (blueprint prefix
`/api/house`) and in `api/*_routes.py` — grep those for the current list. One rule that isn't
visible in the route table: floor-plan and model uploads are **png/jpg/webp only, never SVG** —
files are served back verbatim, so an SVG would be a script-execution vector.

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
**selected** marker/object (selection = open device/object panel) with three's `TransformControls`
— translate (XYZ), rotate (Y only) and uniform scale, one PATCH on release, no rebuild. Endpoints:
`POST /api/house/model` (multipart),
`GET /api/house/models` (with usage counts), `GET /api/house/model/<id>/file`, `PATCH/DELETE
/api/house/model/<id>`, `POST /api/house/room/<id>/object`, `PATCH/DELETE /api/house/object/<id>`.
Max upload 64 MB (`app.py MAX_CONTENT_LENGTH`; api.js maps the bodyless 413 to a friendly error).

**Bound light fixtures** — a furniture `objects` row can carry an `entity_id` and *be* that HA
entity: the lamp GLB already in the room becomes the thing you click to toggle it, and the thing
the room is lit from. Three nullable columns on `objects` (`entity_id`, `visible`, `light_cfg`
JSON: `{color, intensity, offset_y, range, glow_part, emit}`), all in `OBJECT_FIELDS` so they PATCH
through the existing `/api/house/object/<id>`; undo/redo needed no change (`objects` was already in
`HISTORY_TABLES`, and `export_snapshot`/`restore_snapshot` are column-agnostic). Bind from the
object panel's entity `<select>`, or from the room editor's **Light fixtures** section, which pairs
the room's lamp-like objects against its HA area's light/switch/fan entities (name-matched on
`/lamp|light|sconce|chandelier|pendant|fan/i` — deliberately **not** `ceiling`, which names the
room-scale ceiling *plane* in ~7 rooms here; "Ceiling Fan" still matches via `fan`). "Auto-match"
only *proposes* pairings — name matching will not get "Master Lamp Small" → `light.rosemary_bedside_light`.
Binding also overrides `objects.js SURFACE_RE`, so a piece named "Ceiling Fan" becomes pickable.
Not every binding emits: `roomlights.js EMITTING_DOMAINS` is `light`+`switch` (switch-controlled
lamps are common here), so a fan or lock binds for *clicking* without glowing lamp-amber;
`light_cfg.emit` overrides either way. See `frontend/CLAUDE.md` for the pool and the falloff.

**Stairs** connect two floors: a `stairs` row (rect footprint + `direction` of ascent, n/s/e/w)
belongs to the LOWER floor (`floor_id`) and rises that floor's full `floor_height`. In 3D they're
stepped meshes added to the house root (not a floor group) so `setLevel` can show them on **both**
levels they connect (`userData.levels`). In the planner they appear on both floors' tabs ("▲ up" /
"▼ down"), drawn with "+ Stairs" (they connect the active floor down to the one below), moved/
resized as rects, direction set in the side panel. Endpoints: `POST/PATCH/DELETE /api/house/stairs*`.

**Editing the outside** ("Outside" topbar button, `frontend/js/yard.js`) — the exterior is *generated*,
not stored: `environment.js` draws every tree, shrub, bed, slab, prop, neighbour and the street from
one fixed seed, identically on every load, and merges the lot into six meshes. So editing works by
**delta**, and the only thing persisted is what the user changed. While the yard builds, each
geometry is filed under an *item* — one tree, one shrub, one slab of driveway — and the item is keyed
by its kind plus the position the builder gave it (`kind:x*10:z*10`, e.g. `tree:-230:280`; ordinals
were rejected because inserting one tree upstream would renumber everything after it). `yard_edits`
stores `dx/dy/dz/rot_y/scale/deleted` against that key, plus clone rows (`src` = the key they copy).
On the next load the yard is generated exactly as before and the deltas go on top, so an untouched
yard is **vertex-identical** to the one that file drew before any of this existed (verified: 890,769
verts either way). Item boundaries come from two rules — a call to one of `ITEM_FACTORIES` opens an
item and owns everything it pushes (nested calls stay in the outer item, so a shrub built from three
lumps is one shrub), and consecutive *unscoped* pushes group into one item, which is what keeps a
hand-built step platform or a scattered row of cobbles grabbable as one thing. The factories are
wrapped by **reassigning their function declarations** (`installItemScopes`), so no call site in the
~600 lines of `addFrontYard`/`addBackYard` changed, including the
`(cond ? addConifer : addDeciduous)(...)` dispatch. Four things are load-bearing:

- **Empty items are dropped before keys are handed out.** `PLANT_TREES` and `BUILD_NEIGHBOURS` are
  both `false`, so `addDeciduous`/`addConifer`/`addShadeTree`/`addWeeper`/`addNeighbour` still open an
  item and push nothing — 108 of them. An item with no geometry measures at the origin, so every one
  keyed to `0,0` and took a collision suffix: 106 keys whose identity would shift the day either flag
  moved.
- **The yard is drawn per-item only while the editor is open**, and as the same six merged meshes
  otherwise (`setYardEditing`). A piece's group sits at its own pivot — footprint centre at its lowest
  point, so a tree turns about its trunk and grows up from the ground — with its geometry re-centred
  there, which is what lets `drag.js` move it with the normal gizmo and read the gesture straight back
  out as the delta to save (`kind: 'yard'`, subtracting `userData.pivot`).
- **The lawn is not clickable** (`SURFACE_KINDS`). It is one item covering the whole lot, so left
  clickable it swallows every click on open grass — you could never deselect, and never reach anything
  lying flat on it. Same rule `objects.js` applies to room-wide floors and ceilings. It is still an
  item and still takes edits.
- **Erasing hides, it does not destroy.** The group stays in the scene invisible, so putting a piece
  back is a visibility flip, and the bar's *Erased* list is the only handle on something you can no
  longer see. Only a duplicate (which changes the item *set*) rebuilds.

**Adding to the yard** ("Add…" in the Outside editor's bar, `frontend/js/yardkit.js`) — a bottom
tray of everything the exterior is built out of, because the editor could only ever take things away.
Two things make it cheap. The catalogue is **read back off the yard that is standing**, grouped by
`label`, so it can never offer a piece `environment.js` does not draw and never goes stale when a
factory is added or renamed — and each entry keeps *every* generated piece carrying that label, so
adding five bushes picks five different ones out of the 54 shrub mounds rather than stamping one out
five times. And adding is the **existing clone**: a `yard_edits` row with `src` naming a piece already
in the yard, so there is no new storage and undo/redo covers it for free (verified: three adds undo
and redo one at a time). `lawn`, `street` and the unscoped `piece` runs are left out of the tray, for
reasons in `SKIP_KINDS`. Tiles carry a **real render of the piece** — no name separates "Shrub" from
"Shrub mound" from "Bush" — shot with the app's own renderer into a private scene and cropped off the
live canvas, the pattern `snapshots.js` uses for room cards (~11 ms each, once, cached for the module's
life). A tile drops its piece on the ground under the middle of the view, pushed clear of the building
box if the view ray lands inside the house (`clearOfHouse` in `yard.js`), scattered a few feet and —
for kinds with no canonical facing — randomly turned, then selects it with the gizmo on. `placeClone`
is now the single path for both the tray and the panel's Duplicate; it passes the **whole** delta to
`applyYardEdit`, which Duplicate did not — anything not given falls back to `IDENTITY_EDIT`, so a
duplicate used to be drawn exactly on top of its source until the next page load.

Undo/redo needed nothing new beyond adding `yard_edits` to `HISTORY_TABLES` — `export_snapshot`/
`restore_snapshot` are column-agnostic, and restoring original row ids is what makes an undone
duplicate come back as the same `clone:<id>`. Endpoints: `GET /api/house/yard`, `PATCH /api/house/yard`
(upsert by key), `POST /api/house/yard/clone`, `DELETE /api/house/yard/<key>` (revert one piece),
`POST /api/house/yard/reset`. The rows also ride along on `GET /api/house` as `yard`, since
`setEnvironmentData` needs them at build time.

**The shell's measurement is not final when the yard first measures it**
(`settleShellAnchors` in `environment.js`). Measured here: the `roofRect` the boot build sees is
z0 −25.43 / z1 41.36, and a frame later the same measurement gives −25.77 / 41.70. The whole yard is
laid out from that rect, so the yard drawn at boot was **not** the yard any later rebuild produced —
open the planner, hit undo, or sync, and the exterior quietly shifted and reshuffled (187 items
against 189, and every bare tree a few feet off). Nothing noticed while the yard was anonymous
geometry; the Outside editor made it visible, because a piece has to still be the same piece across a
rebuild to be editable at all. The fix re-measures at 0/120/500 ms and rebuilds only if the anchors
really moved, using the same guard `levelChanged` has always used. `setTimeout`, not
`requestAnimationFrame` — rAF is paused in a backgrounded or occluded tab and the yard must settle
whether or not anyone is watching.

**The 2D floor-plan editor** (`frontend/js/planner.js`, "Floor plan" topbar button) is a full-screen
canvas overlay: per-floor tabs, draw rooms as rectangles, drag vertices/edge-midpoints (edges stay
rectilinear), Alt+click an edge to insert a vertex, drag whole rooms, snap in ft (Shift bypasses),
assign HA area/name/color/height, and trace over an uploaded floor-plan image (per-floor
`plan_image`/`plan_scale` (ft/px)/`plan_x`/`plan_z` columns). It edits its own fetched copy of the
house, PATCHes per gesture through the normal room endpoints, and triggers exactly one 3D rebuild
when closed. `demo/seed_demo.py` + `demo/demo_layout.json` seed this instance's real layout (traced
from the screenshots in `demo/`) — idempotent keyed upserts, re-runnable.

**Frontend detail lives in `frontend/CLAUDE.md`** — the dynamic lighting, outdoor
environment/weather, dollhouse cutaway and single-floor presentation systems. It loads
automatically whenever you work under `frontend/`.

**Furnishing the house ("roomkit")** — see the `roomkit` skill; start any room work by reading
`tools/roomkit/RESUME.md`.

## Conventions worth knowing

- Backend modules are organized as Flask blueprints under `api/`, `house/`, `ha/`, `realtime/`,
  each independent and registered in `app.py`'s `create_app()`.
- `config.py` is the only place that reads `.env`; the HA token only ever lives in `config.py` and
  `ha/client.py`/`ha/ws_client.py` — never send it to the frontend.
- **All HTTP to HA goes through `HAClient`** (`ha/client.py`), never a bare `requests` call. Nabu
  Casa's remote proxy drops any new connection whose TLS ClientHello arrives more than ~50 ms after
  the TCP connect, and stock `requests` parses the CA bundle *between* the two, so every verified
  request 502s (`SSLEOFError`). `HAClient` mounts an adapter with a pre-built `SSLContext` and gates
  concurrent HA connections; the comment at the top of `ha/client.py` has the measurements.
- Windows dev environment (PowerShell). Default port is 5000; if that's in use, an alternate
  `3d-ha-5001` launch config exists (see `.claude/launch.json`).
- UI-chrome design language: **Apple.com, dark surfaces only**. The full token set lives at
  `:root` in `frontend/css/style.css`; the spec it implements is vendored in the `apple-design`
  skill (`.claude/skills/apple-design/reference/DESIGN.md`). The five rules that carry it: one
  accent (Action Blue `#0066cc` fills, Sky Link Blue `#2997ff` for links/marks on dark); **no
  shadows on chrome** — `--shadow` is deliberately undefined so a stray `var(--shadow)` fails
  loudly, and elevation comes from a surface step (`--card-bg` panel < `--surface-1` tile <
  `--surface-2` pressed) plus the 8% hairline; **weight 500 does not exist** (300/400/600/700);
  radii don't blend (`--radius-sm` 8 utility · `--radius-lg` 18 cards · `--radius-pill` actions);
  and `transform: scale(0.95)` is the press state on every button — *any button carrying its own
  centring translate must restate it in its own `:active`* (`#focus-exit`, `.cam-nav`), or it
  jumps on press. Three things are documented extrapolations, since the spec is light-dominant and
  its Known Gaps admit dark cards were never surfaced: the hairline is inverted to
  `rgba(255,255,255,.08)`; `.glass` keeps `backdrop-filter` (the spec sanctions it on floating
  bars, and this chrome floats over a live 3D render) but lost its shadow; and `--ok/--warn/
  --danger` are Apple's *system* colours, used only for readouts, never for anything clickable.
  Three `linear-gradient`s survive as functional legibility scrims over photography
  (`.cam-label`, `.rc-body`, `.tile.camera .t-name`) — they are commented as such; decorative
  gradients are banned. `color-scheme: dark` themes the native controls (scrollbars, file input,
  pickers). **Layout is tokenised too**: `--gutter`/`--gap`/`--rail-w`/`--dock-h`/`--sa-*`/
  `--stage-*` at `:root` replaced ~30 hard-coded offsets, and `roomcards.js`/`cameras.js` read the
  gaps and aspects back out of what the browser actually laid out
  (`getComputedStyle(el).columnGap`, `layout.js tokenPx`) rather than keeping private copies.
  Breakpoints key off **width**, not orientation — an iPad Air in portrait and an 11" Pro in
  landscape are both ~820-834px and want the same treatment; orientation moves only the rail's
  axis. Every fixed element folds `env(safe-area-inset-*)` into its own offset, since `<body>` is
  not the containing block for `position:fixed`. See `frontend/CLAUDE.md` for the `--stage-*`
  contract, which is what the 3D camera frames into. Out of scope and still on the old palette: the **planner's canvas drawing colours**
  (`planner.js` `ctx.fillStyle`, ~29 literals) and `floorview.js`'s blue studio backdrop —
  `snapshots.js`'s twin backdrop *was* reneutralised because it is deliberately matched to
  `.room-card`. The 3D scene is lit from HA state, not CSS, and this spec never governed it.
- **It is an app, not a web page** — installable (`frontend/manifest.webmanifest` + `icons/`,
  standalone metas in `index.html`, deliberately no service worker), chrome that slides rather
  than pops, no selectable chrome text, and **never `window.alert`/`confirm`/`prompt`**: use
  `showAlert`/`showConfirm` from `frontend/js/dialog.js`. Details and the rules that keep it that
  way are under "App shell, not web page" in `frontend/CLAUDE.md`.
- Not yet implemented (see `3d-home-assistant-house-spec.md` phases 8-9): drag-to-position for
  *devices* in the 2D planner (rooms drag there already; devices drag in the 3D view once their
  panel is open, or via numeric inputs), app-level login (needed before hosting this anywhere
  public).
