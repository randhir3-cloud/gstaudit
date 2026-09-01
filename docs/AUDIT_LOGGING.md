# Audit Logging

Every significant action in GAIS is recorded in the `audit_logs` table for compliance and forensic review.

## Log Entry Fields

| Field | Description |
|-------|-------------|
| `timestamp` | UTC ISO timestamp |
| `user_id` / `username` | Acting officer |
| `action` | Action code (see below) |
| `resource_type` / `resource_id` | Target entity |
| `dealer_name` / `gstin` | Dealer context |
| `session_id` | Audit session |
| `ip_address` | Client IP |
| `user_agent` | Browser/client |
| `result` | `success` or `failure` |
| `details` | JSON metadata |

## Logged Actions

| Action | Trigger |
|--------|---------|
| `login` | Successful authentication |
| `login_failed` | Failed authentication |
| `logout` | User logout |
| `logout_all` | Revoke all sessions |
| `session_sync` | Audit session sync |
| `comparison` | Comparison job enqueued |
| `merge` | Workbook merge |
| `upload` | File upload/classify |
| `report_generated` | Report job enqueued |
| `case_update` | Investigation case PATCH |
| `case_bulk_update` | Bulk case update |
| `job_created` / `job_cancel` / `job_retry` | Background jobs |
| `user_created` / `user_updated` / `user_deleted` | User management |
| `settings_change` | Department settings update |

## Access

- **API:** `GET /api/admin/audit-logs?limit=100&user_id=`
- **Permission:** `view_audit_logs` (administrators)
- **Dashboard:** Recent activity in Officer Session panel (admin only)

## Implementation

1. **Explicit logging** — auth and user management services call `log_audit_event()`
2. **Mutation middleware** — `AuditLoggingMiddleware` logs successful POST/PATCH/DELETE on `/api/*`

Logs are append-only. No update or delete endpoints exist.

## Retention

PostgreSQL stores all logs. Configure retention via database maintenance policies for your department's compliance requirements.
