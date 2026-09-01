"""Authentication routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response

from auth.jwt_handler import decode_access_token
from models.security import LoginRequest, RefreshRequest
from services.auth_service import get_current_user_profile, list_open_sessions, login, logout, logout_all_devices, refresh_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

REFRESH_COOKIE = "gais_refresh_token"
CSRF_COOKIE = "gais_csrf_token"


def _set_auth_cookies(response: Response, refresh_token: str, csrf_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/api/auth",
    )
    response.set_cookie(
        key=CSRF_COOKIE,
        value=csrf_token,
        httponly=False,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth")
    response.delete_cookie(CSRF_COOKIE, path="/")


@router.post("/login")
async def auth_login(body: LoginRequest, request: Request, response: Response):
    try:
        result, refresh, csrf = login(
            body.username,
            body.password,
            ip_address=getattr(request.state, "client_ip", ""),
            user_agent=getattr(request.state, "user_agent", ""),
        )
        _set_auth_cookies(response, refresh, csrf)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/refresh")
async def auth_refresh(request: Request, response: Response, body: Optional[RefreshRequest] = None):
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if body and body.refresh_token:
        refresh_token = body.refresh_token
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    try:
        result, new_refresh = refresh_access_token(
            refresh_token,
            ip_address=getattr(request.state, "client_ip", ""),
            user_agent=getattr(request.state, "user_agent", ""),
        )
        _set_auth_cookies(response, new_refresh, result.csrf_token)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout")
async def auth_logout(request: Request, response: Response):
    user = getattr(request.state, "user", None)
    token = _extract_session_token(request)
    if user and token:
        logout(token, user, ip_address=getattr(request.state, "client_ip", ""), user_agent=getattr(request.state, "user_agent", ""))
    _clear_auth_cookies(response)
    return {"status": "logged_out"}


@router.post("/logout-all")
async def auth_logout_all(request: Request, response: Response):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = _extract_session_token(request)
    count = logout_all_devices(user, except_session=token, ip_address=getattr(request.state, "client_ip", ""), user_agent=getattr(request.state, "user_agent", ""))
    _clear_auth_cookies(response)
    return {"revoked": count}


@router.get("/me")
async def auth_me(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    profile = get_current_user_profile(user.user_id) or user
    return profile.model_dump()


@router.get("/sessions")
async def auth_sessions(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    sessions = list_open_sessions(user.user_id)
    return {"sessions": [s.model_dump() for s in sessions], "total": len(sessions)}


def _extract_session_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        payload = decode_access_token(auth[7:].strip())
        if payload:
            return payload.get("sid")
    return None
