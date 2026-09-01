# Entity Relationship Diagram

GAIS PostgreSQL schema — normalized tables with session-centric relationships.

---

## ER Diagram

```mermaid
erDiagram
    dealers ||--o{ audit_sessions : "has"
    audit_sessions ||--o{ uploaded_files : "contains"
    audit_sessions ||--o{ merged_datasets : "stores"
    audit_sessions ||--o{ comparison_runs : "executes"
    audit_sessions ||--o{ investigation_cases : "generates"
    audit_sessions ||--o{ audit_reports : "produces"
    audit_sessions ||--o| intelligence_results : "caches"
    comparison_runs ||--o{ comparison_results : "contains"
    comparison_runs ||--o{ audit_observations : "contains"

    dealers {
        uuid id PK
        string gstin UK
        string financial_year UK
        string legal_name
        string trade_name
    }

    audit_sessions {
        string session_id PK
        uuid dealer_id FK
        string financial_year
        string audit_status
        jsonb session_payload
        bool is_active
    }

    uploaded_files {
        uuid id PK
        string session_id FK
        string dataset_key
        string filename
        string month
        int rows
    }

    merged_datasets {
        uuid id PK
        string session_id FK
        string dataset_key UK
        bytea workbook_bytes
        jsonb metadata_json
    }

    comparison_runs {
        uuid id PK
        string session_id FK
        string comparison_id UK
        string status
        jsonb summary_json
    }

    comparison_results {
        uuid id PK
        uuid run_id FK
        string session_id FK
        string result_type
        string invoice_number
        string normalized_invoice
        string gstin_gstr1
        string source_period
        int risk_score
        jsonb record_json
    }

    audit_observations {
        uuid id PK
        uuid run_id FK
        string session_id FK
        string invoice_number
        string observation
    }

    investigation_cases {
        string case_id PK
        string session_id FK
        string invoice_number
        string supplier_gstin
        string source_period
        string status
        string priority
        int risk_score
        jsonb case_payload
    }

    audit_reports {
        uuid id PK
        string session_id FK
        string format
        bytea content
        jsonb report_metadata
    }

    intelligence_results {
        uuid id PK
        string session_id FK UK
        jsonb payload
    }

    system_settings {
        string key PK
        jsonb value
    }
```

---

## Relationships

| Parent | Child | Cardinality | On Delete |
|--------|-------|-------------|-----------|
| `dealers` | `audit_sessions` | 1:N | SET NULL |
| `audit_sessions` | `uploaded_files` | 1:N | CASCADE |
| `audit_sessions` | `merged_datasets` | 1:N | CASCADE |
| `audit_sessions` | `comparison_runs` | 1:N | CASCADE |
| `audit_sessions` | `investigation_cases` | 1:N | CASCADE |
| `audit_sessions` | `audit_reports` | 1:N | CASCADE |
| `audit_sessions` | `intelligence_results` | 1:1 | CASCADE |
| `comparison_runs` | `comparison_results` | 1:N | CASCADE |
| `comparison_runs` | `audit_observations` | 1:N | CASCADE |

---

## Unique Constraints

| Table | Constraint | Columns |
|-------|------------|---------|
| `dealers` | `uq_dealers_gstin_fy` | `gstin`, `financial_year` |
| `merged_datasets` | `uq_merged_datasets_session_dataset` | `session_id`, `dataset_key` |
| `comparison_runs` | `uq_comparison_runs_session_pair` | `session_id`, `comparison_id` |
| `intelligence_results` | unique | `session_id` |

---

## Index Strategy

| Query pattern | Index |
|---------------|-------|
| Lookup session by FY + status | `ix_audit_sessions_fy_status` |
| Filter cases by status | `ix_investigation_cases_session_status` |
| Filter cases by priority | `ix_investigation_cases_session_priority` |
| Search by GSTIN | `ix_investigation_cases_gstin` |
| Search comparison by invoice | `ix_comparison_results_invoice` |
| Filter by result type | `ix_comparison_results_session_type` |
| Risk-based sorting | `ix_comparison_results_risk_score`, `ix_investigation_cases_risk_score` |

---

## JSONB Payloads

Hybrid storage: indexed columns for search + JSONB for full fidelity.

| Table | JSONB column | Contents |
|-------|--------------|----------|
| `audit_sessions` | `session_payload` | datasets, upload_history, discrepancies, comparison_status |
| `comparison_results` | `record_json` | full `ComparisonRecord` |
| `investigation_cases` | `case_payload` | attachments, patterns, intelligence enrichment |
| `intelligence_results` | `payload` | full `IntelligenceFullResponse` |
| `comparison_runs` | `summary_json` | `ComparisonSummary` |

---

## Related

- [DATABASE.md](./DATABASE.md)
- [REPOSITORY_PATTERN.md](./REPOSITORY_PATTERN.md)
