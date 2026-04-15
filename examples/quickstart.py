"""End-to-end live smoke test against the real raclip platform.

Run as a developer / customer would: one script, real API key, real gateway,
real device, real audio. If this prints expected output without raising,
v0.0.1 works.

Usage:
    export RACLIP_API_KEY="raclip_prod_..."
    uv run python examples/quickstart.py

If RACLIP_API_KEY isn't in the environment, the script falls back to reading
it from ~/fastmedical/raclip-api/.env for local dev convenience. Customers
would just set the env var.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from raclip import AsyncClient, Client, RaclipError


DEV_ENV_FALLBACK = Path.home() / "fastmedical" / "raclip-api" / ".env"


def _load_api_key_from_fallback_env() -> None:
    if os.environ.get("RACLIP_API_KEY"):
        return
    if not DEV_ENV_FALLBACK.exists():
        return
    for line in DEV_ENV_FALLBACK.read_text().splitlines():
        if line.startswith("RACLIP_API_KEY="):
            os.environ["RACLIP_API_KEY"] = line.split("=", 1)[1].strip()
            return


def _bytes_human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n //= 1024  # type: ignore[assignment]
    return f"{n} TB"


def run_sync() -> str:
    """Sync path: list devices, pick one, list calls, print latest, download."""
    print("=== SYNC CLIENT ===")
    with Client() as client:
        devices = client.devices.list()
        print(f"Found {devices.total} device(s) in this org")
        for d in devices.devices:
            print(f"  - {d.device_id}  status={d.status}  model={d.device_model}")

        if not devices.devices:
            print("  no devices — cannot continue")
            sys.exit(1)

        stats = client.devices.stats()
        print(
            f"Device stats: online={stats.online_devices} "
            f"offline={stats.offline_devices} total={stats.total_devices}"
        )

        device_id = devices.devices[0].device_id
        print(f"\nUsing device: {device_id}")

        calls = client.calls.list(device_id, per_page=5)
        print(f"Found {calls.total} call(s) in the last 30 days")
        for c in calls.calls:
            print(
                f"  - {c.call_id}  dur={c.duration_seconds:.1f}s  "
                f"size={_bytes_human(c.file_size_bytes)}  "
                f"created={c.created_at.isoformat()}"
            )

        if not calls.calls:
            print("  no calls — skipping download test")
            return device_id

        latest = client.calls.latest(device_id)
        print(f"\nLatest call: {latest.call_id}")
        print(f"  download_url present: {bool(latest.download_url)}")
        if latest.download_url:
            print(f"  download_url prefix: {latest.download_url[:80]}...")

        call_stats = client.calls.statistics(device_id)
        print(
            f"Call stats: {call_stats.total_calls} calls, "
            f"{call_stats.total_duration_seconds:.1f}s total, "
            f"{_bytes_human(call_stats.total_size_bytes)}"
        )

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            dest_path = Path(tmp.name)
        written = client.calls.download(device_id, latest.call_id, dest=dest_path)
        size = Path(written).stat().st_size
        print(f"Downloaded {latest.call_id} -> {written} ({_bytes_human(size)})")
        if size == 0:
            raise RuntimeError("downloaded file is empty")

        return device_id


async def run_async(device_id: str) -> None:
    """Async path: exercise the same surface to prove AsyncClient works."""
    print("\n=== ASYNC CLIENT ===")
    async with AsyncClient() as client:
        devices = await client.devices.list()
        print(f"[async] {devices.total} device(s) via AsyncClient")

        calls = await client.calls.list(device_id, per_page=3)
        print(f"[async] {calls.total} call(s) for {device_id}")
        for c in calls.calls:
            print(f"  - {c.call_id}  dur={c.duration_seconds:.1f}s")


def main() -> None:
    _load_api_key_from_fallback_env()
    if not os.environ.get("RACLIP_API_KEY"):
        print("ERROR: RACLIP_API_KEY not set", file=sys.stderr)
        sys.exit(2)

    try:
        device_id = run_sync()
        asyncio.run(run_async(device_id))
    except RaclipError as e:
        print(f"\nraclip API error: {type(e).__name__}: {e}", file=sys.stderr)
        if e.status_code is not None:
            print(f"  status_code={e.status_code}", file=sys.stderr)
        if e.response_body is not None:
            print(f"  response_body={e.response_body!r}", file=sys.stderr)
        sys.exit(1)

    print("\nOK — SDK v0.0.1 end-to-end smoke passed.")


if __name__ == "__main__":
    main()
