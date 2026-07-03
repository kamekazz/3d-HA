"""Read-through HA data for the browser (/api/ha/*). No token ever leaves here."""
import requests
from flask import Blueprint, current_app, jsonify

bp = Blueprint("ha_api", __name__, url_prefix="/api/ha")


@bp.get("/structure")
def structure():
    cache = current_app.extensions["ha_cache"]
    if not cache.ready:
        realtime = current_app.extensions.get("ha_realtime")
        detail = realtime.last_error if realtime else "HA is not configured (.env)"
        return jsonify({"error": "Home Assistant structure not available yet",
                        "detail": detail}), 503
    return jsonify(cache.structure())


@bp.get("/states")
def states():
    cache = current_app.extensions["ha_cache"]
    if cache.has_states():
        return jsonify(cache.states())
    rest = current_app.extensions.get("ha_rest")
    if rest is None:
        return jsonify({"error": "HA is not configured (.env)"}), 503
    try:
        return jsonify(rest.get_states())
    except requests.RequestException as exc:
        return jsonify({"error": "Home Assistant unreachable",
                        "detail": str(exc)}), 502


@bp.post("/refresh")
def refresh():
    realtime = current_app.extensions.get("ha_realtime")
    if realtime is None:
        return jsonify({"error": "HA is not configured (.env)"}), 503
    realtime.request_registry_refresh()
    return jsonify({"ok": True})


@bp.get("/status")
def status():
    realtime = current_app.extensions.get("ha_realtime")
    cache = current_app.extensions["ha_cache"]
    return jsonify({
        "configured": realtime is not None,
        "connected": bool(realtime and realtime.connected),
        "registries_cached": cache.ready,
        "last_error": realtime.last_error if realtime else None,
    })
