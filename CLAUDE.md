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

**Realtime path:** HA's `state_changed` events arrive on the `HARealtime` background thread, update
`HACache`, and are relayed to all connected browsers via `realtime/socketio.py` (SocketIO event
`state_changed`). The frontend (`js/socket.js`) falls back to 5s polling if the socket drops.
`js/state.js` owns the live entity-state map and re-styles 3D markers (color/emissive/scale) when a
state changes.

**Control path:** browser → `POST /api/control` (`api/control_routes.py`) → `HAClient.call_service`
→ HA. `domain` defaults to the entity_id's prefix and `service` defaults to `toggle` if not given.

**Key endpoints:** `GET /api/ha/structure` (HA tree), `GET /api/ha/states`, `GET /api/ha/status`,
`POST /api/ha/refresh` (re-fetch HA registries) — `GET/POST/PATCH/DELETE /api/house*` (floor/room/
device-placement CRUD, backed by `HouseStore`) — `POST /api/control` — SocketIO event
`state_changed`.

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
- `api.js` — thin fetch wrapper for the Flask endpoints above.

## Conventions worth knowing

- Backend modules are organized as Flask blueprints under `api/`, `house/`, `ha/`, `realtime/`,
  each independent and registered in `app.py`'s `create_app()`.
- `config.py` is the only place that reads `.env`; the HA token only ever lives in `config.py` and
  `ha/client.py`/`ha/ws_client.py` — never send it to the frontend.
- Windows dev environment (PowerShell). Default port is 5000; if that's in use, an alternate
  `3d-ha-5001` launch config exists (see `.claude/launch.json`).
- Not yet implemented (see `3d-home-assistant-house-spec.md` phases 8-9): drag-to-position on a
  top-down grid (positions are numeric inputs for now), non-rectangular room footprints, app-level
  login (needed before hosting this anywhere public).
