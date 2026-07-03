# 3D Home Assistant House — Developer Specification & Build Plan

**Project goal:** A web app that reads a Home Assistant (HA) instance and renders the house as an interactive 3D model (Three.js), split by floor/level, with each device shown live and controllable from the 3D view.

**Stack:** Python **Flask** backend, **vanilla HTML/CSS/JS** frontend, **Three.js** for 3D. Persistence via **SQLite** (or a JSON file for the first pass).

---

## 0. The one non-negotiable: token handling

The long-lived access token controls the entire home. It must **never** reach the browser.

- The token lives **only** on the server, in an environment variable (`.env`, not committed to git).
- The browser talks to **our Flask backend**. Flask talks to Home Assistant.
- The browser never sees the token, the HA URL, or raw HA endpoints.
- Rotate the token if it is ever pasted, logged, or shared. (The token used to scope this project has already been shared and should be revoked and regenerated.)

```
.env  (server only, gitignored)
------------------------------------
HA_BASE_URL = https://<your-instance>.ui.nabu.casa
HA_TOKEN    = <fresh long-lived access token>
APP_SECRET  = <random flask secret>
```

---

## 1. How the pieces map

Home Assistant already models the building. We reuse it:

| Home Assistant concept | Our 3D concept        | Notes |
|------------------------|-----------------------|-------|
| **Floor**              | Level (1, 2, 3)       | Stacked on the Y axis |
| **Area**               | Room                  | Rendered as a box / footprint |
| **Device**             | A thing in a room     | Often groups several entities |
| **Entity**             | A controllable/readable point (a light, a sensor, a switch) | This is what we color/animate and control |

So the flow is: **read the floors and rooms that already exist in HA → let the user add geometry (size + position) → drop the devices into their rooms → make them live.**

---

## 2. Architecture

```
 Browser (Three.js + vanilla JS)
        │  HTTPS / WebSocket  (no HA token here — only talks to Flask)
        ▼
 Flask backend
   ├── HA client  ──► Home Assistant  (REST + WebSocket, token attached here)
   ├── House model store (SQLite/JSON): room sizes, positions, device placements
   └── Realtime relay: subscribes to HA state changes, pushes to browser
```

Two reasons the Flask layer exists (it's not just a pass-through):
1. **Security** — keeps the token off the client.
2. **The house geometry lives here** — HA knows the *rooms and devices*, but it does **not** store 3D sizes/positions. That's our data, and Flask owns it.

---

## 3. Home Assistant API — the important details

There are **two** HA APIs and the developer needs both.

### REST API (simple, for states & control)
Base: `${HA_BASE_URL}/api/` — every request sends `Authorization: Bearer <token>`.

| Purpose | Call |
|---|---|
| All current states | `GET /api/states` |
| One entity's state | `GET /api/states/<entity_id>` |
| Call a service (control) | `POST /api/services/<domain>/<service>` body `{"entity_id": "..."}` |
| Basic config | `GET /api/config` |
| History | `GET /api/history/period/<timestamp>?filter_entity_id=...` |

### WebSocket API (required for the room/device structure)
Base: `${HA_BASE_URL}/api/websocket`

**The floor / area / device / entity registries are only available over WebSocket, not REST.** This is the data that gives us the building structure, so a WebSocket client on the backend is mandatory.

Auth handshake:
```
1. connect  → server sends {"type": "auth_required"}
2. client   → {"type": "auth", "access_token": "<token>"}
3. server   → {"type": "auth_ok"}   (or "auth_invalid")
4. then send commands with an incrementing "id"
```

Structure commands (each returns a list under `result`):
```jsonc
{"id": 1, "type": "config/floor_registry/list"}   // levels
{"id": 2, "type": "config/area_registry/list"}    // rooms  (each area has floor_id)
{"id": 3, "type": "config/device_registry/list"}  // devices (each has area_id)
{"id": 4, "type": "config/entity_registry/list"}  // entities (device_id / area_id)
{"id": 5, "type": "get_states"}                    // current values
```

Live updates:
```jsonc
{"id": 6, "type": "subscribe_events", "event_type": "state_changed"}
// server then streams events whenever any entity changes
```

Control a device:
```jsonc
{"id": 7, "type": "call_service",
 "domain": "light", "service": "toggle",
 "target": {"entity_id": "light.kitchen_ceiling"}}
```

By joining these four registries you get the whole tree:
```
Floor (level) → Areas on that floor → Devices in each area → Entities on each device
```

### Minimal backend HA WebSocket client (sketch, Python)
```python
import asyncio, json, websockets

async def ha_fetch_structure(base_url, token):
    ws_url = base_url.replace("https", "wss") + "/api/websocket"
    async with websockets.connect(ws_url) as ws:
        assert json.loads(await ws.recv())["type"] == "auth_required"
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        assert json.loads(await ws.recv())["type"] == "auth_ok"

        async def cmd(id_, type_):
            await ws.send(json.dumps({"id": id_, "type": type_}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == id_ and msg.get("type") == "result":
                    return msg["result"]

        return {
            "floors":   await cmd(1, "config/floor_registry/list"),
            "areas":    await cmd(2, "config/area_registry/list"),
            "devices":  await cmd(3, "config/device_registry/list"),
            "entities": await cmd(4, "config/entity_registry/list"),
        }
```
Because Flask is synchronous, run this asyncio client in a background thread (or a dedicated worker) and cache the result. Refresh the registries on demand; keep the state-change subscription open continuously for the live relay.

---

## 4. Backend structure (Flask)

```
backend/
  app.py                 # app factory, entrypoint
  config.py              # loads .env (HA_BASE_URL, HA_TOKEN, APP_SECRET)
  ha/
    client.py            # REST calls to HA (states, call_service)
    ws_client.py         # WebSocket: registries + state_changed subscription
    cache.py             # in-memory cache of the floor/area/device/entity tree
  house/
    models.py            # House, Floor, Room, DevicePlacement (data classes / ORM)
    store.py             # persistence (SQLite via SQLAlchemy, or house.json)
    routes.py            # CRUD for rooms & placements (our geometry)
  api/
    ha_routes.py         # /api/ha/* — proxied HA data for the browser
    control_routes.py    # /api/control — call_service
  realtime/
    socketio.py          # relays HA state_changed events to browsers
  requirements.txt
  .env.example
```

### Backend endpoints the frontend will use

| Method | Endpoint | Returns / does |
|---|---|---|
| GET | `/api/ha/structure` | Combined floors→areas→devices→entities tree (from cache) |
| GET | `/api/ha/states` | Current states for all entities |
| GET | `/api/house` | Our house model: rooms with sizes/positions + device placements |
| POST | `/api/house/room` | Create a room (name, size, floor, linked HA area_id) |
| PATCH | `/api/house/room/<id>` | Update size / position |
| DELETE | `/api/house/room/<id>` | Remove a room |
| POST | `/api/house/room/<id>/device` | Place an entity in a room at (x,y,z) |
| POST | `/api/control` | `{entity_id, domain, service}` → calls HA service |
| WS/SocketIO | `/realtime` | Pushes `{entity_id, new_state}` on every change |

**Key separation:** `/api/ha/*` is read-through from Home Assistant (the *what exists*). `/api/house/*` is our own data (the *3D layout*). They are linked by `area_id` (room ↔ HA area) and `entity_id` (marker ↔ HA entity).

---

## 5. The house data model (our own layer)

This is what HA does **not** store and what we persist.

```jsonc
House {
  floors: [
    Floor {
      id: "f1",
      name: "Ground floor",
      level: 1,                 // 1, 2, 3
      ha_floor_id: "ground",    // link to HA floor
      floor_height: 3.0,        // meters, for stacking
      rooms: [
        Room {
          id: "r_kitchen",
          name: "Kitchen",
          ha_area_id: "kitchen",           // link to HA area
          footprint: { x: 0, z: 0, width: 4.0, depth: 3.0 },  // position + size on the floor grid
          height: 2.7,
          color: "#e8e8e8",
          devices: [
            DevicePlacement {
              entity_id: "light.kitchen_ceiling",  // link to HA entity
              position: { x: 2.0, y: 2.5, z: 1.5 }, // inside the room
              type: "light",                        // drives icon + how state is shown
            }
          ]
        }
      ]
    }
  ]
}
```

- **Levels stack on Y:** level 1 at y=0, level 2 at y=`floor_height`, level 3 at y=`2×floor_height`.
- **Rooms sit on the X–Z grid** of their floor.
- **Devices float inside their room** and are colored/animated by live state.

Start with rectangular rooms (`BoxGeometry`). If non-rectangular rooms are needed later, switch the footprint to a polygon and use `ExtrudeGeometry`.

---

## 6. Frontend structure (vanilla + Three.js)

```
frontend/
  index.html
  css/style.css
  js/
    api.js       # fetch wrappers to the Flask backend
    socket.js    # SocketIO client → live state updates
    scene.js     # Three.js scene, camera, OrbitControls, lights
    house.js     # builds floors + rooms from /api/house
    devices.js   # places device markers, binds each to an entity_id
    state.js     # applies live states to markers (on/off color, sensor value)
    ui.js        # level selector, room editor, device side-panel
    main.js      # bootstrap
```

Rendering behavior:
- **Level selector** (1 / 2 / 3): show the selected floor solid, dim/hide the others (or an "exploded" stacked view).
- **Walls** semi-transparent so you can see inside.
- **Device markers**: small sphere/sprite per entity. Lights = yellow when on, grey when off; sensors show their value on hover; switches toggle on click.
- **Click a marker** → side panel with entity name, state, and control buttons → `POST /api/control`.
- **Live updates**: SocketIO event `{entity_id, new_state}` → find the marker → update its color/label. No polling needed once the relay is in place (polling `/api/ha/states` every few seconds is an acceptable MVP shortcut).

---

## 7. The room-building workflow (what you described)

This is the editor flow — build rooms individually, then assemble:

1. **Load structure** — app fetches `/api/ha/structure`; the room editor's "link to area" dropdown is populated from the real HA areas, and the floor dropdown from HA floors.
2. **Create a room** — enter name, pick its floor/level, pick the HA area it maps to, set width × depth × height.
3. **Position it** — drag it on a 2D top-down grid of that floor (or type x/z). Saved via `POST /api/house/room`.
4. **Add devices** — entities that belong to that area are auto-listed; place them inside the room (auto-scatter first, fine-tune positions later). Saved via `POST /api/house/room/<id>/device`.
5. **Assemble** — repeat per room; the 3D view reads `/api/house` and renders the whole building.
6. **Go live** — the realtime relay lights everything up with current state.

MVP can start with just rectangular boxes and numeric sizing; the drag-to-position editor is a fast-follow.

---

## 8. Build plan / to-do list (hand this to the developer)

### Phase 0 — Setup & secrets
- [ ] Repo, `.env.example`, gitignore the real `.env`.
- [ ] Flask app skeleton, serves a blank page.
- [ ] Confirm a **freshly rotated** token + URL are in `.env`.

### Phase 1 — Prove the HA connection
- [ ] REST client: `GET /api/states` returns data with the token.
- [ ] WebSocket client: auth handshake succeeds (`auth_ok`).
- [ ] Fetch and log the four registries (floors, areas, devices, entities).
- [ ] Build `/api/ha/structure` returning the joined tree; cache it.

### Phase 2 — House model & persistence
- [ ] Define `House / Floor / Room / DevicePlacement` models.
- [ ] SQLite (or `house.json`) store.
- [ ] CRUD endpoints under `/api/house/*`.

### Phase 3 — 3D scaffold
- [ ] Three.js scene, camera, OrbitControls, lighting, a ground plane.
- [ ] Render one hard-coded box "room".

### Phase 4 — Render the house from data
- [ ] Read `/api/house`, build floors stacked on Y.
- [ ] Build rooms from footprints; semi-transparent walls.
- [ ] Level selector (1 / 2 / 3) shows/hides floors.

### Phase 5 — Devices in the model
- [ ] Read `/api/ha/states`, place a marker per placed entity.
- [ ] Color/icon by device type (light/switch/sensor).
- [ ] Click marker → side panel with entity details.

### Phase 6 — Live state
- [ ] Backend keeps the `state_changed` subscription open.
- [ ] SocketIO relay pushes changes to the browser.
- [ ] Markers update in real time. (MVP fallback: poll every 5s.)

### Phase 7 — Control
- [ ] `/api/control` → HA `call_service`.
- [ ] Toggle a light from the 3D view and see it reflect back live.

### Phase 8 — Room editor UI
- [ ] Create/edit/delete rooms; link to HA area; set size.
- [ ] Top-down drag positioning on a floor grid.
- [ ] Auto-list a room's entities and place them.

### Phase 9 — Polish
- [ ] Textures/materials, better lighting, camera presets per floor.
- [ ] Loading/error states if HA is unreachable.
- [ ] Auth on the app itself (a simple login for the web app — separate from the HA token).

---

## 9. Decisions to confirm before starting

1. **Are HA Floors set up?** If floors aren't defined in HA yet, level assignment can be manual in our model at first — but defining floors in HA is the clean path.
2. **Persistence:** SQLite (recommended) vs a single `house.json` (fine for one house/MVP)?
3. **Realtime:** proper SocketIO relay from day one, or start with polling and add the relay in Phase 6?
4. **Room shapes:** rectangles only (simpler) or arbitrary footprints (ExtrudeGeometry) later?
5. **App login:** who can open the web app? (This is a separate concern from the HA token and should exist before any public hosting.)

---

## 10. Reference

- Home Assistant WebSocket API (auth flow, registry commands, subscribe_events, call_service)
- Home Assistant REST API (`/api/states`, `/api/services/...`)
- Three.js docs (Scene, PerspectiveCamera, OrbitControls, BoxGeometry, ExtrudeGeometry, Raycaster for clicks)

*(The developer portal at developers.home-assistant.io has the full, authoritative spec for both APIs — point them there for exact field names on each registry object.)*
