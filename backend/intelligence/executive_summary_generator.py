"""Executive insights and intelligence summary cards."""

from __future__ import annotations

from comparison.comparison_types import ComparisonResultType
from comparison.result_models import ComparisonRecord
from intelligence.anomaly_detector import critical_entity_count, rank_customers, rank_suppliers
from intelligence.models import AuditIntelligenceCards, ExecutiveInsights, IntelligenceSummary
from intelligence.pattern_detector import detect_patterns
from intelligence.timeline_builder import build_heatmaps, build_month_analysis
from intelligence.case_prioritizer import prioritize_case
from models.investigation import InvestigationCase


def build_executive_insights(
    records: list[ComparisonRecord],
    cases: list[InvestigationCase],
    patterns: list,
    months: list,
    suppliers: list,
    customers: list,
) -> ExecutiveInsights:
    discrepancies = [r for r in records if r.result_type != ComparisonResultType.MATCHED]
    sorted_cases = sorted(cases, key=lambda c: -c.risk_score)

    top_obs = []
    for case in sorted_cases[:10]:
        top_obs.append(f"{case.result_type}: Invoice {case.invoice_number} (Risk {case.risk_score})")

    top_risks = [p.description for p in patterns[:10]]
    if not top_risks and sorted_cases:
        top_risks = [f"High-risk case {c.case_number} — {c.result_type}" for c in sorted_cases[:5]]

    largest_tax = max((abs(r.difference_amount) for r in discrepancies), default=0.0)
    largest_supplier = suppliers[0].gstin if suppliers else ""
    largest_customer = customers[0].gstin if customers else ""

    verify_months = [
        m.month for m in sorted(months, key=lambda x: -x.mismatch_percent)
        if m.mismatch_percent >= 20 or m.mismatch_count >= 2
    ][:5]

    return ExecutiveInsights(
        top_observations=top_obs,
        top_risks=top_risks,
        largest_tax_impact=round(largest_tax, 2),
        largest_supplier_risk=largest_supplier,
        largest_customer_risk=largest_customer,
        months_requiring_verification=verify_months,
    )


def build_dashboard_cards(
    records: list[ComparisonRecord],
    cases: list[InvestigationCase],
    months: list,
    suppliers: list,
    customers: list,
) -> AuditIntelligenceCards:
    discrepancies = [r for r in records if r.result_type != ComparisonResultType.MATCHED]
    high_risk = sum(1 for c in cases if c.risk_score >= 70)
    open_cases = sum(1 for c in cases if c.status not in {"Accepted", "Rejected", "Verified"})
    largest_diff = max((abs(r.difference_amount) for r in discrepancies), default=0.0)

    highest_risk_month = ""
    if months:
        highest_risk_month = max(months, key=lambda m: m.risk_percent).month

    return AuditIntelligenceCards(
        high_risk_cases=high_risk,
        critical_suppliers=critical_entity_count(suppliers),
        critical_customers=critical_entity_count(customers),
        largest_tax_difference=round(largest_diff, 2),
        highest_risk_month=highest_risk_month,
        open_investigation_cases=open_cases,
    )


def build_intelligence_summary(
    session_id: str,
    records: list[ComparisonRecord],
    cases: list[InvestigationCase],
    case_intel_map: dict[str, object],
) -> IntelligenceSummary:
    patterns = detect_patterns(records)
    months = build_month_analysis(records)
    suppliers = rank_suppliers(records)
    customers = rank_customers(records)
    heatmaps = build_heatmaps(records)
    cards = build_dashboard_cards(records, cases, months, suppliers, customers)
    insights = build_executive_insights(records, cases, patterns, months, suppliers, customers)

    priority_cases = sorted(
        case_intel_map.values(),
        key=lambda c: -getattr(c, "priority_score", 0),
    )[:20]

    return IntelligenceSummary(
        session_id=session_id,
        cards=cards,
        patterns=patterns,
        heatmaps=heatmaps,
        executive_insights=insights,
        priority_cases=list(priority_cases),  # type: ignore[arg-type]
    )
