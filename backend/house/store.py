"""SQLite persistence for the house model (floors, rooms, device placements).

All lengths/positions are in FEET (world unit = 1 ft). Databases created
before the feet switch stored meters; they are converted once, gated by
PRAGMA user_version (0 = meters, 1 = feet).
"""
import json
import math
import sqlite3
import threading

FEET_PER_METER = 3.28084

SCHEMA = """
CREATE TABLE IF NOT EXISTS floors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    level INTEGER NOT NULL UNIQUE,
    ha_floor_id TEXT,
    floor_height REAL NOT NULL DEFAULT 10.0,
    plan_image TEXT,
    plan_scale REAL NOT NULL DEFAULT 0.05,
    plan_x REAL NOT NULL DEFAULT 0,
    plan_z REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    floor_id INTEGER NOT NULL REFERENCES floors(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    ha_area_id TEXT,
    x REAL NOT NULL DEFAULT 0,
    z REAL NOT NULL DEFAULT 0,
    width REAL NOT NULL DEFAULT 13,
    depth REAL NOT NULL DEFAULT 10,
    height REAL NOT NULL DEFAULT 8.0,
    color TEXT NOT NULL DEFAULT '#e8e8e8',
    points TEXT
);
CREATE TABLE IF NOT EXISTS stairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    floor_id INTEGER NOT NULL REFERENCES floors(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'Stairs',
    x REAL NOT NULL DEFAULT 0,
    z REAL NOT NULL DEFAULT 0,
    width REAL NOT NULL DEFAULT 3.5,
    depth REAL NOT NULL DEFAULT 10,
    direction TEXT NOT NULL DEFAULT 'n'
);
CREATE TABLE IF NOT EXISTS placements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    entity_id TEXT NOT NULL,
    x REAL NOT NULL DEFAULT 0,
    y REAL NOT NULL DEFAULT 5.0,
    z REAL NOT NULL DEFAULT 0,
    type TEXT NOT NULL DEFAULT 'sensor',
    visible INTEGER NOT NULL DEFAULT 1,
    model_id INTEGER REFERENCES models(id) ON DELETE SET NULL,
    rot_y REAL NOT NULL DEFAULT 0,
    scale REAL NOT NULL DEFAULT 1.0
);
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    filename TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    model_id INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT '',
    x REAL NOT NULL DEFAULT 0,
    y REAL NOT NULL DEFAULT 0,
    z REAL NOT NULL DEFAULT 0,
    rot_y REAL NOT NULL DEFAULT 0,
    scale REAL NOT NULL DEFAULT 1.0
);
"""

ROOM_FIELDS = ("name", "ha_area_id", "x", "z", "width", "depth", "height",
               "color", "points")
PLACEMENT_FIELDS = ("entity_id", "x", "y", "z", "type", "visible",
                    "model_id", "rot_y", "scale")
# Standalone furniture/decor: a library model placed in a room, no HA entity.
OBJECT_FIELDS = ("name", "model_id", "x", "y", "z", "rot_y", "scale")
MODEL_FIELDS = ("name",)
# stairs.floor_id is the LOWER of the two floors they connect; they rise that
# floor's full floor_height. direction = which way they ascend on the plan.
STAIR_FIELDS = ("name", "x", "z", "width", "depth", "direction", "floor_id")
STAIR_DIRECTIONS = ("n", "s", "e", "w")

# Defaults for rooms generated from HA areas (editable afterwards). Feet.
GEN_ROOM = {"width": 16.0, "depth": 13.0, "height": 8.0, "gap": 3.0}
GEN_PALETTE = ("#8fa8bf", "#b98fbf", "#8fbf9c", "#bfae8f",
               "#bf8f8f", "#8fbfbd", "#a3bf8f", "#9a8fbf")
GEN_DOMAINS = {"light", "switch", "sensor", "binary_sensor", "climate",
               "cover", "media_player", "lock", "fan", "camera",
               "vacuum", "humidifier"}
GEN_HEIGHTS = {"light": 7.5, "camera": 7.2, "cover": 6.5, "switch": 4.0,
               "media_player": 3.0, "vacuum": 0.5}  # default 5.0


def _segments_cross(a, b, c, d):
    """True when segment a-b properly crosses segment c-d (not just touches)."""
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)
    o1, o2 = orient(a, b, c), orient(a, b, d)
    o3, o4 = orient(c, d, a), orient(c, d, b)
    return o1 != o2 and o3 != o4 and 0 not in (o1, o2, o3, o4)


def _self_intersects(pts):
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for j in range(i + 1, n):
            if (j + 1) % n == i or (i + 1) % n == j:
                continue  # adjacent segments share a vertex
            if _segments_cross(a, b, pts[j], pts[(j + 1) % n]):
                return True
    return False


def normalize_points(points):
    """Validate + normalize a room polygon (list of [x, z] pairs, feet).

    Returns (points_json, dx, dz, width, depth) where dx/dz is the bbox-min
    shift to fold into the room's x/z anchor; the JSON polygon has its bbox
    min at (0, 0) and CCW winding (shoelace > 0). Raises ValueError on
    malformed, zero-area, or self-intersecting input.
    """
    if not isinstance(points, (list, tuple)) or len(points) < 3:
        raise ValueError("polygon needs at least 3 [x, z] points")
    pts = []
    for p in points:
        ok = (isinstance(p, (list, tuple)) and len(p) == 2
              and all(isinstance(c, (int, float)) and not isinstance(c, bool)
                      and math.isfinite(c) for c in p))
        if not ok:
            raise ValueError("each point must be an [x, z] pair of finite numbers")
        pts.append((float(p[0]), float(p[1])))
    area2 = sum(x1 * z2 - x2 * z1
                for (x1, z1), (x2, z2) in zip(pts, pts[1:] + pts[:1]))
    if abs(area2) < 1e-9:
        raise ValueError("polygon has zero area")
    if area2 < 0:
        pts.reverse()
    if _self_intersects(pts):
        raise ValueError("polygon edges must not cross")
    min_x = min(p[0] for p in pts)
    min_z = min(p[1] for p in pts)
    width = round(max(p[0] for p in pts) - min_x, 4)
    depth = round(max(p[1] for p in pts) - min_z, 4)
    norm = [[round(p[0] - min_x, 4), round(p[1] - min_z, 4)] for p in pts]
    return json.dumps(norm), min_x, min_z, width, depth


class HouseStore:
    def __init__(self, db_path):
        self._lock = threading.Lock()
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.executescript(SCHEMA)
        # CREATE TABLE IF NOT EXISTS won't add columns to a pre-existing table
        for ddl in (
            "ALTER TABLE placements ADD COLUMN visible INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE rooms ADD COLUMN points TEXT",
            "ALTER TABLE floors ADD COLUMN plan_image TEXT",
            "ALTER TABLE floors ADD COLUMN plan_scale REAL NOT NULL DEFAULT 0.05",
            "ALTER TABLE floors ADD COLUMN plan_x REAL NOT NULL DEFAULT 0",
            "ALTER TABLE floors ADD COLUMN plan_z REAL NOT NULL DEFAULT 0",
            "ALTER TABLE placements ADD COLUMN model_id INTEGER"
            " REFERENCES models(id) ON DELETE SET NULL",
            "ALTER TABLE placements ADD COLUMN rot_y REAL NOT NULL DEFAULT 0",
            "ALTER TABLE placements ADD COLUMN scale REAL NOT NULL DEFAULT 1.0",
        ):
            try:
                self._db.execute(ddl)
            except sqlite3.OperationalError:
                pass  # column already exists
        self._migrate_meters_to_feet()
        self._db.commit()

    def _migrate_meters_to_feet(self):
        """user_version 0 databases stored meters; scale them to feet once.
        A brand-new DB is also version 0 but has no rows, so this is a no-op
        for it beyond stamping the version."""
        if self._db.execute("PRAGMA user_version").fetchone()[0] >= 1:
            return
        f = FEET_PER_METER
        self._db.execute(
            "UPDATE floors SET floor_height = floor_height * ?", (f,))
        self._db.execute(
            "UPDATE rooms SET x=x*?, z=z*?, width=width*?, depth=depth*?,"
            " height=height*?", (f, f, f, f, f))
        self._db.execute(
            "UPDATE placements SET x=x*?, y=y*?, z=z*?", (f, f, f))
        self._db.execute("PRAGMA user_version = 1")

    def _rows(self, sql, params=()):
        return [dict(r) for r in self._db.execute(sql, params).fetchall()]

    # ---- read -------------------------------------------------------------

    def get_house(self):
        with self._lock:
            floors = self._rows("SELECT * FROM floors ORDER BY level")
            rooms = self._rows("SELECT * FROM rooms ORDER BY id")
            placements = self._rows("SELECT * FROM placements ORDER BY id")
            stairs = self._rows("SELECT * FROM stairs ORDER BY id")
            objects = self._rows(
                "SELECT o.*, m.name AS model_name FROM objects o"
                " JOIN models m ON m.id = o.model_id ORDER BY o.id")

        rooms_by_floor = {}
        for room in rooms:
            room["footprint"] = {"x": room["x"], "z": room["z"],
                                 "width": room["width"], "depth": room["depth"],
                                 "points": json.loads(room["points"])
                                 if room.get("points") else None}
            del room["points"]  # footprint is the API surface for geometry
            room["devices"] = []
            room["objects"] = []
            rooms_by_floor.setdefault(room["floor_id"], []).append(room)
        room_by_id = {r["id"]: r for r in rooms}
        for p in placements:
            room = room_by_id.get(p["room_id"])
            if room:
                room["devices"].append({
                    "id": p["id"], "entity_id": p["entity_id"], "type": p["type"],
                    "visible": int(p["visible"]),
                    "model_id": p["model_id"], "rot_y": p["rot_y"],
                    "scale": p["scale"],
                    "position": {"x": p["x"], "y": p["y"], "z": p["z"]},
                })
        for o in objects:
            room = room_by_id.get(o["room_id"])
            if room:
                room["objects"].append({
                    "id": o["id"], "model_id": o["model_id"],
                    "model_name": o["model_name"], "name": o["name"],
                    "rot_y": o["rot_y"], "scale": o["scale"],
                    "position": {"x": o["x"], "y": o["y"], "z": o["z"]},
                })
        stairs_by_floor = {}
        for st in stairs:
            stairs_by_floor.setdefault(st["floor_id"], []).append(st)
        for floor in floors:
            floor["rooms"] = rooms_by_floor.get(floor["id"], [])
            floor["stairs"] = stairs_by_floor.get(floor["id"], [])
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

    def reconcile_floor_levels_from_ha(self, structure):
        """Set each HA-linked floor's level to the level its floor has in HA —
        HA is the source of truth for floor ordering.

        Floors not linked to HA, or whose HA floor reports no level, keep their
        current level (only shifted upward if it would collide with a level HA
        assigned). The `level` column is UNIQUE, so every floor is first parked
        at a temporary negative level before the final levels are written, to
        avoid a mid-update collision. Returns the number of floors that moved.
        """
        ha_level = {}
        for hf in structure.get("floors", []):
            lvl = hf.get("level")
            if hf.get("floor_id") is not None and lvl is not None:
                ha_level[hf["floor_id"]] = int(lvl)
        changed = 0
        with self._lock:
            floors = self._rows("SELECT id, level, ha_floor_id FROM floors")
            current = {f["id"]: f["level"] for f in floors}
            desired, priority = {}, set()
            for f in floors:
                if f["ha_floor_id"] in ha_level:
                    desired[f["id"]] = ha_level[f["ha_floor_id"]]
                    priority.add(f["id"])
                else:
                    desired[f["id"]] = f["level"]
            # Assign HA-linked floors their HA level first; others yield to the
            # next free slot if that level is already taken.
            used = {}
            for fid in sorted(desired, key=lambda i: (i not in priority, desired[i])):
                lvl = desired[fid]
                while lvl in used:
                    lvl += 1
                used[lvl] = fid
                desired[fid] = lvl
            if desired == current:
                return 0
            for f in floors:  # park at unique temp levels to dodge UNIQUE
                self._db.execute("UPDATE floors SET level=? WHERE id=?",
                                 (-1000 - f["id"], f["id"]))
            for fid, lvl in desired.items():
                self._db.execute("UPDATE floors SET level=? WHERE id=?",
                                 (lvl, fid))
                if current[fid] != lvl:
                    changed += 1
            self._db.commit()
        return changed

    def reconcile_rooms_to_ha_floors(self, structure):
        """Move each HA-linked room to the floor its area now lives on in HA.

        Rooms whose area is unassigned in HA, no longer exists in HA, or that
        aren't linked to an area at all are left where they are — we only ever
        follow an explicit area->floor assignment. Returns the number moved.
        """
        area_floor = {}
        for hf in structure.get("floors", []):
            for a in hf.get("areas", []):
                area_floor[a["area_id"]] = hf.get("floor_id")
        moved = 0
        with self._lock:
            floor_rows = self._rows("SELECT id, ha_floor_id FROM floors")
            by_ha_id = {f["ha_floor_id"]: f["id"]
                        for f in floor_rows if f["ha_floor_id"]}
            for r in self._rows("SELECT id, floor_id, ha_area_id FROM rooms"):
                if not r["ha_area_id"]:
                    continue
                target_ha_floor = area_floor.get(r["ha_area_id"])
                if not target_ha_floor:  # area gone or unassigned in HA
                    continue
                target_id = by_ha_id.get(target_ha_floor)
                if target_id and target_id != r["floor_id"]:
                    self._db.execute("UPDATE rooms SET floor_id=? WHERE id=?",
                                     (target_id, r["id"]))
                    moved += 1
            self._db.commit()
        return moved

    def prune_stale_ha_floors(self, ha_floor_ids):
        """Delete floors linked to an HA floor that no longer exists in HA, but
        only when they hold no rooms — never silently drops user geometry."""
        removed = 0
        with self._lock:
            for f in self._rows("SELECT id, ha_floor_id FROM floors"):
                if f["ha_floor_id"] and f["ha_floor_id"] not in ha_floor_ids:
                    has_room = self._db.execute(
                        "SELECT 1 FROM rooms WHERE floor_id=? LIMIT 1",
                        (f["id"],)).fetchone()
                    if not has_room:
                        self._db.execute("DELETE FROM floors WHERE id=?",
                                         (f["id"],))
                        removed += 1
            self._db.commit()
        return removed

    def sync_from_ha(self, structure, ha_floors):
        """Full one-shot reconcile between HA and the local layout, idempotent:
          1. add floor rows for new HA floors
          2. re-level HA-linked floors to match their HA floor's level
          3. move rooms to match their HA area's current floor
          4. add rooms/devices for HA areas not in the layout yet
          5. drop HA-linked floors that no longer exist in HA and hold no rooms

        Room geometry/colors and device positions are never touched."""
        floors_added = self.sync_floors_from_ha(ha_floors)
        levels_changed = self.reconcile_floor_levels_from_ha(structure)
        rooms_moved = self.reconcile_rooms_to_ha_floors(structure)
        generated = self.generate_from_ha(structure)
        floors_removed = self.prune_stale_ha_floors(
            {f["floor_id"] for f in ha_floors})
        return {
            "floors_added": floors_added,
            "levels_changed": levels_changed,
            "rooms_moved": rooms_moved,
            "rooms_added": generated["rooms"],
            "devices_added": generated["devices"],
            "floors_removed": floors_removed,
        }

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
        margin = 2.0
        cols = max(1, math.ceil(math.sqrt(len(entities))))
        n_rows = math.ceil(len(entities) / cols)
        cell_w = (GEN_ROOM["width"] - 2 * margin) / cols
        cell_d = (GEN_ROOM["depth"] - 2 * margin) / n_rows
        for i, e in enumerate(entities):
            y = min(GEN_HEIGHTS.get(e["domain"], 5.0),
                    GEN_ROOM["height"] - 1.0)
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
                 float(data.get("floor_height", 10.0))))
            self._db.commit()
            return cur.lastrowid

    def update_floor(self, floor_id, data):
        allowed = {k: data[k] for k in ("name", "level", "ha_floor_id", "floor_height",
                                        "plan_scale", "plan_x", "plan_z")
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

    def get_floor(self, floor_id):
        with self._lock:
            row = self._db.execute("SELECT * FROM floors WHERE id=?",
                                   (floor_id,)).fetchone()
            return dict(row) if row else None

    def set_floor_plan_image(self, floor_id, filename):
        with self._lock:
            cur = self._db.execute("UPDATE floors SET plan_image=? WHERE id=?",
                                   (filename, floor_id))
            self._db.commit()
            return cur.rowcount > 0

    # ---- rooms ------------------------------------------------------------

    def create_room(self, data):
        footprint = data.get("footprint") or {}
        x = float(footprint.get("x", data.get("x", 0)))
        z = float(footprint.get("z", data.get("z", 0)))
        width = float(footprint.get("width", data.get("width", 13)))
        depth = float(footprint.get("depth", data.get("depth", 10)))
        points = footprint.get("points", data.get("points"))
        points_json = None
        if points is not None:
            points_json, dx, dz, width, depth = normalize_points(points)
            x += dx
            z += dz
        with self._lock:
            cur = self._db.execute(
                "INSERT INTO rooms (floor_id, name, ha_area_id, x, z, width, depth,"
                " height, color, points) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (int(data["floor_id"]), data["name"], data.get("ha_area_id"),
                 x, z, width, depth,
                 float(data.get("height", 8.0)),
                 data.get("color", "#e8e8e8"),
                 points_json))
            self._db.commit()
            return cur.lastrowid

    def update_room(self, room_id, data):
        flat = dict(data)
        for k, v in (data.get("footprint") or {}).items():
            flat[k] = v
        with self._lock:
            if flat.get("points") is not None:
                # normalize: bbox min folds into the anchor, width/depth follow
                points_json, dx, dz, w, d = normalize_points(flat["points"])
                row = self._db.execute("SELECT x, z FROM rooms WHERE id=?",
                                       (room_id,)).fetchone()
                if row is None:
                    return False
                flat["x"] = (float(flat["x"]) if "x" in flat else row["x"]) + dx
                flat["z"] = (float(flat["z"]) if "z" in flat else row["z"]) + dz
                flat["width"], flat["depth"] = w, d
                flat["points"] = points_json
            allowed = {k: flat[k] for k in (*ROOM_FIELDS, "floor_id") if k in flat}
            if not allowed:
                return False
            sets = ", ".join(f"{k}=?" for k in allowed)
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

    # ---- stairs ------------------------------------------------------------

    def create_stairs(self, data):
        direction = data.get("direction", "n")
        if direction not in STAIR_DIRECTIONS:
            raise ValueError("direction must be one of n/s/e/w")
        with self._lock:
            if not self._db.execute("SELECT 1 FROM floors WHERE id=?",
                                    (int(data["floor_id"]),)).fetchone():
                return None
            cur = self._db.execute(
                "INSERT INTO stairs (floor_id, name, x, z, width, depth,"
                " direction) VALUES (?,?,?,?,?,?,?)",
                (int(data["floor_id"]), data.get("name") or "Stairs",
                 float(data.get("x", 0)), float(data.get("z", 0)),
                 float(data.get("width", 3.5)), float(data.get("depth", 10)),
                 direction))
            self._db.commit()
            return cur.lastrowid

    def update_stairs(self, stair_id, data):
        if "direction" in data and data["direction"] not in STAIR_DIRECTIONS:
            raise ValueError("direction must be one of n/s/e/w")
        allowed = {k: data[k] for k in STAIR_FIELDS if k in data}
        if not allowed:
            return False
        sets = ", ".join(f"{k}=?" for k in allowed)
        with self._lock:
            cur = self._db.execute(
                f"UPDATE stairs SET {sets} WHERE id=?",
                (*allowed.values(), stair_id))
            self._db.commit()
            return cur.rowcount > 0

    def delete_stairs(self, stair_id):
        with self._lock:
            cur = self._db.execute("DELETE FROM stairs WHERE id=?", (stair_id,))
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
                 float(pos.get("y", data.get("y", 5.0))),
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
        if "visible" in allowed:
            allowed["visible"] = int(bool(allowed["visible"]))
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

    # ---- model library -------------------------------------------------------

    def list_models(self):
        with self._lock:
            return self._rows(
                "SELECT m.*,"
                " (SELECT COUNT(*) FROM placements WHERE model_id = m.id)"
                "   AS placement_count,"
                " (SELECT COUNT(*) FROM objects WHERE model_id = m.id)"
                "   AS object_count"
                " FROM models m ORDER BY m.name COLLATE NOCASE")

    def get_model(self, model_id):
        with self._lock:
            row = self._db.execute("SELECT * FROM models WHERE id=?",
                                   (model_id,)).fetchone()
            return dict(row) if row else None

    def create_model(self, name):
        with self._lock:
            cur = self._db.execute("INSERT INTO models (name) VALUES (?)",
                                   (name,))
            self._db.commit()
            return cur.lastrowid

    def set_model_filename(self, model_id, filename):
        with self._lock:
            self._db.execute("UPDATE models SET filename=? WHERE id=?",
                             (filename, model_id))
            self._db.commit()

    def update_model(self, model_id, data):
        allowed = {k: data[k] for k in MODEL_FIELDS if k in data}
        if not allowed:
            return False
        sets = ", ".join(f"{k}=?" for k in allowed)
        with self._lock:
            cur = self._db.execute(f"UPDATE models SET {sets} WHERE id=?",
                                   (*allowed.values(), model_id))
            self._db.commit()
            return cur.rowcount > 0

    def delete_model(self, model_id):
        """Delete a model row; FKs revert placements (SET NULL) and remove
        objects (CASCADE). Returns the deleted row (for file cleanup) or None."""
        with self._lock:
            row = self._db.execute("SELECT * FROM models WHERE id=?",
                                   (model_id,)).fetchone()
            if not row:
                return None
            self._db.execute("DELETE FROM models WHERE id=?", (model_id,))
            self._db.commit()
            return dict(row)

    # ---- objects (standalone furniture/decor) --------------------------------

    def add_object(self, room_id, data):
        pos = data.get("position") or {}
        with self._lock:
            if not self._db.execute("SELECT 1 FROM rooms WHERE id=?",
                                    (room_id,)).fetchone():
                return None
            cur = self._db.execute(
                "INSERT INTO objects (room_id, model_id, name, x, y, z,"
                " rot_y, scale) VALUES (?,?,?,?,?,?,?,?)",
                (room_id, int(data["model_id"]), data.get("name") or "",
                 float(pos.get("x", data.get("x", 0))),
                 float(pos.get("y", data.get("y", 0))),
                 float(pos.get("z", data.get("z", 0))),
                 float(data.get("rot_y", 0)),
                 float(data.get("scale", 1.0))))
            self._db.commit()
            return cur.lastrowid

    def update_object(self, object_id, data):
        flat = dict(data)
        for k, v in (data.get("position") or {}).items():
            flat[k] = v
        allowed = {k: flat[k] for k in OBJECT_FIELDS if k in flat}
        if not allowed:
            return False
        sets = ", ".join(f"{k}=?" for k in allowed)
        with self._lock:
            cur = self._db.execute(f"UPDATE objects SET {sets} WHERE id=?",
                                   (*allowed.values(), object_id))
            self._db.commit()
            return cur.rowcount > 0

    def delete_object(self, object_id):
        with self._lock:
            cur = self._db.execute("DELETE FROM objects WHERE id=?",
                                   (object_id,))
            self._db.commit()
            return cur.rowcount > 0
