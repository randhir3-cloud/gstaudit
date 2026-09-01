"""Platform operations routes — system monitor API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from models.system_ops import LogSource
from services.system_monitor_service import (
    get_system_configuration,
    get_system_health,
    get_system_jobs,
    get_system_metrics,
    get_system_storage,
    get_system_users,
    get_system_version,
    search_system_logs,
)

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def system_health(_request: Request):
    return get_system_health().model_dump()


@router.get("/metrics")
async def system_metrics(_request: Request):
    return get_system_metrics().model_dump()


@router.get("/jobs")
async def system_jobs(_request: Request, limit: int = 50):
    return get_system_jobs(limit=limit)


@router.get("/users")
async def system_users(_request: Request):
    return get_system_users()


@router.get("/storage")
async def system_storage(_request: Request):
    return get_system_storage().model_dump()


@router.get("/version")
async def system_version(_request: Request):
    return get_system_version().model_dump()


@router.get("/config")
async def system_config(_request: Request):
    return get_system_configuration().model_dump()


@router.get("/sessions")
async def system_audit_sessions(_request: Request):
    from services.system_monitor_service import _audit_session_metrics

    return _audit_session_metrics().model_dump()


@router.get("/logs")
async def system_logs(
    _request: Request,
    source: Optional[LogSource] = None,
    action: Optional[str] = None,
    user: Optional[str] = None,
    limit: int = 100,
):
    return search_system_logs(source=source, action=action, user=user, limit=limit).model_dump()


@router.get("/logs/export")
async def export_system_logs(
    _request: Request,
    source: Optional[LogSource] = None,
    action: Optional[str] = None,
    user: Optional[str] = None,
    limit: int = 500,
):
    result = search_system_logs(source=source, action=action, user=user, limit=limit)
    lines = ["timestamp,source,level,user,action,message,session_id,result"]
    for entry in result.logs:
        row = [
            entry.timestamp,
            entry.source,
            entry.level,
            entry.user,
            entry.action,
            entry.message.replace(",", ";"),
            entry.session_id,
            entry.result,
        ]
        lines.append(",".join(row))
    return PlainTextResponse("\n".join(lines), media_type="text/csv")
