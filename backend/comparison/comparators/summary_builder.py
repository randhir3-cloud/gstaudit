"""Build comparison summary from classified records."""

from __future__ import annotations

from typing import List

from comparison.comparison_types import ComparisonResultType
from comparison.result_models import ComparisonRecord, ComparisonSummary


def build_summary(
    records: List[ComparisonRecord],
    *,
    comparison_id: str = "gstr1_ewb_outward",
    left_label: str = "GSTR-1",
    right_label: str = "EWB OUTWARD",
    total_gstr1: int = 0,
    total_eway: int = 0,
) -> ComparisonSummary:
    counts = {t: 0 for t in ComparisonResultType}
    total_diff = 0.0
    max_risk = 0

    for rec in records:
        counts[rec.result_type] += 1
        total_diff += rec.difference_amount
        max_risk = max(max_risk, rec.risk_score)

    return ComparisonSummary(
        comparison_id=comparison_id,
        left_label=left_label,
        right_label=right_label,
        matched_count=counts[ComparisonResultType.MATCHED],
        missing_in_gstr1_count=counts[ComparisonResultType.MISSING_IN_GSTR1],
        missing_in_eway_count=counts[ComparisonResultType.MISSING_IN_EWAY],
        gstin_mismatch_count=counts[ComparisonResultType.GSTIN_MISMATCH],
        date_mismatch_count=counts[ComparisonResultType.DATE_MISMATCH],
        value_mismatch_count=counts[ComparisonResultType.VALUE_MISMATCH],
        invoice_mismatch_count=counts[ComparisonResultType.MULTIPLE_MATCHES],
        duplicate_count=counts[ComparisonResultType.DUPLICATE],
        multiple_matches_count=counts[ComparisonResultType.MULTIPLE_MATCHES],
        unknown_count=counts[ComparisonResultType.UNKNOWN],
        total_difference_amount=round(total_diff, 2),
        overall_risk_score=max_risk,
        total_gstr1_records=total_gstr1,
        total_eway_records=total_eway,
    )
