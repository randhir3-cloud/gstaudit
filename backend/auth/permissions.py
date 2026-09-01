"""RBAC role and permission definitions."""

from __future__ import annotations

from models.security import Permission, PermissionCode, Role, RoleName

PERMISSIONS: list[Permission] = [
    Permission(code=PermissionCode.UPLOAD_FILES.value, label="Upload Files", description="Upload GST workbooks"),
    Permission(code=PermissionCode.MERGE_FILES.value, label="Merge Files", description="Merge uploaded workbooks"),
    Permission(code=PermissionCode.RUN_COMPARISON.value, label="Run Comparison", description="Execute comparison jobs"),
    Permission(code=PermissionCode.DELETE_SESSION.value, label="Delete Session", description="Remove audit sessions"),
    Permission(code=PermissionCode.GENERATE_REPORT.value, label="Generate Report", description="Generate audit reports"),
    Permission(code=PermissionCode.EXPORT_EXCEL.value, label="Export Excel", description="Export Excel reports"),
    Permission(code=PermissionCode.EXPORT_PDF.value, label="Export PDF", description="Export PDF reports"),
    Permission(code=PermissionCode.MANAGE_USERS.value, label="Manage Users", description="Create and manage users"),
    Permission(code=PermissionCode.MANAGE_SETTINGS.value, label="Manage Settings", description="Configure system settings"),
    Permission(code=PermissionCode.VIEW_REPORTS.value, label="View Reports", description="View audit reports"),
    Permission(code=PermissionCode.VIEW_DASHBOARD.value, label="View Dashboard", description="Access audit dashboard"),
    Permission(code=PermissionCode.UPDATE_CASES.value, label="Update Cases", description="Modify investigation cases"),
    Permission(code=PermissionCode.VIEW_INTELLIGENCE.value, label="View Intelligence", description="View audit intelligence"),
    Permission(code=PermissionCode.VIEW_AUDIT_LOGS.value, label="View Audit Logs", description="View security audit trail"),
    Permission(code=PermissionCode.MANAGE_SESSIONS.value, label="Manage Sessions", description="Sync and manage audit sessions"),
    Permission(code=PermissionCode.CANCEL_JOBS.value, label="Cancel Jobs", description="Cancel background jobs"),
    Permission(code=PermissionCode.VIEW_ADMIN.value, label="View Admin Panel", description="Access administration panel"),
    Permission(code=PermissionCode.VIEW_SYSTEM_MONITOR.value, label="View System Monitor", description="Access platform operations dashboard"),
    Permission(code=PermissionCode.MANAGE_AUDIT_CASES.value, label="Manage Audit Cases", description="Assign, transition, and manage audit case workflow"),
    Permission(code=PermissionCode.SUPERVISE_AUDIT_CASES.value, label="Supervise Audit Cases", description="Supervisor review and approval of audit cases"),
]

ALL_PERMISSION_CODES = [p.code for p in PERMISSIONS]

OFFICER_PERMS = [
    PermissionCode.UPLOAD_FILES.value,
    PermissionCode.MERGE_FILES.value,
    PermissionCode.RUN_COMPARISON.value,
    PermissionCode.GENERATE_REPORT.value,
    PermissionCode.EXPORT_EXCEL.value,
    PermissionCode.EXPORT_PDF.value,
    PermissionCode.VIEW_REPORTS.value,
    PermissionCode.VIEW_DASHBOARD.value,
    PermissionCode.UPDATE_CASES.value,
    PermissionCode.VIEW_INTELLIGENCE.value,
    PermissionCode.MANAGE_SESSIONS.value,
    PermissionCode.CANCEL_JOBS.value,
    PermissionCode.MANAGE_AUDIT_CASES.value,
]

SENIOR_PERMS = OFFICER_PERMS + [PermissionCode.DELETE_SESSION.value]

SUPERVISOR_PERMS = [
    PermissionCode.VIEW_DASHBOARD.value,
    PermissionCode.VIEW_REPORTS.value,
    PermissionCode.VIEW_INTELLIGENCE.value,
    PermissionCode.UPDATE_CASES.value,
    PermissionCode.GENERATE_REPORT.value,
    PermissionCode.EXPORT_PDF.value,
    PermissionCode.MANAGE_AUDIT_CASES.value,
    PermissionCode.SUPERVISE_AUDIT_CASES.value,
]

VIEWER_PERMS = [
    PermissionCode.VIEW_DASHBOARD.value,
    PermissionCode.VIEW_REPORTS.value,
    PermissionCode.VIEW_INTELLIGENCE.value,
]

DEFAULT_ROLES: list[Role] = [
    Role(role_id="role_admin", name=RoleName.ADMINISTRATOR.value, label="Administrator", description="Full system access", permissions=ALL_PERMISSION_CODES, is_system=True),
    Role(role_id="role_officer", name=RoleName.AUDIT_OFFICER.value, label="Audit Officer", description="Standard audit operations", permissions=OFFICER_PERMS, is_system=True),
    Role(role_id="role_senior", name=RoleName.SENIOR_OFFICER.value, label="Senior Officer", description="Senior audit officer", permissions=SENIOR_PERMS, is_system=True),
    Role(role_id="role_supervisor", name=RoleName.SUPERVISOR.value, label="Supervisor", description="Supervisory review access", permissions=SUPERVISOR_PERMS, is_system=True),
    Role(role_id="role_viewer", name=RoleName.VIEWER.value, label="Viewer", description="Read-only access", permissions=VIEWER_PERMS, is_system=True),
    Role(role_id="role_system", name=RoleName.SYSTEM.value, label="System", description="Internal system account", permissions=ALL_PERMISSION_CODES, is_system=True),
]

# HTTP method + path prefix → required permission
ROUTE_PERMISSIONS: list[tuple[tuple[str, ...], str, str]] = [
    (("POST",), "/api/merge", PermissionCode.MERGE_FILES.value),
    (("POST",), "/api/eway", PermissionCode.UPLOAD_FILES.value),
    (("POST",), "/api/dealer/extract", PermissionCode.UPLOAD_FILES.value),
    (("POST",), "/api/session/sync", PermissionCode.MANAGE_SESSIONS.value),
    (("GET",), "/api/dashboard", PermissionCode.VIEW_DASHBOARD.value),
    (("POST",), "/api/comparison", PermissionCode.RUN_COMPARISON.value),
    (("GET",), "/api/comparison", PermissionCode.VIEW_DASHBOARD.value),
    (("POST",), "/api/jobs", PermissionCode.RUN_COMPARISON.value),
    (("GET",), "/api/jobs", PermissionCode.VIEW_DASHBOARD.value),
    (("POST",), "/api/jobs/", PermissionCode.CANCEL_JOBS.value),
    (("GET",), "/api/investigation", PermissionCode.VIEW_DASHBOARD.value),
    (("PATCH", "POST"), "/api/investigation", PermissionCode.UPDATE_CASES.value),
    (("GET",), "/api/intelligence", PermissionCode.VIEW_INTELLIGENCE.value),
    (("POST",), "/api/intelligence", PermissionCode.VIEW_INTELLIGENCE.value),
    (("GET", "POST"), "/api/msae", PermissionCode.VIEW_INTELLIGENCE.value),
    (("GET",), "/api/audit-cases/supervisor", PermissionCode.SUPERVISE_AUDIT_CASES.value),
    (("GET", "POST"), "/api/audit-cases", PermissionCode.MANAGE_AUDIT_CASES.value),
    (("GET",), "/api/report", PermissionCode.VIEW_REPORTS.value),
    (("POST",), "/api/report", PermissionCode.GENERATE_REPORT.value),
    (("POST",), "/api/reports/excel", PermissionCode.EXPORT_EXCEL.value),
    (("POST",), "/api/reports/pdf", PermissionCode.EXPORT_PDF.value),
    (("GET", "POST", "PATCH", "DELETE"), "/api/admin", PermissionCode.VIEW_ADMIN.value),
    (("GET", "POST", "PATCH", "DELETE"), "/api/admin/users", PermissionCode.MANAGE_USERS.value),
    (("GET", "PATCH"), "/api/admin/settings", PermissionCode.MANAGE_SETTINGS.value),
    (("GET",), "/api/admin/audit-logs", PermissionCode.VIEW_AUDIT_LOGS.value),
    (("GET",), "/api/system", PermissionCode.VIEW_SYSTEM_MONITOR.value),
    (("GET",), "/api/plugins", PermissionCode.VIEW_DASHBOARD.value),
    (("GET",), "/ws/jobs", PermissionCode.VIEW_DASHBOARD.value),
]


def permission_for_route(method: str, path: str) -> str | None:
    """Return required permission for route, or None if only authentication required."""
    for methods, prefix, perm in ROUTE_PERMISSIONS:
        if method.upper() in methods and path.startswith(prefix):
            return perm
    if path.startswith("/api/"):
        return PermissionCode.VIEW_DASHBOARD.value
    return None


def resolve_user_permissions(role_names: list[str], role_permissions: dict[str, list[str]]) -> list[str]:
    perms: set[str] = set()
    for name in role_names:
        perms.update(role_permissions.get(name, []))
    return sorted(perms)
