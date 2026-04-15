"""Offline unit tests — verify auth wiring, error mapping, and the
'never send org_id' invariant without touching the network."""

from __future__ import annotations

import httpx
import pytest
import respx

from raclip import (
    AsyncClient,
    AuthenticationError,
    Client,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ValidationError,
)
from raclip._transport import API_PREFIX, DEFAULT_BASE_URL
from raclip.exceptions import APIError


DEVICE_ID = "00000000-0000-0000-0000-000000000001"
API_BASE = f"{DEFAULT_BASE_URL}{API_PREFIX}"


@pytest.fixture
def client():
    with Client(api_key="test-key") as c:
        yield c


def test_auth_header_is_set(client):
    with respx.mock() as mock:
        route = mock.get(f"{API_BASE}/raclip/devices/stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "org_id": "demo-org",
                    "total_devices": 1,
                    "assigned_devices": 0,
                    "unassigned_devices": 1,
                    "online_devices": 1,
                    "offline_devices": 0,
                    "recent_registrations_7d": 1,
                    "device_status_breakdown": {"active": 1},
                    "assignment_breakdown": {
                        "assigned_to_unit": 0,
                        "assigned_to_location": 0,
                        "assigned_to_employee": 0,
                    },
                },
            )
        )
        result = client.devices.stats()
        assert result.total_devices == 1
        assert route.calls.last.request.headers["authorization"] == "Bearer test-key"
        assert "raclip-python/" in route.calls.last.request.headers["user-agent"]


def test_no_key_in_env_raises(monkeypatch):
    monkeypatch.delenv("RACLIP_API_KEY", raising=False)
    with pytest.raises(AuthenticationError):
        Client()


def test_env_api_key_is_picked_up(monkeypatch):
    monkeypatch.setenv("RACLIP_API_KEY", "env-key")
    c = Client()
    assert c._api_key == "env-key"
    c.close()


def test_base_url_is_prefixed_with_api():
    c = Client(api_key="k")
    assert c._api_base == f"{DEFAULT_BASE_URL}{API_PREFIX}"
    c.close()


def test_org_id_is_never_sent_even_if_caller_tries(client):
    """Regression guard: if a future resource builder accidentally forwards
    an org_id kwarg into params, strip_org_id must drop it before it leaves
    the SDK. The gateway rewrites it anyway — we don't want to send a
    misleading value on the wire."""
    from raclip._transport import strip_org_id

    assert "org_id" not in strip_org_id({"org_id": "leaked", "page": 1})
    assert strip_org_id({"org_id": "leaked"}) == {}
    assert strip_org_id({"page": 1, "per_page": 50}) == {"page": 1, "per_page": 50}
    assert strip_org_id(None) == {}
    assert strip_org_id({"status": None, "page": 2}) == {"page": 2}


@pytest.mark.parametrize(
    "status_code,exc_type",
    [
        (401, AuthenticationError),
        (403, PermissionError),
        (404, NotFoundError),
        (400, ValidationError),
        (422, ValidationError),
        (429, RateLimitError),
        (500, APIError),
        (502, APIError),
    ],
)
def test_error_status_maps_to_typed_exception(client, status_code, exc_type):
    with respx.mock() as mock:
        mock.get(f"{API_BASE}/raclip/devices/stats").mock(
            return_value=httpx.Response(
                status_code, json={"detail": f"stub error {status_code}"}
            )
        )
        with pytest.raises(exc_type) as excinfo:
            client.devices.stats()
        assert excinfo.value.status_code == status_code
        assert "stub error" in excinfo.value.detail


def test_rate_limit_exposes_retry_after(client):
    with respx.mock() as mock:
        mock.get(f"{API_BASE}/raclip/devices/stats").mock(
            return_value=httpx.Response(
                429,
                headers={"retry-after": "12"},
                json={"detail": "Rate limit exceeded"},
            )
        )
        with pytest.raises(RateLimitError) as excinfo:
            client.devices.stats()
        assert excinfo.value.retry_after == 12.0


def test_call_list_parses_real_shape(client):
    body = {
        "device_id": DEVICE_ID,
        "total": 2,
        "page": 1,
        "per_page": 50,
        "calls": [
            {
                "call_id": "call-1",
                "duration_seconds": 12.5,
                "file_size_bytes": 200_000,
                "storage_format": "mp3",
                "bitrate": "128k",
                "created_at": "2026-04-15T10:00:00+00:00",
                "start_timestamp": "2026-04-15T09:59:00+00:00",
                "end_timestamp": "2026-04-15T10:00:00+00:00",
                "call_sequence": 1,
                "download_url": "https://s3.example.com/call-1.mp3?sig=abc",
            },
            {
                "call_id": "call-2",
                "duration_seconds": 30.0,
                "file_size_bytes": 480_000,
                "storage_format": "mp3",
                "bitrate": "128k",
                "created_at": "2026-04-15T11:00:00+00:00",
                "start_timestamp": "2026-04-15T10:59:30+00:00",
                "end_timestamp": "2026-04-15T11:00:00+00:00",
                "call_sequence": 2,
            },
        ],
    }
    with respx.mock() as mock:
        mock.get(f"{API_BASE}/raclip/calls/{DEVICE_ID}").mock(
            return_value=httpx.Response(200, json=body)
        )
        result = client.calls.list(DEVICE_ID, per_page=50)
        assert result.total == 2
        assert len(result.calls) == 2
        assert result.calls[0].download_url.startswith("https://")
        assert result.calls[1].download_url is None


async def test_async_client_works():
    async with AsyncClient(api_key="test-key") as client:
        with respx.mock() as mock:
            mock.get(f"{API_BASE}/raclip/devices/stats").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "org_id": "demo-org",
                        "total_devices": 3,
                        "assigned_devices": 1,
                        "unassigned_devices": 2,
                        "online_devices": 2,
                        "offline_devices": 1,
                        "recent_registrations_7d": 0,
                        "device_status_breakdown": {"active": 2, "inactive": 1},
                        "assignment_breakdown": {
                            "assigned_to_unit": 1,
                            "assigned_to_location": 0,
                            "assigned_to_employee": 0,
                        },
                    },
                )
            )
            result = await client.devices.stats()
            assert result.total_devices == 3
