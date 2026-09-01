# Notice System

GAIS supports formal GST audit notices linked to audit cases.

## Notice Types

- Show Cause Notice
- Demand Notice
- Reminder Notice
- Information Request
- Final Audit Order

## Notice Lifecycle

| Status | Description |
|--------|-------------|
| Draft | Created, not yet issued |
| Issued | Formally issued to dealer |
| Reminder Sent | Follow-up reminder dispatched |
| Reply Received | Dealer response linked |
| Closed | Notice resolved |

## Fields

| Field | Description |
|-------|-------------|
| notice_number | Auto-generated: `SCN/{year}/{session}/{seq}` |
| notice_date | Date of issue |
| reply_due_date | Dealer reply deadline |
| notice_type | One of the types above |
| notice_content | Text body |
| notice_pdf_path | Uploaded PDF storage path |

## API

```
POST /api/audit-cases/{case_id}/notices
POST /api/audit-cases/{case_id}/notices/{notice_id}/issue
POST /api/audit-cases/{case_id}/notices/{notice_id}/reminder
```

## Workflow Integration

1. Case must reach **Under Investigation**
2. Officer creates notice (Draft)
3. Officer issues notice → case moves to **Notice Issued**
4. Dealer response recorded → **Dealer Response Received**
5. Optional reminder via reminder endpoint

## PDF Upload

Notice PDFs can be uploaded as case documents with category `notice_pdf`:

```
POST /api/audit-cases/{case_id}/documents
  category=notice_pdf
  file=<PDF>
```

## Reminders

`POST .../notices/{id}/reminder` sets `reminder_sent=true` and status to **Reminder Sent**. Timeline event recorded automatically.
