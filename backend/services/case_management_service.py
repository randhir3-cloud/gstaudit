"""Audit Case Management service — full government audit lifecycle."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from models.case_management import (
    AuditCase,
    AuditCaseDetail,
    AuditNotice,
    CaseAssignment,
    CaseAssignmentRequest,
    CaseComment,
    CaseDocument,
    CaseManagementReport,
    CaseTimelineEntry,
    CommentCreateRequest,
    DealerResponse,
    DealerResponseRequest,
    NoticeCreateRequest,
    OfficerTaskSummary,
    StatusTransitionRequest,
    SupervisorDashboard,
)
from models.msae import MasterAuditCase
from services.case_management_store import get_case_store
from services.msae_service import get_session_msae
from services.workflow_engine import validate_transition


def _uid(prefix: str = "") -> str:
    return hashlib.sha256(f"{prefix}:{uuid.uuid4()}".encode()).hexdigest()[:12]


def _notice_number(session_id: str) -> str:
    count = sum(1 for n in get_case_store().notices.values() if n.session_id == session_id)
    year = datetime.now(timezone.utc).year
    return f"SCN/{year}/{session_id[-6:]}/{count + 1:04d}"


def sync_cases_from_msae(session_id: str) -> List[AuditCase]:
    """Create Draft audit cases from MSAE master cases."""
    store = get_case_store()
    msae = get_session_msae(session_id)
    existing_master_ids = {
        c.master_case_id for c in store.cases.values()
        if c.session_id == session_id and c.master_case_id
    }
    created: List[AuditCase] = []
    for master in msae.master_cases:
        if master.master_case_id in existing_master_ids:
            continue
        case = AuditCase(
            audit_case_id=master.master_case_id,
            case_number=f"AC-{master.case_number.replace('MSAE-', '')}",
            session_id=session_id,
            master_case_id=master.master_case_id,
            invoice_number=master.invoice_number,
            normalized_invoice=master.normalized_invoice,
            supplier_gstin=master.supplier_gstin,
            recipient_gstin=master.recipient_gstin,
            financial_year=master.financial_year,
            tax_period=master.tax_period,
            risk_score=master.risk_score,
            workflow_status="Draft",
            priority=master.priority if master.priority in ("Low", "Medium", "High", "Critical") else "Medium",
            source_count=master.source_count,
            comparison_ids=master.comparison_ids,
            child_finding_count=len(master.child_findings),
            created_at=AuditCase.now_iso(),
            updated_at=AuditCase.now_iso(),
        )
        store.cases[case.audit_case_id] = case
        _append_timeline(
            case,
            event_type="system_event",
            title="Case created from MSAE",
            description=f"Master case {master.case_number} synced with {master.source_count} source(s)",
            actor="system",
            actor_role="system",
        )
        created.append(case)
    return created


def list_audit_cases(
    session_id: str,
    *,
    status: Optional[str] = None,
    officer: Optional[str] = None,
    high_risk_only: bool = False,
) -> List[AuditCase]:
    sync_cases_from_msae(session_id)
    cases = [c for c in get_case_store().cases.values() if c.session_id == session_id]
    if status:
        cases = [c for c in cases if c.workflow_status == status]
    if officer:
        cases = [c for c in cases if c.assigned_officer == officer]
    if high_risk_only:
        cases = [c for c in cases if c.risk_score >= 70]
    cases.sort(key=lambda c: (-c.risk_score, c.case_number))
    return cases


def get_audit_case(session_id: str, audit_case_id: str) -> Optional[AuditCaseDetail]:
    sync_cases_from_msae(session_id)
    store = get_case_store()
    case = store.cases.get(audit_case_id)
    if not case or case.session_id != session_id:
        return None
    return AuditCaseDetail(
        **case.model_dump(),
        assignment=store.assignments.get(audit_case_id),
        notices=[n for n in store.notices.values() if n.audit_case_id == audit_case_id],
        documents=[d for d in store.documents.values() if d.audit_case_id == audit_case_id],
        comments=[c for c in store.comments.values() if c.audit_case_id == audit_case_id],
        timeline=sorted(
            [t for t in store.timeline.values() if t.audit_case_id == audit_case_id],
            key=lambda t: t.timestamp,
        ),
        dealer_responses=[r for r in store.dealer_responses.values() if r.audit_case_id == audit_case_id],
        workflow_history=sorted(
            [h for h in store.workflow_history.values() if h.audit_case_id == audit_case_id],
            key=lambda h: h.timestamp,
        ),
    )


def assign_case(audit_case_id: str, body: CaseAssignmentRequest, assigned_by: str = "") -> AuditCase:
    store = get_case_store()
    case = store.cases.get(audit_case_id)
    if not case or case.session_id != body.session_id:
        raise ValueError("Case not found")

    assignment = CaseAssignment(
        assignment_id=_uid("asgn"),
        audit_case_id=audit_case_id,
        session_id=body.session_id,
        assigned_officer=body.assigned_officer,
        assigned_supervisor=body.assigned_supervisor,
        due_date=body.due_date,
        priority=body.priority or case.priority,
        circle=body.circle,
        ward=body.ward,
        office=body.office,
        department=body.department,
        assigned_at=AuditCase.now_iso(),
        assigned_by=assigned_by,
    )
    store.assignments[audit_case_id] = assignment

    case.assigned_officer = body.assigned_officer
    case.assigned_supervisor = body.assigned_supervisor
    case.due_date = body.due_date
    if body.priority:
        case.priority = body.priority
    case.circle = body.circle
    case.ward = body.ward
    case.office = body.office
    case.department = body.department
    case.updated_at = AuditCase.now_iso()

    if case.workflow_status == "Draft":
        _transition(case, "Assigned", assigned_by or body.assigned_officer, "Case assigned to officer")
    else:
        _append_timeline(
            case,
            event_type="assignment",
            title="Case reassigned",
            description=f"Assigned to {body.assigned_officer}",
            actor=assigned_by or body.assigned_officer,
            actor_role="officer",
        )
    store.cases[audit_case_id] = case
    return case


def transition_case(audit_case_id: str, body: StatusTransitionRequest) -> AuditCase:
    store = get_case_store()
    case = store.cases.get(audit_case_id)
    if not case or case.session_id != body.session_id:
        raise ValueError("Case not found")
    validate_transition(case.workflow_status, body.to_status)
    _transition(case, body.to_status, body.actor, body.reason)
    if body.to_status == "Closed":
        case.closed_at = AuditCase.now_iso()
    store.cases[audit_case_id] = case
    return case


def _transition(case: AuditCase, to_status: str, actor: str, reason: str) -> None:
    from_status = case.workflow_status
    validate_transition(from_status, to_status)
    store = get_case_store()
    entry = {
        "history_id": _uid("wh"),
        "audit_case_id": case.audit_case_id,
        "session_id": case.session_id,
        "from_status": from_status,
        "to_status": to_status,
        "changed_by": actor,
        "reason": reason,
        "timestamp": AuditCase.now_iso(),
    }
    from models.case_management import WorkflowHistoryEntry
    store.workflow_history[entry["history_id"]] = WorkflowHistoryEntry(**entry)
    case.workflow_status = to_status  # type: ignore[assignment]
    case.updated_at = AuditCase.now_iso()
    _append_timeline(
        case,
        event_type="status_change",
        title=f"Status: {from_status} → {to_status}",
        description=reason or f"Case moved to {to_status}",
        actor=actor,
        metadata={"from_status": from_status, "to_status": to_status},
    )


def _append_timeline(
    case: AuditCase,
    *,
    event_type: str,
    title: str,
    description: str = "",
    actor: str = "",
    actor_role: str = "",
    metadata: Optional[dict] = None,
    attachment_ids: Optional[List[str]] = None,
) -> CaseTimelineEntry:
    store = get_case_store()
    entry = CaseTimelineEntry(
        entry_id=_uid("tl"),
        audit_case_id=case.audit_case_id,
        session_id=case.session_id,
        event_type=event_type,  # type: ignore[arg-type]
        title=title,
        description=description,
        actor=actor,
        actor_role=actor_role,
        metadata=metadata or {},
        attachment_ids=attachment_ids or [],
        timestamp=AuditCase.now_iso(),
    )
    store.timeline[entry.entry_id] = entry
    return entry


def create_notice(audit_case_id: str, body: NoticeCreateRequest, actor: str = "") -> AuditNotice:
    store = get_case_store()
    case = store.cases.get(audit_case_id)
    if not case or case.session_id != body.session_id:
        raise ValueError("Case not found")

    notice = AuditNotice(
        notice_id=_uid("ntc"),
        audit_case_id=audit_case_id,
        session_id=body.session_id,
        notice_number=_notice_number(body.session_id),
        notice_date=body.notice_date or AuditCase.now_iso()[:10],
        reply_due_date=body.reply_due_date,
        notice_type=body.notice_type,
        notice_status="Draft",
        notice_content=body.notice_content,
        created_at=AuditCase.now_iso(),
        updated_at=AuditCase.now_iso(),
    )
    store.notices[notice.notice_id] = notice
    _append_timeline(
        case,
        event_type="notice_issued",
        title=f"Notice drafted: {notice.notice_number}",
        description=body.notice_content[:200],
        actor=actor,
        actor_role="officer",
        metadata={"notice_id": notice.notice_id},
    )
    return notice


def issue_notice(audit_case_id: str, notice_id: str, session_id: str, actor: str = "") -> AuditNotice:
    store = get_case_store()
    notice = store.notices.get(notice_id)
    case = store.cases.get(audit_case_id)
    if not notice or not case or notice.session_id != session_id:
        raise ValueError("Notice not found")
    notice.notice_status = "Issued"
    notice.updated_at = AuditCase.now_iso()
    if case.workflow_status in ("Under Investigation", "Assigned"):
        _transition(case, "Notice Issued", actor, f"Notice {notice.notice_number} issued")
    store.cases[audit_case_id] = case
    _append_timeline(
        case,
        event_type="notice_issued",
        title=f"Notice issued: {notice.notice_number}",
        description=f"{notice.notice_type} — reply due {notice.reply_due_date}",
        actor=actor,
        actor_role="officer",
        metadata={"notice_id": notice_id},
    )
    return notice


def send_notice_reminder(audit_case_id: str, notice_id: str, session_id: str, actor: str = "") -> AuditNotice:
    store = get_case_store()
    notice = store.notices.get(notice_id)
    case = store.cases.get(audit_case_id)
    if not notice or not case:
        raise ValueError("Notice not found")
    notice.reminder_sent = True
    notice.notice_status = "Reminder Sent"
    notice.updated_at = AuditCase.now_iso()
    _append_timeline(case, event_type="system_event", title="Notice reminder sent", actor=actor, actor_role="officer")
    return notice


def add_comment(audit_case_id: str, body: CommentCreateRequest) -> CaseComment:
    store = get_case_store()
    case = store.cases.get(audit_case_id)
    if not case or case.session_id != body.session_id:
        raise ValueError("Case not found")
    comment = CaseComment(
        comment_id=_uid("cmt"),
        audit_case_id=audit_case_id,
        session_id=body.session_id,
        author=body.author,
        author_role=body.author_role,
        comment_type=body.comment_type,
        body=body.body,
        created_at=AuditCase.now_iso(),
    )
    store.comments[comment.comment_id] = comment
    _append_timeline(
        case,
        event_type=body.comment_type,
        title=f"{body.comment_type.replace('_', ' ').title()}",
        description=body.body,
        actor=body.author,
        actor_role=body.author_role,
    )
    return comment


def record_dealer_response(audit_case_id: str, body: DealerResponseRequest, received_by: str = "") -> DealerResponse:
    store = get_case_store()
    case = store.cases.get(audit_case_id)
    if not case or case.session_id != body.session_id:
        raise ValueError("Case not found")
    response = DealerResponse(
        response_id=_uid("dr"),
        audit_case_id=audit_case_id,
        session_id=body.session_id,
        notice_id=body.notice_id,
        response_date=body.response_date or AuditCase.now_iso()[:10],
        response_summary=body.response_summary,
        document_ids=body.document_ids,
        received_by=received_by,
        created_at=AuditCase.now_iso(),
    )
    store.dealer_responses[response.response_id] = response
    if case.workflow_status == "Notice Issued":
        _transition(case, "Dealer Response Received", received_by, "Dealer response recorded")
    store.cases[audit_case_id] = case
    _append_timeline(
        case,
        event_type="dealer_reply",
        title="Dealer response received",
        description=body.response_summary[:200],
        actor=received_by,
        actor_role="officer",
    )
    return response


def upload_document(
    audit_case_id: str,
    session_id: str,
    *,
    category: str,
    filename: str,
    content_type: str,
    file_size: int,
    uploaded_by: str,
    description: str = "",
    storage_path: str = "",
) -> CaseDocument:
    store = get_case_store()
    case = store.cases.get(audit_case_id)
    if not case or case.session_id != session_id:
        raise ValueError("Case not found")
    doc = CaseDocument(
        document_id=_uid("doc"),
        audit_case_id=audit_case_id,
        session_id=session_id,
        category=category,  # type: ignore[arg-type]
        filename=filename,
        content_type=content_type,
        file_size=file_size,
        storage_path=storage_path or f"cases/{session_id}/{audit_case_id}/{filename}",
        uploaded_by=uploaded_by,
        description=description,
        uploaded_at=AuditCase.now_iso(),
    )
    store.documents[doc.document_id] = doc
    _append_timeline(
        case,
        event_type="document_upload",
        title=f"Document uploaded: {filename}",
        description=f"Category: {category}",
        actor=uploaded_by,
        attachment_ids=[doc.document_id],
    )
    return doc


def get_officer_tasks(session_id: str, officer: str = "") -> OfficerTaskSummary:
    cases = list_audit_cases(session_id, officer=officer or None)
    now = datetime.now(timezone.utc)
    today_str = now.date().isoformat()
    week_end = (now + timedelta(days=7)).date().isoformat()

    today, overdue, due_week, high_risk = [], [], [], []
    for case in cases:
        if case.workflow_status in ("Closed", "Archived"):
            continue
        if case.risk_score >= 70:
            high_risk.append(case)
        if case.due_date:
            if case.due_date < today_str:
                overdue.append(case)
            elif case.due_date == today_str:
                today.append(case)
            elif case.due_date <= week_end:
                due_week.append(case)

    return OfficerTaskSummary(
        today=today,
        overdue=overdue,
        due_this_week=due_week,
        high_risk=high_risk,
        counts={
            "today": len(today),
            "overdue": len(overdue),
            "due_this_week": len(due_week),
            "high_risk": len(high_risk),
            "total_open": sum(1 for c in cases if c.workflow_status not in ("Closed", "Archived")),
        },
    )


def get_supervisor_dashboard(session_id: str) -> SupervisorDashboard:
    cases = list_audit_cases(session_id)
    store = get_case_store()
    pending = [c for c in cases if c.workflow_status == "Supervisor Review"]
    workload: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    risk_dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    closure_days: list[float] = []
    for case in cases:
        status_counts[case.workflow_status] = status_counts.get(case.workflow_status, 0) + 1
        if case.assigned_officer:
            workload[case.assigned_officer] = workload.get(case.assigned_officer, 0) + 1
        if case.risk_score >= 90:
            risk_dist["critical"] += 1
        elif case.risk_score >= 70:
            risk_dist["high"] += 1
        elif case.risk_score >= 40:
            risk_dist["medium"] += 1
        else:
            risk_dist["low"] += 1
        if case.closed_at and case.created_at:
            try:
                created = datetime.fromisoformat(case.created_at.replace("Z", "+00:00"))
                closed = datetime.fromisoformat(case.closed_at.replace("Z", "+00:00"))
                closure_days.append((closed - created).total_seconds() / 86400)
            except ValueError:
                pass

    return SupervisorDashboard(
        pending_approvals=pending,
        officer_workload=[{"officer": k, "case_count": v} for k, v in sorted(workload.items(), key=lambda x: -x[1])],
        cases_by_status=status_counts,
        average_closure_days=sum(closure_days) / len(closure_days) if closure_days else 0.0,
        risk_distribution=risk_dist,
        total_open=sum(1 for c in cases if c.workflow_status not in ("Closed", "Archived")),
    )


def build_case_report(session_id: str, audit_case_id: str) -> CaseManagementReport:
    detail = get_audit_case(session_id, audit_case_id)
    if not detail:
        raise ValueError("Case not found")
    summary = (
        f"Investigation of invoice {detail.invoice_number} (GSTIN {detail.supplier_gstin}). "
        f"Risk score {detail.risk_score}. Status: {detail.workflow_status}. "
        f"{detail.child_finding_count} plugin finding(s) from {detail.source_count} source(s)."
    )
    return CaseManagementReport(
        audit_case_id=audit_case_id,
        session_id=session_id,
        title="Final Audit Order",
        investigation_summary=summary,
        timeline=detail.timeline,
        evidence_index=detail.documents,
        notices=detail.notices,
        workflow_history=detail.workflow_history,
        generated_at=AuditCase.now_iso(),
    )


def approve_case(audit_case_id: str, session_id: str, supervisor: str, remarks: str = "") -> AuditCase:
    store = get_case_store()
    case = store.cases.get(audit_case_id)
    if not case or case.session_id != session_id:
        raise ValueError("Case not found")
    if case.workflow_status != "Supervisor Review":
        raise ValueError("Case is not pending supervisor review")
    add_comment(
        audit_case_id,
        CommentCreateRequest(
            session_id=session_id,
            body=remarks or "Approved by supervisor",
            comment_type="supervisor_remark",
            author=supervisor,
            author_role="supervisor",
        ),
    )
    _transition(case, "Approved", supervisor, remarks or "Supervisor approved")
    store.cases[audit_case_id] = case
    return case
