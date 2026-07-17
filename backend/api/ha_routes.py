"""Read-through HA data for the browser (/api/ha/*). No token ever leaves here."""
import re
from datetime import datetime, timedelta, timezone

import requests
from flask import Blueprint, Response, current_app, jsonify, request

bp = Blueprint("ha_api", __name__, url_prefix="/api/ha")

# HA area pictures uploaded through the UI land on /api/image/serve/<id>[/WxH];
# rewrite the size suffix so HA serves a card-sized variant.
IMAGE_SERVE_RE = re.compile(r"^/api/image/serve/([^/]+)(?:/\d+x\d+)?$")


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


@bp.get("/area-picture/<area_id>")
def area_picture(area_id):
    """Proxy an area's registry picture. The browser only names the area —
    the image path always comes from HA's own registry (no client paths)."""
    cache = current_app.extensions["ha_cache"]
    path = cache.area_picture(area_id)
    if not path or not path.startswith("/") or path.startswith("//"):
        return jsonify({"error": "no picture for this area"}), 404
    m = IMAGE_SERVE_RE.match(path)
    if m:
        path = f"/api/image/serve/{m.group(1)}/512x512"
    rest = current_app.extensions.get("ha_rest")
    if rest is None:
        return jsonify({"error": "HA is not configured (.env)"}), 503
    try:
        content, ctype = rest.get_image(path)
    except requests.RequestException as exc:
        return jsonify({"error": "Home Assistant unreachable",
                        "detail": str(exc)}), 502
    return Response(content, mimetype=ctype,
                    headers={"Cache-Control": "private, max-age=3600"})


@bp.get("/calendar")
def calendar():
    """Upcoming events across all HA calendars, merged and sorted."""
    rest = current_app.extensions.get("ha_rest")
    if rest is None:
        return jsonify({"error": "HA is not configured (.env)"}), 503
    try:
        days = min(max(int(request.args.get("days", 30)), 1), 180)
    except ValueError:
        return jsonify({"error": "days must be an integer"}), 400
    start = datetime.now(timezone.utc)
    end = start + timedelta(days=days)
    try:
        calendars = rest.get_calendars()
    except requests.RequestException as exc:
        return jsonify({"error": "Home Assistant unreachable",
                        "detail": str(exc)}), 502

    events = []
    for cal in calendars:
        entity_id = cal.get("entity_id")
        if not entity_id:
            continue
        try:
            raw = rest.get_calendar_events(entity_id, start.isoformat(),
                                           end.isoformat())
        except requests.RequestException:
            continue  # one broken integration must not kill the card
        for ev in raw or []:
            # HA start/end: {"dateTime": iso} or, for all-day, {"date": "YYYY-MM-DD"}
            # (kept verbatim — converting all-day dates to UTC shifts the day).
            s, e = ev.get("start") or {}, ev.get("end") or {}
            all_day = "date" in s
            events.append({
                "calendar": entity_id,
                "summary": ev.get("summary") or "(untitled)",
                "start": s.get("dateTime") or s.get("date"),
                "end": e.get("dateTime") or e.get("date"),
                "all_day": all_day,
            })
    events = [e for e in events if e["start"]]
    events.sort(key=lambda e: e["start"])
    return jsonify({
        "calendars": [{"entity_id": c.get("entity_id"), "name": c.get("name")}
                      for c in calendars],
        "events": events[:30],
    })


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
