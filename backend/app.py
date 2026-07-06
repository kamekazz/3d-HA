"""3D Home Assistant House — Flask entrypoint.

Serves the frontend, proxies HA data (token stays server-side), owns the
house geometry store, and relays HA state changes to browsers via SocketIO.
"""
import logging

from flask import Flask, send_from_directory

import config
from api.camera_routes import bp as camera_bp
from api.control_routes import bp as control_bp
from api.ha_routes import bp as ha_bp
from ha.cache import HACache
from ha.client import HAClient
from ha.ws_client import HARealtime
from house.routes import bp as house_bp
from house.store import HouseStore
from realtime.socketio import make_state_relay, socketio

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("app")


def create_app():
    app = Flask(__name__, static_folder=str(config.FRONTEND_DIR),
                static_url_path="")
    app.secret_key = config.APP_SECRET
    # floor-plan images and 3D model (.glb) uploads
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024

    app.extensions["ha_cache"] = HACache()
    app.extensions["house_store"] = HouseStore(config.DB_PATH)
    app.extensions["ha_rest"] = None
    app.extensions["ha_realtime"] = None

    app.register_blueprint(ha_bp)
    app.register_blueprint(control_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(house_bp)
    socketio.init_app(app)

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    if config.ha_configured():
        app.extensions["ha_rest"] = HAClient(config.HA_BASE_URL, config.HA_TOKEN)
        realtime = HARealtime(config.HA_BASE_URL, config.HA_TOKEN,
                              app.extensions["ha_cache"], make_state_relay())
        realtime.start()
        app.extensions["ha_realtime"] = realtime
        log.info("HA realtime thread started (%s)", realtime.ws_url)
    else:
        log.warning("HA_BASE_URL / HA_TOKEN not set — copy backend/.env.example "
                    "to backend/.env and fill it in. Running without HA data.")

    return app


if __name__ == "__main__":
    app = create_app()
    # debug/reloader off: the HA websocket thread must only start once.
    # Werkzeug is fine for local/LAN use; put a real server in front if hosted.
    socketio.run(app, host="127.0.0.1", port=5000, debug=False,
                 allow_unsafe_werkzeug=True)
