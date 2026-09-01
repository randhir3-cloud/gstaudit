"""Audit Case Management API routes."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from models.case_management import (
    CaseAssignmentRequest,
    CommentCreateRequest,
    DealerResponseRequest,
    NoticeCreateRequest,
    StatusTransitionRequest,
)
from services.case_management_service import (
    add_comment,
    approve_case,
    assign_case,
    build_case_report,
    create_notice,
    get_audit_case,
    get_officer_tasks,
    get_supervisor_dashboard,
    issue_notice,
    list_audit_cases,
    record_dealer_response,
    send_notice_reminder,
    sync_cases_from_msae,
    transition_case,
    upload_document,
)
from services.case_management_store import get_case_store
from services.workflow_engine import allowed_transitions

router = APIRouter(prefix="/api/audit-cases", tags=["audit-cases"])

UPLOAD_ROOT = Path(os.environ.get("GAIS_CASE_UPLOAD_DIR", "uploads/cases"))


@router.post("/dev/seed-demo")
async def seed_demo_cases(session_id: str = Query(...)):
    """Seed comparison + MSAE + audit cases for E2E (requires GAIS_ALLOW_DEMO_SEED=true)."""
    import os
    if os.getenv("GAIS_ALLOW_DEMO_SEED", "").lower() not in ("1", "true", "yes"):
        raise HTTPException(status_code=403, detail="Demo seed disabled")
    from services.comparison_store import save_result
    from services.msae_service import orchestrate_session
    from services.case_management_service import sync_cases_from_msae
    from tests.msae_fixtures import build_gstr1_result, build_gstr2a_result

    save_result(build_gstr1_result(session_id))
    save_result(build_gstr2a_result(session_id))
    orchestrate_session(session_id, force=True)
    cases = sync_cases_from_msae(session_id)
    get_case_store().clear_session(session_id)
    cases = sync_cases_from_msae(session_id)
    return {"session_id": session_id, "cases": len(cases)}


@router.post("/reset")
async def reset_cases(session_id: str = Query(...)):
    """Clear workflow state and re-sync draft cases from MSAE."""
    from services.case_management_store import get_case_store
    get_case_store().clear_session(session_id)
    cases = sync_cases_from_msae(session_id)
    return {"session_id": session_id, "cases": len(cases)}


@router.get("")
async def list_cases(
    session_id: str = Query(...),
    status: Optional[str] = None,
    officer: Optional[str] = None,
    high_risk_only: bool = False,
):
    cases = list_audit_cases(session_id, status=status, officer=officer, high_risk_only=high_risk_only)
    return {"session_id": session_id, "total": len(cases), "cases": [c.model_dump() for c in cases]}


@router.get("/tasks")
async def officer_tasks(session_id: str = Query(...), officer: str = Query("")):
    return get_officer_tasks(session_id, officer).model_dump()


@router.get("/supervisor")
async def supervisor_dashboard(session_id: str = Query(...)):
    return get_supervisor_dashboard(session_id).model_dump()


@router.get("/{audit_case_id}")
async def case_detail(session_id: str = Query(...), audit_case_id: str = ""):
    detail = get_audit_case(session_id, audit_case_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Audit case not found")
    return detail.model_dump()


@router.get("/{audit_case_id}/transitions")
async def case_transitions(session_id: str = Query(...), audit_case_id: str = ""):
    detail = get_audit_case(session_id, audit_case_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Audit case not found")
    return {
        "current_status": detail.workflow_status,
        "allowed_transitions": allowed_transitions(detail.workflow_status),
    }


@router.post("/{audit_case_id}/assign")
async def assign(audit_case_id: str, body: CaseAssignmentRequest):
    try:
        case = assign_case(audit_case_id, body)
        return case.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{audit_case_id}/transition")
async def transition(audit_case_id: str, body: StatusTransitionRequest):
    try:
        case = transition_case(audit_case_id, body)
        return case.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{audit_case_id}/approve")
async def approve(
    audit_case_id: str,
    session_id: str = Query(...),
    supervisor: str = Query("supervisor"),
    remarks: str = Query(""),
):
    try:
        case = approve_case(audit_case_id, session_id, supervisor, remarks)
        return case.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{audit_case_id}/notices")
async def create_case_notice(audit_case_id: str, body: NoticeCreateRequest):
    try:
        notice = create_notice(audit_case_id, body)
        return notice.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{audit_case_id}/notices/{notice_id}/issue")
async def issue_case_notice(
    audit_case_id: str,
    notice_id: str,
    session_id: str = Query(...),
    actor: str = Query("officer"),
):
    try:
        notice = issue_notice(audit_case_id, notice_id, session_id, actor)
        return notice.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{audit_case_id}/notices/{notice_id}/reminder")
async def remind_notice(
    audit_case_id: str,
    notice_id: str,
    session_id: str = Query(...),
    actor: str = Query("officer"),
):
    try:
        notice = send_notice_reminder(audit_case_id, notice_id, session_id, actor)
        return notice.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{audit_case_id}/comments")
async def post_comment(audit_case_id: str, body: CommentCreateRequest):
    try:
        comment = add_comment(audit_case_id, body)
        return comment.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{audit_case_id}/dealer-response")
async def post_dealer_response(audit_case_id: str, body: DealerResponseRequest):
    try:
        response = record_dealer_response(audit_case_id, body)
        return response.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{audit_case_id}/documents")
async def post_document(
    audit_case_id: str,
    session_id: str = Form(...),
    category: str = Form("other"),
    uploaded_by: str = Form("officer"),
    description: str = Form(""),
    file: UploadFile = File(...),
):
    try:
        UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
        dest_dir = UPLOAD_ROOT / session_id / audit_case_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        dest_path = dest_dir / file.filename
        dest_path.write_bytes(content)
        doc = upload_document(
            audit_case_id,
            session_id,
            category=category,
            filename=file.filename or "document",
            content_type=file.content_type or "application/octet-stream",
            file_size=len(content),
            uploaded_by=uploaded_by,
            description=description,
            storage_path=str(dest_path),
        )
        return doc.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{audit_case_id}/report")
async def case_report(session_id: str = Query(...), audit_case_id: str = ""):
    try:
        return build_case_report(session_id, audit_case_id).model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
