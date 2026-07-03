"""REST client for Home Assistant. The token is attached here and only here."""
import requests


class HAClient:
    def __init__(self, base_url: str, token: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

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

    def call_service(self, domain: str, service: str, data: dict):
        r = self.session.post(
            self._url(f"services/{domain}/{service}"),
            json=data,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()
