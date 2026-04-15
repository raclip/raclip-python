from __future__ import annotations

import os
from typing import Any

import httpx

from ._transport import API_PREFIX, DEFAULT_BASE_URL, build_headers
from .exceptions import AuthenticationError
from .resources import AsyncCallsResource, AsyncDevicesResource


class AsyncClient:
    """Asynchronous raclip API client.

    Example:
        import asyncio
        from raclip import AsyncClient

        async def main():
            async with AsyncClient() as client:
                result = await client.devices.list()
                for device in result.devices:
                    print(device.device_id, device.status)

        asyncio.run(main())
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
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
            self._http = httpx.AsyncClient(
                base_url=self._api_base,
                headers=build_headers(resolved_key),
                timeout=timeout,
            )
            self._owns_http = True

        self.devices = AsyncDevicesResource(self)
        self.calls = AsyncCallsResource(self)

    @property
    def base_url(self) -> str:
        return self._base_url

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.aclose()
