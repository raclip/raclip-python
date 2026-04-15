from __future__ import annotations

import os
from typing import Any

import httpx

from ._transport import API_PREFIX, DEFAULT_BASE_URL, build_headers
from .exceptions import AuthenticationError
from .resources import CallsResource, DevicesResource


class Client:
    """Synchronous raclip API client.

    Example:
        from raclip import Client

        with Client() as client:               # RACLIP_API_KEY from env
            for device in client.devices.list().devices:
                print(device.device_id, device.status)
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("RACLIP_API_KEY")
        if not resolved_key:
            raise AuthenticationError(
                "No API key provided. Pass api_key= or set RACLIP_API_KEY "
                "in the environment."
            )
        self._api_key = resolved_key
        self._base_url = base_url.rstrip("/")
        self._api_base = f"{self._base_url}{API_PREFIX}"

        if http_client is not None:
            self._http = http_client
            self._owns_http = False
        else:
            self._http = httpx.Client(
                base_url=self._api_base,
                headers=build_headers(resolved_key),
                timeout=timeout,
            )
            self._owns_http = True

        self.devices = DevicesResource(self)
        self.calls = CallsResource(self)

    @property
    def base_url(self) -> str:
        return self._base_url

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
