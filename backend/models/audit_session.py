"""Audit session models — central container for GST audit workflow state."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from models.dealer_metadata import DealerMetadata
from models.investigation import CaseTrackingSummary

DatasetKey = Literal["gstr1", "gstr2a", "ewb_outward", "ewb_inward"]
ComparisonStatus = Literal["not_started", "ready", "running", "completed"]
AuditStatus = Literal["draft", "in_progress", "ready", "completed"]
DuplicateAction = Literal["replace", "keep_latest", "delete"]

DATASET_LABELS: Dict[str, str] = {
    "gstr1": "GSTR-1",
    "gstr2a": "GSTR-2A",
    "ewb_outward": "EWB OUTWARD",
    "ewb_inward": "EWB INWARD",
}

COMPARISON_PAIRS = [
    {"id": "gstr1_ewb_outward", "left": "gstr1", "right": "ewb_outward", "label": "GSTR-1 ↔ EWB OUTWARD"},
    {"id": "gstr2a_ewb_inward", "left": "gstr2a", "right": "ewb_inward", "label": "GSTR-2A ↔ EWB INWARD"},
]


class UploadHistoryEntry(BaseModel):
    timestamp: str
    dataset: str
    dataset_label: str
    month: str = ""
    filename: str
    rows: int = 0
    status: str = "uploaded"


class DatasetStatistics(BaseModel):
    files_uploaded: int = 0
    total_rows: int = 0
    total_invoices: int = 0
    total_taxable_value: float = 0.0
    total_invoice_value: float = 0.0
    total_suppliers: int = 0
    total_customers: int = 0
    total_eway_bills: int = 0
    duplicate_records: int = 0
    unique_records: int = 0
    duplicate_percent: float = 0.0
    months_uploaded: int = 0
    months_total: int = 12


class TopSummaryPanel(BaseModel):
    files_uploaded: int = 0
    rows_imported: int = 0
    unique_records: int = 0
    duplicate_records: int = 0
    duplicate_percent: float = 0.0


class DuplicateDetectionSummary(BaseModel):
    duplicate_files: int = 0
    duplicate_months: int = 0
    duplicate_rows: int = 0
    duplicate_rows_percent: float = 0.0
    duplicate_invoices: int = 0
    duplicate_invoices_percent: float = 0.0
    duplicate_eway_bills: int = 0
    duplicate_eway_bills_percent: float = 0.0
    duplicate_gstin_invoice: int = 0
    duplicate_gstin_invoice_percent: float = 0.0


class UploadHealthCheck(BaseModel):
    label: str
    passed: bool
    status: Literal["ok", "warning", "error"] = "ok"
    detail: str = ""


class UploadHealth(BaseModel):
    score_percent: float = 0.0
    checks: List["UploadHealthCheck"] = Field(default_factory=list)


class WorkbookSummary(BaseModel):
    dataset_key: str
    dataset_label: str
    workbook_name: str = ""
    sheets: int = 0
    rows: int = 0
    columns: int = 0
    files: int = 0
    months: int = 0
    duplicate_records: int = 0
    unique_records: int = 0


class DuplicateMonthGroup(BaseModel):
    month: str
    short: str
    file_count: int
    filenames: List[str] = Field(default_factory=list)
    resolution: Optional[str] = None


MonthCellStatus = Literal["uploaded", "missing", "duplicate", "processing"]


class MonthCoverageMonth(BaseModel):
    month: str
    short: str
    uploaded: bool
    file_count: int = 0
    filenames: List[str] = Field(default_factory=list)
    row_count: int = 0
    duplicate_rows: int = 0
    unique_rows: int = 0
    status: MonthCellStatus = "missing"
    upload_time: str = ""
    merge_status: str = ""


class MonthCoverage(BaseModel):
    months: List[MonthCoverageMonth] = Field(default_factory=list)
    uploaded_count: int = 0
    total_months: int = 12
    missing_months: List[str] = Field(default_factory=list)
    duplicate_months: List[DuplicateMonthGroup] = Field(default_factory=list)
    coverage_percent: float = 0.0


class DatasetRecord(BaseModel):
    dataset_key: DatasetKey
    label: str
    source_files: List[str] = Field(default_factory=list)
    staged_files: List[str] = Field(default_factory=list)
    merged: bool = False
    workbook_id: str = ""
    current_dataset: str = ""
    dealer_gstin: str = ""
    financial_year: str = ""
    row_count: int = 0
    invoice_count: int = 0
    duplicate_record_count: int = 0
    unique_record_count: int = 0
    workbook_sheets: int = 0
    workbook_columns: int = 0
    uploaded_months: List[str] = Field(default_factory=list)
    missing_months: List[str] = Field(default_factory=list)
    duplicate_months: List[DuplicateMonthGroup] = Field(default_factory=list)
    last_upload_at: str = ""
    last_merge_at: str = ""
    merge_processing_ms: int = 0
    status: str = "empty"
    preview_available: bool = False
    download_available: bool = False


class ComparisonPairStatus(BaseModel):
    id: str
    label: str
    left_dataset: str
    right_dataset: str
    status: ComparisonStatus = "not_started"


class DiscrepancySummary(BaseModel):
    missing_invoice: int = 0
    duplicate_invoice: int = 0
    gstin_mismatch: int = 0
    invoice_mismatch: int = 0
    value_mismatch: int = 0
    date_mismatch: int = 0
    hsn_mismatch: int = 0
    state_mismatch: int = 0
    risk_score: int = 0
    total: int = 0


class ReadinessBreakdown(BaseModel):
    gstr1: float = 0.0
    gstr2a: float = 0.0
    ewb_outward: float = 0.0
    ewb_inward: float = 0.0
    overall: float = 0.0


class AuditSession(BaseModel):
    session_id: str
    dealer: DealerMetadata = Field(default_factory=DealerMetadata)
    financial_year: str = ""
    tax_period: str = ""
    audit_status: AuditStatus = "draft"
    datasets: Dict[str, DatasetRecord] = Field(default_factory=dict)
    upload_history: List[UploadHistoryEntry] = Field(default_factory=list)
    comparison_status: List[ComparisonPairStatus] = Field(default_factory=list)
    discrepancies: DiscrepancySummary = Field(default_factory=DiscrepancySummary)
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def build_session_id(gstin: str, financial_year: str) -> str:
        raw = f"{gstin.upper()}:{financial_year.strip()}"
        digest = hashlib.sha256(raw.encode()).hexdigest()[:12]
        return f"session_{digest}"

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


class DashboardResponse(BaseModel):
    session: AuditSession
    dealer_name: str
    gstin: str
    trade_name: str
    financial_year: str
    audit_status: AuditStatus
    audit_readiness_percent: float
    readiness: ReadinessBreakdown
    dataset_cards: List[dict]
    month_coverage: Dict[str, MonthCoverage]
    statistics: Dict[str, DatasetStatistics]
    summary_statistics: DatasetStatistics
    top_summary: TopSummaryPanel = Field(default_factory=TopSummaryPanel)
    comparison_status: List[ComparisonPairStatus]
    discrepancies: DiscrepancySummary
    upload_history: List[UploadHistoryEntry]
    merge_summaries: List[dict]
    upload_health: UploadHealth = Field(default_factory=UploadHealth)
    duplicate_detection: DuplicateDetectionSummary = Field(default_factory=DuplicateDetectionSummary)
    workbook_summaries: List[WorkbookSummary] = Field(default_factory=list)
    month_statistics: Dict[str, Dict[str, dict]] = Field(default_factory=dict)
    can_start_audit: bool
    audit_not_ready_reason: str = ""
    warnings: List[str]
    dataset_keys: List[str] = Field(default_factory=list)
    comparison_summary: Optional[dict] = None
    case_tracking: CaseTrackingSummary = Field(default_factory=CaseTrackingSummary)
    audit_intelligence: Optional[dict] = None
