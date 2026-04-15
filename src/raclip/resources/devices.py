from __future__ import annotations

from typing import TYPE_CHECKING

from .._transport import handle_response, strip_org_id
from ..models import Device, DeviceListResponse, DeviceStats, DeviceStatusSnapshot

if TYPE_CHECKING:
    from ..async_client import AsyncClient
    from ..client import Client


class DevicesResource:
    def __init__(self, client: "Client") -> None:
        self._client = client

    def list(
        self,
        *,
        status: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> DeviceListResponse:
        params = strip_org_id({"status": status, "page": page, "per_page": per_page})
        response = self._client._http.get("/raclip/devices", params=params)
        return DeviceListResponse.model_validate(handle_response(response))

    def stats(self) -> DeviceStats:
        response = self._client._http.get("/raclip/devices/stats")
        return DeviceStats.model_validate(handle_response(response))

    def get(self, device_id: str) -> Device:
        response = self._client._http.get(f"/raclip/devices/{device_id}")
        return Device.model_validate(handle_response(response))

    def status(self, device_id: str) -> DeviceStatusSnapshot:
        response = self._client._http.get(f"/raclip/devices/{device_id}/status")
        return DeviceStatusSnapshot.model_validate(handle_response(response))


class AsyncDevicesResource:
    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def list(
        self,
        *,
        status: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> DeviceListResponse:
        params = strip_org_id({"status": status, "page": page, "per_page": per_page})
        response = await self._client._http.get("/raclip/devices", params=params)
        return DeviceListResponse.model_validate(handle_response(response))

    async def stats(self) -> DeviceStats:
        response = await self._client._http.get("/raclip/devices/stats")
        return DeviceStats.model_validate(handle_response(response))

    async def get(self, device_id: str) -> Device:
        response = await self._client._http.get(f"/raclip/devices/{device_id}")
        return Device.model_validate(handle_response(response))

    async def status(self, device_id: str) -> DeviceStatusSnapshot:
        response = await self._client._http.get(f"/raclip/devices/{device_id}/status")
        return DeviceStatusSnapshot.model_validate(handle_response(response))
