from __future__ import annotations

from typing import Any


class RaclipError(Exception):
    """Base class for all raclip SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    @property
    def detail(self) -> str:
        if isinstance(self.response_body, dict):
            value = self.response_body.get("detail")
            if isinstance(value, str):
                return value
        return self.message

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(status_code={self.status_code!r}, "
            f"message={self.message!r})"
        )


class APIConnectionError(RaclipError):
    """Network-level failure reaching the gateway."""


class APIError(RaclipError):
    """5xx response from the gateway or raclip-api."""


class AuthenticationError(RaclipError):
    """401 — missing or invalid API key."""


class PermissionError(RaclipError):  # noqa: A001 - intentional shadow of builtin
    """403 — caller is authenticated but not allowed."""


class NotFoundError(RaclipError):
    """404 — resource (device, call) does not exist."""


class ValidationError(RaclipError):
    """400 / 422 — request did not pass validation."""


class RateLimitError(RaclipError):
    """429 — per-key rate limit exceeded."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: Any = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)
        self.retry_after = retry_after
