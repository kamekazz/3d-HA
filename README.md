# 3D Home Assistant House

Reads a Home Assistant instance and renders the house as an interactive 3D model
(Three.js), split by floor, with each device shown live and controllable from
the 3D view. Flask backend, vanilla JS frontend.

The HA long-lived access token **never reaches the browser** — the browser only
talks to Flask; Flask talks to Home Assistant.

## Quick start

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

Open http://127.0.0.1:5000

> **Token hygiene:** create the token in HA under Profile → Security →
> Long-lived access tokens. If a token was ever pasted into a chat, log, or
> commit, revoke it and create a new one.

The app also starts without `.env` — you can build rooms, but no HA data or
live states until it's configured.

## Using it

1. **Room editor** (top-right button): create a room — name, floor, the HA area
   it maps to, width/depth/height and X/Z position on the floor grid.
2. With a room selected, its HA area's **entities are auto-listed** — click
   *Place* to drop them into the room (lights go near the ceiling), then
   fine-tune x/y/z in the placement list.
3. **Level selector** (top-left): show one floor or the whole house.
4. **Click a device marker** → side panel with state + controls (toggle
   lights/switches, open/close covers, lock/unlock…).
5. Everything updates **live** via a SocketIO relay of HA's `state_changed`
   stream (falls back to 5s polling if the socket drops).
6. **Refresh HA** re-reads the floor/area/device/entity registries after you
   change things in Home Assistant.

Floors are seeded automatically from HA's floor registry on first load.

## Architecture

```
Browser (Three.js + vanilla JS)
     │ HTTP + SocketIO (no HA token here)
     ▼
Flask backend
  ├── ha/client.py     REST → HA (states, call_service)
  ├── ha/ws_client.py  WebSocket → HA (registries + state_changed, auto-reconnect)
  ├── ha/cache.py      in-memory floors/areas/devices/entities + states
  ├── house/           our 3D layout (SQLite: backend/house.db)
  └── realtime/        SocketIO relay of state changes to browsers
```

Key endpoints: `GET /api/ha/structure`, `GET /api/ha/states`, `GET /api/house`
+ room/placement CRUD, `POST /api/control`, SocketIO event `state_changed`.

## Not yet implemented (spec phases 8–9)

- Drag-to-position on a top-down grid (positions are numeric inputs for now)
- Non-rectangular room footprints
- App-level login (add before hosting this anywhere public)
