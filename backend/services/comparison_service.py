"""Comparison orchestration service."""

from __future__ import annotations

import base64
from typing import Callable, List, Optional

from comparison import bootstrap as _comparison_bootstrap  # noqa: F401 — register comparators
from comparison.comparison_types import ComparisonResultType
from comparison.engine import ComparisonEngine
from comparison.result_models import ComparisonDetailPage, ComparisonRecord, ComparisonResult
from models.audit_session import AuditSession, ComparisonPairStatus, DiscrepancySummary
from models.job import JobCreateRequest, JobType
from services.audit_session_store import get_session, upsert_session
from services.comparison_store import (
    cache_workbook,
    get_comparison_status,
    get_result,
    get_workbook,
    save_result,
    set_comparison_status,
)
from services.dashboard_service import build_dashboard, ensure_session_datasets
from services.job_service import create_job

_engine = ComparisonEngine()


def _decode_b64(data: str) -> bytes:
    return base64.b64decode(data)


def enqueue_gstr1_eway_comparison(
    session_id: str,
    *,
    gstr1_workbook_base64: str = "",
    ewb_outward_workbook_base64: str = "",
) -> dict:
    """Enqueue comparison as background job — HTTP must use this."""
    session = get_session(session_id)
    if not session:
        raise ValueError("Session not found")
    job = create_job(
        JobCreateRequest(
            session_id=session_id,
            job_type=JobType.COMPARISON,
            title="GSTR-1 ↔ EWB Outward Comparison",
            payload={
                "comparison_id": "gstr1_ewb_outward",
                "gstr1_workbook_base64": gstr1_workbook_base64,
                "ewb_outward_workbook_base64": ewb_outward_workbook_base64,
            },
        )
    )
    set_comparison_status(session_id, "running")
    return {"job_id": job.job_id, "status": job.status.value, "session_id": session_id}


def run_gstr1_eway_comparison_with_progress(
    session_id: str,
    *,
    gstr1_workbook_base64: str = "",
    ewb_outward_workbook_base64: str = "",
    progress_callback: Optional[Callable] = None,
    checkpoint: Optional[dict] = None,
    job_id: Optional[str] = None,
) -> ComparisonResult:
    """Worker entry point with progress reporting and checkpoint resume."""
    from services.job_service import _is_cancelled

    session = get_session(session_id)
    if not session:
        raise ValueError("Session not found")

    gstr1_bytes = get_workbook(session_id, "gstr1")
    ewb_bytes = get_workbook(session_id, "ewb_outward")
    if gstr1_workbook_base64:
        gstr1_bytes = _decode_b64(gstr1_workbook_base64)
        cache_workbook(session_id, "gstr1", gstr1_bytes)
    if ewb_outward_workbook_base64:
        ewb_bytes = _decode_b64(ewb_outward_workbook_base64)
        cache_workbook(session_id, "ewb_outward", ewb_bytes)

    if not gstr1_bytes or not ewb_bytes:
        set_comparison_status(session_id, "ready")
        raise ValueError("Both GSTR-1 and EWB Outward workbooks are required")

    # Restore classified records from checkpoint
    restored_checkpoint = None
    if checkpoint and checkpoint.get("classified"):
        restored_checkpoint = {
            "eway_index": checkpoint.get("eway_index", 0),
            "matched_gstr1_keys": checkpoint.get("matched_gstr1_keys", []),
            "classified": [ComparisonRecord.model_validate(c) for c in checkpoint["classified"]],
        }

    def cancel_check() -> bool:
        return bool(job_id and _is_cancelled(job_id))

    result = _engine.run(
        "gstr1_ewb_outward",
        gstr1_bytes,
        ewb_bytes,
        session_id,
        progress_callback=progress_callback,
        checkpoint=restored_checkpoint,
        cancel_check=cancel_check,
    )
    save_result(result)

    return result


def run_gstr1_eway_comparison(
    session_id: str,
    *,
    gstr1_workbook_base64: str = "",
    ewb_outward_workbook_base64: str = "",
) -> ComparisonResult:
    """Synchronous path for unit tests."""
    result = run_gstr1_eway_comparison_with_progress(
        session_id,
        gstr1_workbook_base64=gstr1_workbook_base64,
        ewb_outward_workbook_base64=ewb_outward_workbook_base64,
    )
    from intelligence.intelligence_service import analyze_session
    from services.investigation_service import enrich_cases_from_intelligence, sync_cases_from_comparison

    sync_cases_from_comparison(session_id)
    analyze_session(session_id, force=True)
    enrich_cases_from_intelligence(session_id)
    session = get_session(session_id)
    if session:
        session = apply_result_to_session(session, result)
        upsert_session(session)
    return result


def apply_result_to_session(session: AuditSession, result: ComparisonResult) -> AuditSession:
    ensure_session_datasets(session)
    summary = result.summary
    session.discrepancies = DiscrepancySummary(
        missing_invoice=summary.missing_in_gstr1_count,
        duplicate_invoice=summary.duplicate_count,
        gstin_mismatch=summary.gstin_mismatch_count,
        invoice_mismatch=summary.missing_in_eway_count + summary.multiple_matches_count,
        value_mismatch=summary.value_mismatch_count,
        date_mismatch=summary.date_mismatch_count,
        risk_score=summary.overall_risk_score,
        total=(
            summary.missing_in_gstr1_count
            + summary.missing_in_eway_count
            + summary.gstin_mismatch_count
            + summary.value_mismatch_count
            + summary.date_mismatch_count
            + summary.duplicate_count
            + summary.multiple_matches_count
        ),
    )
    updated_pairs: List[ComparisonPairStatus] = []
    for pair in session.comparison_status:
        if pair.id == result.comparison_id:
            updated_pairs.append(pair.model_copy(update={"status": "completed"}))
        else:
            updated_pairs.append(pair)
    if not updated_pairs:
        updated_pairs = [
            ComparisonPairStatus(
                id=result.comparison_id,
                label="GSTR-1 ↔ EWB OUTWARD",
                left_dataset="gstr1",
                right_dataset="ewb_outward",
                status="completed",
            )
        ]
    session.comparison_status = updated_pairs
    session.audit_status = "in_progress"
    return session


def get_comparison_summary(session_id: str) -> Optional[dict]:
    result = get_result(session_id)
    if not result:
        return None
    return result.summary.model_dump()


def get_comparison_details(
    session_id: str,
    result_type: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
) -> ComparisonDetailPage:
    result = get_result(session_id)
    if not result:
        return ComparisonDetailPage(result_type=result_type or "ALL", total=0, records=[], offset=offset, limit=limit)

    records = result.records
    if result_type and result_type != "ALL":
        try:
            rt = ComparisonResultType(result_type)
            records = [r for r in records if r.result_type == rt]
        except ValueError:
            records = [r for r in records if r.result_type.value == result_type.upper()]

    page = records[offset : offset + limit]
    return ComparisonDetailPage(
        result_type=result_type or "ALL",
        total=len(records),
        records=page,
        offset=offset,
        limit=limit,
    )


def get_risk(session_id: str) -> dict:
    result = get_result(session_id)
    if not result:
        return {"risk_level": "LOW", "overall_risk_score": 0}
    return {
        "risk_level": result.summary.risk_level.value,
        "overall_risk_score": result.summary.overall_risk_score,
    }


def get_observations(session_id: str) -> List[dict]:
    result = get_result(session_id)
    if not result:
        return []
    return [o.model_dump() for o in result.observations]


def get_full_comparison(session_id: str) -> dict:
    result = get_result(session_id)
    status = get_comparison_status(session_id)
    if not result:
        return {"session_id": session_id, "status": status, "summary": None}
    return {
        "session_id": session_id,
        "status": status,
        "comparison_id": result.comparison_id,
        "summary": result.summary.model_dump(),
        "completed_at": result.completed_at,
    }
