# Case Management

GAIS Audit Case Management implements the complete government GST audit lifecycle on top of MSAE master cases.

## Overview

Comparison plugins identify discrepancies. MSAE consolidates cross-plugin findings into master cases. **Case Management** adds workflow, assignment, notices, documents, and closure.

```
MSAE Master Case (Draft)
        ↓
Audit Case (workflow-managed)
        ↓
Assignment → Investigation → Notice → Response → Verification → Review → Closed
```

## Workflow States

| Status | Description |
|--------|-------------|
| Draft | Synced from MSAE, not yet assigned |
| Assigned | Officer and supervisor assigned |
| Under Investigation | Active officer investigation |
| Notice Issued | Show cause / demand notice issued |
| Dealer Response Received | Dealer reply recorded |
| Verification Pending | Officer verifying response |
| Supervisor Review | Awaiting supervisor approval |
| Approved | Supervisor approved findings |
| Closed | Case closed |
| Archived | Long-term archive |

## API

Base path: `/api/audit-cases`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/audit-cases` | GET | List cases (syncs from MSAE) |
| `/api/audit-cases/tasks` | GET | Officer task lists |
| `/api/audit-cases/supervisor` | GET | Supervisor dashboard |
| `/api/audit-cases/{id}` | GET | Full case detail + timeline |
| `/api/audit-cases/{id}/assign` | POST | Assign officer/supervisor |
| `/api/audit-cases/{id}/transition` | POST | Workflow status change |
| `/api/audit-cases/{id}/approve` | POST | Supervisor approval |
| `/api/audit-cases/{id}/notices` | POST | Create notice |
| `/api/audit-cases/{id}/notices/{id}/issue` | POST | Issue notice |
| `/api/audit-cases/{id}/documents` | POST | Upload document |
| `/api/audit-cases/{id}/report` | GET | Final audit order report |

## Permissions

- `manage_audit_cases` — officers: assign, transition, notices, documents
- `supervise_audit_cases` — supervisors: dashboard, approvals

## Database Tables

- `audit_cases` — primary case record
- `case_assignments` — officer/supervisor assignment
- `audit_notices` — notice management
- `case_documents` — evidence uploads
- `case_comments` — remarks
- `case_timelines` — visual timeline events
- `dealer_responses` — dealer replies
- `workflow_history` — status change audit trail

Migration: `004_case_management_schema.py`

## Frontend

- `/audit-cases` — Case Management
- `/officer-tasks` — Officer Task List
- `/supervisor-dashboard` — Supervisor Dashboard

See also: [WORKFLOW_ENGINE.md](./WORKFLOW_ENGINE.md), [NOTICE_SYSTEM.md](./NOTICE_SYSTEM.md), [TIMELINE.md](./TIMELINE.md)
