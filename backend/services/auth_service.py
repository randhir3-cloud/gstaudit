"""Authentication service — login, refresh, logout, session management."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from auth.jwt_handler import create_access_token, create_csrf_token, create_refresh_token, hash_token
from auth.password import hash_password, validate_password, verify_password
from models.security import LoginResponse, User, UserSession, UserStatus
from repositories.security_repository import get_security_repository
from services.audit_log_service import log_audit_event


def _repo():
    return get_security_repository()


def bootstrap_security() -> None:
    """Seed roles and default admin user if none exist."""
    repo = _repo()
    repo.seed_defaults()
    if repo.user_count() > 0:
        return
    default_password = os.getenv("GAIS_ADMIN_PASSWORD", "Admin@123456!")
    admin = User(
        user_id=str(uuid.uuid4()),
        username=os.getenv("GAIS_ADMIN_USERNAME", "admin"),
        email="admin@gais.local",
        full_name="System Administrator",
        department="GST Audit",
        office="Head Office",
        designation="Administrator",
        role_ids=["role_admin"],
        status=UserStatus.ACTIVE,
        must_change_password=False,
        created_at=User.now_iso(),
        updated_at=User.now_iso(),
    )
    repo.create_user(admin, hash_password(default_password))


def login(username: str, password: str, *, ip_address: str = "", user_agent: str = "") -> Tuple[LoginResponse, str, str]:
    repo = _repo()
    user = repo.get_user_by_username(username)
    if not user or user.status != UserStatus.ACTIVE:
        raise ValueError("Invalid username or password")
    pwd_hash = repo.get_user_password_hash(user.user_id)
    if not pwd_hash or not verify_password(password, pwd_hash):
        if user:
            log_audit_event(user, "login_failed", ip_address=ip_address, user_agent=user_agent, result="failure")
        raise ValueError("Invalid username or password")

    settings = repo.get_settings()
    active = repo.list_user_sessions(user.user_id)
    if len(active) >= settings.max_concurrent_sessions:
        repo.revoke_session(active[0].session_token)

    session_token = str(uuid.uuid4())
    refresh_token = create_refresh_token()
    refresh_hash = hash_token(refresh_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    repo.create_session(
        UserSession(
            session_token=session_token,
            user_id=user.user_id,
            refresh_token_hash=refresh_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            last_activity_at=User.now_iso(),
            created_at=User.now_iso(),
            expires_at=expires_at,
        )
    )

    user.last_login_at = User.now_iso()
    repo.update_user(user)

    access_token, expires_in = create_access_token(user.user_id, user.username, user.roles, user.permissions, session_token)
    csrf = create_csrf_token()
    log_audit_event(user, "login", ip_address=ip_address, user_agent=user_agent)
    return LoginResponse(access_token=access_token, expires_in=expires_in, user=user, csrf_token=csrf), refresh_token, csrf


def refresh_access_token(refresh_token: str, *, ip_address: str = "", user_agent: str = "") -> Tuple[LoginResponse, str]:
    repo = _repo()
    refresh_hash = hash_token(refresh_token)
    session = repo.get_session_by_refresh_hash(refresh_hash)
    if not session or not session.is_active:
        raise ValueError("Invalid refresh token")
    user = repo.get_user_by_id(session.user_id)
    if not user or user.status != UserStatus.ACTIVE:
        raise ValueError("User inactive")

    repo.touch_session(session.session_token)
    new_refresh = create_refresh_token()
    repo.revoke_session(session.session_token)
    repo.create_session(
        UserSession(
            session_token=session.session_token,
            user_id=user.user_id,
            refresh_token_hash=hash_token(new_refresh),
            ip_address=ip_address,
            user_agent=user_agent,
            last_activity_at=User.now_iso(),
            created_at=User.now_iso(),
            expires_at=session.expires_at,
        )
    )
    access_token, expires_in = create_access_token(user.user_id, user.username, user.roles, user.permissions, session.session_token)
    csrf = create_csrf_token()
    return LoginResponse(access_token=access_token, expires_in=expires_in, user=user, csrf_token=csrf), new_refresh


def logout(session_token: str, user: User, *, ip_address: str = "", user_agent: str = "") -> None:
    _repo().revoke_session(session_token)
    log_audit_event(user, "logout", ip_address=ip_address, user_agent=user_agent)


def logout_all_devices(user: User, except_session: Optional[str] = None, *, ip_address: str = "", user_agent: str = "") -> int:
    count = _repo().revoke_all_sessions(user.user_id, except_token=except_session)
    log_audit_event(user, "logout_all", ip_address=ip_address, user_agent=user_agent, details={"revoked": count})
    return count


def get_current_user_profile(user_id: str) -> Optional[User]:
    return _repo().get_user_by_id(user_id)


def list_open_sessions(user_id: str) -> list[UserSession]:
    return _repo().list_user_sessions(user_id)
