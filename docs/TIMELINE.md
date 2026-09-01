# Case Timeline

Every audit case maintains a visual timeline of all actions.

## Event Types

| Type | Description |
|------|-------------|
| `status_change` | Workflow transition |
| `assignment` | Officer/supervisor assignment |
| `officer_remark` | Officer comment |
| `dealer_reply` | Dealer response received |
| `supervisor_remark` | Supervisor comment |
| `notice_issued` | Notice created or issued |
| `document_upload` | Evidence uploaded |
| `system_event` | Automated events (MSAE sync, reminders) |

## Timeline Entry Structure

```json
{
  "entry_id": "abc123",
  "event_type": "status_change",
  "title": "Status: Assigned → Under Investigation",
  "description": "Officer began investigation",
  "actor": "officer1",
  "actor_role": "officer",
  "timestamp": "2026-07-09T12:00:00Z",
  "metadata": { "from_status": "Assigned", "to_status": "Under Investigation" },
  "attachment_ids": []
}
```

## Automatic Events

The system records timeline entries for:

- MSAE case sync (system_event)
- Assignment and reassignment
- Every workflow transition (workflow_history mirror)
- Notice creation, issue, reminder
- Document uploads
- Comments and dealer responses

## API

Timeline included in case detail:

```
GET /api/audit-cases/{case_id}?session_id=...
```

Returns `timeline[]` sorted chronologically.

Comments API adds timeline entries:

```
POST /api/audit-cases/{case_id}/comments
```

## Frontend

Case Management page renders timeline via `CaseTimeline` component (`data-testid="case-timeline"`).

Final audit report includes full timeline:

```
GET /api/audit-cases/{case_id}/report?session_id=...
```

## Database

Stored in `case_timelines` table (Postgres) or in-memory store (development/tests).

Related: `workflow_history` for status-only audit trail; `case_comments` for free-form remarks.
