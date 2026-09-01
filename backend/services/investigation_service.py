"""Investigation workbench service — cases from comparison discrepancies."""

from __future__ import annotations

import hashlib
from typing import List, Optional

from comparison.comparison_types import ComparisonResultType, RiskLevel
from comparison.normalizer import normalize_invoice
from comparison.comparators.observation_generator import generate_observations
from comparison.result_models import ComparisonRecord
from intelligence.intelligence_service import get_session_intelligence
from models.investigation import (
    BulkCaseUpdateRequest,
    CaseTrackingSummary,
    CaseUpdateRequest,
    InvestigationCase,
    InvestigationFilterParams,
    InvestigationListResponse,
)
from services.comparison_store import get_result
from services.investigation_store import get_case, list_cases, save_case, save_cases

CATEGORY_MAP = {
    "MISSING_IN_GSTR1": "Missing in GSTR-1",
    "MISSING_IN_EWAY": "Missing in EWB",
    "GSTIN_MISMATCH": "GSTIN Mismatch",
    "DATE_MISMATCH": "Date Mismatch",
    "VALUE_MISMATCH": "Value Mismatch",
    "DUPLICATE": "Duplicate",
    "MULTIPLE_MATCHES": "Multiple Matches",
    "HIGH_RISK": "High Risk",
}

CLOSED_STATUSES = {"Accepted", "Rejected", "Verified"}


def _case_id(session_id: str, record: ComparisonRecord, index: int) -> str:
    raw = f"{session_id}:{record.normalized_invoice}:{record.result_type}:{index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _priority(risk_score: int) -> str:
    if risk_score >= 95:
        return "Critical"
    if risk_score >= 70:
        return "High"
    if risk_score >= 40:
        return "Medium"
    return "Low"


def _record_to_case(session_id: str, record: ComparisonRecord, index: int, obs_map: dict) -> InvestigationCase:
    obs = obs_map.get(record.normalized_invoice)
    case_id = _case_id(session_id, record, index)
    return InvestigationCase(
        case_id=case_id,
        case_number=f"CASE-{case_id[:8].upper()}",
        session_id=session_id,
        result_type=record.result_type.value if hasattr(record.result_type, "value") else str(record.result_type),
        invoice_number=record.invoice_number,
        normalized_invoice=record.normalized_invoice,
        supplier_gstin=record.gstin_gstr1 or record.gstin_eway,
        recipient_gstin=record.gstin_eway or record.gstin_gstr1,
        invoice_date=record.date_gstr1 or record.date_eway,
        invoice_value=record.invoice_value_gstr1 or record.invoice_value_eway,
        taxable_value=record.taxable_value_gstr1 or record.taxable_value_eway,
        comparison_result=record.result_type.value if hasattr(record.result_type, "value") else str(record.result_type),
        risk_score=record.risk_score,
        possible_reason=obs.possible_reasons[0] if obs and obs.possible_reasons else "",
        suggested_verification=obs.officer_action if obs else "Verify source documents and books of account.",
        source_period=record.source_period,
        ewb_number=record.ewb_number,
        difference_amount=record.difference_amount,
        priority=_priority(record.risk_score),
        created_at=InvestigationCase.now_iso(),
        updated_at=InvestigationCase.now_iso(),
    )


def _apply_intelligence(case: InvestigationCase, intel_map: dict) -> InvestigationCase:
    intel = intel_map.get(case.case_id)
    if not intel:
        return case
    return case.model_copy(update={
        "priority": intel.priority,
        "priority_score": intel.priority_score,
        "priority_reason": intel.priority_reason,
        "patterns": intel.patterns,
        "recommended_documents": intel.recommended_documents,
        "possible_causes": intel.possible_causes,
        "possible_reason": intel.priority_reason or case.possible_reason,
        "suggested_verifications": intel.suggested_verifications,
        "suggested_verification": ", ".join(intel.suggested_verifications[:3]) or case.suggested_verification,
        "gst_provisions": intel.gst_provisions,
        "related_case_ids": intel.related_case_ids,
    })


def enrich_cases_from_intelligence(session_id: str) -> List[InvestigationCase]:
    """Apply cached intelligence enrichment to existing cases."""
    cases = list_cases(session_id)
    intel_data = get_session_intelligence(session_id)
    if not intel_data.cases:
        return cases
    intel_map = {c.case_id: c for c in intel_data.cases}
    enriched = [_apply_intelligence(c, intel_map) for c in cases]
    save_cases(session_id, enriched)
    return enriched


def sync_cases_from_comparison(session_id: str) -> List[InvestigationCase]:
    existing = {c.normalized_invoice + c.result_type: c for c in list_cases(session_id)}
    result = get_result(session_id)
    if not result:
        return list_cases(session_id)

    observations = generate_observations(result.records, limit=500)
    obs_map = {normalize_invoice(o.invoice_number): o for o in observations}

    new_cases: List[InvestigationCase] = []
    for idx, record in enumerate(result.records):
        if record.result_type == ComparisonResultType.MATCHED:
            continue
        key = record.normalized_invoice + (record.result_type.value if hasattr(record.result_type, "value") else str(record.result_type))
        if key in existing:
            new_cases.append(existing[key])
            continue
        new_cases.append(_record_to_case(session_id, record, idx, obs_map))

    save_cases(session_id, new_cases)
    intel_data = get_session_intelligence(session_id)
    if not intel_data.cases:
        return new_cases
    intel_map = {c.case_id: c for c in intel_data.cases}
    enriched = [_apply_intelligence(c, intel_map) for c in new_cases]
    save_cases(session_id, enriched)
    return enriched


def _apply_filters(cases: List[InvestigationCase], params: InvestigationFilterParams) -> List[InvestigationCase]:
    filtered = cases
    if params.category and params.category != "ALL":
        if params.category == "HIGH_RISK":
            filtered = [c for c in filtered if c.risk_score >= 70]
        else:
            filtered = [c for c in filtered if c.result_type == params.category]
    if params.high_risk_only:
        filtered = [c for c in filtered if c.risk_score >= 70]
    if params.month:
        filtered = [c for c in filtered if params.month.lower() in (c.source_period or "").lower()]
    if params.gstin:
        g = params.gstin.upper()
        filtered = [c for c in filtered if g in (c.supplier_gstin or "").upper() or g in (c.recipient_gstin or "").upper()]
    if params.status:
        filtered = [c for c in filtered if c.status == params.status]
    if params.comparison_type:
        filtered = [c for c in filtered if c.comparison_type == params.comparison_type]
    if params.risk_min is not None:
        filtered = [c for c in filtered if c.risk_score >= params.risk_min]
    if params.search:
        q = params.search.lower()
        filtered = [
            c for c in filtered
            if q in c.invoice_number.lower()
            or q in c.normalized_invoice.lower()
            or q in c.case_number.lower()
            or q in (c.supplier_gstin or "").lower()
        ]
    return filtered


def build_summary(cases: List[InvestigationCase]) -> CaseTrackingSummary:
    return CaseTrackingSummary(
        total=len(cases),
        open=sum(1 for c in cases if c.status not in CLOSED_STATUSES),
        closed=sum(1 for c in cases if c.status in CLOSED_STATUSES),
        pending=sum(1 for c in cases if c.status == "Pending"),
        verified=sum(1 for c in cases if c.status == "Verified"),
        accepted=sum(1 for c in cases if c.status == "Accepted"),
        rejected=sum(1 for c in cases if c.status == "Rejected"),
        high_risk=sum(1 for c in cases if c.risk_score >= 70),
    )


def build_categories(cases: List[InvestigationCase]) -> dict:
    counts = {k: 0 for k in CATEGORY_MAP}
    counts["HIGH_RISK"] = sum(1 for c in cases if c.risk_score >= 70)
    for case in cases:
        if case.result_type in counts:
            counts[case.result_type] += 1
    return {CATEGORY_MAP[k]: counts[k] for k in CATEGORY_MAP}


def get_investigation(params: InvestigationFilterParams) -> InvestigationListResponse:
    cases = sync_cases_from_comparison(params.session_id)
    filtered = _apply_filters(cases, params)
    filtered.sort(key=lambda c: (-c.risk_score, c.invoice_number))
    page = filtered[params.offset : params.offset + params.limit]
    return InvestigationListResponse(
        session_id=params.session_id,
        summary=build_summary(cases),
        cases=page,
        categories=build_categories(cases),
    )


def get_case_detail(session_id: str, case_id: str) -> Optional[InvestigationCase]:
    sync_cases_from_comparison(session_id)
    case = get_case(session_id, case_id)
    if not case:
        return None
    intel = get_case_intelligence(session_id, case_id)
    if intel:
        return _apply_intelligence(case, {case_id: intel})
    return case


def update_case(case_id: str, body: CaseUpdateRequest) -> InvestigationCase:
    case = get_case(body.session_id, case_id)
    if not case:
        raise ValueError("Case not found")
    if body.status is not None:
        case.status = body.status
    if body.priority is not None:
        case.priority = body.priority
    if body.assigned_officer is not None:
        case.assigned_officer = body.assigned_officer
    if body.officer_remarks is not None:
        case.officer_remarks = body.officer_remarks
    if body.attachments is not None:
        case.attachments = body.attachments
    case.updated_at = InvestigationCase.now_iso()
    save_case(case)
    return case


def bulk_update_cases(body: BulkCaseUpdateRequest) -> List[InvestigationCase]:
    updated = []
    for case_id in body.case_ids:
        case = get_case(body.session_id, case_id)
        if not case:
            continue
        if body.status is not None:
            case.status = body.status
        if body.officer_remarks:
            case.officer_remarks = body.officer_remarks
        case.updated_at = InvestigationCase.now_iso()
        save_case(case)
        updated.append(case)
    return updated


def export_cases(session_id: str, case_ids: Optional[List[str]] = None, high_risk_only: bool = False) -> List[InvestigationCase]:
    cases = sync_cases_from_comparison(session_id)
    if case_ids:
        id_set = set(case_ids)
        cases = [c for c in cases if c.case_id in id_set]
    if high_risk_only:
        cases = [c for c in cases if c.risk_score >= 70]
    return cases
