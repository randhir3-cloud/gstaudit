# GAIS Security Architecture (v0.7)

Enterprise security layer for government deployment of the GST Audit Intelligence System.

## Overview

| Layer | Implementation |
|-------|----------------|
| Authentication | JWT access tokens + httpOnly refresh cookies |
| Authorization | RBAC with 6 roles and 17 permissions |
| Audit logging | Immutable `audit_logs` table + mutation middleware |
| Session management | `user_sessions` with concurrent limit, logout-all |
| Password policy | Configurable via department settings |
| API protection | Security middleware on all `/api/*` routes |
| Rate limiting | In-memory per-IP/route limiter |

## Deployment Checklist

```bash
AUTH_DISABLED=false          # Required in production
JWT_SECRET=<strong-secret>   # Required — rotate periodically
GAIS_ADMIN_PASSWORD=<secure> # Initial admin password
CORS_ORIGINS=https://gais.dept.gov.in
DATABASE_PROVIDER=postgres
```

## Threat Controls

- All API routes require valid JWT (except `/health`, `/api/auth/login`, `/api/auth/refresh`)
- Role-based permission checks per route prefix
- Failed login attempts logged
- Password history prevents reuse
- Session idle timeout configurable
- Rate limit: 120 requests/minute per IP/route group (default)

## Future SSO

Settings include flags for LDAP and OIDC (`ldap_enabled`, `oidc_enabled`, `oidc_issuer`). Local auth is fully implemented; external IdP integration is configuration-ready.

See also: [AUTHENTICATION.md](./AUTHENTICATION.md), [RBAC.md](./RBAC.md), [AUDIT_LOGGING.md](./AUDIT_LOGGING.md), [ADMIN_GUIDE.md](./ADMIN_GUIDE.md)
