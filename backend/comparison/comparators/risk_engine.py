"""Risk scoring engine for comparison discrepancies."""

from __future__ import annotations

from comparison.comparison_types import ComparisonResultType, RiskLevel

RISK_WEIGHTS = {
    ComparisonResultType.MISSING_IN_GSTR1: 100,
    ComparisonResultType.MISSING_IN_EWAY: 95,
    ComparisonResultType.GSTIN_MISMATCH: 80,
    ComparisonResultType.VALUE_MISMATCH: 70,
    ComparisonResultType.DATE_MISMATCH: 40,
    ComparisonResultType.DUPLICATE: 30,
    ComparisonResultType.MULTIPLE_MATCHES: 60,
    ComparisonResultType.UNKNOWN: 20,
    ComparisonResultType.MATCHED: 0,
}


def score_result(result_type: ComparisonResultType, difference_amount: float = 0.0) -> int:
    base = RISK_WEIGHTS.get(result_type, 10)
    if result_type == ComparisonResultType.VALUE_MISMATCH and difference_amount <= 1.0:
        return 10
    return base


def overall_risk_level(scores: list[int]) -> RiskLevel:
    if not scores:
        return RiskLevel.LOW
    peak = max(scores)
    if peak >= 95:
        return RiskLevel.CRITICAL
    if peak >= 80:
        return RiskLevel.HIGH
    if peak >= 40:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
