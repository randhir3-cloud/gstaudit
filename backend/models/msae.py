"""Multi-Source Audit Engine (MSAE) — platform orchestration models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

CorrelationKey = Literal[
    "invoice",
    "supplier_gstin",
    "recipient_gstin",
    "financial_year",
    "tax_period",
    "ewb_number",
    "document_number",
]

TimelineStage = Literal[
    "upload",
    "merge",
    "comparison",
    "investigation",
    "officer_action",
    "report",
    "msae_orchestration",
]


class PluginFinding(BaseModel):
    """Single discrepancy published by a comparison plugin."""

    finding_id: str
    comparison_id: str
    comparison_label: str = ""
    result_type: str
    invoice_number: str = ""
    normalized_invoice: str = ""
    supplier_gstin: str = ""
    recipient_gstin: str = ""
    invoice_date: str = ""
    invoice_value: float = 0.0
    taxable_value: float = 0.0
    source_period: str = ""
    ewb_number: str = ""
    document_number: str = ""
    difference_amount: float = 0.0
    risk_score: int = 0
    description: str = ""
    record_index: int = 0


class MasterAuditCase(BaseModel):
    """Consolidated investigation case spanning multiple plugin sources."""

    master_case_id: str
    case_number: str
    session_id: str
    correlation_key: CorrelationKey = "invoice"
    correlation_value: str = ""
    invoice_number: str = ""
    normalized_invoice: str = ""
    supplier_gstin: str = ""
    recipient_gstin: str = ""
    financial_year: str = ""
    tax_period: str = ""
    ewb_number: str = ""
    document_number: str = ""
    invoice_value: float = 0.0
    difference_amount: float = 0.0
    risk_score: int = 0
    priority: str = "Medium"
    priority_score: int = 0
    status: str = "Pending"
    source_count: int = 0
    comparison_ids: List[str] = Field(default_factory=list)
    result_types: List[str] = Field(default_factory=list)
    patterns: List[str] = Field(default_factory=list)
    child_findings: List[PluginFinding] = Field(default_factory=list)
    officer_remarks: str = ""
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


class EntityRiskScore(BaseModel):
    entity_type: str
    entity_id: str
    label: str = ""
    risk_score: int = 0
    issue_count: int = 0
    total_difference: float = 0.0


class AuditScores(BaseModel):
    dealer_risk_score: int = 0
    month_risk_scores: List[EntityRiskScore] = Field(default_factory=list)
    supplier_risk_scores: List[EntityRiskScore] = Field(default_factory=list)
    customer_risk_scores: List[EntityRiskScore] = Field(default_factory=list)
    officer_priority_score: int = 0
    audit_confidence: float = 0.0
    confidence_factors: List[str] = Field(default_factory=list)


class PatternHit(BaseModel):
    pattern_type: str
    description: str
    severity: str = "Medium"
    affected_count: int = 0
    entities: List[str] = Field(default_factory=list)
    source_plugins: List[str] = Field(default_factory=list)


class AuditTimelineEvent(BaseModel):
    stage: TimelineStage
    title: str
    description: str = ""
    timestamp: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MSAESummary(BaseModel):
    session_id: str
    master_case_count: int = 0
    cross_plugin_case_count: int = 0
    total_findings: int = 0
    high_risk_cases: int = 0
    sources_analyzed: List[str] = Field(default_factory=list)
    top_risks: List[str] = Field(default_factory=list)
    scores: AuditScores = Field(default_factory=AuditScores)
    generated_at: str = ""


class MSAEFullResponse(BaseModel):
    session_id: str
    summary: MSAESummary
    master_cases: List[MasterAuditCase] = Field(default_factory=list)
    patterns: List[PatternHit] = Field(default_factory=list)
    timeline: List[AuditTimelineEvent] = Field(default_factory=list)
    heatmaps: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    trend: List[Dict[str, Any]] = Field(default_factory=list)


class ConsolidatedAuditReport(BaseModel):
    session_id: str
    title: str = "Consolidated Audit Report"
    executive_summary: str = ""
    master_cases: List[MasterAuditCase] = Field(default_factory=list)
    scores: AuditScores = Field(default_factory=AuditScores)
    patterns: List[PatternHit] = Field(default_factory=list)
    timeline: List[AuditTimelineEvent] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    generated_at: str = ""
