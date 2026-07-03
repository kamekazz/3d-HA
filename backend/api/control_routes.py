"""Control endpoint: browser -> Flask -> HA call_service."""
import requests
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("control", __name__)


@bp.post("/api/control")
def control():
    body = request.get_json(force=True)
    entity_id = body.get("entity_id")
    if not entity_id or "." not in entity_id:
        return jsonify({"error": "a valid entity_id is required"}), 400

    domain = body.get("domain") or entity_id.split(".", 1)[0]
    service = body.get("service") or "toggle"
    data = {"entity_id": entity_id}
    extra = body.get("data")
    if isinstance(extra, dict):
        data.update(extra)

    rest = current_app.extensions.get("ha_rest")
    if rest is None:
        return jsonify({"error": "HA is not configured (.env)"}), 503
    try:
        result = rest.call_service(domain, service, data)
    except requests.RequestException as exc:
        return jsonify({"error": "service call failed", "detail": str(exc)}), 502
    return jsonify({"ok": True, "result": result})
