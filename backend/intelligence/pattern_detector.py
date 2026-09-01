"""Cross-record pattern detection across comparison results."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from comparison.comparison_types import ComparisonResultType
from comparison.result_models import ComparisonRecord
from intelligence.models import PatternFinding
from intelligence.risk_classifier import score_to_priority


def _supplier(rec: ComparisonRecord) -> str:
    return (rec.gstin_gstr1 or rec.details.get("supplier_gstin") or "UNKNOWN").upper()


def _customer(rec: ComparisonRecord) -> str:
    return (rec.gstin_eway or rec.details.get("recipient_gstin") or "UNKNOWN").upper()


def _month(rec: ComparisonRecord) -> str:
    period = rec.source_period or rec.date_gstr1 or rec.date_eway or ""
    m = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]?(\d{2,4})?", period, re.I)
    if m:
        return f"{m.group(1).title()} {m.group(2) or ''}".strip()
    return period[:20] or "Unknown"


def _invoice_value(rec: ComparisonRecord) -> float:
    return max(rec.invoice_value_gstr1, rec.invoice_value_eway, rec.taxable_value_gstr1, rec.taxable_value_eway)


def detect_patterns(records: list[ComparisonRecord]) -> list[PatternFinding]:
    discrepancies = [r for r in records if r.result_type != ComparisonResultType.MATCHED]
    if not discrepancies:
        return []

    findings: list[PatternFinding] = []

    # Repeated missing invoices by customer
    missing_g1_by_customer: Counter[str] = Counter()
    for rec in discrepancies:
        if rec.result_type == ComparisonResultType.MISSING_IN_GSTR1:
            missing_g1_by_customer[_customer(rec)] += 1
    for gstin, count in missing_g1_by_customer.items():
        if count >= 2 and gstin != "UNKNOWN":
            findings.append(PatternFinding(
                pattern_type="repeated_missing_invoices",
                description=f"Customer {gstin} has {count} invoices in EWB missing from GSTR-1.",
                severity=score_to_priority(min(100, 70 + count * 5)),  # type: ignore[arg-type]
                affected_count=count,
                entities=[gstin],
            ))

    # Repeated GSTIN mismatch
    gstin_mismatch_pairs: Counter[str] = Counter()
    for rec in discrepancies:
        if rec.result_type == ComparisonResultType.GSTIN_MISMATCH:
            pair = f"{rec.gstin_gstr1}|{rec.gstin_eway}"
            gstin_mismatch_pairs[pair] += 1
    for pair, count in gstin_mismatch_pairs.items():
        if count >= 2:
            findings.append(PatternFinding(
                pattern_type="repeated_gstin_mismatch",
                description=f"Repeated GSTIN mismatch ({count}x) for pair {pair.replace('|', ' ↔ ')}.",
                severity="High",
                affected_count=count,
                entities=[pair],
            ))

    # Month-wise spikes
    by_month: Counter[str] = Counter()
    for rec in discrepancies:
        by_month[_month(rec)] += 1
    if by_month:
        avg = sum(by_month.values()) / len(by_month)
        for month, count in by_month.items():
            if count >= max(3, avg * 2):
                findings.append(PatternFinding(
                    pattern_type="month_wise_spike",
                    description=f"{month}: {count} discrepancies ({count / max(avg, 1):.1f}× average).",
                    severity="High" if count >= avg * 3 else "Medium",
                    affected_count=count,
                    entities=[month],
                ))

    # Supplier anomalies
    supplier_issues: Counter[str] = Counter()
    for rec in discrepancies:
        supplier_issues[_supplier(rec)] += 1
    for gstin, count in supplier_issues.most_common(3):
        if count >= 3 and gstin != "UNKNOWN":
            findings.append(PatternFinding(
                pattern_type="supplier_anomaly",
                description=f"Supplier {gstin} linked to {count} discrepancies.",
                severity="High",
                affected_count=count,
                entities=[gstin],
            ))

    # Customer anomalies
    customer_issues: Counter[str] = Counter()
    for rec in discrepancies:
        customer_issues[_customer(rec)] += 1
    for gstin, count in customer_issues.most_common(3):
        if count >= 3 and gstin != "UNKNOWN":
            findings.append(PatternFinding(
                pattern_type="customer_anomaly",
                description=f"Customer {gstin} linked to {count} discrepancies.",
                severity="High",
                affected_count=count,
                entities=[gstin],
            ))

    # Large value concentration
    total_diff = sum(abs(r.difference_amount) for r in discrepancies)
    sorted_by_diff = sorted(discrepancies, key=lambda r: abs(r.difference_amount), reverse=True)
    top_n = max(1, len(sorted_by_diff) // 10)
    top_diff = sum(abs(r.difference_amount) for r in sorted_by_diff[:top_n])
    if total_diff > 0 and top_diff / total_diff >= 0.5:
        findings.append(PatternFinding(
            pattern_type="large_value_concentration",
            description=f"Top {top_n} discrepancies account for {top_diff / total_diff * 100:.0f}% of total value difference.",
            severity="Critical",
            affected_count=top_n,
        ))

    # Round value invoices
    round_count = sum(
        1 for r in discrepancies
        if _invoice_value(r) >= 10000 and _invoice_value(r) % 1000 == 0
    )
    if round_count >= 2:
        findings.append(PatternFinding(
            pattern_type="round_value_invoices",
            description=f"{round_count} discrepancies involve round-value invoices (≥ ₹10,000).",
            severity="Medium",
            affected_count=round_count,
        ))

    # Frequent duplicates
    dup_count = sum(1 for r in discrepancies if r.result_type == ComparisonResultType.DUPLICATE)
    if dup_count >= 2:
        findings.append(PatternFinding(
            pattern_type="frequent_duplicates",
            description=f"{dup_count} duplicate invoice entries detected.",
            severity="Medium",
            affected_count=dup_count,
        ))

    # Sequential invoice gaps (numeric invoices)
    numeric_invoices: dict[str, list[int]] = defaultdict(list)
    for rec in records:
        num = re.sub(r"\D", "", rec.normalized_invoice or rec.invoice_number)
        if num and len(num) >= 3:
            prefix = (rec.normalized_invoice or rec.invoice_number)[:3]
            numeric_invoices[prefix].append(int(num))
    for prefix, nums in numeric_invoices.items():
        nums = sorted(set(nums))
        gaps = sum(1 for a, b in zip(nums, nums[1:]) if b - a > 1)
        if gaps >= 2:
            findings.append(PatternFinding(
                pattern_type="sequential_invoice_gaps",
                description=f"Invoice series '{prefix}*' has {gaps} numbering gaps.",
                severity="Medium",
                affected_count=gaps,
                entities=[prefix],
            ))

    return findings


def patterns_for_record(record: ComparisonRecord, findings: list[PatternFinding]) -> list[str]:
    supplier = _supplier(record)
    customer = _customer(record)
    month = _month(record)
    matched: list[str] = []
    for f in findings:
        if f.pattern_type == "repeated_missing_invoices" and record.result_type == ComparisonResultType.MISSING_IN_GSTR1:
            if customer in f.entities:
                matched.append(f.description)
        elif f.pattern_type == "repeated_gstin_mismatch" and record.result_type == ComparisonResultType.GSTIN_MISMATCH:
            pair = f"{record.gstin_gstr1}|{record.gstin_eway}"
            if pair in f.entities:
                matched.append(f.description)
        elif f.pattern_type == "month_wise_spike" and month in f.entities:
            matched.append(f.description)
        elif f.pattern_type == "supplier_anomaly" and supplier in f.entities:
            matched.append(f.description)
        elif f.pattern_type == "customer_anomaly" and customer in f.entities:
            matched.append(f.description)
        elif f.pattern_type == "round_value_invoices":
            val = _invoice_value(record)
            if val >= 10000 and val % 1000 == 0:
                matched.append("Round-value invoice pattern")
    return matched[:5]
