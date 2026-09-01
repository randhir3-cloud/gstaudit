"""Job executors — run background work outside HTTP handlers."""

from __future__ import annotations

import base64
import io
import traceback
from typing import Any, Dict

from models.job import BackgroundJob, JobCreateRequest, JobType
from services.job_service import (
    JobCancelledError,
    make_progress_callback,
    mark_completed,
    mark_failed,
    update_progress,
)
from services.comparison_service import (
    apply_result_to_session,
)
from plugins.sdk.loader import ensure_plugins_loaded
from plugins.sdk.registry import plugin_registry
from services.audit_session_store import get_session, upsert_session
from services.comparison_store import set_comparison_status


def execute_job(job: BackgroundJob) -> None:
    handlers = {
        JobType.COMPARISON: _run_comparison_job,
        JobType.INTELLIGENCE: _run_intelligence_job,
        JobType.REPORT: _run_report_job,
        JobType.MERGE: _run_merge_job,
        JobType.IMPORT: _run_import_job,
    }
    handler = handlers.get(job.job_type)
    if not handler:
        raise ValueError(f"Unsupported job type: {job.job_type}")
    handler(job)


def _run_comparison_job(job: BackgroundJob) -> None:
    from services.job_service import get_job

    ensure_plugins_loaded()
    payload = job.payload
    session_id = job.session_id
    comparison_id = payload.get("comparison_id", "gstr1_ewb_outward")
    runner = plugin_registry.get_comparison_runner(comparison_id)
    if not runner:
        raise ValueError(f"No plugin registered comparison runner: {comparison_id}")

    progress = make_progress_callback(job.job_id)
    checkpoint = job.checkpoint or {}

    set_comparison_status(session_id, "running")
    update_progress(job.job_id, percent=5, stage="Loading workbooks", rows_processed=0, rows_total=0)

    result = runner(
        session_id,
        gstr1_workbook_base64=payload.get("gstr1_workbook_base64", ""),
        ewb_outward_workbook_base64=payload.get("ewb_outward_workbook_base64", ""),
        progress_callback=progress,
        checkpoint=checkpoint,
        job_id=job.job_id,
    )

    update_progress(job.job_id, percent=95, stage="Finalizing session", rows_processed=result.summary.matched_count, rows_total=result.summary.total_gstr1_records + result.summary.total_eway_records)
    session = get_session(session_id)
    if session:
        session = apply_result_to_session(session, result)
        upsert_session(session)

    fresh = get_job(job.job_id) or job
    mark_completed(fresh, result_ref={
        "session_id": session_id,
        "comparison_id": result.comparison_id,
        "status": result.status,
        "summary": result.summary.model_dump(),
    })

    from services.investigation_service import sync_cases_from_comparison
    from intelligence.intelligence_service import enqueue_intelligence_analysis

    sync_cases_from_comparison(session_id)
    enqueue_intelligence_analysis(session_id)

    from services.msae_service import enqueue_msae_orchestration
    enqueue_msae_orchestration(session_id)


def _run_intelligence_job(job: BackgroundJob) -> None:
    from intelligence.intelligence_service import analyze_session
    from services.investigation_service import enrich_cases_from_intelligence

    progress = make_progress_callback(job.job_id)
    update_progress(job.job_id, percent=10, stage="Analyzing patterns")
    data = analyze_session(job.session_id, force=True)
    update_progress(job.job_id, percent=80, stage="Enriching investigation cases")
    enrich_cases_from_intelligence(job.session_id)
    update_progress(job.job_id, percent=90, stage="Building intelligence summary")
    mark_completed(job, result_ref={"session_id": job.session_id, "cards": data.summary.cards.model_dump()})


def _run_report_job(job: BackgroundJob) -> None:
    from services.audit_report_service import build_full_docx_report, build_full_excel_report, build_full_pdf_report, report_filename
    from services.investigation_service import export_cases
    from repositories.factory import get_repositories

    progress = make_progress_callback(job.job_id)
    session = get_session(job.session_id)
    if not session:
        raise ValueError("Session not found")

    fmt = job.payload.get("format", "excel")
    case_ids = job.payload.get("case_ids")
    high_risk_only = job.payload.get("high_risk_only", False)

    update_progress(job.job_id, percent=15, stage="Collecting cases")
    cases = export_cases(job.session_id, case_ids=case_ids, high_risk_only=high_risk_only)

    update_progress(job.job_id, percent=40, stage=f"Generating {fmt.upper()} report")
    if fmt == "pdf":
        buffer = build_full_pdf_report(session, cases)
        media = "pdf"
    elif fmt == "docx":
        buffer = build_full_docx_report(session, cases)
        media = "docx"
    else:
        buffer = build_full_excel_report(session, cases)
        media = "xlsx"

    content = buffer.getvalue()
    update_progress(job.job_id, percent=85, stage="Saving report")
    report_id = get_repositories().audit_report.create(job.session_id, media, content, {"format": fmt, "case_count": len(cases)})

    mark_completed(job, result_ref={
        "report_id": report_id,
        "format": fmt,
        "filename": report_filename(session.dealer, media if media != "xlsx" else "xlsx"),
        "file_size": len(content),
    })


def _run_merge_job(job: BackgroundJob) -> None:
    from merger import merge_gstr1_files, merge_gstr2a_files
    from services.comparison_store import cache_workbook

    progress = make_progress_callback(job.job_id)
    merge_type = job.payload.get("merge_type", "gstr1")
    files_b64: Dict[str, str] = job.payload.get("files", {})

    update_progress(job.job_id, percent=10, stage="Reading source files")
    file_data = [(name, base64.b64decode(data)) for name, data in files_b64.items()]

    if merge_type == "gstr2a":
        output_buffer, auto_name, _, dealer, workbook_id = merge_gstr2a_files(file_data)
        dataset_key = "gstr2a"
    else:
        output_buffer, auto_name, _, dealer, workbook_id = merge_gstr1_files(file_data)
        dataset_key = "gstr1"

    update_progress(job.job_id, percent=80, stage="Caching merged workbook")
    workbook_bytes = output_buffer.getvalue()
    cache_workbook(job.session_id, dataset_key, workbook_bytes)

    mark_completed(job, result_ref={
        "dataset_key": dataset_key,
        "filename": auto_name,
        "workbook_id": workbook_id,
        "dealer": dealer.model_dump(),
    })


def _run_import_job(job: BackgroundJob) -> None:
    from services.comparison_store import cache_workbook

    progress = make_progress_callback(job.job_id)
    dataset_key = job.payload.get("dataset_key", "gstr1")
    workbook_b64 = job.payload.get("workbook_base64", "")
    if not workbook_b64:
        raise ValueError("workbook_base64 required")

    update_progress(job.job_id, percent=20, stage="Importing workbook")
    data = base64.b64decode(workbook_b64)
    cache_workbook(job.session_id, dataset_key, data)
    mark_completed(job, result_ref={"dataset_key": dataset_key, "bytes": len(data)})


def safe_execute(job: BackgroundJob) -> None:
    try:
        execute_job(job)
    except JobCancelledError:
        from services.job_service import cancel_job
        cancel_job(job.job_id)
    except Exception as exc:
        mark_failed(job, str(exc))
        traceback.print_exc()
