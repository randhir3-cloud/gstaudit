"""Cross-source pattern detection for MSAE."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from comparison.comparison_types import ComparisonResultType
from models.msae import MasterAuditCase, PatternHit, PluginFinding


def _invoice_value(finding: PluginFinding) -> float:
    return max(finding.invoice_value, finding.taxable_value)


def detect_cross_source_patterns(
    master_cases: list[MasterAuditCase],
    findings: list[PluginFinding],
) -> list[PatternHit]:
    hits: list[PatternHit] = []
    if not findings:
        return hits

    # Cross-plugin cases (same invoice in multiple comparisons)
    cross_plugin = [c for c in master_cases if c.source_count > 1]
    if cross_plugin:
        hits.append(PatternHit(
            pattern_type="cross_plugin_discrepancy",
            description=f"{len(cross_plugin)} invoices appear across multiple comparison sources.",
            severity="High",
            affected_count=len(cross_plugin),
            source_plugins=sorted({cid for c in cross_plugin for cid in c.comparison_ids}),
        ))

    # Repeated supplier mismatch across plugins
    supplier_issues: Counter[str] = Counter()
    for f in findings:
        if f.supplier_gstin and f.supplier_gstin != "UNKNOWN":
            supplier_issues[f.supplier_gstin.upper()] += 1
    for gstin, count in supplier_issues.items():
        if count >= 2:
            plugins = sorted({f.comparison_id for f in findings if f.supplier_gstin.upper() == gstin})
            hits.append(PatternHit(
                pattern_type="repeated_supplier_mismatch",
                description=f"Supplier {gstin} linked to {count} discrepancies across sources.",
                severity="High" if count >= 3 else "Medium",
                affected_count=count,
                entities=[gstin],
                source_plugins=plugins,
            ))

    # Repeated month issues
    month_issues: Counter[str] = Counter()
    for f in findings:
        period = f.source_period or f.invoice_date or "Unknown"
        month_issues[period[:20]] += 1
    if month_issues:
        avg = sum(month_issues.values()) / len(month_issues)
        for month, count in month_issues.items():
            if count >= max(2, avg * 1.5):
                hits.append(PatternHit(
                    pattern_type="repeated_month_issues",
                    description=f"{month}: {count} cross-source discrepancies.",
                    severity="High" if count >= avg * 2 else "Medium",
                    affected_count=count,
                    entities=[month],
                ))

    # Round-value invoices
    round_count = sum(
        1 for f in findings
        if _invoice_value(f) >= 10000 and _invoice_value(f) % 1000 == 0
    )
    if round_count >= 2:
        hits.append(PatternHit(
            pattern_type="round_value_invoices",
            description=f"{round_count} discrepancies involve round-value invoices (≥ ₹10,000).",
            severity="Medium",
            affected_count=round_count,
        ))

    # Duplicate invoices across sources
    dup_by_invoice: Counter[str] = Counter()
    for f in findings:
        if f.result_type == ComparisonResultType.DUPLICATE.value:
            dup_by_invoice[f.normalized_invoice or f.invoice_number] += 1
    dup_total = sum(dup_by_invoice.values())
    if dup_total >= 2:
        hits.append(PatternHit(
            pattern_type="duplicate_invoices",
            description=f"{dup_total} duplicate invoice entries detected across sources.",
            severity="Medium",
            affected_count=dup_total,
        ))

    # Split invoices (same supplier, similar values, sequential docs)
    by_supplier: dict[str, list[PluginFinding]] = defaultdict(list)
    for f in findings:
        if f.supplier_gstin:
            by_supplier[f.supplier_gstin.upper()].append(f)
    split_count = 0
    for gstin, group in by_supplier.items():
        values = sorted(_invoice_value(f) for f in group if _invoice_value(f) > 0)
        for i in range(len(values) - 1):
            if values[i] > 0 and 0.9 <= values[i] / values[i + 1] <= 1.1 and values[i] >= 50000:
                split_count += 1
                break
    if split_count >= 1:
        hits.append(PatternHit(
            pattern_type="split_invoice_pattern",
            description=f"{split_count} supplier(s) show potential split-invoice patterns.",
            severity="High",
            affected_count=split_count,
        ))

    # Repeated GSTIN errors
    gstin_pairs: Counter[str] = Counter()
    for f in findings:
        if f.result_type == ComparisonResultType.GSTIN_MISMATCH.value:
            pair = f"{f.supplier_gstin}|{f.recipient_gstin}"
            gstin_pairs[pair] += 1
    for pair, count in gstin_pairs.items():
        if count >= 2:
            hits.append(PatternHit(
                pattern_type="repeated_gstin_errors",
                description=f"Repeated GSTIN mismatch ({count}×) for {pair.replace('|', ' ↔ ')}.",
                severity="High",
                affected_count=count,
                entities=[pair],
            ))

    # Tax variance patterns
    high_variance = [f for f in findings if abs(f.difference_amount) >= 50000]
    if len(high_variance) >= 2:
        total_var = sum(abs(f.difference_amount) for f in high_variance)
        hits.append(PatternHit(
            pattern_type="tax_variance_pattern",
            description=f"{len(high_variance)} findings with tax variance ≥ ₹50,000 (total ₹{total_var:,.0f}).",
            severity="Critical",
            affected_count=len(high_variance),
        ))

    return hits


def patterns_for_master_case(case: MasterAuditCase, hits: list[PatternHit]) -> list[str]:
    matched: list[str] = []
    for hit in hits:
        if hit.pattern_type == "cross_plugin_discrepancy" and case.source_count > 1:
            matched.append(hit.description)
        elif hit.pattern_type == "repeated_supplier_mismatch" and case.supplier_gstin.upper() in hit.entities:
            matched.append(hit.description)
        elif hit.pattern_type == "repeated_month_issues" and case.tax_period[:20] in hit.entities:
            matched.append(hit.description)
        elif hit.pattern_type == "round_value_invoices":
            val = case.invoice_value
            if val >= 10000 and val % 1000 == 0:
                matched.append("Round-value invoice pattern")
        elif hit.pattern_type == "repeated_gstin_errors":
            pair = f"{case.supplier_gstin}|{case.recipient_gstin}"
            if pair in hit.entities:
                matched.append(hit.description)
    return matched[:5]
