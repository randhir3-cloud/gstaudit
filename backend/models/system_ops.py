"""Platform operations models — system monitor responses."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


LogSource = Literal["system", "worker", "security", "application"]


class ComponentHealth(BaseModel):
    name: str
    status: str = "healthy"
    detail: str = ""


class SystemHealthResponse(BaseModel):
    status: str = "healthy"
    application: str = "healthy"
    database: str = "healthy"
    workers: str = "healthy"
    job_queue: str = "healthy"
    disk: str = "healthy"
    memory: str = "healthy"
    cpu: str = "healthy"
    storage: str = "healthy"
    version: str = ""
    uptime_seconds: int = 0
    components: List[ComponentHealth] = Field(default_factory=list)


class DatabaseMetrics(BaseModel):
    provider: str = "memory"
    connected: bool = True
    pool_size: int = 0
    pool_checked_out: int = 0
    pool_overflow: int = 0
    query_count_estimate: int = 0
    migration_version: str = ""
    database_size_bytes: Optional[int] = None
    connection_detail: str = ""


class JobMonitorMetrics(BaseModel):
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    retrying: int = 0
    cancelled: int = 0
    total: int = 0
    average_duration_seconds: Optional[float] = None
    oldest_job_at: Optional[str] = None
    worker_utilization_percent: float = 0.0
    recent_jobs: List[Dict[str, Any]] = Field(default_factory=list)


class AuditSessionMetrics(BaseModel):
    total_sessions: int = 0
    open_sessions: int = 0
    completed_audits: int = 0
    archived_audits: int = 0
    average_audit_duration_hours: Optional[float] = None


class UserActivityMetrics(BaseModel):
    active_users: int = 0
    logged_in_users: int = 0
    failed_logins_24h: int = 0
    last_login_at: Optional[str] = None
    concurrent_sessions: int = 0


class PerformanceMetrics(BaseModel):
    average_merge_seconds: Optional[float] = None
    average_comparison_seconds: Optional[float] = None
    average_report_seconds: Optional[float] = None
    largest_workbook_bytes: int = 0
    average_workbook_bytes: Optional[float] = None


class StorageMetrics(BaseModel):
    disk_total_bytes: int = 0
    disk_used_bytes: int = 0
    disk_free_bytes: int = 0
    disk_used_percent: float = 0.0
    memory_total_bytes: Optional[int] = None
    memory_used_bytes: Optional[int] = None
    memory_used_percent: Optional[float] = None
    cpu_percent: Optional[float] = None


class BackupMetrics(BaseModel):
    last_backup_at: Optional[str] = None
    next_backup_at: Optional[str] = None
    backup_size_bytes: Optional[int] = None
    restore_point: Optional[str] = None
    configured: bool = False


class SystemConfiguration(BaseModel):
    database_provider: str = "memory"
    worker_count: int = 2
    worker_embedded: bool = True
    auth_provider: str = "local"
    auth_disabled: bool = False
    ldap_enabled: bool = False
    oidc_enabled: bool = False
    version: str = ""
    build_id: str = ""
    environment: str = "development"
    department_name: str = ""
    theme_default: str = "dark"
    session_timeout_minutes: int = 480
    rate_limit_per_minute: int = 120


class SystemMetricsResponse(BaseModel):
    database: DatabaseMetrics
    jobs: JobMonitorMetrics
    audit_sessions: AuditSessionMetrics
    users: UserActivityMetrics
    performance: PerformanceMetrics
    storage: StorageMetrics
    backup: BackupMetrics


class SystemLogEntry(BaseModel):
    timestamp: str
    source: LogSource
    level: str = "info"
    user: str = ""
    action: str = ""
    message: str = ""
    session_id: str = ""
    result: str = ""


class SystemLogsResponse(BaseModel):
    logs: List[SystemLogEntry] = Field(default_factory=list)
    total: int = 0
    source: Optional[LogSource] = None


class SystemVersionResponse(BaseModel):
    version: str
    build_id: str
    service: str = "GAIS"
    environment: str = "development"
    uptime_seconds: int = 0
    started_at: str = ""
