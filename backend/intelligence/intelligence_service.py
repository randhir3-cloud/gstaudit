"""Orchestrates full audit intelligence analysis for a session."""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional

from comparison.comparison_types import ComparisonResultType
from comparison.result_models import ComparisonRecord
from intelligence.anomaly_detector import rank_customers, rank_suppliers
from intelligence.case_prioritizer import prioritize_case
from intelligence.document_recommender import build_document_catalog
from intelligence.executive_summary_generator import build_intelligence_summary
from intelligence.intelligence_store import get_intelligence, save_intelligence
from intelligence.models import CaseIntelligence, IntelligenceFullResponse
from intelligence.pattern_detector import detect_patterns
from intelligence.timeline_builder import build_month_analysis
from models.investigation import InvestigationCase
from services.comparison_store import get_result
from services.investigation_store import list_cases


def _case_id(session_id: str, record: ComparisonRecord, index: int) -> str:
    raw = f"{session_id}:{record.normalized_invoice}:{record.result_type}:{index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _related_cases(record: ComparisonRecord, records: list[ComparisonRecord], session_id: str) -> list[str]:
    related: list[str] = []
    customer = (record.gstin_eway or "").upper()
    supplier = (record.gstin_gstr1 or "").upper()
    for idx, rec in enumerate(records):
        if rec.result_type == ComparisonResultType.MATCHED:
            continue
        if rec.normalized_invoice == record.normalized_invoice and rec is not record:
            related.append(_case_id(session_id, rec, idx))
        elif customer and (rec.gstin_eway or "").upper() == customer and rec.result_type == record.result_type:
            cid = _case_id(session_id, rec, idx)
            if cid not in related:
                related.append(cid)
        elif supplier and (rec.gstin_gstr1 or "").upper() == supplier and rec.result_type == record.result_type:
            cid = _case_id(session_id, rec, idx)
            if cid not in related:
                related.append(cid)
    return related[:5]


def get_session_intelligence(session_id: str) -> IntelligenceFullResponse:
    """Read cached intelligence only — never runs analysis."""
    cached = get_intelligence(session_id)
    return cached or IntelligenceFullResponse(session_id=session_id)


def enqueue_intelligence_analysis(session_id: str) -> dict:
    """Enqueue intelligence as a background job."""
    from models.job import JobCreateRequest, JobType
    from services.job_service import create_job

    job = create_job(
        JobCreateRequest(
            session_id=session_id,
            job_type=JobType.INTELLIGENCE,
            title="Audit Intelligence Analysis",
        )
    )
    return {"job_id": job.job_id, "status": job.status.value, "session_id": session_id}


def analyze_session(session_id: str, *, force: bool = False) -> IntelligenceFullResponse:
    cached = get_intelligence(session_id)
    if cached and not force:
        return cached

    result = get_result(session_id)
    if not result:
        empty = IntelligenceFullResponse(session_id=session_id)
        save_intelligence(session_id, empty)
        return empty

    records = result.records
    cases = list_cases(session_id)
    patterns = detect_patterns(records)

    case_intel_map: Dict[str, CaseIntelligence] = {}
    for idx, rec in enumerate(records):
        if rec.result_type == ComparisonResultType.MATCHED:
            continue
        cid = _case_id(session_id, rec, idx)
        related = _related_cases(rec, records, session_id)
        case_intel_map[cid] = prioritize_case(cid, rec, patterns, related)

    summary = build_intelligence_summary(session_id, records, cases, case_intel_map)
    full = IntelligenceFullResponse(
        session_id=session_id,
        summary=summary,
        months=build_month_analysis(records),
        suppliers=rank_suppliers(records),
        customers=rank_customers(records),
        cases=sorted(case_intel_map.values(), key=lambda c: -c.priority_score),
        document_recommendations=build_document_catalog(),
    )
    save_intelligence(session_id, full)
    return full


def get_case_intelligence(session_id: str, case_id: str) -> Optional[CaseIntelligence]:
    data = analyze_session(session_id)
    for case in data.cases:
        if case.case_id == case_id:
            return case
    return None


def enrich_investigation_case(case: InvestigationCase, intel: Optional[CaseIntelligence]) -> InvestigationCase:
    if not intel:
        return case
    updates = {
        "priority": intel.priority,
        "possible_reason": intel.priority_reason or case.possible_reason,
        "suggested_verification": ", ".join(intel.suggested_verifications[:3]) or case.suggested_verification,
    }
    enriched = case.model_copy(update=updates)
    enriched.__dict__["intelligence"] = intel.model_dump()
    return enriched
