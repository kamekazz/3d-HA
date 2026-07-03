"""SocketIO instance that relays HA state_changed events to connected browsers."""
from flask_socketio import SocketIO

socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")


def make_state_relay():
    """Callback for the HA websocket thread -> pushes to all browsers."""
    def relay(entity_id, new_state):
        socketio.emit("state_changed", {
            "entity_id": entity_id,
            "new_state": new_state,
        })
    return relay
