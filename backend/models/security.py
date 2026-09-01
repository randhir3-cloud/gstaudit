"""Security domain models — users, roles, permissions, audit logs, sessions."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    PENDING = "pending"


class RoleName(str, Enum):
    ADMINISTRATOR = "administrator"
    AUDIT_OFFICER = "audit_officer"
    SENIOR_OFFICER = "senior_officer"
    SUPERVISOR = "supervisor"
    VIEWER = "viewer"
    SYSTEM = "system"


class PermissionCode(str, Enum):
    UPLOAD_FILES = "upload_files"
    MERGE_FILES = "merge_files"
    RUN_COMPARISON = "run_comparison"
    DELETE_SESSION = "delete_session"
    GENERATE_REPORT = "generate_report"
    EXPORT_EXCEL = "export_excel"
    EXPORT_PDF = "export_pdf"
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_REPORTS = "view_reports"
    VIEW_DASHBOARD = "view_dashboard"
    UPDATE_CASES = "update_cases"
    VIEW_INTELLIGENCE = "view_intelligence"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_SESSIONS = "manage_sessions"
    CANCEL_JOBS = "cancel_jobs"
    VIEW_ADMIN = "view_admin"
    VIEW_SYSTEM_MONITOR = "view_system_monitor"
    MANAGE_AUDIT_CASES = "manage_audit_cases"
    SUPERVISE_AUDIT_CASES = "supervise_audit_cases"


class Permission(BaseModel):
    code: str
    label: str
    description: str = ""


class Role(BaseModel):
    role_id: str
    name: str
    label: str
    description: str = ""
    permissions: List[str] = Field(default_factory=list)
    is_system: bool = False


class User(BaseModel):
    user_id: str
    username: str
    email: str = ""
    full_name: str = ""
    department: str = ""
    office: str = ""
    designation: str = ""
    role_ids: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    status: UserStatus = UserStatus.ACTIVE
    must_change_password: bool = False
    password_changed_at: Optional[str] = None
    last_login_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def has_permission(self, code: str) -> bool:
        if PermissionCode.MANAGE_USERS.value in self.permissions or RoleName.ADMINISTRATOR.value in self.roles:
            return True
        return code in self.permissions


class UserCreateRequest(BaseModel):
    username: str
    password: str
    email: str = ""
    full_name: str = ""
    department: str = ""
    office: str = ""
    designation: str = ""
    role_ids: List[str] = Field(default_factory=list)
    status: UserStatus = UserStatus.ACTIVE


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    office: Optional[str] = None
    designation: Optional[str] = None
    role_ids: Optional[List[str]] = None
    status: Optional[UserStatus] = None
    password: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User
    csrf_token: str = ""


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class AuditLogEntry(BaseModel):
    log_id: str
    timestamp: str
    user_id: str
    username: str
    action: str
    resource_type: str = ""
    resource_id: str = ""
    dealer_name: str = ""
    gstin: str = ""
    session_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    result: str = "success"
    details: Dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


class UserSession(BaseModel):
    session_token: str
    user_id: str
    refresh_token_hash: str = ""
    ip_address: str = ""
    user_agent: str = ""
    is_active: bool = True
    last_activity_at: str = ""
    created_at: str = ""
    expires_at: str = ""


class PasswordPolicy(BaseModel):
    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True
    history_count: int = 5
    expiry_days: int = 90


class DepartmentSettings(BaseModel):
    department_name: str = "GST Audit Department"
    office_name: str = ""
    logo_url: str = ""
    theme_default: str = "dark"
    password_policy: PasswordPolicy = Field(default_factory=PasswordPolicy)
    session_timeout_minutes: int = 480
    idle_timeout_minutes: int = 30
    max_concurrent_sessions: int = 5
    worker_count: int = 2
    database_provider: str = "memory"
    auth_provider: str = "local"
    ldap_enabled: bool = False
    oidc_enabled: bool = False
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    rate_limit_per_minute: int = 120


class SystemHealth(BaseModel):
    status: str = "healthy"
    database: str = "memory"
    worker_embedded: bool = True
    worker_count: int = 2
    active_sessions: int = 0
    queued_jobs: int = 0
    user_count: int = 0
