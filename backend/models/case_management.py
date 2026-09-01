"""Audit Case Management — government GST audit lifecycle models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

CaseWorkflowStatus = Literal[
    "Draft",
    "Assigned",
    "Under Investigation",
    "Notice Issued",
    "Dealer Response Received",
    "Verification Pending",
    "Supervisor Review",
    "Approved",
    "Closed",
    "Archived",
]

NoticeType = Literal[
    "Show Cause Notice",
    "Demand Notice",
    "Reminder Notice",
    "Information Request",
    "Final Audit Order",
]

NoticeStatus = Literal[
    "Draft",
    "Issued",
    "Reminder Sent",
    "Reply Received",
    "Closed",
]

DocumentCategory = Literal[
    "invoice",
    "purchase_register",
    "sales_register",
    "bank_statement",
    "ewb_pdf",
    "gst_return",
    "officer_note",
    "dealer_reply",
    "notice_pdf",
    "other",
]

TimelineEventType = Literal[
    "status_change",
    "assignment",
    "officer_remark",
    "dealer_reply",
    "supervisor_remark",
    "notice_issued",
    "document_upload",
    "system_event",
]

CasePriority = Literal["Low", "Medium", "High", "Critical"]


class CaseAssignment(BaseModel):
    assignment_id: str
    audit_case_id: str
    session_id: str
    assigned_officer: str = ""
    assigned_supervisor: str = ""
    due_date: str = ""
    priority: CasePriority = "Medium"
    circle: str = ""
    ward: str = ""
    office: str = ""
    department: str = ""
    assigned_at: str = ""
    assigned_by: str = ""


class AuditNotice(BaseModel):
    notice_id: str
    audit_case_id: str
    session_id: str
    notice_number: str = ""
    notice_date: str = ""
    reply_due_date: str = ""
    notice_type: NoticeType = "Show Cause Notice"
    reminder_sent: bool = False
    notice_status: NoticeStatus = "Draft"
    notice_pdf_path: str = ""
    notice_content: str = ""
    created_at: str = ""
    updated_at: str = ""


class CaseDocument(BaseModel):
    document_id: str
    audit_case_id: str
    session_id: str
    category: DocumentCategory = "other"
    filename: str = ""
    content_type: str = "application/octet-stream"
    file_size: int = 0
    storage_path: str = ""
    uploaded_by: str = ""
    description: str = ""
    uploaded_at: str = ""


class CaseComment(BaseModel):
    comment_id: str
    audit_case_id: str
    session_id: str
    author: str = ""
    author_role: str = ""
    comment_type: TimelineEventType = "officer_remark"
    body: str = ""
    created_at: str = ""


class CaseTimelineEntry(BaseModel):
    entry_id: str
    audit_case_id: str
    session_id: str
    event_type: TimelineEventType
    title: str
    description: str = ""
    actor: str = ""
    actor_role: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    attachment_ids: List[str] = Field(default_factory=list)
    timestamp: str = ""


class DealerResponse(BaseModel):
    response_id: str
    audit_case_id: str
    session_id: str
    notice_id: str = ""
    response_date: str = ""
    response_summary: str = ""
    document_ids: List[str] = Field(default_factory=list)
    received_by: str = ""
    created_at: str = ""


class WorkflowHistoryEntry(BaseModel):
    history_id: str
    audit_case_id: str
    session_id: str
    from_status: str
    to_status: str
    changed_by: str = ""
    reason: str = ""
    timestamp: str = ""


class AuditCase(BaseModel):
    audit_case_id: str
    case_number: str
    session_id: str
    master_case_id: str = ""
    invoice_number: str = ""
    normalized_invoice: str = ""
    supplier_gstin: str = ""
    recipient_gstin: str = ""
    financial_year: str = ""
    tax_period: str = ""
    risk_score: int = 0
    workflow_status: CaseWorkflowStatus = "Draft"
    priority: CasePriority = "Medium"
    assigned_officer: str = ""
    assigned_supervisor: str = ""
    due_date: str = ""
    circle: str = ""
    ward: str = ""
    office: str = ""
    department: str = ""
    source_count: int = 0
    comparison_ids: List[str] = Field(default_factory=list)
    child_finding_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    closed_at: str = ""

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


class CaseAssignmentRequest(BaseModel):
    session_id: str
    assigned_officer: str
    assigned_supervisor: str = ""
    due_date: str = ""
    priority: Optional[CasePriority] = None
    circle: str = ""
    ward: str = ""
    office: str = ""
    department: str = ""


class StatusTransitionRequest(BaseModel):
    session_id: str
    to_status: CaseWorkflowStatus
    reason: str = ""
    actor: str = ""


class NoticeCreateRequest(BaseModel):
    session_id: str
    notice_type: NoticeType = "Show Cause Notice"
    notice_date: str = ""
    reply_due_date: str = ""
    notice_content: str = ""


class CommentCreateRequest(BaseModel):
    session_id: str
    body: str
    comment_type: TimelineEventType = "officer_remark"
    author: str = ""
    author_role: str = ""


class DealerResponseRequest(BaseModel):
    session_id: str
    notice_id: str = ""
    response_date: str = ""
    response_summary: str = ""
    document_ids: List[str] = Field(default_factory=list)


class AuditCaseDetail(AuditCase):
    assignment: Optional[CaseAssignment] = None
    notices: List[AuditNotice] = Field(default_factory=list)
    documents: List[CaseDocument] = Field(default_factory=list)
    comments: List[CaseComment] = Field(default_factory=list)
    timeline: List[CaseTimelineEntry] = Field(default_factory=list)
    dealer_responses: List[DealerResponse] = Field(default_factory=list)
    workflow_history: List[WorkflowHistoryEntry] = Field(default_factory=list)


class OfficerTaskSummary(BaseModel):
    today: List[AuditCase] = Field(default_factory=list)
    overdue: List[AuditCase] = Field(default_factory=list)
    due_this_week: List[AuditCase] = Field(default_factory=list)
    high_risk: List[AuditCase] = Field(default_factory=list)
    counts: Dict[str, int] = Field(default_factory=dict)


class SupervisorDashboard(BaseModel):
    pending_approvals: List[AuditCase] = Field(default_factory=list)
    officer_workload: List[Dict[str, Any]] = Field(default_factory=list)
    cases_by_status: Dict[str, int] = Field(default_factory=dict)
    average_closure_days: float = 0.0
    risk_distribution: Dict[str, int] = Field(default_factory=dict)
    total_open: int = 0


class CaseManagementReport(BaseModel):
    audit_case_id: str
    session_id: str
    title: str = "Final Audit Order"
    investigation_summary: str = ""
    timeline: List[CaseTimelineEntry] = Field(default_factory=list)
    evidence_index: List[CaseDocument] = Field(default_factory=list)
    notices: List[AuditNotice] = Field(default_factory=list)
    workflow_history: List[WorkflowHistoryEntry] = Field(default_factory=list)
    generated_at: str = ""
