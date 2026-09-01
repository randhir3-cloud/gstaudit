"""Pydantic models for audit intelligence outputs."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

PriorityLevel = Literal["Critical", "High", "Medium", "Low"]


class CasePriorityResult(BaseModel):
    priority: PriorityLevel = "Medium"
    score: int = 0
    reason: str = ""


class DocumentRecommendation(BaseModel):
    discrepancy_type: str = ""
    documents: List[str] = Field(default_factory=list)


class PatternFinding(BaseModel):
    pattern_type: str
    description: str
    severity: PriorityLevel = "Medium"
    affected_count: int = 0
    entities: List[str] = Field(default_factory=list)


class HeatmapCell(BaseModel):
    label: str
    count: int = 0
    risk_score: int = 0
    risk_percent: float = 0.0


class MonthAnalysis(BaseModel):
    month: str
    invoices: int = 0
    matched_count: int = 0
    mismatch_count: int = 0
    matched_percent: float = 0.0
    mismatch_percent: float = 0.0
    risk_percent: float = 0.0
    top_suppliers: List[str] = Field(default_factory=list)
    top_customers: List[str] = Field(default_factory=list)
    largest_difference: float = 0.0


class EntityRanking(BaseModel):
    gstin: str = ""
    name: str = ""
    mismatch_count: int = 0
    value_difference: float = 0.0
    duplicate_count: int = 0
    risk_score: int = 0
    missing_invoice_count: int = 0


class CaseIntelligence(BaseModel):
    case_id: str = ""
    priority: PriorityLevel = "Medium"
    priority_score: int = 0
    priority_reason: str = ""
    patterns: List[str] = Field(default_factory=list)
    recommended_documents: List[str] = Field(default_factory=list)
    possible_causes: List[str] = Field(default_factory=list)
    suggested_verifications: List[str] = Field(default_factory=list)
    gst_provisions: List[str] = Field(default_factory=list)
    related_case_ids: List[str] = Field(default_factory=list)


class ExecutiveInsights(BaseModel):
    top_observations: List[str] = Field(default_factory=list)
    top_risks: List[str] = Field(default_factory=list)
    largest_tax_impact: float = 0.0
    largest_supplier_risk: str = ""
    largest_customer_risk: str = ""
    months_requiring_verification: List[str] = Field(default_factory=list)


class AuditIntelligenceCards(BaseModel):
    high_risk_cases: int = 0
    critical_suppliers: int = 0
    critical_customers: int = 0
    largest_tax_difference: float = 0.0
    highest_risk_month: str = ""
    open_investigation_cases: int = 0


class RiskHeatmaps(BaseModel):
    months: List[HeatmapCell] = Field(default_factory=list)
    suppliers: List[HeatmapCell] = Field(default_factory=list)
    customers: List[HeatmapCell] = Field(default_factory=list)
    categories: List[HeatmapCell] = Field(default_factory=list)


class IntelligenceSummary(BaseModel):
    session_id: str = ""
    cards: AuditIntelligenceCards = Field(default_factory=AuditIntelligenceCards)
    patterns: List[PatternFinding] = Field(default_factory=list)
    heatmaps: RiskHeatmaps = Field(default_factory=RiskHeatmaps)
    executive_insights: ExecutiveInsights = Field(default_factory=ExecutiveInsights)
    priority_cases: List[CaseIntelligence] = Field(default_factory=list)


class IntelligenceFullResponse(BaseModel):
    session_id: str = ""
    summary: IntelligenceSummary = Field(default_factory=IntelligenceSummary)
    months: List[MonthAnalysis] = Field(default_factory=list)
    suppliers: List[EntityRanking] = Field(default_factory=list)
    customers: List[EntityRanking] = Field(default_factory=list)
    cases: List[CaseIntelligence] = Field(default_factory=list)
    document_recommendations: List[DocumentRecommendation] = Field(default_factory=list)
