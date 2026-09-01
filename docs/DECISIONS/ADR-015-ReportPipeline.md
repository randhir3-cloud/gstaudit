# ADR-015: Report Generation Pipeline

## Status

Proposed

## Context

Reports are generated synchronously in `audit_report_service.py` as Excel, PDF, and DOCX. As report sections grow (intelligence, plugins, attachments), monolithic generation becomes fragile.

## Decision

**Pipeline architecture:**

```
ReportRequest
  → SectionProvider[] (each plugin/module contributes sections)
  → ReportAssembler (ordering, TOC)
  → FormatRenderer (xlsx | pdf | docx)
  → StreamResponse
```

Each section provider implements:

```python
class ReportSection(Protocol):
    section_id: str
    order: int
    def build(self, ctx: ReportContext) -> SectionData: ...
```

## Consequences

- Plugins register report sections via manifest (ADR-010)
- Preview API returns section list without full render
- Background job for large reports (ADR-011)

## References

- [INVESTIGATION_ENGINE.md](../INVESTIGATION_ENGINE.md)
- `backend/services/audit_report_service.py`
