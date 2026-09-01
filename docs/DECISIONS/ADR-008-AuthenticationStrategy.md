# ADR-008: Authentication Strategy

## Status

Proposed

## Context

GAIS has no authentication (v0.1). Production deployment on a shared network requires officer identity, session isolation, and optional role-based access.

## Options

| Option | Use case |
|--------|----------|
| Session cookies + local user store | Single department, air-gapped |
| OIDC / SSO (Azure AD, Keycloak) | Enterprise GST department |
| API keys | Machine-to-machine integrations only |

## Decision (recommended)

**OIDC SSO** for production; **dev bypass** via env `GAIS_AUTH_DISABLED=true`.

Officer ID attached to investigation case updates and report generation audit log.

## Consequences

- FastAPI dependency `get_current_officer()`
- Session tokens decoupled from GSTIN hash (see ROADMAP v0.2)
- Frontend login redirect + token refresh

## References

- [SECURITY.md](../SECURITY.md)
