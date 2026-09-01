"""Administration routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from models.security import DepartmentSettings, UserCreateRequest, UserUpdateRequest
from services.audit_log_service import list_recent_audit_logs
from services.settings_service import get_department_settings, get_system_health, update_department_settings
from services.user_service import create_user, delete_user, list_permissions, list_roles, list_users, update_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _actor(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/users")
async def admin_list_users(request: Request, limit: int = 100):
    _actor(request)
    return {"users": [u.model_dump() for u in list_users(limit=limit)]}


@router.post("/users", status_code=201)
async def admin_create_user(body: UserCreateRequest, request: Request):
    actor = _actor(request)
    try:
        return create_user(body, actor).model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/users/{user_id}")
async def admin_update_user(user_id: str, body: UserUpdateRequest, request: Request):
    actor = _actor(request)
    try:
        return update_user(user_id, body, actor).model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/users/{user_id}")
async def admin_delete_user(user_id: str, request: Request):
    actor = _actor(request)
    try:
        delete_user(user_id, actor)
        return {"deleted": user_id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/roles")
async def admin_list_roles(request: Request):
    _actor(request)
    return {"roles": [r.model_dump() for r in list_roles()]}


@router.get("/permissions")
async def admin_list_permissions(request: Request):
    _actor(request)
    return {"permissions": [p.model_dump() for p in list_permissions()]}


@router.get("/audit-logs")
async def admin_audit_logs(request: Request, limit: int = 100, user_id: Optional[str] = None):
    _actor(request)
    logs = list_recent_audit_logs(limit=limit, user_id=user_id)
    return {"logs": [l.model_dump() for l in logs], "total": len(logs)}


@router.get("/settings")
async def admin_get_settings(request: Request):
    _actor(request)
    return get_department_settings().model_dump()


@router.patch("/settings")
async def admin_update_settings(body: DepartmentSettings, request: Request):
    actor = _actor(request)
    return update_department_settings(body, actor).model_dump()


@router.get("/health")
async def admin_system_health(request: Request):
    _actor(request)
    return get_system_health().model_dump()
