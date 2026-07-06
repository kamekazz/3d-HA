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
+ `GET /api/house/plan/<id>` (floor-plan tracing images, saved under gitignored `backend/uploads/`;
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
table + gitignored `backend/uploads/models/model_<id>.<ext>` (same deterministic-filename pattern as
floor plans; `MODEL_EXTENSIONS` whitelist). A model can (a) **replace a device marker** —
`placements.model_id` (FK, `ON DELETE SET NULL` so deleting a model reverts the primitive), plus
`rot_y` (radians) and `scale` — or (b) be placed as **standalone furniture**: an `objects` row
(room-anchored like placements, `model_id ON DELETE CASCADE`). `frontend/js/models.js` owns the
GLTFLoader (+ DRACO decoder from the CDN) and a per-model cache; instances are `scene.clone(true)`
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

**Frontend module layout** (`frontend/js/`, loaded as native ES modules, Three.js via CDN
importmap — no npm/bundler):
- `main.js` — bootstraps: loads HA structure + house layout, builds the scene, wires picking
  (raycasting for click/hover on rooms and device markers) and realtime.
- `scene.js` — Three.js scene/camera/renderer/controls setup.
- `house.js` — builds room geometry (floors, walls) from `/api/house` data.
- `devices.js` — builds device markers from placements; owns the `markers` map (entity_id → mesh)
  and per-domain base colors.
- `state.js` — live entity-state store; restyles markers on state change (color/emissive/scale
  encode on/off/unavailable).
- `socket.js` — SocketIO client wrapper with polling fallback.
- `ui.js` — room editor panel, device detail/control panel, level selector, connection banner.
- `planner.js` — the 2D per-floor floor-plan editor (canvas overlay, feet grid, polygon editing,
  plan-image tracing).
- `api.js` — thin fetch wrapper for the Flask endpoints above.

## Conventions worth knowing

- Backend modules are organized as Flask blueprints under `api/`, `house/`, `ha/`, `realtime/`,
  each independent and registered in `app.py`'s `create_app()`.
- `config.py` is the only place that reads `.env`; the HA token only ever lives in `config.py` and
  `ha/client.py`/`ha/ws_client.py` — never send it to the frontend.
- Windows dev environment (PowerShell). Default port is 5000; if that's in use, an alternate
  `3d-ha-5001` launch config exists (see `.claude/launch.json`).
- Not yet implemented (see `3d-home-assistant-house-spec.md` phases 8-9): drag-to-position for
  *devices* in the 2D planner (rooms drag there already; devices drag in the 3D view once their
  panel is open, or via numeric inputs), app-level login (needed before hosting this anywhere
  public).
