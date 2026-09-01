"""Authentication and authorization middleware."""

from __future__ import annotations

from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from auth.jwt_handler import decode_access_token
from auth.permissions import permission_for_route
from auth.rate_limit import rate_limiter
from config.settings import get_settings
from models.security import PermissionCode, RoleName, User, UserStatus
from repositories.security_repository import get_security_repository


PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}
PUBLIC_PREFIXES = ("/api/auth/login", "/api/auth/refresh")


def _bypass_user() -> User:
    return User(
        user_id="system-bypass",
        username="system",
        full_name="System Bypass",
        roles=[RoleName.SYSTEM.value, RoleName.ADMINISTRATOR.value],
        permissions=[p.value for p in PermissionCode],
        status=UserStatus.ACTIVE,
    )


def _extract_bearer(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.headers.get("x-access-token")


def _user_from_token(token: str) -> Optional[User]:
    payload = decode_access_token(token)
    if not payload:
        return None
    repo = get_security_repository()
    user = repo.get_user_by_id(payload.get("sub", ""))
    if not user or user.status != UserStatus.ACTIVE:
        return None
    return user


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        request.state.client_ip = client_ip
        request.state.user_agent = request.headers.get("user-agent", "")

        if settings.auth_disabled:
            request.state.user = _bypass_user()
            return await call_next(request)

        if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        if path.startswith("/api/") or path.startswith("/ws/"):
            if not settings.rate_limit_disabled:
                limit_key = f"{client_ip}:{path.split('/')[2] if len(path.split('/')) > 2 else 'root'}"
                if not rate_limiter.allow(limit_key):
                    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

            token = _extract_bearer(request)
            if not token and path.startswith("/ws/"):
                token = request.query_params.get("token")
            if not token:
                return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

            user = _user_from_token(token)
            if not user:
                return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

            perm = permission_for_route(request.method, path)
            if perm and not user.has_permission(perm):
                return JSONResponse(status_code=403, content={"detail": f"Permission denied: {perm}"})

            request.state.user = user

        return await call_next(request)
