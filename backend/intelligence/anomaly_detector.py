"""Statistical anomaly detection for months and entities."""

from __future__ import annotations

from collections import defaultdict

from comparison.comparison_types import ComparisonResultType
from comparison.result_models import ComparisonRecord
from intelligence.models import EntityRanking


def _supplier(rec: ComparisonRecord) -> str:
    return (rec.gstin_gstr1 or "UNKNOWN").upper()


def _customer(rec: ComparisonRecord) -> str:
    return (rec.gstin_eway or "UNKNOWN").upper()


def rank_suppliers(records: list[ComparisonRecord], limit: int = 20) -> list[EntityRanking]:
    discrepancies = [r for r in records if r.result_type != ComparisonResultType.MATCHED]
    stats: dict[str, dict] = defaultdict(lambda: {
        "mismatch_count": 0, "value_difference": 0.0, "duplicate_count": 0,
        "risk_score": 0, "missing_invoice_count": 0,
    })
    for rec in discrepancies:
        gstin = _supplier(rec)
        s = stats[gstin]
        s["mismatch_count"] += 1
        s["value_difference"] += abs(rec.difference_amount)
        s["risk_score"] = max(s["risk_score"], rec.risk_score)
        if rec.result_type == ComparisonResultType.DUPLICATE:
            s["duplicate_count"] += 1
        if rec.result_type == ComparisonResultType.MISSING_IN_GSTR1:
            s["missing_invoice_count"] += 1

    ranked = sorted(stats.items(), key=lambda x: (-x[1]["risk_score"], -x[1]["value_difference"]))
    return [
        EntityRanking(
            gstin=gstin,
            name=gstin,
            mismatch_count=data["mismatch_count"],
            value_difference=round(data["value_difference"], 2),
            duplicate_count=data["duplicate_count"],
            risk_score=data["risk_score"],
            missing_invoice_count=data["missing_invoice_count"],
        )
        for gstin, data in ranked[:limit]
        if gstin != "UNKNOWN"
    ]


def rank_customers(records: list[ComparisonRecord], limit: int = 20) -> list[EntityRanking]:
    discrepancies = [r for r in records if r.result_type != ComparisonResultType.MATCHED]
    stats: dict[str, dict] = defaultdict(lambda: {
        "mismatch_count": 0, "value_difference": 0.0, "duplicate_count": 0,
        "risk_score": 0, "missing_invoice_count": 0,
    })
    for rec in discrepancies:
        gstin = _customer(rec)
        s = stats[gstin]
        s["mismatch_count"] += 1
        s["value_difference"] += abs(rec.difference_amount or max(rec.invoice_value_gstr1, rec.invoice_value_eway))
        s["risk_score"] = max(s["risk_score"], rec.risk_score)
        if rec.result_type == ComparisonResultType.DUPLICATE:
            s["duplicate_count"] += 1
        if rec.result_type in (ComparisonResultType.MISSING_IN_GSTR1, ComparisonResultType.MISSING_IN_EWAY):
            s["missing_invoice_count"] += 1

    ranked = sorted(stats.items(), key=lambda x: (-x[1]["risk_score"], -x[1]["value_difference"]))
    return [
        EntityRanking(
            gstin=gstin,
            name=gstin,
            mismatch_count=data["mismatch_count"],
            value_difference=round(data["value_difference"], 2),
            duplicate_count=data["duplicate_count"],
            risk_score=data["risk_score"],
            missing_invoice_count=data["missing_invoice_count"],
        )
        for gstin, data in ranked[:limit]
        if gstin != "UNKNOWN"
    ]


def critical_entity_count(rankings: list[EntityRanking], threshold: int = 70) -> int:
    return sum(1 for r in rankings if r.risk_score >= threshold)
