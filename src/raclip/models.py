from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _RaclipModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Device(_RaclipModel):
    device_id: str
    org_id: str | None = None
    hardware_id: str
    mac_address: str
    serial_number: str | None = None
    firmware_version: str
    device_model: str

    unit_id: str | None = None
    location_id: str | None = None
    employee_id: str | None = None
    custom_fields: dict[str, Any] | None = None

    status: str
    last_seen: datetime | None = None
    last_registration: datetime
    assigned_at: datetime | None = None
    created_at: datetime


class DeviceListResponse(_RaclipModel):
    devices: list[Device]
    total: int
    page: int
    per_page: int


class DeviceAssignmentBreakdown(_RaclipModel):
    assigned_to_unit: int
    assigned_to_location: int
    assigned_to_employee: int


class DeviceStats(_RaclipModel):
    org_id: str
    total_devices: int
    assigned_devices: int
    unassigned_devices: int
    online_devices: int
    offline_devices: int
    recent_registrations_7d: int
    device_status_breakdown: dict[str, int]
    assignment_breakdown: DeviceAssignmentBreakdown


class DeviceStatusSnapshot(_RaclipModel):
    status: str
    last_seen: datetime | None = None
    is_online: bool


class Call(_RaclipModel):
    """A call recording.

    Shape is the union of what the list and retrieval endpoints return — fields
    present on one endpoint but not the other are marked optional, so the same
    model works in both contexts.
    """

    call_id: str
    device_id: str | None = None
    duration_seconds: float
    file_size_bytes: int
    storage_format: str = "mp3"
    bitrate: str = "128k"
    created_at: datetime
    download_url: str | None = None

    s3_path: str | None = None
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None
    call_sequence: int | None = None


class CallListResponse(_RaclipModel):
    device_id: str
    calls: list[Call]
    total: int
    page: int
    per_page: int


class CallStatistics(_RaclipModel):
    total_calls: int
    total_duration_seconds: float
    total_size_bytes: int
    avg_duration_seconds: float = Field(default=0.0)
    first_call: datetime | None = None
    latest_call: datetime | None = None
