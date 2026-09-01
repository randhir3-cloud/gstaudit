"""Typed comparison result models — no raw Pandas exposed to API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from comparison.comparison_types import ComparisonResultType, RiskLevel


class ComparisonRecord(BaseModel):
    result_type: ComparisonResultType
    invoice_number: str = ""
    normalized_invoice: str = ""
    gstin_gstr1: str = ""
    gstin_eway: str = ""
    date_gstr1: str = ""
    date_eway: str = ""
    taxable_value_gstr1: float = 0.0
    taxable_value_eway: float = 0.0
    invoice_value_gstr1: float = 0.0
    invoice_value_eway: float = 0.0
    igst_gstr1: float = 0.0
    igst_eway: float = 0.0
    cgst_gstr1: float = 0.0
    cgst_eway: float = 0.0
    sgst_gstr1: float = 0.0
    sgst_eway: float = 0.0
    difference_amount: float = 0.0
    risk_score: int = 0
    source_period: str = ""
    ewb_number: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)


class ComparisonSummary(BaseModel):
    comparison_id: str = "gstr1_ewb_outward"
    left_label: str = "GSTR-1"
    right_label: str = "EWB OUTWARD"
    matched_count: int = 0
    missing_in_gstr1_count: int = 0
    missing_in_eway_count: int = 0
    gstin_mismatch_count: int = 0
    date_mismatch_count: int = 0
    value_mismatch_count: int = 0
    invoice_mismatch_count: int = 0
    duplicate_count: int = 0
    multiple_matches_count: int = 0
    unknown_count: int = 0
    total_difference_amount: float = 0.0
    overall_risk_score: int = 0
    risk_level: RiskLevel = RiskLevel.LOW
    total_gstr1_records: int = 0
    total_eway_records: int = 0


class ComparisonDetailPage(BaseModel):
    result_type: str
    total: int
    records: List[ComparisonRecord] = Field(default_factory=list)
    offset: int = 0
    limit: int = 100


class AuditObservation(BaseModel):
    invoice_number: str
    result_type: ComparisonResultType
    observation: str
    possible_reasons: List[str] = Field(default_factory=list)
    officer_action: str = ""


class ComparisonResult(BaseModel):
    session_id: str
    comparison_id: str
    status: str = "completed"
    summary: ComparisonSummary
    records: List[ComparisonRecord] = Field(default_factory=list)
    observations: List[AuditObservation] = Field(default_factory=list)
    completed_at: str = ""
