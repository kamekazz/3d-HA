"""Home Assistant WebSocket client.

Runs in a background thread (Flask is synchronous). It:
  - authenticates with the long-lived token,
  - fetches the four registries (floors/areas/devices/entities) into the cache,
  - fetches all current states,
  - keeps a `state_changed` subscription open and forwards events,
  - reconnects with exponential backoff.
"""
import asyncio
import json
import logging
import threading

import websockets

log = logging.getLogger(__name__)

REGISTRY_COMMANDS = {
    "floors": "config/floor_registry/list",
    "areas": "config/area_registry/list",
    "devices": "config/device_registry/list",
    "entities": "config/entity_registry/list",
}


class HARealtime(threading.Thread):
    def __init__(self, base_url, token, cache, on_state_changed=None):
        super().__init__(daemon=True, name="ha-realtime")
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._cache = cache
        self._on_state_changed = on_state_changed
        self._loop = None
        self._refresh = None
        self._msg_id = 0
        self._pending = {}
        self.connected = False
        self.last_error = None

    @property
    def ws_url(self):
        url = self._base_url
        if url.startswith("https://"):
            url = "wss://" + url[len("https://"):]
        elif url.startswith("http://"):
            url = "ws://" + url[len("http://"):]
        return url + "/api/websocket"

    def request_registry_refresh(self):
        """Thread-safe: ask the worker to re-fetch the registries."""
        if self._loop and self._refresh:
            self._loop.call_soon_threadsafe(self._refresh.set)

    def run(self):
        asyncio.run(self._main())

    async def _main(self):
        self._loop = asyncio.get_running_loop()
        self._refresh = asyncio.Event()
        backoff = 2
        while True:
            try:
                await self._session()
                backoff = 2
            except Exception as exc:
                self.connected = False
                self.last_error = str(exc)
                log.warning("HA websocket lost (%s); retrying in %ss", exc, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def _session(self):
        async with websockets.connect(self.ws_url, max_size=32 * 1024 * 1024) as ws:
            self._pending = {}
            self._msg_id = 0

            first = json.loads(await ws.recv())
            if first.get("type") != "auth_required":
                raise RuntimeError(f"unexpected first message: {first.get('type')}")
            await ws.send(json.dumps({"type": "auth", "access_token": self._token}))
            reply = json.loads(await ws.recv())
            if reply.get("type") != "auth_ok":
                raise RuntimeError(f"HA auth failed: {reply.get('message', reply)}")
            log.info("HA websocket authenticated")

            reader = asyncio.ensure_future(self._reader(ws))
            worker = asyncio.ensure_future(self._worker(ws))
            done, pending = await asyncio.wait(
                {reader, worker}, return_when=asyncio.FIRST_EXCEPTION
            )
            for t in pending:
                t.cancel()
            for t in done:
                t.result()

    async def _cmd(self, ws, payload):
        self._msg_id += 1
        mid = self._msg_id
        fut = asyncio.get_running_loop().create_future()
        self._pending[mid] = fut
        await ws.send(json.dumps({"id": mid, **payload}))
        return await fut

    async def _reader(self, ws):
        async for raw in ws:
            msg = json.loads(raw)
            mid = msg.get("id")
            if msg.get("type") == "result" and mid in self._pending:
                fut = self._pending.pop(mid)
                if msg.get("success", True):
                    fut.set_result(msg.get("result"))
                else:
                    fut.set_exception(RuntimeError(str(msg.get("error"))))
            elif msg.get("type") == "event":
                self._handle_event(msg)
        raise ConnectionError("HA websocket closed")

    async def _worker(self, ws):
        await self._fetch_registries(ws)
        states = await self._cmd(ws, {"type": "get_states"})
        self._cache.set_states(states)
        await self._cmd(ws, {"type": "subscribe_events",
                             "event_type": "state_changed"})
        self.connected = True
        self.last_error = None
        log.info("HA registries cached, state_changed subscription open")
        while True:
            await self._refresh.wait()
            self._refresh.clear()
            await self._fetch_registries(ws)
            log.info("HA registries refreshed")

    async def _fetch_registries(self, ws):
        results = {}
        for key, cmd_type in REGISTRY_COMMANDS.items():
            results[key] = await self._cmd(ws, {"type": cmd_type})
        self._cache.set_registries(**results)

    def _handle_event(self, msg):
        data = msg.get("event", {}).get("data", {})
        entity_id = data.get("entity_id")
        if not entity_id:
            return
        new_state = data.get("new_state")
        self._cache.update_state(entity_id, new_state)
        if self._on_state_changed:
            try:
                self._on_state_changed(entity_id, new_state)
            except Exception:
                log.exception("state_changed relay callback failed")
