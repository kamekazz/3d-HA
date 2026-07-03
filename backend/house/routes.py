"""CRUD for our own 3D layout data (/api/house/*)."""
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("house", __name__, url_prefix="/api/house")


def _store():
    return current_app.extensions["house_store"]


@bp.get("")
def get_house():
    store = _store()
    # Keep our floors in sync with HA's floor registry (idempotent: only adds
    # HA floors we haven't linked yet). Without HA, seed a default floor so
    # the editor still works.
    cache = current_app.extensions["ha_cache"]
    if cache.ready and cache.ha_floors():
        store.sync_floors_from_ha(cache.ha_floors())
        # First boot with HA data: pre-generate rooms from HA areas and place
        # their entities, so the scene isn't empty. Never runs again once any
        # room exists — user edits win. Also drop the placeholder floor that
        # was seeded while HA was still unconfigured.
        if not store.has_rooms():
            store.prune_unlinked_empty_floors()
            store.generate_from_ha(cache.structure())
    elif not store.has_floors():
        store.create_floor({"name": "Ground floor", "level": 1})
    return jsonify(store.get_house())


@bp.post("/generate")
def generate_from_ha():
    """Re-generate on demand: adds floors/rooms/devices HA knows about that we
    don't have yet. Existing rooms and placements are never touched."""
    cache = current_app.extensions["ha_cache"]
    if not cache.ready:
        return jsonify({"error": "Home Assistant structure not available yet"}), 503
    store = _store()
    store.sync_floors_from_ha(cache.ha_floors())
    result = store.generate_from_ha(cache.structure())
    return jsonify(result)


@bp.post("/floor")
def create_floor():
    data = request.get_json(force=True)
    if not data.get("name") or data.get("level") is None:
        return jsonify({"error": "name and level are required"}), 400
    try:
        floor_id = _store().create_floor(data)
    except Exception as exc:  # e.g. duplicate level
        return jsonify({"error": str(exc)}), 400
    return jsonify({"id": floor_id}), 201


@bp.patch("/floor/<int:floor_id>")
def update_floor(floor_id):
    if not _store().update_floor(floor_id, request.get_json(force=True)):
        return jsonify({"error": "floor not found or nothing to update"}), 404
    return jsonify({"ok": True})


@bp.post("/room")
def create_room():
    data = request.get_json(force=True)
    if not data.get("name") or data.get("floor_id") is None:
        return jsonify({"error": "name and floor_id are required"}), 400
    room_id = _store().create_room(data)
    return jsonify({"id": room_id}), 201


@bp.patch("/room/<int:room_id>")
def update_room(room_id):
    if not _store().update_room(room_id, request.get_json(force=True)):
        return jsonify({"error": "room not found or nothing to update"}), 404
    return jsonify({"ok": True})


@bp.delete("/room/<int:room_id>")
def delete_room(room_id):
    if not _store().delete_room(room_id):
        return jsonify({"error": "room not found"}), 404
    return jsonify({"ok": True})


@bp.post("/room/<int:room_id>/device")
def place_device(room_id):
    data = request.get_json(force=True)
    if not data.get("entity_id"):
        return jsonify({"error": "entity_id is required"}), 400
    placement_id = _store().add_placement(room_id, data)
    if placement_id is None:
        return jsonify({"error": "room not found"}), 404
    return jsonify({"id": placement_id}), 201


@bp.patch("/device/<int:placement_id>")
def update_placement(placement_id):
    if not _store().update_placement(placement_id, request.get_json(force=True)):
        return jsonify({"error": "placement not found or nothing to update"}), 404
    return jsonify({"ok": True})


@bp.delete("/device/<int:placement_id>")
def delete_placement(placement_id):
    if not _store().delete_placement(placement_id):
        return jsonify({"error": "placement not found"}), 404
    return jsonify({"ok": True})
