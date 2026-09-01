"""FastAPI auth dependencies."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request

from models.security import User


def get_request_user(request: Request) -> User:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_permission(code: str):
    def _checker(request: Request) -> User:
        user = get_request_user(request)
        if not user.has_permission(code):
            raise HTTPException(status_code=403, detail=f"Permission denied: {code}")
        return user

    return _checker


def optional_user(request: Request) -> Optional[User]:
    return getattr(request.state, "user", None)
