import io
import os
from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional

from services.eway_merge_service import (
    merge_eway_workflow,
    merge_eway_bills_legacy as merge_eway_bills,
)
from services.eway_errors import EwayValidationError
from models.dealer_metadata import DealerMetadata, WorkbookMetadataResponse
from models.eway_classification import EwayClassifyResponse, EwayValidateResponse
from services.dealer_metadata_service import extract_from_files
from services.dealer_validation import DealerValidationError, validate_dealer_consistency
from merger import find_missing_months, merge_gstr2a_files
from models.audit_session import AuditSession, DashboardResponse
from services.audit_session_store import get_session, upsert_session
from services.dashboard_service import build_dashboard, build_month_coverage_map, compute_readiness
from services.comparison_service import (
    get_comparison_details,
    get_comparison_summary,
    get_full_comparison,
    get_observations,
    get_risk,
)
from comparison.models import WorkbookCacheRequest
from services.comparison_store import cache_workbook
from services.eway_classification_service import classify_eway_files, validate_eway_batch
from services.report_export import (
    build_excel_audit_report,
    build_pdf_audit_report,
    safe_report_filename,
)
from models.investigation import BulkCaseUpdateRequest, CaseUpdateRequest, InvestigationFilterParams
from services.investigation_service import (
    bulk_update_cases,
    export_cases,
    get_case_detail,
    get_investigation,
    update_case,
)
from services.audit_report_service import (
    build_full_docx_report,
    build_full_excel_report,
    build_full_pdf_report,
    build_report_preview,
    report_filename,
)
from intelligence.intelligence_service import enqueue_intelligence_analysis, get_session_intelligence
from contextlib import asynccontextmanager

from config.settings import get_settings
from jobs.broadcaster import job_broadcaster
from jobs.worker import start_worker, stop_worker
from models.job import JobCreateRequest, JobType
from services.job_service import cancel_job, create_job, get_job, list_jobs, retry_job
from fastapi import WebSocket, WebSocketDisconnect
from auth.middleware import SecurityMiddleware
from auth.audit_middleware import AuditLoggingMiddleware
from routes.auth_routes import router as auth_router
from routes.admin_routes import router as admin_router
from routes.system_routes import router as system_router
from routes.plugin_routes import router as plugin_catalog_router
from routes.msae_routes import router as msae_router
from routes.case_management_routes import router as case_management_router
from plugins.sdk.loader import load_plugins, ensure_plugins_loaded
from services.auth_service import bootstrap_security
from app_state import mark_started, set_build_metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    mark_started()
    set_build_metadata(version=app.version, build_id=os.getenv("GAIS_BUILD_ID", "local"))
    job_broadcaster.set_loop(asyncio.get_running_loop())
    bootstrap_security()
    ensure_plugins_loaded(app=app)
    if get_settings().job_worker_embedded:
        start_worker()
    yield
    stop_worker()


app = FastAPI(title="Excel Merger API", version="1.3", lifespan=lifespan)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "Content-Disposition",
        "X-Suggested-Filename",
        "X-Workbook-Metadata",
    ],
)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(SecurityMiddleware)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(system_router)
app.include_router(plugin_catalog_router)
app.include_router(msae_router)
app.include_router(case_management_router)
load_plugins(app)


def _workbook_metadata_header(
    workbook_id: str,
    dealer: DealerMetadata,
    return_type: str,
    source_files: List[str],
    current_dataset: str = "",
) -> dict:
    payload = WorkbookMetadataResponse(
        workbook_id=workbook_id,
        dealer=dealer,
        return_type=return_type,
        source_files=source_files,
        current_dataset=current_dataset,
    )
    return {"X-Workbook-Metadata": payload.model_dump_json()}


async def _read_upload_files(files: List[UploadFile]) -> List[tuple[str, bytes]]:
    file_data = []
    for file in files:
        content = await file.read()
        file_data.append((file.filename, content))
    return file_data


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Excel Merger API"}


@app.post("/api/dealer/extract")
async def api_extract_dealer_metadata(
    files: List[UploadFile] = File(...),
    return_type: str = Query(..., pattern="^(gstr1|gstr2a)$"),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    try:
        file_data = await _read_upload_files(files)
        records = extract_from_files(file_data, return_type)
        dealer = validate_dealer_consistency(records)
        filenames = [name for name, _ in file_data]
        workbook_id = WorkbookMetadataResponse.build_workbook_id(
            return_type, dealer, filenames
        )
        return WorkbookMetadataResponse(
            workbook_id=workbook_id,
            dealer=dealer,
            return_type=return_type,
            source_files=filenames,
            current_dataset=f"{return_type.upper()} Upload ({len(filenames)} files)",
        )
    except DealerValidationError as exc:
        return JSONResponse(status_code=400, content=exc.to_dict())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/reports/excel")
async def api_export_excel_report(
    dealer_json: str = Form(...),
    current_dataset: str = Form(""),
    report_title: str = Form("GST Audit Report"),
):
    try:
        dealer = DealerMetadata.model_validate_json(dealer_json)
        buffer = build_excel_audit_report(
            dealer,
            current_dataset=current_dataset,
            report_title=report_title,
        )
        filename = safe_report_filename(dealer, "xlsx")
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reports/pdf")
async def api_export_pdf_report(
    dealer_json: str = Form(...),
    current_dataset: str = Form(""),
    report_title: str = Form("GST Audit Report"),
):
    try:
        dealer = DealerMetadata.model_validate_json(dealer_json)
        buffer = build_pdf_audit_report(
            dealer,
            current_dataset=current_dataset,
            report_title=report_title,
        )
        filename = safe_report_filename(dealer, "pdf")
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/eway/classify", response_model=EwayClassifyResponse)
async def api_eway_classify(
    ewb_files: List[UploadFile] = File(...),
    dealer_gstin: Optional[str] = Query(None),
    expected_direction: Optional[str] = Query(None, pattern="^(outward|inward)$"),
    gstr1_files: Optional[List[UploadFile]] = File(None),
    gstr2a_files: Optional[List[UploadFile]] = File(None),
):
    if not ewb_files:
        raise HTTPException(status_code=400, detail="No E-Way Bill files uploaded.")
    try:
        ewb_data = await _read_upload_files(ewb_files)
        gstr1_data = await _read_upload_files(gstr1_files) if gstr1_files else None
        gstr2a_data = await _read_upload_files(gstr2a_files) if gstr2a_files else None
        return classify_eway_files(
            ewb_data,
            user_gstin=dealer_gstin,
            gstr1_files=gstr1_data,
            gstr2a_files=gstr2a_data,
            expected_direction=expected_direction,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/eway/validate", response_model=EwayValidateResponse)
async def api_eway_validate(
    ewb_files: List[UploadFile] = File(...),
    expected_direction: str = Query(..., pattern="^(outward|inward)$"),
    dealer_gstin: Optional[str] = Query(None),
    gstr1_files: Optional[List[UploadFile]] = File(None),
    gstr2a_files: Optional[List[UploadFile]] = File(None),
):
    if not ewb_files:
        raise HTTPException(status_code=400, detail="No E-Way Bill files uploaded.")
    try:
        ewb_data = await _read_upload_files(ewb_files)
        gstr1_data = await _read_upload_files(gstr1_files) if gstr1_files else None
        gstr2a_data = await _read_upload_files(gstr2a_files) if gstr2a_files else None
        return validate_eway_batch(
            ewb_data,
            expected_direction,
            user_gstin=dealer_gstin,
            gstr1_files=gstr1_data,
            gstr2a_files=gstr2a_data,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/merge/eway/outward")
async def api_merge_eway_outward(
    files: List[UploadFile] = File(...),
    ignore_missing: bool = Query(False),
    dealer_gstin: Optional[str] = Query(None),
):
    return await _merge_eway_direction(files, "outward", ignore_missing, dealer_gstin)


@app.post("/api/merge/eway/inward")
async def api_merge_eway_inward(
    files: List[UploadFile] = File(...),
    ignore_missing: bool = Query(False),
    dealer_gstin: Optional[str] = Query(None),
):
    return await _merge_eway_direction(files, "inward", ignore_missing, dealer_gstin)


async def _merge_eway_direction(
    files: List[UploadFile],
    direction: str,
    ignore_missing: bool,
    dealer_gstin: Optional[str] = None,
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    try:
        file_data = await _read_upload_files(files)
        result = merge_eway_workflow(
            file_data,
            direction,
            ignore_missing=ignore_missing,
            dealer_gstin=dealer_gstin,
        )
        return result
    except EwayValidationError as exc:
        status = 400
        return JSONResponse(status_code=status, content=exc.to_dict())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/merge/eway")
async def api_merge_eway(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    try:
        file_data = await _read_upload_files(files)
        output_buffer = merge_eway_bills(file_data)

        headers = {
            "Content-Disposition": 'attachment; filename="eway_merged_output.xlsx"',
            "X-Suggested-Filename": "eway_merged_output.xlsx",
        }
        return StreamingResponse(
            output_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/merge/gstr2a")
async def api_merge_gstr2a(
    files: List[UploadFile] = File(...),
    ignore_missing: bool = Query(False),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    try:
        file_data = await _read_upload_files(files)

        if not ignore_missing:
            filenames = [f[0] for f in file_data]
            missing = find_missing_months(filenames)
            if missing:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "warning",
                        "error_type": "missing_months",
                        "missing": missing,
                        "message": "Missing months detected between selected files.",
                    },
                )

        output_buffer, auto_name, _, dealer, workbook_id = merge_gstr2a_files(file_data)
        filenames = [f[0] for f in file_data]

        headers = {
            "Content-Disposition": f'attachment; filename="{auto_name}"',
            "X-Suggested-Filename": auto_name,
            **_workbook_metadata_header(
                workbook_id,
                dealer,
                "gstr2a",
                filenames,
                current_dataset=auto_name,
            ),
        }
        return StreamingResponse(
            output_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )
    except DealerValidationError as exc:
        return JSONResponse(status_code=400, content=exc.to_dict())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/session/sync", response_model=DashboardResponse)
async def api_session_sync(session: AuditSession):
    """Persist audit session state from frontend after upload/merge events."""
    session.updated_at = AuditSession.now_iso()
    if not session.created_at:
        session.created_at = session.updated_at
    upsert_session(session)
    return build_dashboard(session)


@app.get("/api/dashboard", response_model=DashboardResponse)
async def api_dashboard(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    return build_dashboard(session)


@app.get("/api/dashboard/month-coverage")
async def api_dashboard_month_coverage(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    if not session:
        return {key: {} for key in ("gstr1", "gstr2a", "ewb_outward", "ewb_inward")}
    from services.dashboard_service import ensure_session_datasets

    ensure_session_datasets(session)
    coverage = build_month_coverage_map(session)
    return {k: v.model_dump() for k, v in coverage.items()}


@app.get("/api/dashboard/statistics")
async def api_dashboard_statistics(session_id: Optional[str] = Query(None)):
    dash = build_dashboard(get_session(session_id))
    return {
        "per_module": dash.statistics,
        "summary": dash.summary_statistics.model_dump(),
    }


@app.get("/api/dashboard/upload-history")
async def api_dashboard_upload_history(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    if not session:
        return {"history": []}
    return {"history": [h.model_dump() for h in session.upload_history]}


@app.get("/api/dashboard/discrepancies")
async def api_dashboard_discrepancies(session_id: Optional[str] = Query(None)):
    dash = build_dashboard(get_session(session_id))
    return dash.discrepancies.model_dump()


@app.get("/api/dashboard/readiness")
async def api_dashboard_readiness(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    if not session:
        return {"readiness": {}, "audit_readiness_percent": 0.0, "can_start_audit": False}
    from services.dashboard_service import ensure_session_datasets

    ensure_session_datasets(session)
    readiness = compute_readiness(session)
    dash = build_dashboard(session)
    return {
        "readiness": readiness.model_dump(),
        "audit_readiness_percent": readiness.overall,
        "can_start_audit": dash.can_start_audit,
        "audit_status": dash.audit_status,
    }


@app.post("/api/jobs", status_code=202)
async def api_create_job(body: JobCreateRequest):
    try:
        job = create_job(body)
        return JSONResponse(status_code=202, content=job.model_dump(mode="json"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/jobs")
async def api_list_jobs(session_id: Optional[str] = Query(None)):
    jobs = list_jobs(session_id=session_id)
    return {"jobs": [j.model_dump(mode="json") for j in jobs], "total": len(jobs)}


@app.get("/api/jobs/{job_id}")
async def api_get_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.model_dump(mode="json")


@app.post("/api/jobs/{job_id}/cancel")
async def api_cancel_job(job_id: str):
    try:
        return cancel_job(job_id).model_dump(mode="json")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/jobs/{job_id}/retry")
async def api_retry_job(job_id: str):
    try:
        return retry_job(job_id).model_dump(mode="json")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}/download")
async def api_download_job_result(job_id: str):
    from repositories.factory import get_repositories

    job = get_job(job_id)
    if not job or job.status.value != "completed":
        raise HTTPException(status_code=404, detail="Completed job not found")
    report_id = job.result_ref.get("report_id")
    if not report_id:
        raise HTTPException(status_code=404, detail="No downloadable result")
    report = get_repositories().audit_report.get_by_id(report_id)
    if not report or not report.get("content"):
        raise HTTPException(status_code=404, detail="Report content missing")
    fmt = report.get("format", "pdf")
    media = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }.get(fmt, "application/octet-stream")
    filename = job.result_ref.get("filename", f"report.{fmt}")
    return StreamingResponse(
        io.BytesIO(report["content"]),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.websocket("/ws/jobs/{session_id}")
async def ws_jobs(websocket: WebSocket, session_id: str):
    await job_broadcaster.connect(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        job_broadcaster.disconnect(session_id, websocket)


@app.post("/api/comparison/cache-workbook")
async def api_comparison_cache_workbook(body: WorkbookCacheRequest):
    import base64

    try:
        cache_workbook(body.session_id, body.dataset_key, base64.b64decode(body.workbook_base64))
        return {"cached": True, "dataset_key": body.dataset_key}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/comparison/{session_id}")
async def api_comparison_get(session_id: str):
    return get_full_comparison(session_id)


@app.get("/api/comparison/{session_id}/summary")
async def api_comparison_summary(session_id: str):
    summary = get_comparison_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return summary


@app.get("/api/comparison/{session_id}/details")
async def api_comparison_details(
    session_id: str,
    result_type: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    page = get_comparison_details(session_id, result_type=result_type, offset=offset, limit=limit)
    return page.model_dump()


@app.get("/api/comparison/{session_id}/risk")
async def api_comparison_risk(session_id: str):
    return get_risk(session_id)


@app.get("/api/comparison/{session_id}/observations")
async def api_comparison_observations(session_id: str):
    return {"observations": get_observations(session_id)}


@app.get("/api/investigation")
async def api_investigation_list(
    session_id: str = Query(...),
    category: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    gstin: Optional[str] = Query(None),
    risk_min: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    comparison_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    high_risk_only: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    params = InvestigationFilterParams(
        session_id=session_id,
        category=category,
        month=month,
        gstin=gstin,
        risk_min=risk_min,
        status=status,
        comparison_type=comparison_type,
        search=search,
        high_risk_only=high_risk_only,
        offset=offset,
        limit=limit,
    )
    return get_investigation(params).model_dump()


@app.get("/api/investigation/{case_id}")
async def api_investigation_case(case_id: str, session_id: str = Query(...)):
    case = get_case_detail(session_id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case.model_dump()


@app.patch("/api/investigation/{case_id}")
async def api_investigation_update(case_id: str, body: CaseUpdateRequest):
    try:
        return update_case(case_id, body).model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/investigation/bulk")
async def api_investigation_bulk(body: BulkCaseUpdateRequest):
    updated = bulk_update_cases(body)
    return {"updated": len(updated), "cases": [c.model_dump() for c in updated]}


@app.get("/api/intelligence")
async def api_intelligence(session_id: str = Query(...)):
    data = get_session_intelligence(session_id)
    return data.model_dump()


@app.post("/api/intelligence/analyze", status_code=202)
async def api_intelligence_analyze(session_id: str = Query(...)):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return JSONResponse(status_code=202, content=enqueue_intelligence_analysis(session_id))


@app.get("/api/intelligence/summary")
async def api_intelligence_summary(session_id: str = Query(...)):
    data = get_session_intelligence(session_id)
    return data.summary.model_dump()


@app.get("/api/intelligence/months")
async def api_intelligence_months(session_id: str = Query(...)):
    data = get_session_intelligence(session_id)
    return {"months": [m.model_dump() for m in data.months]}


@app.get("/api/intelligence/suppliers")
async def api_intelligence_suppliers(session_id: str = Query(...)):
    data = get_session_intelligence(session_id)
    return {"suppliers": [s.model_dump() for s in data.suppliers]}


@app.get("/api/intelligence/customers")
async def api_intelligence_customers(session_id: str = Query(...)):
    data = get_session_intelligence(session_id)
    return {"customers": [c.model_dump() for c in data.customers]}


@app.get("/api/intelligence/cases")
async def api_intelligence_cases(session_id: str = Query(...), limit: int = Query(50, ge=1, le=500)):
    data = get_session_intelligence(session_id)
    cases = data.cases[:limit]
    return {"cases": [c.model_dump() for c in cases], "total": len(data.cases)}


@app.get("/api/report/preview")
async def api_report_preview(session_id: str = Query(...)):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return build_report_preview(session)


@app.post("/api/report/generate", status_code=202)
async def api_report_generate(
    session_id: str = Query(...),
    format: str = Query("excel", pattern="^(excel|pdf|docx)$"),
    high_risk_only: bool = Query(False),
    case_ids: Optional[str] = Query(None, description="Comma-separated case IDs"),
):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    ids = [x.strip() for x in case_ids.split(",")] if case_ids else None
    job = create_job(
        JobCreateRequest(
            session_id=session_id,
            job_type=JobType.REPORT,
            title=f"Audit Report ({format.upper()})",
            payload={"format": format, "case_ids": ids, "high_risk_only": high_risk_only},
        )
    )
    return JSONResponse(status_code=202, content=job.model_dump(mode="json"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
