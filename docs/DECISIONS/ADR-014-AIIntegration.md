# ADR-014: AI Integration

## Status

Proposed

## Context

Audit intelligence today is rule-based (patterns, risk scoring, recommendations). Officers may benefit from natural-language executive summaries and guided investigation prompts.

## Decision

**Optional AI layer** — never required for core audit workflow.

### Phase 1 (v1.x)
- Template-based executive summary (current)
- Structured recommendation catalog (current)

### Phase 2 (optional)
- LLM-generated narrative from structured intelligence JSON
- Officer review required before export
- PII redaction before external API calls
- Env flag: `GAIS_AI_ENABLED=false` by default

## Principles

1. AI augments, never replaces, deterministic comparison results
2. All LLM outputs marked `ai_generated: true` in reports
3. Offline/air-gapped installs must work with AI disabled

## References

- [AUDIT_INTELLIGENCE.md](../AUDIT_INTELLIGENCE.md)
- [SECURITY.md](../SECURITY.md)
