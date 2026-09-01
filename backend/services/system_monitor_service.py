"""Platform operations — health, metrics, logs, and configuration."""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app_state import get_build_id, get_started_at, get_version
from config.settings import get_settings
from models.job import BackgroundJob, JobStatus, JobType
from models.system_ops import (
    AuditSessionMetrics,
    BackupMetrics,
    ComponentHealth,
    DatabaseMetrics,
    JobMonitorMetrics,
    PerformanceMetrics,
    StorageMetrics,
    SystemConfiguration,
    SystemHealthResponse,
    SystemLogEntry,
    SystemLogsResponse,
    SystemMetricsResponse,
    SystemVersionResponse,
    UserActivityMetrics,
    LogSource,
)
from repositories.factory import get_repositories
from repositories.job_repository import get_job_repository
from repositories.security_repository import get_security_repository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _job_duration_seconds(job: BackgroundJob) -> Optional[float]:
    start = _parse_iso(job.started_at or job.created_at)
    end = _parse_iso(job.completed_at)
    if not start or not end:
        return None
    return max(0.0, (end - start).total_seconds())


def _list_all_jobs(limit: int = 500) -> List[BackgroundJob]:
    repo = get_job_repository()
    if hasattr(repo, "list_all"):
        return repo.list_all(limit=limit)
    if hasattr(repo, "_jobs"):
        jobs = list(repo._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]
    return []


def _list_audit_sessions(limit: int = 500):
    repos = get_repositories()
    return repos.audit_session.search(limit=limit)


def _host_metrics() -> StorageMetrics:
    metrics = StorageMetrics()
    try:
        usage = shutil.disk_usage(Path.cwd().anchor or "/")
        metrics.disk_total_bytes = usage.total
        metrics.disk_used_bytes = usage.used
        metrics.disk_free_bytes = usage.free
        metrics.disk_used_percent = round((usage.used / usage.total) * 100, 1) if usage.total else 0.0
    except OSError:
        pass
    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        metrics.memory_total_bytes = vm.total
        metrics.memory_used_bytes = vm.used
        metrics.memory_used_percent = round(vm.percent, 1)
        metrics.cpu_percent = round(psutil.cpu_percent(interval=0.1), 1)
    except Exception:
        pass
    return metrics


def _database_metrics() -> DatabaseMetrics:
    settings = get_settings()
    metrics = DatabaseMetrics(provider=settings.database_provider, connected=True)
    if settings.is_memory:
        metrics.connection_detail = "In-memory repository (no persistent connection)"
        metrics.migration_version = "memory"
        return metrics
    try:
        from sqlalchemy import text

        from db.session import get_engine, session_scope

        engine = get_engine()
        pool = engine.pool
        metrics.pool_size = pool.size()
        metrics.pool_checked_out = pool.checkedout()
        metrics.pool_overflow = pool.overflow()
        with session_scope() as db:
            db.execute(text("SELECT 1"))
            metrics.query_count_estimate = 1
            row = db.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
            if row:
                metrics.migration_version = str(row[0])
            size_row = db.execute(text("SELECT pg_database_size(current_database())")).first()
            if size_row:
                metrics.database_size_bytes = int(size_row[0])
        metrics.connection_detail = "PostgreSQL connected"
    except Exception as exc:
        metrics.connected = False
        metrics.connection_detail = str(exc)
    return metrics


def _job_metrics() -> JobMonitorMetrics:
    settings = get_settings()
    jobs = _list_all_jobs()
    metrics = JobMonitorMetrics(total=len(jobs))
    durations: List[float] = []
    oldest: Optional[datetime] = None
    for job in jobs:
        metrics.queued += job.status == JobStatus.QUEUED
        metrics.running += job.status == JobStatus.RUNNING
        metrics.completed += job.status == JobStatus.COMPLETED
        metrics.failed += job.status == JobStatus.FAILED
        metrics.retrying += job.status == JobStatus.RETRYING
        metrics.cancelled += job.status == JobStatus.CANCELLED
        created = _parse_iso(job.created_at)
        if created and (oldest is None or created < oldest):
            oldest = created
        duration = _job_duration_seconds(job)
        if duration is not None:
            durations.append(duration)
    if durations:
        metrics.average_duration_seconds = round(sum(durations) / len(durations), 2)
    if oldest:
        metrics.oldest_job_at = oldest.isoformat()
    running = metrics.running + metrics.retrying
    worker_count = max(1, settings.job_worker_count)
    metrics.worker_utilization_percent = round(min(100.0, (running / worker_count) * 100), 1)
    metrics.recent_jobs = [
        {
            "job_id": j.job_id,
            "title": j.title,
            "job_type": j.job_type.value,
            "status": j.status.value,
            "session_id": j.session_id,
            "created_at": j.created_at,
            "progress_percent": j.progress.percent,
        }
        for j in jobs[:10]
    ]
    return metrics


def _audit_session_metrics() -> AuditSessionMetrics:
    sessions = _list_audit_sessions()
    metrics = AuditSessionMetrics(total_sessions=len(sessions))
    durations: List[float] = []
    for session in sessions:
        if session.audit_status in ("draft", "in_progress", "ready"):
            metrics.open_sessions += 1
        if session.audit_status == "completed":
            metrics.completed_audits += 1
        updated = _parse_iso(session.updated_at)
        created = _parse_iso(session.created_at)
        if session.audit_status == "completed" and created and updated:
            durations.append((updated - created).total_seconds() / 3600)
        if session.audit_status == "completed" and updated:
            age_days = (_utcnow() - updated).days
            if age_days >= 90:
                metrics.archived_audits += 1
    if durations:
        metrics.average_audit_duration_hours = round(sum(durations) / len(durations), 2)
    return metrics


def _user_metrics() -> UserActivityMetrics:
    repo = get_security_repository()
    users = repo.list_users(limit=500)
    metrics = UserActivityMetrics(active_users=sum(1 for u in users if u.status.value == "active"))
    last_login: Optional[datetime] = None
    for user in users:
        login_at = _parse_iso(user.last_login_at)
        if login_at and (last_login is None or login_at > last_login):
            last_login = login_at
        sessions = repo.list_user_sessions(user.user_id)
        active = [s for s in sessions if s.is_active]
        metrics.concurrent_sessions += len(active)
        if active:
            metrics.logged_in_users += 1
    if last_login:
        metrics.last_login_at = last_login.isoformat()
    cutoff = _utcnow().timestamp() - 86400
    for entry in repo.list_audit_logs(limit=500):
        if entry.action != "login_failed":
            continue
        ts = _parse_iso(entry.timestamp)
        if ts and ts.timestamp() >= cutoff:
            metrics.failed_logins_24h += 1
    return metrics


def _performance_metrics() -> PerformanceMetrics:
    jobs = _list_all_jobs()
    merge_durations: List[float] = []
    comparison_durations: List[float] = []
    report_durations: List[float] = []
    workbook_sizes: List[int] = []
    for job in jobs:
        duration = _job_duration_seconds(job)
        if duration is None:
            continue
        if job.job_type == JobType.MERGE:
            merge_durations.append(duration)
        elif job.job_type == JobType.COMPARISON:
            comparison_durations.append(duration)
        elif job.job_type == JobType.REPORT:
            report_durations.append(duration)
        size = job.payload.get("workbook_size_bytes") or job.result_ref.get("workbook_size_bytes")
        if isinstance(size, (int, float)) and size > 0:
            workbook_sizes.append(int(size))
    metrics = PerformanceMetrics()
    if merge_durations:
        metrics.average_merge_seconds = round(sum(merge_durations) / len(merge_durations), 2)
    if comparison_durations:
        metrics.average_comparison_seconds = round(sum(comparison_durations) / len(comparison_durations), 2)
    if report_durations:
        metrics.average_report_seconds = round(sum(report_durations) / len(report_durations), 2)
    if workbook_sizes:
        metrics.largest_workbook_bytes = max(workbook_sizes)
        metrics.average_workbook_bytes = round(sum(workbook_sizes) / len(workbook_sizes), 2)
    return metrics


def _backup_metrics() -> BackupMetrics:
    last = os.getenv("GAIS_BACKUP_LAST_RUN")
    nxt = os.getenv("GAIS_BACKUP_NEXT_RUN")
    size = os.getenv("GAIS_BACKUP_SIZE_BYTES")
    restore = os.getenv("GAIS_BACKUP_RESTORE_POINT")
    configured = bool(last or nxt or size or restore)
    return BackupMetrics(
        last_backup_at=last,
        next_backup_at=nxt,
        backup_size_bytes=int(size) if size and size.isdigit() else None,
        restore_point=restore,
        configured=configured,
    )


def get_system_health() -> SystemHealthResponse:
    settings = get_settings()
    storage = _host_metrics()
    db = _database_metrics()
    jobs = _job_metrics()
    uptime = int((_utcnow() - get_started_at()).total_seconds())
    components = [
        ComponentHealth(name="Application", status="healthy", detail="FastAPI service running"),
        ComponentHealth(
            name="Database",
            status="healthy" if db.connected else "unhealthy",
            detail=db.connection_detail,
        ),
        ComponentHealth(
            name="Background Workers",
            status="healthy" if settings.job_worker_embedded else "degraded",
            detail=f"{settings.job_worker_count} worker(s), embedded={settings.job_worker_embedded}",
        ),
        ComponentHealth(
            name="Job Queue",
            status="degraded" if jobs.failed else "healthy",
            detail=f"{jobs.queued} queued, {jobs.running} running, {jobs.failed} failed",
        ),
    ]
    disk_status = "healthy" if storage.disk_used_percent < 90 else "degraded"
    memory_status = "healthy"
    if storage.memory_used_percent is not None and storage.memory_used_percent >= 90:
        memory_status = "degraded"
    cpu_status = "healthy"
    if storage.cpu_percent is not None and storage.cpu_percent >= 90:
        cpu_status = "degraded"
    overall = "healthy"
    if not db.connected or jobs.failed > 0 or disk_status == "degraded":
        overall = "degraded"
    if not db.connected:
        overall = "unhealthy"
    return SystemHealthResponse(
        status=overall,
        application="healthy",
        database="healthy" if db.connected else "unhealthy",
        workers="healthy" if settings.job_worker_embedded else "degraded",
        job_queue="degraded" if jobs.failed else "healthy",
        disk=disk_status,
        memory=memory_status,
        cpu=cpu_status,
        storage=disk_status,
        version=get_version(),
        uptime_seconds=uptime,
        components=components,
    )


def get_system_metrics() -> SystemMetricsResponse:
    return SystemMetricsResponse(
        database=_database_metrics(),
        jobs=_job_metrics(),
        audit_sessions=_audit_session_metrics(),
        users=_user_metrics(),
        performance=_performance_metrics(),
        storage=_host_metrics(),
        backup=_backup_metrics(),
    )


def get_system_jobs(limit: int = 50) -> dict:
    jobs = _list_all_jobs(limit=limit)
    return {
        "jobs": [j.model_dump() for j in jobs],
        "summary": _job_metrics().model_dump(),
        "total": len(jobs),
    }


def get_system_users() -> dict:
    repo = get_security_repository()
    users = repo.list_users(limit=200)
    return {"users": [u.model_dump() for u in users], "summary": _user_metrics().model_dump()}


def get_system_storage() -> StorageMetrics:
    return _host_metrics()


def get_system_version() -> SystemVersionResponse:
    settings = get_settings()
    env = os.getenv("GAIS_ENV", "development" if settings.is_memory else "production")
    started = get_started_at()
    return SystemVersionResponse(
        version=get_version(),
        build_id=get_build_id(),
        environment=env,
        uptime_seconds=int((_utcnow() - started).total_seconds()),
        started_at=started.isoformat(),
    )


def get_system_configuration() -> SystemConfiguration:
    settings = get_settings()
    dept = get_security_repository().get_settings()
    env = os.getenv("GAIS_ENV", "development" if settings.is_memory else "production")
    return SystemConfiguration(
        database_provider=settings.database_provider,
        worker_count=settings.job_worker_count,
        worker_embedded=settings.job_worker_embedded,
        auth_provider=dept.auth_provider,
        auth_disabled=settings.auth_disabled,
        ldap_enabled=dept.ldap_enabled,
        oidc_enabled=dept.oidc_enabled,
        version=get_version(),
        build_id=get_build_id(),
        environment=env,
        department_name=dept.department_name,
        theme_default=dept.theme_default,
        session_timeout_minutes=dept.session_timeout_minutes,
        rate_limit_per_minute=dept.rate_limit_per_minute,
    )


def _classify_log_source(action: str) -> LogSource:
    security_actions = {"login", "logout", "login_failed", "logout_all", "password_change", "settings_change"}
    worker_actions = {"job_queued", "job_completed", "job_failed", "job_cancelled"}
    if action in security_actions:
        return "security"
    if action in worker_actions:
        return "worker"
    if action.startswith("job_"):
        return "worker"
    return "application"


def search_system_logs(
    *,
    source: Optional[LogSource] = None,
    action: Optional[str] = None,
    user: Optional[str] = None,
    limit: int = 100,
) -> SystemLogsResponse:
    repo = get_security_repository()
    entries = repo.list_audit_logs(limit=500)
    logs: List[SystemLogEntry] = []
    for entry in entries:
        src = _classify_log_source(entry.action)
        if source and src != source:
            continue
        if action and action.lower() not in entry.action.lower():
            continue
        if user and user.lower() not in entry.username.lower():
            continue
        logs.append(
            SystemLogEntry(
                timestamp=entry.timestamp,
                source=src,
                level="error" if entry.result != "success" else "info",
                user=entry.username,
                action=entry.action,
                message=entry.details.get("message", entry.action) if entry.details else entry.action,
                session_id=entry.session_id,
                result=entry.result,
            )
        )
        if len(logs) >= limit:
            break
    for job in _list_all_jobs(limit=20):
        for log in job.logs[-5:]:
            src: LogSource = "worker"
            if source and src != source:
                continue
            logs.append(
                SystemLogEntry(
                    timestamp=log.created_at or job.updated_at,
                    source=src,
                    level=log.level,
                    user="system",
                    action=f"job:{job.job_type.value}",
                    message=log.message,
                    session_id=job.session_id,
                    result=job.status.value,
                )
            )
    logs.sort(key=lambda item: item.timestamp, reverse=True)
    trimmed = logs[:limit]
    return SystemLogsResponse(logs=trimmed, total=len(trimmed), source=source)
