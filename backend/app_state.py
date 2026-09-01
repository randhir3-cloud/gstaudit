"""Process-wide runtime state for operations monitoring."""

from __future__ import annotations

from datetime import datetime, timezone

_started_at: datetime = datetime.now(timezone.utc)
_build_id: str = "dev"
_version: str = "0.7.0"


def mark_started() -> None:
    global _started_at
    _started_at = datetime.now(timezone.utc)


def get_started_at() -> datetime:
    return _started_at


def set_build_metadata(*, version: str, build_id: str) -> None:
    global _version, _build_id
    _version = version
    _build_id = build_id


def get_version() -> str:
    return _version


def get_build_id() -> str:
    return _build_id
