"""Investigation case models for GAIS Audit Workbench."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

CaseStatus = Literal[
    "Pending",
    "Verified",
    "Accepted",
    "Rejected",
    "Needs Clarification",
    "Additional Documents Required",
]
CasePriority = Literal["Low", "Medium", "High", "Critical"]


class CaseAttachment(BaseModel):
    """Text-based attachment metadata — file upload reserved for future phase."""

    notes: str = ""
    reference_number: str = ""
    document_reference: str = ""
    book_page: str = ""
    supporting_evidence: str = ""


class InvestigationCase(BaseModel):
    case_id: str
    case_number: str
    session_id: str
    result_type: str
    invoice_number: str = ""
    normalized_invoice: str = ""
    supplier_gstin: str = ""
    recipient_gstin: str = ""
    invoice_date: str = ""
    invoice_value: float = 0.0
    taxable_value: float = 0.0
    comparison_result: str = ""
    risk_score: int = 0
    possible_reason: str = ""
    suggested_verification: str = ""
    source_period: str = ""
    ewb_number: str = ""
    difference_amount: float = 0.0
    status: CaseStatus = "Pending"
    priority: CasePriority = "Medium"
    priority_score: int = 0
    priority_reason: str = ""
    patterns: List[str] = Field(default_factory=list)
    recommended_documents: List[str] = Field(default_factory=list)
    possible_causes: List[str] = Field(default_factory=list)
    suggested_verifications: List[str] = Field(default_factory=list)
    gst_provisions: List[str] = Field(default_factory=list)
    related_case_ids: List[str] = Field(default_factory=list)
    assigned_officer: str = ""
    officer_remarks: str = ""
    attachments: CaseAttachment = Field(default_factory=CaseAttachment)
    comparison_type: str = "gstr1_ewb_outward"
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


class CaseTrackingSummary(BaseModel):
    total: int = 0
    open: int = 0
    closed: int = 0
    pending: int = 0
    verified: int = 0
    accepted: int = 0
    rejected: int = 0
    high_risk: int = 0


class InvestigationListResponse(BaseModel):
    session_id: str
    summary: CaseTrackingSummary
    cases: List[InvestigationCase] = Field(default_factory=list)
    categories: dict = Field(default_factory=dict)


class CaseUpdateRequest(BaseModel):
    session_id: str
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    assigned_officer: Optional[str] = None
    officer_remarks: Optional[str] = None
    attachments: Optional[CaseAttachment] = None


class BulkCaseUpdateRequest(BaseModel):
    session_id: str
    case_ids: List[str]
    status: Optional[CaseStatus] = None
    officer_remarks: Optional[str] = None


class InvestigationFilterParams(BaseModel):
    session_id: str
    category: Optional[str] = None
    month: Optional[str] = None
    gstin: Optional[str] = None
    risk_min: Optional[int] = None
    status: Optional[str] = None
    comparison_type: Optional[str] = None
    search: Optional[str] = None
    high_risk_only: bool = False
    offset: int = 0
    limit: int = 50
