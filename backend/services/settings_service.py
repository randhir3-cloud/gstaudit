"""Department and system settings service."""

from __future__ import annotations

from models.security import DepartmentSettings, SystemHealth
from repositories.security_repository import get_security_repository
from services.audit_log_service import log_audit_event
from models.security import User


def get_department_settings() -> DepartmentSettings:
    return get_security_repository().get_settings()


def update_department_settings(settings: DepartmentSettings, actor: User) -> DepartmentSettings:
    saved = get_security_repository().save_settings(settings)
    log_audit_event(actor, "settings_change", resource_type="settings", details={"keys": list(settings.model_dump().keys())})
    return saved


def get_system_health() -> SystemHealth:
    from config.settings import get_settings
    from repositories.job_repository import get_job_repository
    from models.job import JobStatus

    settings = get_settings()
    repo = get_security_repository()
    jobs = []
    try:
        job_repo = get_job_repository()
        if hasattr(job_repo, "_jobs"):
            jobs = list(job_repo._jobs.values())
    except Exception:
        jobs = []
    queued = sum(1 for j in jobs if j.status == JobStatus.QUEUED)
    active_sessions = sum(len(repo.list_user_sessions(u.user_id)) for u in repo.list_users(500))
    return SystemHealth(
        status="healthy",
        database=settings.database_provider,
        worker_embedded=settings.job_worker_embedded,
        worker_count=settings.job_worker_count,
        active_sessions=active_sessions,
        queued_jobs=queued,
        user_count=repo.user_count(),
    )
