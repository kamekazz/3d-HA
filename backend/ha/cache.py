"""Thread-safe in-memory cache of the HA floor/area/device/entity tree + states."""
import threading
from collections import defaultdict


class HACache:
    def __init__(self):
        self._lock = threading.Lock()
        self._floors = []
        self._areas = []
        self._devices = []
        self._entities = []
        self._states = {}
        self.ready = False

    def set_registries(self, floors, areas, devices, entities):
        with self._lock:
            self._floors = floors or []
            self._areas = areas or []
            self._devices = devices or []
            self._entities = entities or []
            self.ready = True

    def set_states(self, states):
        with self._lock:
            self._states = {s["entity_id"]: s for s in (states or [])}

    def update_state(self, entity_id, new_state):
        with self._lock:
            if new_state is None:
                self._states.pop(entity_id, None)
            else:
                self._states[entity_id] = new_state

    def states(self):
        with self._lock:
            return list(self._states.values())

    def has_states(self):
        with self._lock:
            return bool(self._states)

    def ha_floors(self):
        with self._lock:
            return list(self._floors)

    def area_picture(self, area_id):
        """Raw HA-relative picture path for one area, or None."""
        with self._lock:
            for a in self._areas:
                if a.get("area_id") == area_id:
                    return a.get("picture")
            return None

    def structure(self):
        """Join the four registries into floors -> areas -> devices/entities."""
        with self._lock:
            floors = list(self._floors)
            areas = list(self._areas)
            devices = list(self._devices)
            entities = [e for e in self._entities if not e.get("disabled_by")]

        device_by_id = {d["id"]: d for d in devices}
        entities_by_area = defaultdict(list)
        for e in entities:
            area_id = e.get("area_id")
            if not area_id and e.get("device_id"):
                area_id = device_by_id.get(e["device_id"], {}).get("area_id")
            entities_by_area[area_id].append({
                "entity_id": e["entity_id"],
                "name": e.get("name") or e.get("original_name") or e["entity_id"],
                "domain": e["entity_id"].split(".", 1)[0],
                "device_id": e.get("device_id"),
                "hidden": bool(e.get("hidden_by")),
                # 'diagnostic'/'config' — HA hides these from dashboards too
                "category": e.get("entity_category"),
            })

        devices_by_area = defaultdict(list)
        for d in devices:
            if d.get("area_id"):
                devices_by_area[d["area_id"]].append({
                    "id": d["id"],
                    "name": d.get("name_by_user") or d.get("name"),
                })

        def area_node(a):
            return {
                "area_id": a["area_id"],
                "name": a.get("name"),
                "floor_id": a.get("floor_id"),
                "picture": a.get("picture"),
                "devices": devices_by_area.get(a["area_id"], []),
                "entities": sorted(entities_by_area.get(a["area_id"], []),
                                   key=lambda x: (x["domain"], x["name"])),
            }

        areas_by_floor = defaultdict(list)
        for a in areas:
            areas_by_floor[a.get("floor_id")].append(area_node(a))

        def floor_sort_key(f):
            lvl = f.get("level")
            return (lvl is None, lvl if lvl is not None else 0, f.get("name") or "")

        tree = []
        for f in sorted(floors, key=floor_sort_key):
            tree.append({
                "floor_id": f["floor_id"],
                "name": f.get("name"),
                "level": f.get("level"),
                "areas": areas_by_floor.pop(f["floor_id"], []),
            })
        leftover = areas_by_floor.pop(None, [])
        for remaining in areas_by_floor.values():
            leftover.extend(remaining)
        if leftover:
            tree.append({"floor_id": None, "name": "Unassigned", "level": None,
                         "areas": leftover})
        return {"floors": tree}
