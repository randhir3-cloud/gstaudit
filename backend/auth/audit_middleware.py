"""Post-request audit logging for mutating API calls."""

from __future__ import annotations

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from services.audit_log_service import log_audit_event

ACTION_MAP = {
    "/api/session/sync": "session_sync",
    "/api/comparison/gstr1-eway": "comparison",
    "/api/comparison/cache-workbook": "upload",
    "/api/report/generate": "report_generated",
    "/api/investigation/bulk": "case_bulk_update",
    "/api/jobs": "job_created",
    "/api/intelligence/analyze": "intelligence",
    "/api/merge/gstr1": "merge",
    "/api/merge/gstr2a": "merge",
    "/api/merge/eway": "merge",
    "/api/eway/classify": "upload",
    "/api/eway/validate": "upload",
}


def _action_for_path(method: str, path: str) -> str | None:
    if method not in ("POST", "PATCH", "PUT", "DELETE"):
        return None
    if path.startswith("/api/auth") or path.startswith("/api/admin"):
        return None
    for prefix, action in ACTION_MAP.items():
        if path.startswith(prefix):
            return action
    if path.startswith("/api/investigation/") and method == "PATCH":
        return "case_update"
    if path.startswith("/api/jobs/") and "cancel" in path:
        return "job_cancel"
    if path.startswith("/api/jobs/") and "retry" in path:
        return "job_retry"
    if path.startswith("/api/"):
        return f"{method.lower()}_{path.split('/')[2] if len(path.split('/')) > 2 else 'api'}"
    return None


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        user = getattr(request.state, "user", None)
        action = _action_for_path(request.method, request.url.path)
        if user and action and response.status_code < 400:
            session_id = request.query_params.get("session_id", "")
            if not session_id and request.method == "POST":
                try:
                    body = await request.body()
                    # body may be consumed - skip details
                except Exception:
                    pass
            log_audit_event(
                user,
                action,
                session_id=session_id,
                ip_address=getattr(request.state, "client_ip", ""),
                user_agent=getattr(request.state, "user_agent", ""),
                details={"method": request.method, "path": request.url.path, "status": response.status_code},
            )
        return response
