"""Official Python SDK for the raclip platform."""

from ._version import __version__
from .async_client import AsyncClient
from .client import Client
from .exceptions import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    NotFoundError,
    PermissionError,
    RaclipError,
    RateLimitError,
    ValidationError,
)
from .models import (
    Call,
    CallListResponse,
    CallStatistics,
    Device,
    DeviceAssignmentBreakdown,
    DeviceListResponse,
    DeviceStats,
    DeviceStatusSnapshot,
)

__all__ = [
    "__version__",
    "Client",
    "AsyncClient",
    "RaclipError",
    "APIConnectionError",
    "APIError",
    "AuthenticationError",
    "NotFoundError",
    "PermissionError",
    "RateLimitError",
    "ValidationError",
    "Call",
    "CallListResponse",
    "CallStatistics",
    "Device",
    "DeviceAssignmentBreakdown",
    "DeviceListResponse",
    "DeviceStats",
    "DeviceStatusSnapshot",
]
