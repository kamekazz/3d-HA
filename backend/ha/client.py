"""REST client for Home Assistant. The token is attached here and only here."""
import ssl
import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Nabu Casa's remote proxy closes a fresh connection (SSLEOFError:
# UNEXPECTED_EOF_WHILE_READING) unless the TLS ClientHello arrives within
# ~50 ms of the TCP connect — measured here by sleeping between the two.
# Stock `requests` never makes that: it connects first and *then* parses the
# certifi bundle for the new connection (~150 ms), so every verified request
# was dropped while curl, the websocket and raw sockets (context built before
# connecting) all sailed through. `_PrebuiltTLSAdapter` hands urllib3 a fully
# built SSLContext so a new connection goes TCP connect -> ClientHello with
# nothing in between. Two things still widen that gap: a Python-side stall
# (GC, GIL contention while Flask threads serve GLBs at boot) and a burst of
# handshakes at once (16 parallel raw connections lost 15) — and a page load
# asks for the calendar plus one area picture per room all at once, one Flask
# thread each. So every REST call also passes through a gate of at most
# MAX_CONCURRENT connections, reused via keep-alive, and the GET retry below
# absorbs the occasional drop. The websocket is one long-lived connection and
# was never affected.
MAX_CONCURRENT = 2


class _PrebuiltTLSAdapter(HTTPAdapter):
    """HTTPAdapter whose pools use one pre-built SSLContext (bundle already
    loaded) instead of building/loading one per connection after connect."""

    def __init__(self, ssl_context, **kwargs):
        self._ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self._ssl_context
        super().init_poolmanager(*args, **kwargs)

    def cert_verify(self, conn, url, verify, cert):
        super().cert_verify(conn, url, verify, cert)
        if verify is True:
            # Drop the bundle *path* requests just pinned on the pool: the
            # context already holds it, and urllib3 would otherwise re-parse
            # the file on every new connection — after the TCP connect.
            conn.ca_certs = None
            conn.ca_cert_dir = None


class HAClient:
    def __init__(self, base_url: str, token: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        # GETs are idempotent here, so retry them (sleeps 0/1/2/4s between
        # attempts — a dropped handshake is instant, so this costs little);
        # POSTs (call_service) never retry.
        retry = Retry(total=4, connect=4, read=2, status=0,
                      backoff_factor=0.5,
                      allowed_methods=frozenset({"GET"}))
        ctx = ssl.create_default_context(cafile=requests.certs.where())
        self.session.mount("https://", _PrebuiltTLSAdapter(ctx, max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self._gate = threading.BoundedSemaphore(MAX_CONCURRENT)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/{path.lstrip('/')}"

    def _get(self, url: str, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        with self._gate:
            return self.session.get(url, **kwargs)

    def _post(self, url: str, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        with self._gate:
            return self.session.post(url, **kwargs)

    def get_states(self):
        r = self._get(self._url("states"))
        r.raise_for_status()
        return r.json()

    def get_state(self, entity_id: str):
        r = self._get(self._url(f"states/{entity_id}"))
        r.raise_for_status()
        return r.json()

    def get_config(self):
        r = self._get(self._url("config"))
        r.raise_for_status()
        return r.json()

    def get_image(self, path: str):
        """Fetch an HA-relative image path (e.g. an area picture's
        /api/image/serve/<id>/512x512). Path comes from HA's own registry,
        never from the browser."""
        r = self._get(f"{self.base_url}{path}")
        r.raise_for_status()
        return r.content, r.headers.get("Content-Type", "image/jpeg")

    def get_camera_image(self, entity_id: str):
        """One JPEG snapshot from HA's camera proxy."""
        r = self._get(self._url(f"camera_proxy/{entity_id}"))
        r.raise_for_status()
        return r.content, r.headers.get("Content-Type", "image/jpeg")

    def open_camera_stream(self, entity_id: str):
        """MJPEG stream from HA's camera proxy. Caller must close the response.

        Read timeout is per-chunk, not total — HA needs a few seconds to spin
        up ffmpeg for stream-capable cameras (e.g. Ring) before frames flow.
        The gate is held only until the headers arrive, not for the stream's
        lifetime.
        """
        r = self._get(self._url(f"camera_proxy_stream/{entity_id}"),
                      stream=True, timeout=(self.timeout, 30))
        r.raise_for_status()
        return r

    def get_calendars(self):
        r = self._get(self._url("calendars"))
        r.raise_for_status()
        return r.json()

    def get_calendar_events(self, entity_id: str, start_iso: str, end_iso: str):
        r = self._get(self._url(f"calendars/{entity_id}"),
                      params={"start": start_iso, "end": end_iso})
        r.raise_for_status()
        return r.json()

    def call_service(self, domain: str, service: str, data: dict):
        r = self._post(self._url(f"services/{domain}/{service}"), json=data)
        r.raise_for_status()
        return r.json()
