"""Audit logging service."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from models.security import AuditLogEntry, User
from repositories.security_repository import get_security_repository


def log_audit_event(
    user: User,
    action: str,
    *,
    resource_type: str = "",
    resource_id: str = "",
    dealer_name: str = "",
    gstin: str = "",
    session_id: str = "",
    ip_address: str = "",
    user_agent: str = "",
    result: str = "success",
    details: Optional[Dict[str, Any]] = None,
) -> AuditLogEntry:
    entry = AuditLogEntry(
        log_id=str(uuid.uuid4()),
        timestamp=AuditLogEntry.now_iso(),
        user_id=user.user_id,
        username=user.username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        dealer_name=dealer_name,
        gstin=gstin,
        session_id=session_id,
        ip_address=ip_address,
        user_agent=user_agent,
        result=result,
        details=details or {},
    )
    return get_security_repository().append_audit_log(entry)


def list_recent_audit_logs(limit: int = 20, user_id: Optional[str] = None) -> list[AuditLogEntry]:
    return get_security_repository().list_audit_logs(limit=limit, user_id=user_id)
