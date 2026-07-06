"""Camera proxy: browser -> Flask -> HA camera_proxy*. The token stays here."""
import requests
from flask import Blueprint, Response, current_app, jsonify

bp = Blueprint("camera", __name__, url_prefix="/api/camera")


def _rest_or_error():
    rest = current_app.extensions.get("ha_rest")
    if rest is None:
        return None, (jsonify({"error": "HA is not configured (.env)"}), 503)
    return rest, None


@bp.get("/<entity_id>/snapshot")
def snapshot(entity_id):
    if not entity_id.startswith("camera."):
        return jsonify({"error": "not a camera entity"}), 400
    rest, err = _rest_or_error()
    if err:
        return err
    try:
        content, ctype = rest.get_camera_image(entity_id)
    except requests.RequestException as exc:
        return jsonify({"error": "snapshot failed", "detail": str(exc)}), 502
    return Response(content, mimetype=ctype,
                    headers={"Cache-Control": "no-store"})


@bp.get("/<entity_id>/stream")
def stream(entity_id):
    if not entity_id.startswith("camera."):
        return jsonify({"error": "not a camera entity"}), 400
    rest, err = _rest_or_error()
    if err:
        return err
    try:
        upstream = rest.open_camera_stream(entity_id)
    except requests.RequestException as exc:
        return jsonify({"error": "stream failed", "detail": str(exc)}), 502

    def relay():
        try:
            yield from upstream.iter_content(chunk_size=16384)
        finally:
            upstream.close()

    # Each open stream occupies one Werkzeug worker thread until the browser
    # drops the <img> — fine for local use with a handful of viewers.
    return Response(
        relay(),
        mimetype=upstream.headers.get("Content-Type",
                                      "multipart/x-mixed-replace"),
        headers={"Cache-Control": "no-store"},
        direct_passthrough=True,
    )
