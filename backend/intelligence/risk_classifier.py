"""Risk classification for comparison records and aggregates."""

from __future__ import annotations

from comparison.comparison_types import ComparisonResultType, RiskLevel
from comparison.comparators.risk_engine import overall_risk_level, score_result
from comparison.result_models import ComparisonRecord

PRIORITY_REASONS = {
    ComparisonResultType.MISSING_IN_GSTR1: "Invoice exists in EWB but absent in GSTR-1 — potential suppressed turnover.",
    ComparisonResultType.MISSING_IN_EWAY: "Invoice declared in GSTR-1 without corresponding E-Way Bill.",
    ComparisonResultType.GSTIN_MISMATCH: "GSTIN mismatch between GSTR-1 and E-Way Bill records.",
    ComparisonResultType.VALUE_MISMATCH: "Taxable/invoice value difference between matched records.",
    ComparisonResultType.DATE_MISMATCH: "Invoice date mismatch across datasets.",
    ComparisonResultType.DUPLICATE: "Duplicate invoice entry detected in uploaded data.",
    ComparisonResultType.MULTIPLE_MATCHES: "One invoice maps to multiple counterpart records.",
}


def classify_record(record: ComparisonRecord) -> tuple[int, RiskLevel, str]:
    score = record.risk_score or score_result(record.result_type, record.difference_amount)
    level = _score_to_level(score)
    reason = PRIORITY_REASONS.get(record.result_type, f"Discrepancy type {record.result_type.value} requires review.")
    if record.difference_amount > 100000:
        score = min(100, score + 10)
        reason = f"{reason} Large value difference (₹{record.difference_amount:,.0f})."
    return score, level, reason


def _score_to_level(score: int) -> RiskLevel:
    if score >= 95:
        return RiskLevel.CRITICAL
    if score >= 70:
        return RiskLevel.HIGH
    if score >= 40:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def score_to_priority(score: int) -> str:
    if score >= 90:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def aggregate_risk(records: list[ComparisonRecord]) -> tuple[int, RiskLevel]:
    scores = [
        r.risk_score or score_result(r.result_type, r.difference_amount)
        for r in records
        if r.result_type != ComparisonResultType.MATCHED
    ]
    if not scores:
        return 0, RiskLevel.LOW
    peak = max(scores)
    return peak, overall_risk_level(scores)
