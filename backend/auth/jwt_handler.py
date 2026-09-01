"""JWT access and refresh token handling."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from config.settings import get_settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str, username: str, roles: list[str], permissions: list[str], session_id: str) -> tuple[str, int]:
    settings = get_settings()
    expires = _now() + timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": user_id,
        "username": username,
        "roles": roles,
        "permissions": permissions,
        "sid": session_id,
        "type": "access",
        "exp": expires,
        "iat": _now(),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, int(settings.access_token_minutes * 60)


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.PyJWTError:
        return None


def create_csrf_token() -> str:
    return secrets.token_urlsafe(32)
