"""CRUD for our own 3D layout data (/api/house/*)."""
import functools
import os
import sqlite3

from flask import Blueprint, current_app, jsonify, request, send_from_directory

bp = Blueprint("house", __name__, url_prefix="/api/house")

# floor-plan tracing images (served back verbatim — no SVG, to rule out
# stored XSS from an uploaded file)
PLAN_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
# 3D model library files: parsed by three.js, never rendered as a document,
# so serving them verbatim is safe. .glb strongly preferred (.gltf must have
# embedded buffers/textures — external references can't resolve).
MODEL_EXTENSIONS = {".glb", ".gltf"}


def _plans_dir():
    return os.path.join(current_app.root_path, "uploads", "plans")


def _models_dir():
    return os.path.join(current_app.root_path, "uploads", "models")


def _remove_plan_files(floor_id):
    for ext in PLAN_EXTENSIONS:
        path = os.path.join(_plans_dir(), f"floor_{floor_id}{ext}")
        if os.path.exists(path):
            os.remove(path)


def _store():
    return current_app.extensions["house_store"]


def _history():
    return current_app.extensions["house_history"]


def undoable(view):
    """Snapshot the layout before a mutating endpoint; record it only if the
    call succeeded AND actually changed something, so no-op PATCHes never
    burn an undo step. Goes between the route decorator and the function."""
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        store = _store()
        before = store.export_snapshot()
        resp = view(*args, **kwargs)
        status = resp[1] if isinstance(resp, tuple) else resp.status_code
        if status < 400 and store.export_snapshot() != before:
            _history().record(before)
        return resp
    return wrapper


@bp.post("/undo")
def undo_house():
    store, hist = _store(), _history()
    snap = hist.undo(store.export_snapshot())
    if snap is None:
        return jsonify({"ok": False, **hist.counts()})
    try:
        store.restore_snapshot(snap)
    except Exception as exc:
        hist.restore_failed(snap, was_undo=True)
        return jsonify({"error": str(exc)}), 500
    return jsonify({"ok": True, **hist.counts()})


@bp.post("/redo")
def redo_house():
    store, hist = _store(), _history()
    snap = hist.redo(store.export_snapshot())
    if snap is None:
        return jsonify({"ok": False, **hist.counts()})
    try:
        store.restore_snapshot(snap)
    except Exception as exc:
        hist.restore_failed(snap, was_undo=False)
        return jsonify({"error": str(exc)}), 500
    return jsonify({"ok": True, **hist.counts()})


@bp.get("/history")
def history_counts():
    return jsonify(_history().counts())


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
@undoable
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
@undoable
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
@undoable
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
@undoable
def update_floor(floor_id):
    if not _store().update_floor(floor_id, request.get_json(force=True)):
        return jsonify({"error": "floor not found or nothing to update"}), 404
    return jsonify({"ok": True})


@bp.post("/floor/<int:floor_id>/plan")
@undoable
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
@undoable
def delete_floor_plan(floor_id):
    if not _store().get_floor(floor_id):
        return jsonify({"error": "floor not found"}), 404
    # Only null the pointer — keep the file on disk so undo can bring the
    # image back. upload_floor_plan removes stale files on the next upload.
    _store().set_floor_plan_image(floor_id, None)
    return jsonify({"ok": True})


@bp.post("/room")
@undoable
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
@undoable
def update_room(room_id):
    try:
        updated = _store().update_room(room_id, request.get_json(force=True))
    except ValueError as exc:  # invalid polygon
        return jsonify({"error": str(exc)}), 400
    if not updated:
        return jsonify({"error": "room not found or nothing to update"}), 404
    return jsonify({"ok": True})


@bp.delete("/room/<int:room_id>")
@undoable
def delete_room(room_id):
    if not _store().delete_room(room_id):
        return jsonify({"error": "room not found"}), 404
    return jsonify({"ok": True})


@bp.post("/stairs")
@undoable
def create_stairs():
    data = request.get_json(force=True)
    if data.get("floor_id") is None:
        return jsonify({"error": "floor_id (the lower floor) is required"}), 400
    try:
        stair_id = _store().create_stairs(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if stair_id is None:
        return jsonify({"error": "floor not found"}), 404
    return jsonify({"id": stair_id}), 201


@bp.patch("/stairs/<int:stair_id>")
@undoable
def update_stairs(stair_id):
    try:
        updated = _store().update_stairs(stair_id, request.get_json(force=True))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if not updated:
        return jsonify({"error": "stairs not found or nothing to update"}), 404
    return jsonify({"ok": True})


@bp.delete("/stairs/<int:stair_id>")
@undoable
def delete_stairs(stair_id):
    if not _store().delete_stairs(stair_id):
        return jsonify({"error": "stairs not found"}), 404
    return jsonify({"ok": True})


@bp.post("/room/<int:room_id>/device")
@undoable
def place_device(room_id):
    data = request.get_json(force=True)
    if not data.get("entity_id"):
        return jsonify({"error": "entity_id is required"}), 400
    placement_id = _store().add_placement(room_id, data)
    if placement_id is None:
        return jsonify({"error": "room not found"}), 404
    return jsonify({"id": placement_id}), 201


@bp.patch("/device/<int:placement_id>")
@undoable
def update_placement(placement_id):
    try:
        updated = _store().update_placement(placement_id,
                                            request.get_json(force=True))
    except sqlite3.IntegrityError:  # model_id referencing a missing model
        return jsonify({"error": "model not found"}), 400
    if not updated:
        return jsonify({"error": "placement not found or nothing to update"}), 404
    return jsonify({"ok": True})


@bp.delete("/device/<int:placement_id>")
@undoable
def delete_placement(placement_id):
    if not _store().delete_placement(placement_id):
        return jsonify({"error": "placement not found"}), 404
    return jsonify({"ok": True})


# ---- model library (uploaded .glb/.gltf files) ------------------------------

@bp.post("/model")
def upload_model():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "no file uploaded"}), 400
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in MODEL_EXTENSIONS:
        return jsonify({"error": f"file type {ext or '?'} not allowed "
                                 "(glb, gltf)"}), 400
    # display name: explicit form field, else the uploaded file's stem
    name = (request.form.get("name") or "").strip() \
        or os.path.splitext(os.path.basename(file.filename))[0]
    store = _store()
    model_id = store.create_model(name)
    filename = f"model_{model_id}{ext}"
    os.makedirs(_models_dir(), exist_ok=True)
    try:
        file.save(os.path.join(_models_dir(), filename))
    except OSError as exc:
        store.delete_model(model_id)
        return jsonify({"error": f"could not save file: {exc}"}), 500
    store.set_model_filename(model_id, filename)
    return jsonify({"id": model_id, "name": name, "filename": filename}), 201


@bp.get("/models")
def list_models():
    return jsonify(_store().list_models())


@bp.get("/model/<int:model_id>/file")
def get_model_file(model_id):
    model = _store().get_model(model_id)
    if not model or not model.get("filename"):
        return jsonify({"error": "model not found"}), 404
    mimetype = ("model/gltf-binary" if model["filename"].endswith(".glb")
                else "model/gltf+json")
    return send_from_directory(_models_dir(), model["filename"],
                               mimetype=mimetype)


@bp.patch("/model/<int:model_id>")
def update_model(model_id):
    if not _store().update_model(model_id, request.get_json(force=True)):
        return jsonify({"error": "model not found or nothing to update"}), 404
    return jsonify({"ok": True})


@bp.delete("/model/<int:model_id>")
def delete_model(model_id):
    model = _store().delete_model(model_id)
    if model is None:
        return jsonify({"error": "model not found"}), 404
    if model.get("filename"):
        path = os.path.join(_models_dir(), model["filename"])
        if os.path.exists(path):
            os.remove(path)
    return jsonify({"ok": True})


# ---- house shell (whole-house model view) -----------------------------------
# Singleton config: which library model renders as the whole house in the
# "House" view, plus a single rigid transform to align it. Not @undoable
# (like the model endpoints — app config, not versioned layout).

@bp.get("/shell")
def get_shell():
    return jsonify(_store().get_house_shell())


@bp.put("/shell")
def set_shell():
    data = request.get_json(force=True) or {}
    store = _store()
    fields = {}
    if "model_id" in data:
        mid = data["model_id"]
        if mid is not None:
            if not isinstance(mid, int) or store.get_model(mid) is None:
                return jsonify({"error": "unknown model_id"}), 400
        fields["model_id"] = mid
    for key in ("x", "y", "z", "rot_y", "scale"):
        if key in data and data[key] is not None:
            try:
                fields[key] = float(data[key])
            except (TypeError, ValueError):
                return jsonify({"error": f"{key} must be a number"}), 400
    return jsonify(store.set_house_shell(fields))


# ---- objects (standalone furniture/decor placed in rooms) -------------------

@bp.post("/room/<int:room_id>/object")
@undoable
def place_object(room_id):
    data = request.get_json(force=True)
    if data.get("model_id") is None:
        return jsonify({"error": "model_id is required"}), 400
    try:
        object_id = _store().add_object(room_id, data)
    except sqlite3.IntegrityError:
        return jsonify({"error": "model not found"}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if object_id is None:
        return jsonify({"error": "room not found"}), 404
    return jsonify({"id": object_id}), 201


@bp.patch("/object/<int:object_id>")
@undoable
def update_object(object_id):
    try:
        updated = _store().update_object(object_id, request.get_json(force=True))
    except sqlite3.IntegrityError:
        return jsonify({"error": "model not found"}), 400
    except ValueError as exc:
        # a malformed light_cfg is the caller's mistake, not a server fault
        return jsonify({"error": str(exc)}), 400
    if not updated:
        return jsonify({"error": "object not found or nothing to update"}), 404
    return jsonify({"ok": True})


@bp.delete("/object/<int:object_id>")
@undoable
def delete_object(object_id):
    if not _store().delete_object(object_id):
        return jsonify({"error": "object not found"}), 404
    return jsonify({"ok": True})


# ---- openings (doors and windows) -------------------------------------------

@bp.post("/room/<int:room_id>/opening")
@undoable
def place_opening(room_id):
    data = request.get_json(force=True)
    if "edge_index" not in data:
        return jsonify({"error": "edge_index is required"}), 400
    opening_id = _store().add_opening(room_id, data)
    if opening_id is None:
        return jsonify({"error": "room not found"}), 404
    return jsonify({"id": opening_id}), 201


@bp.patch("/opening/<int:opening_id>")
@undoable
def update_opening(opening_id):
    updated = _store().update_opening(opening_id, request.get_json(force=True))
    if not updated:
        return jsonify({"error": "opening not found or nothing to update"}), 404
    return jsonify({"ok": True})


@bp.delete("/opening/<int:opening_id>")
@undoable
def delete_opening(opening_id):
    if not _store().delete_opening(opening_id):
        return jsonify({"error": "opening not found"}), 404
    return jsonify({"ok": True})

