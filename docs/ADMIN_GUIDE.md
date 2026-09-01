# GAIS Administration Guide

## Access

Navigate to **Administration** in the main nav (administrators only) or `/admin`.

Requires `view_admin` permission.

## Users

### List users
`GET /api/admin/users`

### Create user
```json
POST /api/admin/users
{
  "username": "officer.singh",
  "password": "SecurePass@123",
  "full_name": "Randhir Singh",
  "department": "GST Audit",
  "office": "Amritsar",
  "designation": "Audit Officer",
  "role_ids": ["role_officer"]
}
```

### Update user
`PATCH /api/admin/users/{user_id}` — email, roles, status, password

### Delete user
`DELETE /api/admin/users/{user_id}`

## Roles & Permissions

- `GET /api/admin/roles` — list roles with permissions
- `GET /api/admin/permissions` — full permission catalog

System roles cannot be deleted (`is_system: true`).

## Department Settings

`GET/PATCH /api/admin/settings`

Configurable:

| Setting | Description |
|---------|-------------|
| `department_name` | Display name |
| `office_name` | Office label |
| `logo_url` | Department logo |
| `theme_default` | `dark` or `light` |
| `password_policy` | Min length, complexity, history, expiry |
| `session_timeout_minutes` | Max session duration |
| `idle_timeout_minutes` | Idle logout threshold |
| `max_concurrent_sessions` | Per-user session limit |
| `worker_count` | Background job workers |
| `database_provider` | Display only |
| `rate_limit_per_minute` | API rate limit |

## System Health

`GET /api/admin/health`

Returns database provider, worker status, active sessions, queued jobs, user count.

## Audit Logs

`GET /api/admin/audit-logs?limit=100`

Filter by `user_id` for officer-specific trails.

## Session Management

Officers can view open sessions on the dashboard **Officer Session** panel.

- **Logout** — ends current session (header button)
- **Logout all devices** — `POST /api/auth/logout-all`

Administrators can monitor active sessions via `/api/auth/sessions`.

## Production Deployment

1. Set `AUTH_DISABLED=false`
2. Set strong `JWT_SECRET`
3. Change default admin password
4. Configure `CORS_ORIGINS` to department domain
5. Enable PostgreSQL (`DATABASE_PROVIDER=postgres`)
6. Deploy behind HTTPS reverse proxy
7. Restrict `/docs` in production Nginx config
