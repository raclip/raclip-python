# raclip

The official Python SDK for the [raclip](https://raclip.ai) platform. Read
device state and fetch call recordings from the raclip API with a few lines
of idiomatic Python.

> **Status:** `0.0.1` — read-only surface (devices + calls). Device mutation
> and call deletion land in a later release.

## Install

```bash
pip install raclip
# or
uv add raclip
```

Requires Python 3.10+.

## Authenticate

Grab an API key from the raclip console and either pass it explicitly or set
`RACLIP_API_KEY` in your environment:

```bash
export RACLIP_API_KEY="raclip_prod_..."
```

The SDK never sends your `org_id` on the wire — the API gateway derives it
from your key and enforces it server-side, so there is nothing to configure.

## Quickstart

```python
from raclip import Client

with Client() as client:
    devices = client.devices.list()
    print(f"{devices.total} devices in this org")

    for device in devices.devices:
        print(device.device_id, device.status, device.last_seen)

    if devices.devices:
        device_id = devices.devices[0].device_id
        calls = client.calls.list(device_id, per_page=5)
        for call in calls.calls:
            print(call.call_id, call.duration_seconds, "sec")
            print("  download:", call.download_url)
```

`call.download_url` is a short-lived presigned S3 URL — fetch it with `curl`,
`httpx`, `aws s3 cp`, or the streaming helper the SDK ships:

```python
client.calls.download(device_id, call.call_id, dest="recording.mp3")
```

## Async

The SDK ships a fully async client that mirrors the sync API one-for-one:

```python
import asyncio
from raclip import AsyncClient

async def main():
    async with AsyncClient() as client:
        devices = await client.devices.list()
        print(f"{devices.total} devices")

asyncio.run(main())
```

## Endpoints covered in 0.0.1

| Method | Description |
|---|---|
| `client.devices.list()` | paginated list of devices |
| `client.devices.stats()` | per-org device health summary |
| `client.devices.get(device_id)` | full device record |
| `client.devices.status(device_id)` | current status snapshot |
| `client.calls.list(device_id)` | paginated list of call recordings |
| `client.calls.latest(device_id)` | most recent recording |
| `client.calls.get(device_id, call_id)` | call metadata + presigned URL |
| `client.calls.info(device_id, call_id)` | metadata without generating a URL |
| `client.calls.statistics(device_id)` | aggregate call stats |
| `client.calls.download(device_id, call_id, dest=...)` | stream MP3 to a file or file-like |

`AsyncClient` exposes the same methods under the same names.

## Errors

Every non-2xx response is converted into a typed exception so you can
`try/except` the specific failures you care about:

```python
from raclip import (
    Client, AuthenticationError, NotFoundError, RateLimitError
)

with Client() as client:
    try:
        call = client.calls.get("device-id", "call-id")
    except NotFoundError:
        print("call is gone")
    except RateLimitError as e:
        print(f"slow down; retry after {e.retry_after}s")
    except AuthenticationError:
        print("check your API key")
```

Full hierarchy: `RaclipError` → `AuthenticationError`, `PermissionError`,
`NotFoundError`, `ValidationError`, `RateLimitError`, `APIError`,
`APIConnectionError`.

## License

MIT.
