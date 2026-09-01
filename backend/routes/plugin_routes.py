"""Plugin catalog API."""

from __future__ import annotations

from fastapi import APIRouter, Request

from plugins.sdk.loader import ensure_plugins_loaded
from plugins.sdk.registry import plugin_registry

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


@router.get("")
async def list_plugins(_request: Request):
    ensure_plugins_loaded()
    return plugin_registry.public_catalog()
