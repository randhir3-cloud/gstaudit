"""Month-wise timeline and analysis builder."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from comparison.comparison_types import ComparisonResultType
from comparison.result_models import ComparisonRecord
from intelligence.models import HeatmapCell, MonthAnalysis, RiskHeatmaps


def _month(rec: ComparisonRecord) -> str:
    period = rec.source_period or rec.date_gstr1 or rec.date_eway or ""
    m = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]?(\d{2,4})?", period, re.I)
    if m:
        return f"{m.group(1).title()} {m.group(2) or ''}".strip()
    return period[:20] or "Unknown"


def build_month_analysis(records: list[ComparisonRecord]) -> list[MonthAnalysis]:
    by_month: dict[str, list[ComparisonRecord]] = defaultdict(list)
    for rec in records:
        by_month[_month(rec)].append(rec)

    results: list[MonthAnalysis] = []
    for month, month_records in sorted(by_month.items()):
        total = len(month_records)
        matched = sum(1 for r in month_records if r.result_type == ComparisonResultType.MATCHED)
        mismatches = total - matched
        risk_scores = [r.risk_score for r in month_records if r.result_type != ComparisonResultType.MATCHED]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

        suppliers: Counter[str] = Counter()
        customers: Counter[str] = Counter()
        largest_diff = 0.0
        for r in month_records:
            if r.gstin_gstr1:
                suppliers[r.gstin_gstr1.upper()] += 1
            if r.gstin_eway:
                customers[r.gstin_eway.upper()] += 1
            largest_diff = max(largest_diff, abs(r.difference_amount))

        results.append(MonthAnalysis(
            month=month,
            invoices=total,
            matched_count=matched,
            mismatch_count=mismatches,
            matched_percent=round(matched / total * 100, 1) if total else 0,
            mismatch_percent=round(mismatches / total * 100, 1) if total else 0,
            risk_percent=round(avg_risk, 1),
            top_suppliers=[g for g, _ in suppliers.most_common(3)],
            top_customers=[g for g, _ in customers.most_common(3)],
            largest_difference=round(largest_diff, 2),
        ))
    return results


def build_heatmaps(records: list[ComparisonRecord]) -> RiskHeatmaps:
    discrepancies = [r for r in records if r.result_type != ComparisonResultType.MATCHED]

    def _cells(group_fn, limit=12) -> list[HeatmapCell]:
        groups: dict[str, list[ComparisonRecord]] = defaultdict(list)
        for rec in discrepancies:
            groups[group_fn(rec)].append(rec)
        cells = []
        for label, group in sorted(groups.items(), key=lambda x: -len(x[1])):
            risk = max((r.risk_score for r in group), default=0)
            cells.append(HeatmapCell(
                label=label,
                count=len(group),
                risk_score=risk,
                risk_percent=round(risk, 1),
            ))
        return cells[:limit]

    category_cells = []
    cat_groups: dict[str, list[ComparisonRecord]] = defaultdict(list)
    for rec in discrepancies:
        rt = rec.result_type.value if hasattr(rec.result_type, "value") else str(rec.result_type)
        cat_groups[rt].append(rec)
    for label, group in cat_groups.items():
        risk = max((r.risk_score for r in group), default=0)
        category_cells.append(HeatmapCell(label=label, count=len(group), risk_score=risk, risk_percent=round(risk, 1)))

    return RiskHeatmaps(
        months=_cells(_month),
        suppliers=_cells(lambda r: (r.gstin_gstr1 or "Unknown").upper()),
        customers=_cells(lambda r: (r.gstin_eway or "Unknown").upper()),
        categories=sorted(category_cells, key=lambda c: -c.risk_score),
    )
