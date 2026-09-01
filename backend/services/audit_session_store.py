"""Audit session store — delegates to repository layer."""

from __future__ import annotations

from typing import Optional

from models.audit_session import AuditSession
from repositories.factory import get_repositories


def get_session(session_id: Optional[str] = None) -> Optional[AuditSession]:
    repos = get_repositories()
    sid = session_id or repos.audit_session.get_active_session_id()
    if not sid:
        return None
    return repos.audit_session.get_by_id(sid)


def set_active_session(session_id: str) -> None:
    get_repositories().audit_session.set_active_session_id(session_id)


def upsert_session(session: AuditSession) -> AuditSession:
    repos = get_repositories()
    existing = repos.audit_session.get_by_id(session.session_id)
    if existing:
        return repos.audit_session.update(session)
    return repos.audit_session.create(session)


def clear_sessions() -> None:
    get_repositories().audit_session.clear_all()
