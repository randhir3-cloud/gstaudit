"""MSAE result cache — in-memory per session."""

from __future__ import annotations

from typing import Optional

from models.msae import MSAEFullResponse

_cache: dict[str, MSAEFullResponse] = {}


def save_msae(session_id: str, data: MSAEFullResponse) -> None:
    _cache[session_id] = data


def get_msae(session_id: str) -> Optional[MSAEFullResponse]:
    return _cache.get(session_id)


def clear_msae(session_id: str) -> None:
    _cache.pop(session_id, None)


def clear_all() -> None:
    _cache.clear()
