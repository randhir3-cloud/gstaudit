# Authentication

GAIS v0.7 implements JWT-based authentication with secure refresh token cookies.

## Flow

```
POST /api/auth/login  →  access_token (JSON) + refresh_token (httpOnly cookie)
GET  /api/*           →  Authorization: Bearer <access_token>
POST /api/auth/refresh → new access_token (uses refresh cookie)
POST /api/auth/logout  → revoke session + clear cookies
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Username/password login |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/auth/logout` | End current session |
| POST | `/api/auth/logout-all` | Revoke all sessions |
| GET | `/api/auth/me` | Current user profile |
| GET | `/api/auth/sessions` | Open sessions for user |

## Default Admin

On first startup (no users in database):

| Field | Default |
|-------|---------|
| Username | `admin` |
| Password | `Admin@123456!` (override with `GAIS_ADMIN_PASSWORD`) |

**Change the default password immediately after deployment.**

## Frontend

- Token stored in `localStorage` as `gais_access_token`
- Refresh token in httpOnly cookie (`gais_refresh_token`)
- CSRF token cookie (`gais_csrf_token`) for refresh/logout
- Unauthenticated users redirected to `/login`
- 401 responses clear token and redirect to login

## Development Bypass

```bash
AUTH_DISABLED=true
```

Grants system administrator permissions without JWT. **Never use in production.**

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_DISABLED` | `false` | Disable auth middleware |
| `JWT_SECRET` | auto-generated | HMAC signing key |
| `ACCESS_TOKEN_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_DAYS` | `7` | Refresh token TTL |
| `GAIS_ADMIN_USERNAME` | `admin` | Bootstrap admin username |
| `GAIS_ADMIN_PASSWORD` | `Admin@123456!` | Bootstrap admin password |

## Future Providers

Department settings support:

- `auth_provider`: `local` | `ldap` | `oidc`
- `ldap_enabled`, `oidc_enabled`, `oidc_issuer`, `oidc_client_id`

LDAP/OIDC adapters are configuration-ready; local auth is production-ready today.
