"""CRUD for our own 3D layout data (/api/house/*)."""
import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory

bp = Blueprint("house", __name__, url_prefix="/api/house")

# floor-plan tracing images (served back verbatim — no SVG, to rule out
# stored XSS from an uploaded file)
PLAN_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def _plans_dir():
    return os.path.join(current_app.root_path, "uploads", "plans")


def _remove_plan_files(floor_id):
    for ext in PLAN_EXTENSIONS:
        path = os.path.join(_plans_dir(), f"floor_{floor_id}{ext}")
        if os.path.exists(path):
            os.remove(path)


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


@bp.post("/sync")
def sync_house():
    """Reconcile the whole layout with HA in one shot: add new floors, move
    rooms to the floor their HA area now lives on, add rooms/devices for new
    areas, and drop empty floors that were deleted in HA. Existing room
    geometry and device positions are preserved."""
    cache = current_app.extensions["ha_cache"]
    if not cache.ready or not cache.ha_floors():
        return jsonify({"error": "Home Assistant structure not available yet"}), 503
    result = _store().sync_from_ha(cache.structure(), cache.ha_floors())
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


@bp.post("/floor/<int:floor_id>/plan")
def upload_floor_plan(floor_id):
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "no file uploaded"}), 400
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in PLAN_EXTENSIONS:
        return jsonify({"error": f"file type {ext or '?'} not allowed "
                                 "(png, jpg, webp)"}), 400
    if not _store().get_floor(floor_id):
        return jsonify({"error": "floor not found"}), 404
    os.makedirs(_plans_dir(), exist_ok=True)
    _remove_plan_files(floor_id)  # drop a previous image with another ext
    filename = f"floor_{floor_id}{ext}"
    file.save(os.path.join(_plans_dir(), filename))
    _store().set_floor_plan_image(floor_id, filename)
    return jsonify({"ok": True, "plan_image": filename})


@bp.get("/plan/<int:floor_id>")
def get_floor_plan(floor_id):
    floor = _store().get_floor(floor_id)
    if not floor or not floor.get("plan_image"):
        return jsonify({"error": "no plan image for this floor"}), 404
    return send_from_directory(_plans_dir(), floor["plan_image"])


@bp.delete("/floor/<int:floor_id>/plan")
def delete_floor_plan(floor_id):
    if not _store().get_floor(floor_id):
        return jsonify({"error": "floor not found"}), 404
    _remove_plan_files(floor_id)
    _store().set_floor_plan_image(floor_id, None)
    return jsonify({"ok": True})


@bp.post("/room")
def create_room():
    data = request.get_json(force=True)
    if not data.get("name") or data.get("floor_id") is None:
        return jsonify({"error": "name and floor_id are required"}), 400
    try:
        room_id = _store().create_room(data)
    except ValueError as exc:  # invalid polygon
        return jsonify({"error": str(exc)}), 400
    return jsonify({"id": room_id}), 201


@bp.patch("/room/<int:room_id>")
def update_room(room_id):
    try:
        updated = _store().update_room(room_id, request.get_json(force=True))
    except ValueError as exc:  # invalid polygon
        return jsonify({"error": str(exc)}), 400
    if not updated:
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
