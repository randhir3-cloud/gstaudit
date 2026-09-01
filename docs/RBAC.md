# Role-Based Access Control (RBAC)

## Roles

| Role | Description |
|------|-------------|
| `administrator` | Full system access |
| `audit_officer` | Standard audit operations |
| `senior_officer` | Officer + delete session |
| `supervisor` | Review cases and reports |
| `viewer` | Read-only dashboard and reports |
| `system` | Internal system account |

## Permissions

| Permission | Description |
|------------|-------------|
| `upload_files` | Upload GST workbooks |
| `merge_files` | Merge workbooks |
| `run_comparison` | Execute comparisons |
| `delete_session` | Remove audit sessions |
| `generate_report` | Generate audit reports |
| `export_excel` | Export Excel |
| `export_pdf` | Export PDF |
| `manage_users` | User administration |
| `manage_settings` | System settings |
| `view_reports` | View reports |
| `view_dashboard` | View dashboard |
| `update_cases` | Modify investigation cases |
| `view_intelligence` | View audit intelligence |
| `view_audit_logs` | View security audit trail |
| `manage_sessions` | Sync audit sessions |
| `cancel_jobs` | Cancel background jobs |
| `view_admin` | Access admin panel |
| `view_system_monitor` | Access platform operations dashboard |

## Role → Permission Matrix

| Permission | Admin | Officer | Senior | Supervisor | Viewer |
|------------|:-----:|:-------:|:------:|:----------:|:------:|
| upload_files | ✓ | ✓ | ✓ | | |
| merge_files | ✓ | ✓ | ✓ | | |
| run_comparison | ✓ | ✓ | ✓ | | |
| delete_session | ✓ | | ✓ | | |
| generate_report | ✓ | ✓ | ✓ | ✓ | |
| export_excel | ✓ | ✓ | ✓ | | |
| export_pdf | ✓ | ✓ | ✓ | ✓ | |
| manage_users | ✓ | | | | |
| manage_settings | ✓ | | | | |
| view_reports | ✓ | ✓ | ✓ | ✓ | ✓ |
| view_dashboard | ✓ | ✓ | ✓ | ✓ | ✓ |
| update_cases | ✓ | ✓ | ✓ | ✓ | |
| view_intelligence | ✓ | ✓ | ✓ | ✓ | ✓ |
| view_audit_logs | ✓ | | | | |
| manage_sessions | ✓ | ✓ | ✓ | | |
| cancel_jobs | ✓ | ✓ | ✓ | | |
| view_admin | ✓ | | | | |
| view_system_monitor | ✓ | | | | |

## Enforcement

Route permissions are defined in `backend/auth/permissions.py` (`ROUTE_PERMISSIONS`). The security middleware validates JWT and checks permissions before the request reaches handlers.

403 responses include the denied permission code.

## User Assignment

Users can hold multiple roles via `user_roles` table. Effective permissions are the union of all role permissions.

Admin API: `POST /api/admin/users` with `role_ids` array.
