"""REST client for Home Assistant. The token is attached here and only here."""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class HAClient:
    def __init__(self, base_url: str, token: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        # Nabu Casa's remote proxy drops TLS connections in short bursts
        # (SSLEOFError) when several open at once; observed bursts last
        # ~1-2s, so back off far enough to outlast one. GETs are idempotent
        # here, so retry them; POSTs (call_service) never retry.
        retry = Retry(total=3, connect=3, read=2, status=0,
                      backoff_factor=1.0,
                      allowed_methods=frozenset({"GET"}))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/{path.lstrip('/')}"

    def get_states(self):
        r = self.session.get(self._url("states"), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_state(self, entity_id: str):
        r = self.session.get(self._url(f"states/{entity_id}"), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_config(self):
        r = self.session.get(self._url("config"), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_camera_image(self, entity_id: str):
        """One JPEG snapshot from HA's camera proxy."""
        r = self.session.get(self._url(f"camera_proxy/{entity_id}"),
                             timeout=self.timeout)
        r.raise_for_status()
        return r.content, r.headers.get("Content-Type", "image/jpeg")

    def open_camera_stream(self, entity_id: str):
        """MJPEG stream from HA's camera proxy. Caller must close the response.

        Read timeout is per-chunk, not total — HA needs a few seconds to spin
        up ffmpeg for stream-capable cameras (e.g. Ring) before frames flow.
        """
        r = self.session.get(self._url(f"camera_proxy_stream/{entity_id}"),
                             stream=True, timeout=(self.timeout, 30))
        r.raise_for_status()
        return r

    def call_service(self, domain: str, service: str, data: dict):
        r = self.session.post(
            self._url(f"services/{domain}/{service}"),
            json=data,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()
