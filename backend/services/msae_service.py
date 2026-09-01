"""Multi-Source Audit Engine — platform orchestration over plugin comparison outputs."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

from comparison.comparison_types import ComparisonResultType
from comparison.result_models import ComparisonRecord, ComparisonResult
from models.msae import (
    AuditScores,
    AuditTimelineEvent,
    ConsolidatedAuditReport,
    EntityRiskScore,
    MasterAuditCase,
    MSAEFullResponse,
    MSAESummary,
    PluginFinding,
)
from plugins.sdk.loader import ensure_plugins_loaded
from plugins.sdk.registry import plugin_registry
from services.audit_session_store import get_session
from services.comparison_store import list_results
from services.msae_pattern_engine import detect_cross_source_patterns, patterns_for_master_case
from services.msae_store import get_msae, save_msae

COMPARISON_LABELS = {
    "gstr1_ewb_outward": "GSTR-1 ↔ EWB Outward",
    "gstr2a_ewb_inward": "GSTR-2A ↔ EWB Inward",
}


def _comparison_label(comparison_id: str) -> str:
    ensure_plugins_loaded()
    for pair in plugin_registry.comparison_pairs:
        if pair.get("comparison_id") == comparison_id:
            return pair.get("label", comparison_id)
    return COMPARISON_LABELS.get(comparison_id, comparison_id)


def _finding_id(session_id: str, comparison_id: str, record: ComparisonRecord, index: int) -> str:
    raw = f"{session_id}:{comparison_id}:{record.normalized_invoice}:{record.result_type}:{index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _master_case_id(session_id: str, correlation_value: str) -> str:
    raw = f"{session_id}:invoice:{correlation_value}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _priority(risk_score: int) -> Tuple[str, int]:
    if risk_score >= 95:
        return "Critical", risk_score
    if risk_score >= 70:
        return "High", risk_score
    if risk_score >= 40:
        return "Medium", risk_score
    return "Low", risk_score


def _record_to_finding(
    session_id: str,
    result: ComparisonResult,
    record: ComparisonRecord,
    index: int,
) -> PluginFinding:
    return PluginFinding(
        finding_id=_finding_id(session_id, result.comparison_id, record, index),
        comparison_id=result.comparison_id,
        comparison_label=_comparison_label(result.comparison_id),
        result_type=record.result_type.value if hasattr(record.result_type, "value") else str(record.result_type),
        invoice_number=record.invoice_number,
        normalized_invoice=record.normalized_invoice,
        supplier_gstin=(record.gstin_gstr1 or record.details.get("supplier_gstin", "")).upper(),
        recipient_gstin=(record.gstin_eway or record.details.get("recipient_gstin", "")).upper(),
        invoice_date=record.date_gstr1 or record.date_eway,
        invoice_value=max(record.invoice_value_gstr1, record.invoice_value_eway),
        taxable_value=max(record.taxable_value_gstr1, record.taxable_value_eway),
        source_period=record.source_period,
        ewb_number=record.ewb_number,
        document_number=record.invoice_number or record.normalized_invoice,
        difference_amount=record.difference_amount,
        risk_score=record.risk_score,
        description=f"{record.result_type}: {record.invoice_number or record.normalized_invoice}",
        record_index=index,
    )


def extract_plugin_findings(session_id: str, results: Optional[List[ComparisonResult]] = None) -> List[PluginFinding]:
    """Consume all stored comparison outputs for a session."""
    results = results if results is not None else list_results(session_id)
    findings: List[PluginFinding] = []
    for result in results:
        for idx, record in enumerate(result.records):
            if record.result_type == ComparisonResultType.MATCHED:
                continue
            findings.append(_record_to_finding(session_id, result, record, idx))
    return findings


def correlate_findings(
    session_id: str,
    findings: List[PluginFinding],
    financial_year: str = "",
) -> List[MasterAuditCase]:
    """Group plugin findings into master investigation cases by invoice (primary key)."""
    groups: Dict[str, List[PluginFinding]] = defaultdict(list)
    for finding in findings:
        key = finding.normalized_invoice or finding.invoice_number or finding.finding_id
        groups[key.upper()].append(finding)

    master_cases: List[MasterAuditCase] = []
    for corr_value, group in groups.items():
        if not corr_value:
            continue
        max_risk = max((f.risk_score for f in group), default=0)
        priority, priority_score = _priority(max_risk)
        comparison_ids = sorted({f.comparison_id for f in group})
        result_types = sorted({f.result_type for f in group})
        primary = max(group, key=lambda f: f.risk_score)
        total_diff = sum(abs(f.difference_amount) for f in group)
        case_id = _master_case_id(session_id, corr_value)

        master_cases.append(MasterAuditCase(
            master_case_id=case_id,
            case_number=f"MSAE-{case_id[:8].upper()}",
            session_id=session_id,
            correlation_key="invoice",
            correlation_value=corr_value,
            invoice_number=primary.invoice_number,
            normalized_invoice=primary.normalized_invoice,
            supplier_gstin=primary.supplier_gstin,
            recipient_gstin=primary.recipient_gstin,
            financial_year=financial_year,
            tax_period=primary.source_period,
            ewb_number=primary.ewb_number,
            document_number=primary.document_number,
            invoice_value=max(f.invoice_value for f in group),
            difference_amount=total_diff,
            risk_score=max_risk,
            priority=priority,
            priority_score=priority_score,
            source_count=len(comparison_ids),
            comparison_ids=comparison_ids,
            result_types=result_types,
            child_findings=sorted(group, key=lambda f: (-f.risk_score, f.comparison_id)),
            created_at=MasterAuditCase.now_iso(),
            updated_at=MasterAuditCase.now_iso(),
        ))

    master_cases.sort(key=lambda c: (-c.risk_score, c.invoice_number))
    return master_cases


def compute_audit_scores(
    master_cases: List[MasterAuditCase],
    findings: List[PluginFinding],
    sources: List[str],
) -> AuditScores:
    if not findings:
        return AuditScores(audit_confidence=0.0, confidence_factors=["No comparison data available"])

    dealer_risk = min(100, max((c.risk_score for c in master_cases), default=0))

    month_map: Counter[str] = Counter()
    month_risk: dict[str, int] = defaultdict(int)
    for f in findings:
        month = (f.source_period or f.invoice_date or "Unknown")[:20]
        month_map[month] += 1
        month_risk[month] = max(month_risk[month], f.risk_score)

    supplier_map: Counter[str] = Counter()
    supplier_diff: dict[str, float] = defaultdict(float)
    supplier_risk: dict[str, int] = defaultdict(int)
    customer_map: Counter[str] = Counter()
    customer_diff: dict[str, float] = defaultdict(float)
    customer_risk: dict[str, int] = defaultdict(int)

    for f in findings:
        if f.supplier_gstin and f.supplier_gstin != "UNKNOWN":
            supplier_map[f.supplier_gstin] += 1
            supplier_diff[f.supplier_gstin] += abs(f.difference_amount)
            supplier_risk[f.supplier_gstin] = max(supplier_risk[f.supplier_gstin], f.risk_score)
        if f.recipient_gstin and f.recipient_gstin != "UNKNOWN":
            customer_map[f.recipient_gstin] += 1
            customer_diff[f.recipient_gstin] += abs(f.difference_amount)
            customer_risk[f.recipient_gstin] = max(customer_risk[f.recipient_gstin], f.risk_score)

    month_scores = [
        EntityRiskScore(
            entity_type="month",
            entity_id=m,
            label=m,
            risk_score=min(100, month_risk[m] + month_map[m] * 3),
            issue_count=month_map[m],
        )
        for m in sorted(month_map, key=lambda x: -month_map[x])
    ][:12]

    supplier_scores = [
        EntityRiskScore(
            entity_type="supplier",
            entity_id=g,
            label=g,
            risk_score=min(100, supplier_risk[g] + supplier_map[g] * 5),
            issue_count=supplier_map[g],
            total_difference=supplier_diff[g],
        )
        for g in supplier_map
    ]
    supplier_scores.sort(key=lambda s: -s.risk_score)

    customer_scores = [
        EntityRiskScore(
            entity_type="customer",
            entity_id=g,
            label=g,
            risk_score=min(100, customer_risk[g] + customer_map[g] * 5),
            issue_count=customer_map[g],
            total_difference=customer_diff[g],
        )
        for g in customer_map
    ]
    customer_scores.sort(key=lambda s: -s.risk_score)

    cross_plugin = sum(1 for c in master_cases if c.source_count > 1)
    high_risk = sum(1 for c in master_cases if c.risk_score >= 70)
    officer_priority = min(100, high_risk * 10 + cross_plugin * 15 + dealer_risk // 2)

    confidence = 0.4
    factors = []
    if sources:
        confidence += min(0.3, len(sources) * 0.15)
        factors.append(f"{len(sources)} comparison source(s) analyzed")
    if findings:
        confidence += 0.2
        factors.append(f"{len(findings)} plugin findings ingested")
    if cross_plugin:
        confidence += 0.1
        factors.append(f"{cross_plugin} cross-plugin correlations")

    return AuditScores(
        dealer_risk_score=dealer_risk,
        month_risk_scores=month_scores,
        supplier_risk_scores=supplier_scores[:10],
        customer_risk_scores=customer_scores[:10],
        officer_priority_score=officer_priority,
        audit_confidence=min(1.0, confidence),
        confidence_factors=factors,
    )


def build_audit_timeline(session_id: str, results: List[ComparisonResult]) -> List[AuditTimelineEvent]:
    session = get_session(session_id)
    events: List[AuditTimelineEvent] = []

    if session:
        for entry in session.upload_history or []:
            events.append(AuditTimelineEvent(
                stage="upload",
                title=f"Uploaded {entry.dataset_label}",
                description=entry.filename,
                timestamp=entry.timestamp,
                metadata={"dataset": entry.dataset, "rows": entry.rows},
            ))
        for key, ds in (session.datasets or {}).items():
            if ds.merged:
                events.append(AuditTimelineEvent(
                    stage="merge",
                    title=f"Merged {ds.label}",
                    description=f"{ds.row_count} rows",
                    timestamp=session.updated_at,
                    metadata={"dataset": key},
                ))

    for result in results:
        events.append(AuditTimelineEvent(
            stage="comparison",
            title=f"Comparison: {_comparison_label(result.comparison_id)}",
            description=f"{result.summary.matched_count} matched, risk {result.summary.overall_risk_score}",
            timestamp=result.summary.model_dump().get("completed_at", MasterAuditCase.now_iso()),
            metadata={"comparison_id": result.comparison_id, "summary": result.summary.model_dump()},
        ))

    events.append(AuditTimelineEvent(
        stage="msae_orchestration",
        title="Multi-Source Audit Engine",
        description="Consolidated cross-plugin findings into master cases",
        timestamp=MasterAuditCase.now_iso(),
        metadata={"session_id": session_id},
    ))

    if session and session.comparison_status:
        for pair in session.comparison_status:
            if pair.status == "completed":
                events.append(AuditTimelineEvent(
                    stage="investigation",
                    title=f"Investigation ready: {pair.label}",
                    description=f"Status: {pair.status}",
                    timestamp=session.updated_at,
                    metadata={"comparison_id": pair.id},
                ))

    events.sort(key=lambda e: e.timestamp or "")
    return events


def _build_heatmaps(master_cases: List[MasterAuditCase]) -> dict:
    month_cells = []
    month_counts: Counter[str] = Counter()
    month_risk: dict[str, int] = defaultdict(int)
    for case in master_cases:
        month = (case.tax_period or "Unknown")[:15]
        month_counts[month] += 1
        month_risk[month] = max(month_risk[month], case.risk_score)
    for label, count in month_counts.most_common(12):
        month_cells.append({"label": label, "count": count, "risk_score": month_risk[label]})

    category_cells = []
    cat_counts: Counter[str] = Counter()
    cat_risk: dict[str, int] = defaultdict(int)
    for case in master_cases:
        for rt in case.result_types:
            cat_counts[rt] += 1
            cat_risk[rt] = max(cat_risk[rt], case.risk_score)
    for label, count in cat_counts.most_common(8):
        category_cells.append({"label": label.replace("_", " "), "count": count, "risk_score": cat_risk[label]})

    return {"months": month_cells, "categories": category_cells}


def _build_trend(findings: List[PluginFinding]) -> List[dict]:
    by_period: Counter[str] = Counter()
    for f in findings:
        by_period[(f.source_period or "Unknown")[:15]] += 1
    return [{"period": p, "count": c} for p, c in sorted(by_period.items())]


def orchestrate_session(session_id: str, *, force: bool = False) -> MSAEFullResponse:
    """Run full MSAE pipeline: ingest → correlate → score → pattern → timeline."""
    if not force:
        cached = get_msae(session_id)
        if cached:
            return cached

    results = list_results(session_id)
    findings = extract_plugin_findings(session_id, results)
    session = get_session(session_id)
    fy = (session.financial_year or session.dealer.financial_year) if session else ""

    master_cases = correlate_findings(session_id, findings, financial_year=fy)
    patterns = detect_cross_source_patterns(master_cases, findings)

    for case in master_cases:
        case.patterns = patterns_for_master_case(case, patterns)

    sources = sorted({r.comparison_id for r in results})
    scores = compute_audit_scores(master_cases, findings, sources)
    timeline = build_audit_timeline(session_id, results)

    cross_plugin = sum(1 for c in master_cases if c.source_count > 1)
    high_risk = sum(1 for c in master_cases if c.risk_score >= 70)
    top_risks = [p.description for p in patterns[:5]]
    if cross_plugin:
        top_risks.insert(0, f"{cross_plugin} invoices span multiple comparison sources")

    summary = MSAESummary(
        session_id=session_id,
        master_case_count=len(master_cases),
        cross_plugin_case_count=cross_plugin,
        total_findings=len(findings),
        high_risk_cases=high_risk,
        sources_analyzed=sources,
        top_risks=top_risks,
        scores=scores,
        generated_at=MasterAuditCase.now_iso(),
    )

    response = MSAEFullResponse(
        session_id=session_id,
        summary=summary,
        master_cases=master_cases,
        patterns=patterns,
        timeline=timeline,
        heatmaps=_build_heatmaps(master_cases),
        trend=_build_trend(findings),
    )
    save_msae(session_id, response)
    return response


def get_session_msae(session_id: str) -> MSAEFullResponse:
    """Read cached MSAE or orchestrate if missing."""
    cached = get_msae(session_id)
    if cached:
        return cached
    return orchestrate_session(session_id)


def get_master_case(session_id: str, master_case_id: str) -> Optional[MasterAuditCase]:
    data = get_session_msae(session_id)
    for case in data.master_cases:
        if case.master_case_id == master_case_id:
            return case
    return None


def build_consolidated_report(session_id: str) -> ConsolidatedAuditReport:
    data = get_session_msae(session_id)
    session = get_session(session_id)
    dealer = session.dealer.legal_name if session else "Dealer"
    cross = data.summary.cross_plugin_case_count
    exec_summary = (
        f"Consolidated audit for {dealer}: {data.summary.master_case_count} master cases "
        f"from {data.summary.total_findings} plugin findings across "
        f"{len(data.summary.sources_analyzed)} source(s). "
        f"{cross} case(s) span multiple comparison plugins. "
        f"Dealer risk score: {data.summary.scores.dealer_risk_score}/100."
    )
    return ConsolidatedAuditReport(
        session_id=session_id,
        executive_summary=exec_summary,
        master_cases=data.master_cases[:50],
        scores=data.summary.scores,
        patterns=data.patterns,
        timeline=data.timeline,
        sources=data.summary.sources_analyzed,
        generated_at=data.summary.generated_at,
    )


def enqueue_msae_orchestration(session_id: str) -> dict:
    """Trigger MSAE orchestration (sync for now; extensible to background job)."""
    data = orchestrate_session(session_id, force=True)
    from services.case_management_service import sync_cases_from_msae
    sync_cases_from_msae(session_id)
    return {
        "session_id": session_id,
        "master_case_count": data.summary.master_case_count,
        "sources_analyzed": data.summary.sources_analyzed,
    }
