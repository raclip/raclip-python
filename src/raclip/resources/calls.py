from __future__ import annotations

import os
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Union

import httpx

from .._transport import handle_response, strip_org_id
from ..exceptions import APIError
from ..models import Call, CallListResponse, CallStatistics

if TYPE_CHECKING:
    from ..async_client import AsyncClient
    from ..client import Client


DownloadDest = Union[str, os.PathLike[str], IO[bytes]]


def _dest_is_path(dest: DownloadDest) -> bool:
    return isinstance(dest, (str, os.PathLike))


def _require_download_url(call: Call) -> str:
    if not call.download_url:
        raise APIError(
            "Call metadata did not include a download_url. "
            "The recording may not be ready or include_urls was disabled server-side."
        )
    return call.download_url


class CallsResource:
    def __init__(self, client: "Client") -> None:
        self._client = client

    def list(
        self,
        device_id: str,
        *,
        page: int = 1,
        per_page: int = 50,
        days_back: int = 30,
        include_urls: bool = True,
    ) -> CallListResponse:
        params = strip_org_id(
            {
                "page": page,
                "per_page": per_page,
                "days_back": days_back,
                "include_urls": str(include_urls).lower(),
            }
        )
        response = self._client._http.get(f"/raclip/calls/{device_id}", params=params)
        return CallListResponse.model_validate(handle_response(response))

    def latest(self, device_id: str, *, download: bool = True) -> Call:
        params = strip_org_id({"download": str(download).lower()})
        response = self._client._http.get(
            f"/raclip/calls/{device_id}/latest", params=params
        )
        return Call.model_validate(handle_response(response))

    def get(self, device_id: str, call_id: str, *, download: bool = True) -> Call:
        params = strip_org_id({"download": str(download).lower()})
        response = self._client._http.get(
            f"/raclip/calls/{device_id}/{call_id}", params=params
        )
        return Call.model_validate(handle_response(response))

    def info(self, device_id: str, call_id: str) -> dict[str, Any]:
        response = self._client._http.get(
            f"/raclip/calls/{device_id}/{call_id}/info"
        )
        return handle_response(response)  # type: ignore[return-value]

    def statistics(self, device_id: str, *, days_back: int = 30) -> CallStatistics:
        params = strip_org_id({"days_back": days_back})
        response = self._client._http.get(
            f"/raclip/calls/{device_id}/statistics", params=params
        )
        return CallStatistics.model_validate(handle_response(response))

    def download(
        self,
        device_id: str,
        call_id: str,
        *,
        dest: DownloadDest,
        chunk_size: int = 64 * 1024,
    ) -> Path | IO[bytes]:
        """Stream a call's MP3 to a file path or file-like.

        Fetches metadata to resolve the presigned S3 URL, then downloads the
        bytes over a fresh httpx stream that does NOT carry the Authorization
        header — S3 rejects unexpected auth headers on presigned URLs.
        """
        call = self.get(device_id, call_id, download=True)
        url = _require_download_url(call)
        return _stream_download_sync(url, dest, chunk_size)


class AsyncCallsResource:
    def __init__(self, client: "AsyncClient") -> None:
        self._client = client

    async def list(
        self,
        device_id: str,
        *,
        page: int = 1,
        per_page: int = 50,
        days_back: int = 30,
        include_urls: bool = True,
    ) -> CallListResponse:
        params = strip_org_id(
            {
                "page": page,
                "per_page": per_page,
                "days_back": days_back,
                "include_urls": str(include_urls).lower(),
            }
        )
        response = await self._client._http.get(
            f"/raclip/calls/{device_id}", params=params
        )
        return CallListResponse.model_validate(handle_response(response))

    async def latest(self, device_id: str, *, download: bool = True) -> Call:
        params = strip_org_id({"download": str(download).lower()})
        response = await self._client._http.get(
            f"/raclip/calls/{device_id}/latest", params=params
        )
        return Call.model_validate(handle_response(response))

    async def get(self, device_id: str, call_id: str, *, download: bool = True) -> Call:
        params = strip_org_id({"download": str(download).lower()})
        response = await self._client._http.get(
            f"/raclip/calls/{device_id}/{call_id}", params=params
        )
        return Call.model_validate(handle_response(response))

    async def info(self, device_id: str, call_id: str) -> dict[str, Any]:
        response = await self._client._http.get(
            f"/raclip/calls/{device_id}/{call_id}/info"
        )
        return handle_response(response)  # type: ignore[return-value]

    async def statistics(self, device_id: str, *, days_back: int = 30) -> CallStatistics:
        params = strip_org_id({"days_back": days_back})
        response = await self._client._http.get(
            f"/raclip/calls/{device_id}/statistics", params=params
        )
        return CallStatistics.model_validate(handle_response(response))

    async def download(
        self,
        device_id: str,
        call_id: str,
        *,
        dest: DownloadDest,
        chunk_size: int = 64 * 1024,
    ) -> Path | IO[bytes]:
        call = await self.get(device_id, call_id, download=True)
        url = _require_download_url(call)
        return await _stream_download_async(url, dest, chunk_size)


def _stream_download_sync(
    url: str, dest: DownloadDest, chunk_size: int
) -> Path | IO[bytes]:
    if _dest_is_path(dest):
        path = Path(os.fspath(dest))  # type: ignore[arg-type]
        with httpx.stream("GET", url) as response:
            response.raise_for_status()
            with open(path, "wb") as fh:
                for chunk in response.iter_bytes(chunk_size):
                    fh.write(chunk)
        return path

    file_like: IO[bytes] = dest  # type: ignore[assignment]
    with httpx.stream("GET", url) as response:
        response.raise_for_status()
        for chunk in response.iter_bytes(chunk_size):
            file_like.write(chunk)
    return file_like


async def _stream_download_async(
    url: str, dest: DownloadDest, chunk_size: int
) -> Path | IO[bytes]:
    if _dest_is_path(dest):
        path = Path(os.fspath(dest))  # type: ignore[arg-type]
        async with httpx.AsyncClient() as downloader:
            async with downloader.stream("GET", url) as response:
                response.raise_for_status()
                with open(path, "wb") as fh:
                    async for chunk in response.aiter_bytes(chunk_size):
                        fh.write(chunk)
        return path

    file_like: IO[bytes] = dest  # type: ignore[assignment]
    async with httpx.AsyncClient() as downloader:
        async with downloader.stream("GET", url) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size):
                file_like.write(chunk)
    return file_like
