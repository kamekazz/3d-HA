"""SQLite persistence for the house model (floors, rooms, device placements)."""
import math
import sqlite3
import threading

SCHEMA = """
CREATE TABLE IF NOT EXISTS floors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    level INTEGER NOT NULL UNIQUE,
    ha_floor_id TEXT,
    floor_height REAL NOT NULL DEFAULT 3.0
);
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    floor_id INTEGER NOT NULL REFERENCES floors(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    ha_area_id TEXT,
    x REAL NOT NULL DEFAULT 0,
    z REAL NOT NULL DEFAULT 0,
    width REAL NOT NULL DEFAULT 4,
    depth REAL NOT NULL DEFAULT 3,
    height REAL NOT NULL DEFAULT 2.7,
    color TEXT NOT NULL DEFAULT '#e8e8e8'
);
CREATE TABLE IF NOT EXISTS placements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    entity_id TEXT NOT NULL,
    x REAL NOT NULL DEFAULT 0,
    y REAL NOT NULL DEFAULT 1.5,
    z REAL NOT NULL DEFAULT 0,
    type TEXT NOT NULL DEFAULT 'sensor'
);
"""

ROOM_FIELDS = ("name", "ha_area_id", "x", "z", "width", "depth", "height", "color")
PLACEMENT_FIELDS = ("entity_id", "x", "y", "z", "type")

# Defaults for rooms generated from HA areas (editable afterwards).
GEN_ROOM = {"width": 5.0, "depth": 4.0, "height": 2.7, "gap": 1.0}
GEN_PALETTE = ("#8fa8bf", "#b98fbf", "#8fbf9c", "#bfae8f",
               "#bf8f8f", "#8fbfbd", "#a3bf8f", "#9a8fbf")
GEN_DOMAINS = {"light", "switch", "sensor", "binary_sensor", "climate",
               "cover", "media_player", "lock", "fan", "camera",
               "vacuum", "humidifier"}
GEN_HEIGHTS = {"light": 2.3, "camera": 2.2, "cover": 2.0, "switch": 1.2,
               "media_player": 0.9, "vacuum": 0.15}  # default 1.5


class HouseStore:
    def __init__(self, db_path):
        self._lock = threading.Lock()
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.executescript(SCHEMA)
        self._db.commit()

    def _rows(self, sql, params=()):
        return [dict(r) for r in self._db.execute(sql, params).fetchall()]

    # ---- read -------------------------------------------------------------

    def get_house(self):
        with self._lock:
            floors = self._rows("SELECT * FROM floors ORDER BY level")
            rooms = self._rows("SELECT * FROM rooms ORDER BY id")
            placements = self._rows("SELECT * FROM placements ORDER BY id")

        rooms_by_floor = {}
        for room in rooms:
            room["footprint"] = {"x": room["x"], "z": room["z"],
                                 "width": room["width"], "depth": room["depth"]}
            room["devices"] = []
            rooms_by_floor.setdefault(room["floor_id"], []).append(room)
        room_by_id = {r["id"]: r for r in rooms}
        for p in placements:
            room = room_by_id.get(p["room_id"])
            if room:
                room["devices"].append({
                    "id": p["id"], "entity_id": p["entity_id"], "type": p["type"],
                    "position": {"x": p["x"], "y": p["y"], "z": p["z"]},
                })
        for floor in floors:
            floor["rooms"] = rooms_by_floor.get(floor["id"], [])
        return {"floors": floors}

    def has_floors(self):
        with self._lock:
            return self._db.execute("SELECT COUNT(*) FROM floors").fetchone()[0] > 0

    def has_rooms(self):
        with self._lock:
            return self._db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] > 0

    # ---- floors -----------------------------------------------------------

    def sync_floors_from_ha(self, ha_floors):
        """Create a floor row for each HA floor that isn't linked yet."""
        created = 0
        with self._lock:
            existing = {r["ha_floor_id"] for r in
                        self._rows("SELECT ha_floor_id FROM floors")}
            used_levels = {r["level"] for r in self._rows("SELECT level FROM floors")}

            def next_level():
                lvl = 1
                while lvl in used_levels:
                    lvl += 1
                return lvl

            def sort_key(f):
                lvl = f.get("level")
                return (lvl is None, lvl if lvl is not None else 0)

            for f in sorted(ha_floors, key=sort_key):
                if f["floor_id"] in existing:
                    continue
                level = f.get("level")
                if level is None or level in used_levels:
                    level = next_level()
                used_levels.add(level)
                self._db.execute(
                    "INSERT INTO floors (name, level, ha_floor_id) VALUES (?,?,?)",
                    (f.get("name") or f["floor_id"], level, f["floor_id"]))
                created += 1
            self._db.commit()
        return created

    def prune_unlinked_empty_floors(self):
        """Drop floors that aren't linked to HA and hold no rooms (e.g. the
        'Ground floor' seeded before HA was configured), as long as at least
        one HA-linked floor exists."""
        with self._lock:
            cur = self._db.execute(
                "DELETE FROM floors WHERE ha_floor_id IS NULL "
                "AND id NOT IN (SELECT DISTINCT floor_id FROM rooms) "
                "AND EXISTS (SELECT 1 FROM floors WHERE ha_floor_id IS NOT NULL)")
            self._db.commit()
            return cur.rowcount

    def generate_from_ha(self, structure):
        """Create a room for each HA area that isn't linked yet, laid out on a
        grid per floor, and place the area's entities inside it.

        Idempotent on areas/entities already in the DB, so user edits survive
        re-runs. Areas whose HA floor isn't known land on the lowest floor.
        """
        w, d, gap = GEN_ROOM["width"], GEN_ROOM["depth"], GEN_ROOM["gap"]
        created_rooms = created_devices = 0
        with self._lock:
            floors = self._rows("SELECT * FROM floors ORDER BY level")
            if not floors:
                return {"rooms": 0, "devices": 0}
            by_ha_id = {f["ha_floor_id"]: f for f in floors if f["ha_floor_id"]}
            rooms = self._rows("SELECT * FROM rooms")
            linked = {r["ha_area_id"] for r in rooms if r["ha_area_id"]}
            placed = {r["entity_id"] for r in
                      self._rows("SELECT entity_id FROM placements")}

            # group the not-yet-linked HA areas by the floor row they belong to
            new_by_floor = {}
            for ha_floor in structure.get("floors", []):
                target = by_ha_id.get(ha_floor.get("floor_id"), floors[0])
                for area in ha_floor.get("areas", []):
                    if area["area_id"] in linked:
                        continue
                    new_by_floor.setdefault(target["id"], []).append(area)

            color_i = len(rooms)
            for floor_id, areas in new_by_floor.items():
                existing = [r for r in rooms if r["floor_id"] == floor_id]
                start_x = max((r["x"] + r["width"] for r in existing), default=0)
                if existing:
                    start_x += gap
                cols = max(1, math.ceil(math.sqrt(len(areas))))
                for i, area in enumerate(areas):
                    cur = self._db.execute(
                        "INSERT INTO rooms (floor_id, name, ha_area_id, x, z,"
                        " width, depth, height, color) VALUES (?,?,?,?,?,?,?,?,?)",
                        (floor_id, area.get("name") or area["area_id"],
                         area["area_id"],
                         start_x + (i % cols) * (w + gap),
                         (i // cols) * (d + gap),
                         w, d, GEN_ROOM["height"],
                         GEN_PALETTE[color_i % len(GEN_PALETTE)]))
                    color_i += 1
                    created_rooms += 1
                    created_devices += self._generate_placements(
                        cur.lastrowid, area, placed)
            self._db.commit()
        return {"rooms": created_rooms, "devices": created_devices}

    def _generate_placements(self, room_id, area, placed):
        """Spread an area's entities on a grid inside its generated room."""
        entities = [e for e in area.get("entities", [])
                    if not e.get("hidden") and not e.get("category")
                    and e.get("domain") in GEN_DOMAINS
                    and e["entity_id"] not in placed]
        # One marker per device per domain: LED strips and the like expose
        # dozens of "segment" sub-entities; keep the main entity, skip the rest.
        entities.sort(key=lambda e: ("_segment_" in e["entity_id"], e["entity_id"]))
        seen, picked = set(), []
        for e in entities:
            key = (e.get("device_id"), e["domain"])
            if e.get("device_id") and key in seen:
                continue
            seen.add(key)
            picked.append(e)
        entities = picked
        if not entities:
            return 0
        margin = 0.6
        cols = max(1, math.ceil(math.sqrt(len(entities))))
        n_rows = math.ceil(len(entities) / cols)
        cell_w = (GEN_ROOM["width"] - 2 * margin) / cols
        cell_d = (GEN_ROOM["depth"] - 2 * margin) / n_rows
        for i, e in enumerate(entities):
            y = min(GEN_HEIGHTS.get(e["domain"], 1.5),
                    GEN_ROOM["height"] - 0.3)
            self._db.execute(
                "INSERT INTO placements (room_id, entity_id, x, y, z, type) "
                "VALUES (?,?,?,?,?,?)",
                (room_id, e["entity_id"],
                 round(margin + (i % cols + 0.5) * cell_w, 2), y,
                 round(margin + (i // cols + 0.5) * cell_d, 2),
                 e["domain"]))
            placed.add(e["entity_id"])
        return len(entities)

    def create_floor(self, data):
        with self._lock:
            cur = self._db.execute(
                "INSERT INTO floors (name, level, ha_floor_id, floor_height) "
                "VALUES (?,?,?,?)",
                (data["name"], int(data["level"]), data.get("ha_floor_id"),
                 float(data.get("floor_height", 3.0))))
            self._db.commit()
            return cur.lastrowid

    def update_floor(self, floor_id, data):
        allowed = {k: data[k] for k in ("name", "level", "ha_floor_id", "floor_height")
                   if k in data}
        if not allowed:
            return False
        sets = ", ".join(f"{k}=?" for k in allowed)
        with self._lock:
            cur = self._db.execute(
                f"UPDATE floors SET {sets} WHERE id=?",
                (*allowed.values(), floor_id))
            self._db.commit()
            return cur.rowcount > 0

    # ---- rooms ------------------------------------------------------------

    def create_room(self, data):
        footprint = data.get("footprint") or {}
        with self._lock:
            cur = self._db.execute(
                "INSERT INTO rooms (floor_id, name, ha_area_id, x, z, width, depth,"
                " height, color) VALUES (?,?,?,?,?,?,?,?,?)",
                (int(data["floor_id"]), data["name"], data.get("ha_area_id"),
                 float(footprint.get("x", data.get("x", 0))),
                 float(footprint.get("z", data.get("z", 0))),
                 float(footprint.get("width", data.get("width", 4))),
                 float(footprint.get("depth", data.get("depth", 3))),
                 float(data.get("height", 2.7)),
                 data.get("color", "#e8e8e8")))
            self._db.commit()
            return cur.lastrowid

    def update_room(self, room_id, data):
        flat = dict(data)
        for k, v in (data.get("footprint") or {}).items():
            flat[k] = v
        allowed = {k: flat[k] for k in (*ROOM_FIELDS, "floor_id") if k in flat}
        if not allowed:
            return False
        sets = ", ".join(f"{k}=?" for k in allowed)
        with self._lock:
            cur = self._db.execute(
                f"UPDATE rooms SET {sets} WHERE id=?",
                (*allowed.values(), room_id))
            self._db.commit()
            return cur.rowcount > 0

    def delete_room(self, room_id):
        with self._lock:
            cur = self._db.execute("DELETE FROM rooms WHERE id=?", (room_id,))
            self._db.commit()
            return cur.rowcount > 0

    # ---- device placements -------------------------------------------------

    def add_placement(self, room_id, data):
        pos = data.get("position") or {}
        with self._lock:
            if not self._db.execute("SELECT 1 FROM rooms WHERE id=?",
                                    (room_id,)).fetchone():
                return None
            cur = self._db.execute(
                "INSERT INTO placements (room_id, entity_id, x, y, z, type) "
                "VALUES (?,?,?,?,?,?)",
                (room_id, data["entity_id"],
                 float(pos.get("x", data.get("x", 0))),
                 float(pos.get("y", data.get("y", 1.5))),
                 float(pos.get("z", data.get("z", 0))),
                 data.get("type") or data["entity_id"].split(".", 1)[0]))
            self._db.commit()
            return cur.lastrowid

    def update_placement(self, placement_id, data):
        flat = dict(data)
        for k, v in (data.get("position") or {}).items():
            flat[k] = v
        allowed = {k: flat[k] for k in PLACEMENT_FIELDS if k in flat}
        if not allowed:
            return False
        sets = ", ".join(f"{k}=?" for k in allowed)
        with self._lock:
            cur = self._db.execute(
                f"UPDATE placements SET {sets} WHERE id=?",
                (*allowed.values(), placement_id))
            self._db.commit()
            return cur.rowcount > 0

    def delete_placement(self, placement_id):
        with self._lock:
            cur = self._db.execute("DELETE FROM placements WHERE id=?",
                                   (placement_id,))
            self._db.commit()
            return cur.rowcount > 0
