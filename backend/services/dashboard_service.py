"""GST Audit Dashboard aggregation — reusable across API endpoints."""

from __future__ import annotations

from typing import Dict, List, Optional

from models.dealer_metadata import DealerMetadata
from models.investigation import CaseTrackingSummary
from models.audit_session import (
    COMPARISON_PAIRS,
    DATASET_LABELS,
    AuditSession,
    ComparisonPairStatus,
    ComparisonStatus,
    DashboardResponse,
    DatasetRecord,
    DatasetStatistics,
    DiscrepancySummary,
    DuplicateDetectionSummary,
    DuplicateMonthGroup,
    MonthCoverage,
    MonthCoverageMonth,
    ReadinessBreakdown,
    TopSummaryPanel,
    UploadHealth,
    UploadHealthCheck,
    UploadHistoryEntry,
    WorkbookSummary,
)
from services.fy_months import month_coverage_from_filenames, parse_month_from_filename

DATASET_KEYS = tuple(DATASET_LABELS.keys())


def get_session_dataset_keys(session: AuditSession) -> List[str]:
    """Ordered dataset keys — known keys first, then any future modules."""
    extra = [k for k in (session.datasets or {}) if k not in DATASET_KEYS]
    return list(DATASET_KEYS) + extra


def _empty_datasets() -> Dict[str, DatasetRecord]:
    return {
        key: DatasetRecord(
            dataset_key=key,
            label=DATASET_LABELS.get(key, key.replace("_", " ").upper()),
            status="empty",
        )
        for key in DATASET_KEYS
    }


def _rows_by_filename(history: List[UploadHistoryEntry]) -> Dict[str, int]:
    rows: Dict[str, int] = {}
    for entry in history:
        if entry.filename and entry.rows:
            rows[entry.filename] = entry.rows
    return rows


def _upload_time_by_filename(history: List[UploadHistoryEntry]) -> Dict[str, str]:
    times: Dict[str, str] = {}
    for entry in history:
        if entry.filename:
            times[entry.filename] = entry.timestamp
    return times


def _pct(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return round((part / whole) * 100, 2)


def _month_cell_status(uploaded: bool, file_count: int, processing: bool) -> str:
    if not uploaded:
        return "missing"
    if file_count > 1:
        return "duplicate"
    if processing:
        return "processing"
    return "uploaded"


def _enrich_month_coverage(
    raw: Dict,
    *,
    dataset_key: str,
    ds: Optional[DatasetRecord],
    history: List[UploadHistoryEntry],
) -> MonthCoverage:
    rows_map = _rows_by_filename(history)
    times_map = _upload_time_by_filename(history)
    processing = bool(ds and (ds.staged_files or ds.status == "uploaded") and not ds.merged)
    merge_status = "Completed" if ds and ds.merged else ("Pending" if ds and ds.source_files or ds and ds.staged_files else "")

    avg_rows = 0
    if ds and ds.row_count and raw["uploaded_count"]:
        avg_rows = ds.row_count // raw["uploaded_count"]

    enriched_months = []
    for m in raw["months"]:
        filenames = m.get("filenames") or []
        row_count = sum(rows_map.get(f, 0) for f in filenames)
        if not row_count and m["uploaded"] and avg_rows:
            row_count = avg_rows
        duplicate_rows = 0
        if m["file_count"] > 1 and row_count:
            per_file = row_count // m["file_count"] if m["file_count"] else 0
            duplicate_rows = per_file * (m["file_count"] - 1)
        elif m["file_count"] > 1 and avg_rows:
            duplicate_rows = avg_rows * (m["file_count"] - 1)
            row_count = avg_rows * m["file_count"]
        unique_rows = max(0, row_count - duplicate_rows)
        upload_time = ""
        if filenames:
            upload_time = max((times_map.get(f, "") for f in filenames), default="")
        status = _month_cell_status(m["uploaded"], m["file_count"], processing and m["uploaded"])
        enriched_months.append(
            MonthCoverageMonth(
                month=m["month"],
                short=m["short"],
                uploaded=m["uploaded"],
                file_count=m["file_count"],
                filenames=filenames,
                row_count=row_count,
                duplicate_rows=duplicate_rows,
                unique_rows=unique_rows,
                status=status,
                upload_time=upload_time,
                merge_status=merge_status,
            )
        )

    return MonthCoverage(
        months=enriched_months,
        uploaded_count=raw["uploaded_count"],
        total_months=raw["total_months"],
        missing_months=raw["missing_months"],
        duplicate_months=[DuplicateMonthGroup(**d) for d in raw["duplicate_months"]],
        coverage_percent=raw["coverage_percent"],
    )


def ensure_session_datasets(session: AuditSession) -> AuditSession:
    if not session.datasets:
        session.datasets = _empty_datasets()
    keys = get_session_dataset_keys(session)
    for key in keys:
        if key not in session.datasets:
            session.datasets[key] = DatasetRecord(
                dataset_key=key,
                label=DATASET_LABELS.get(key, key.replace("_", " ").upper()),
                status="empty",
            )
    return session


def build_dataset_record(
    dataset_key: str,
    *,
    source_files: Optional[List[str]] = None,
    staged_files: Optional[List[str]] = None,
    merged: bool = False,
    workbook_id: str = "",
    current_dataset: str = "",
    dealer_gstin: str = "",
    financial_year: str = "",
    row_count: int = 0,
    last_upload_at: str = "",
    last_merge_at: str = "",
    merge_processing_ms: int = 0,
) -> DatasetRecord:
    all_files = list(source_files or []) + [f for f in (staged_files or []) if f not in (source_files or [])]
    coverage = month_coverage_from_filenames(all_files) if all_files else month_coverage_from_filenames([])

    status = "empty"
    if merged:
        status = "merged"
    elif all_files:
        status = "uploaded"

    invoice_count = row_count if dataset_key in ("gstr1", "gstr2a") else 0
    ewb_count = row_count if dataset_key.startswith("ewb_") else 0

    return DatasetRecord(
        dataset_key=dataset_key,
        label=DATASET_LABELS[dataset_key],
        source_files=list(source_files or []),
        staged_files=list(staged_files or []),
        merged=merged,
        workbook_id=workbook_id,
        current_dataset=current_dataset,
        dealer_gstin=dealer_gstin,
        financial_year=financial_year,
        row_count=row_count,
        invoice_count=invoice_count,
        uploaded_months=[m["month"] for m in coverage["months"] if m["uploaded"]],
        missing_months=coverage["missing_months"],
        duplicate_months=[DuplicateMonthGroup(**d) for d in coverage["duplicate_months"]],
        last_upload_at=last_upload_at,
        last_merge_at=last_merge_at,
        merge_processing_ms=merge_processing_ms,
        status=status,
        preview_available=merged,
        download_available=merged,
    )


def compute_readiness(session: AuditSession) -> ReadinessBreakdown:
    keys = get_session_dataset_keys(session)
    scores = {}
    for key in keys:
        ds = session.datasets.get(key)
        if not ds or (not ds.source_files and not ds.staged_files and not ds.merged):
            scores[key] = 0.0
            continue
        files = list(ds.source_files) + list(ds.staged_files)
        coverage = month_coverage_from_filenames(files) if files else {"coverage_percent": 0.0}
        base = coverage["coverage_percent"]
        if ds.merged:
            base = min(100.0, base + 10.0)
        scores[key] = round(min(100.0, base), 1)

    active = [scores[k] for k in keys if scores.get(k, 0) > 0]
    overall = round(sum(active) / len(active), 1) if active else 0.0

    return ReadinessBreakdown(
        gstr1=scores.get("gstr1", 0.0),
        gstr2a=scores.get("gstr2a", 0.0),
        ewb_outward=scores.get("ewb_outward", 0.0),
        ewb_inward=scores.get("ewb_inward", 0.0),
        overall=overall,
    )


def compute_comparison_status(session: AuditSession) -> List[ComparisonPairStatus]:
    from services.comparison_store import get_comparison_status

    runtime_status = get_comparison_status(session.session_id)
    results = []
    for pair in COMPARISON_PAIRS:
        left = session.datasets.get(pair["left"])
        right = session.datasets.get(pair["right"])
        status: ComparisonStatus = "not_started"
        if left and right and left.merged and right.merged:
            status = "ready"
        existing = next((c for c in session.comparison_status if c.id == pair["id"]), None)
        if existing and existing.status in ("completed", "running"):
            status = existing.status
        if pair["id"] == "gstr1_ewb_outward" and runtime_status == "running":
            status = "running"
        if pair["id"] == "gstr1_ewb_outward" and runtime_status == "completed":
            status = "completed"
        results.append(
            ComparisonPairStatus(
                id=pair["id"],
                label=pair["label"],
                left_dataset=pair["left"],
                right_dataset=pair["right"],
                status=status,
            )
        )
    return results


def _duplicate_records_for_dataset(ds: DatasetRecord, history: List[UploadHistoryEntry], dataset_key: str) -> int:
    if ds.duplicate_record_count:
        return ds.duplicate_record_count
    dup_files = sum(max(0, d.file_count - 1) for d in ds.duplicate_months)
    if not dup_files:
        return 0
    rows_map = _rows_by_filename([h for h in history if h.dataset == dataset_key])
    if rows_map:
        extra = 0
        for dup in ds.duplicate_months:
            for fn in dup.filenames[1:]:
                extra += rows_map.get(fn, 0)
        return extra
    if ds.row_count and ds.uploaded_months:
        avg = ds.row_count // max(len(ds.uploaded_months), 1)
        return avg * dup_files
    return dup_files * 100


def dataset_statistics(ds: DatasetRecord, history: Optional[List[UploadHistoryEntry]] = None, dataset_key: str = "") -> DatasetStatistics:
    files = list(ds.source_files) + list(ds.staged_files)
    is_eway = ds.dataset_key.startswith("ewb_")
    is_gstr2a = ds.dataset_key == "gstr2a"
    dup_records = _duplicate_records_for_dataset(ds, history or [], dataset_key or ds.dataset_key)
    total_rows = ds.row_count
    unique_records = ds.unique_record_count or max(0, total_rows - dup_records)
    if ds.unique_record_count:
        dup_records = max(0, total_rows - unique_records)
    return DatasetStatistics(
        files_uploaded=len(files),
        total_rows=total_rows,
        total_invoices=ds.invoice_count if not is_eway else 0,
        total_taxable_value=0.0,
        total_invoice_value=0.0,
        total_suppliers=ds.invoice_count if is_gstr2a else 0,
        total_customers=ds.invoice_count if ds.dataset_key == "gstr1" else 0,
        total_eway_bills=ds.row_count if is_eway else 0,
        duplicate_records=dup_records,
        unique_records=unique_records,
        duplicate_percent=_pct(dup_records, total_rows),
        months_uploaded=len(ds.uploaded_months),
        months_total=12,
    )


def build_month_coverage_map(session: AuditSession) -> Dict[str, MonthCoverage]:
    result = {}
    keys = get_session_dataset_keys(session)
    history = session.upload_history or []
    for key in keys:
        ds = session.datasets.get(key)
        files = list(ds.source_files) + list(ds.staged_files) if ds else []
        raw = month_coverage_from_filenames(files) if files else month_coverage_from_filenames([])
        ds_history = [h for h in history if h.dataset == key]
        result[key] = _enrich_month_coverage(raw, dataset_key=key, ds=ds, history=ds_history)
    return result


def build_month_statistics_map(coverage_map: Dict[str, MonthCoverage]) -> Dict[str, Dict[str, dict]]:
    stats: Dict[str, Dict[str, dict]] = {}
    for key, cov in coverage_map.items():
        stats[key] = {}
        for m in cov.months:
            stats[key][m.short] = {
                "month": m.month,
                "short": m.short,
                "status": m.status,
                "row_count": m.row_count,
                "duplicate_rows": m.duplicate_rows,
                "unique_rows": m.unique_rows,
                "file_count": m.file_count,
                "filenames": m.filenames,
                "upload_time": m.upload_time,
                "merge_status": m.merge_status,
            }
    return stats


def build_dataset_cards(session: AuditSession) -> List[dict]:
    cards = []
    keys = get_session_dataset_keys(session)
    history = session.upload_history or []
    coverage_map = build_month_coverage_map(session)
    for key in keys:
        ds = session.datasets.get(key)
        if not ds:
            continue
        files = list(ds.source_files) + list(ds.staged_files)
        stats = dataset_statistics(ds, history, key)
        cov = coverage_map.get(key)
        cards.append(
            {
                "dataset_key": key,
                "name": ds.label,
                "files_uploaded": len(files),
                "rows": ds.row_count,
                "rows_imported": ds.row_count,
                "invoices": ds.invoice_count,
                "duplicate_records": stats.duplicate_records,
                "unique_records": stats.unique_records,
                "duplicate_percent": stats.duplicate_percent,
                "months_uploaded": cov.uploaded_count if cov else len(ds.uploaded_months),
                "months_total": cov.total_months if cov else 12,
                "merged": ds.merged,
                "merge_status": "Completed" if ds.merged else ("Pending" if files else "Not Started"),
                "dealer_name": session.dealer.display_name(),
                "dealer_gstin": ds.dealer_gstin or session.dealer.gstin,
                "financial_year": ds.financial_year or session.financial_year,
                "last_upload": ds.last_upload_at or ds.last_merge_at,
                "status": "Ready" if ds.merged else ("Uploaded" if files else "Empty"),
                "workbook_id": ds.workbook_id,
                "current_dataset": ds.current_dataset,
                "preview_available": ds.preview_available,
                "download_available": ds.download_available,
                "missing_months": ds.missing_months,
                "duplicate_months": [d.model_dump() for d in ds.duplicate_months],
            }
        )
    return cards


def build_merge_summaries(session: AuditSession) -> List[dict]:
    summaries = []
    keys = get_session_dataset_keys(session)
    history = session.upload_history or []
    for key in keys:
        ds = session.datasets.get(key)
        if not ds or not ds.merged:
            continue
        files = list(ds.source_files)
        stats = dataset_statistics(ds, history, key)
        summaries.append(
            {
                "dataset_key": key,
                "dataset_label": ds.label,
                "merged_files": len(files),
                "months_covered": ds.uploaded_months,
                "months_covered_count": len(ds.uploaded_months),
                "missing_months": ds.missing_months,
                "duplicate_months": [d.month for d in ds.duplicate_months],
                "total_rows": ds.row_count,
                "rows_imported": ds.row_count,
                "duplicate_records": stats.duplicate_records,
                "rows_after_deduplication": stats.unique_records,
                "processing_time_ms": ds.merge_processing_ms,
                "processing_time_sec": round(ds.merge_processing_ms / 1000, 1) if ds.merge_processing_ms else 0,
                "workbook_id": ds.workbook_id,
                "filename": ds.current_dataset,
            }
        )
    return summaries


def build_workbook_summaries(session: AuditSession) -> List[WorkbookSummary]:
    summaries = []
    keys = get_session_dataset_keys(session)
    history = session.upload_history or []
    for key in keys:
        ds = session.datasets.get(key)
        if not ds:
            continue
        files = list(ds.source_files) + list(ds.staged_files)
        if not files and not ds.merged:
            continue
        stats = dataset_statistics(ds, history, key)
        summaries.append(
            WorkbookSummary(
                dataset_key=key,
                dataset_label=ds.label,
                workbook_name=ds.current_dataset or (files[0] if files else ""),
                sheets=ds.workbook_sheets or (1 if ds.merged else 0),
                rows=ds.row_count,
                columns=ds.workbook_columns or 0,
                files=len(files),
                months=len(ds.uploaded_months),
                duplicate_records=stats.duplicate_records,
                unique_records=stats.unique_records,
            )
        )
    return summaries


def build_duplicate_detection(session: AuditSession, summary: DatasetStatistics) -> DuplicateDetectionSummary:
    dup_files = 0
    dup_months = 0
    dup_invoices = 0
    dup_eway = 0
    keys = get_session_dataset_keys(session)
    for key in keys:
        ds = session.datasets.get(key)
        if not ds:
            continue
        for dup in ds.duplicate_months:
            dup_months += 1
            dup_files += max(0, dup.file_count - 1)
        stats = dataset_statistics(ds, session.upload_history or [], key)
        if key.startswith("ewb_"):
            dup_eway += stats.duplicate_records
        elif key in ("gstr1", "gstr2a"):
            dup_invoices += stats.duplicate_records

    disc = session.discrepancies
    dup_gstin_invoice = disc.duplicate_invoice + disc.invoice_mismatch

    return DuplicateDetectionSummary(
        duplicate_files=dup_files,
        duplicate_months=dup_months,
        duplicate_rows=summary.duplicate_records,
        duplicate_rows_percent=summary.duplicate_percent,
        duplicate_invoices=dup_invoices,
        duplicate_invoices_percent=_pct(dup_invoices, summary.total_invoices),
        duplicate_eway_bills=dup_eway,
        duplicate_eway_bills_percent=_pct(dup_eway, summary.total_eway_bills),
        duplicate_gstin_invoice=dup_gstin_invoice,
        duplicate_gstin_invoice_percent=_pct(dup_gstin_invoice, summary.total_invoices),
    )


def build_upload_health(session: AuditSession, readiness: ReadinessBreakdown, can_start: bool) -> UploadHealth:
    dealer = session.dealer
    checks: List[UploadHealthCheck] = []
    keys = get_session_dataset_keys(session)

    dealer_ok = bool(dealer.gstin)
    checks.append(UploadHealthCheck(label="Dealer Matched", passed=dealer_ok, status="ok" if dealer_ok else "error", detail=dealer.gstin or "No GSTIN"))

    fy_ok = bool(session.financial_year or dealer.financial_year)
    checks.append(UploadHealthCheck(label="Financial Year Matched", passed=fy_ok, status="ok" if fy_ok else "error", detail=session.financial_year or dealer.financial_year or "Not set"))

    has_files = any(
        (session.datasets.get(k) and (session.datasets[k].source_files or session.datasets[k].staged_files))
        for k in keys
    )
    checks.append(UploadHealthCheck(label="Read Me Valid", passed=dealer_ok and fy_ok, status="ok" if dealer_ok and fy_ok else "warning"))

    parsed_ok = has_files
    checks.append(UploadHealthCheck(label="Files Parsed", passed=parsed_ok, status="ok" if parsed_ok else "warning", detail="At least one dataset uploaded" if parsed_ok else "No files yet"))

    dup_any = any(session.datasets.get(k) and session.datasets[k].duplicate_months for k in keys)
    checks.append(UploadHealthCheck(label="Duplicate Upload", passed=not dup_any, status="warning" if dup_any else "ok", detail="Duplicate months detected" if dup_any else "No duplicate months"))

    missing_any = []
    for k in keys:
        ds = session.datasets.get(k)
        if ds and ds.missing_months:
            missing_any.extend(ds.missing_months[:2])
    missing_label = f"{missing_any[0]} Missing" if missing_any else "All months covered"
    checks.append(UploadHealthCheck(label=missing_label if missing_any else "Month Coverage", passed=not missing_any, status="warning" if missing_any else "ok"))

    checks.append(UploadHealthCheck(label="Ready for Audit", passed=can_start, status="ok" if can_start else "warning", detail="Audit can start" if can_start else "More data required"))

    passed = sum(1 for c in checks if c.passed)
    score = round((passed / len(checks)) * 100, 1) if checks else 0.0
    return UploadHealth(score_percent=score, checks=checks)


def build_top_summary(summary: DatasetStatistics) -> TopSummaryPanel:
    return TopSummaryPanel(
        files_uploaded=summary.files_uploaded,
        rows_imported=summary.total_rows,
        unique_records=summary.unique_records,
        duplicate_records=summary.duplicate_records,
        duplicate_percent=summary.duplicate_percent,
    )


def derive_audit_not_ready_reason(session: AuditSession, readiness: ReadinessBreakdown, can_start: bool) -> str:
    if can_start:
        return ""
    reasons = []
    keys = get_session_dataset_keys(session)
    for key in keys:
        ds = session.datasets.get(key)
        if not ds:
            continue
        if ds.missing_months:
            reasons.append(f"{ds.label}: missing {', '.join(ds.missing_months[:3])}")
        if ds.duplicate_months:
            reasons.append(f"{ds.label}: duplicate uploads unresolved")
    gstr1 = session.datasets.get("gstr1")
    gstr2a = session.datasets.get("gstr2a")
    if not (gstr1 and gstr1.merged) and not (gstr2a and gstr2a.merged):
        reasons.append("GSTR-1 or GSTR-2A must be merged before audit")
    if readiness.overall < 75:
        reasons.append(f"Overall readiness {readiness.overall}% (minimum 75%)")
    return "; ".join(reasons) if reasons else "Upload and merge required datasets"


def build_warnings(session: AuditSession) -> List[str]:
    warnings = []
    keys = get_session_dataset_keys(session)
    for key in keys:
        ds = session.datasets.get(key)
        if not ds:
            continue
        if ds.missing_months:
            warnings.append(f"{ds.label}: missing {', '.join(ds.missing_months)}")
        if ds.duplicate_months:
            for dup in ds.duplicate_months:
                warnings.append(f"{ds.label}: duplicate month {dup.month} ({dup.file_count} files)")
    return warnings


def derive_audit_status(session: AuditSession, readiness: ReadinessBreakdown) -> str:
    if readiness.overall >= 90:
        return "ready"
    if readiness.overall > 0:
        return "in_progress"
    return "draft"


def build_dashboard(session: Optional[AuditSession]) -> DashboardResponse:
    if not session:
        empty = AuditSession(session_id="", dealer=DealerMetadata())
        ensure_session_datasets(empty)
        readiness = ReadinessBreakdown()
        keys = list(DATASET_KEYS)
        return DashboardResponse(
            session=empty,
            dealer_name="",
            gstin="",
            trade_name="",
            financial_year="",
            audit_status="draft",
            audit_readiness_percent=0.0,
            readiness=readiness,
            dataset_cards=build_dataset_cards(empty),
            month_coverage={k: v.model_dump() for k, v in build_month_coverage_map(empty).items()},
            statistics={k: DatasetStatistics().model_dump() for k in keys},
            summary_statistics=DatasetStatistics(),
            top_summary=TopSummaryPanel(),
            comparison_status=compute_comparison_status(empty),
            discrepancies=DiscrepancySummary(),
            upload_history=[],
            merge_summaries=[],
            upload_health=UploadHealth(),
            duplicate_detection=DuplicateDetectionSummary(),
            workbook_summaries=[],
            month_statistics={},
            can_start_audit=False,
            audit_not_ready_reason="Upload and merge required datasets",
            warnings=[],
            dataset_keys=keys,
            case_tracking=CaseTrackingSummary(),
            audit_intelligence=None,
        )

    ensure_session_datasets(session)
    keys = get_session_dataset_keys(session)
    readiness = compute_readiness(session)
    session.audit_status = derive_audit_status(session, readiness)
    session.comparison_status = compute_comparison_status(session)

    coverage_map = build_month_coverage_map(session)
    month_stats = build_month_statistics_map(coverage_map)
    history = session.upload_history or []

    stats = {key: dataset_statistics(session.datasets[key], history, key) for key in keys if key in session.datasets}
    summary = DatasetStatistics(
        files_uploaded=sum(s.files_uploaded for s in stats.values()),
        total_rows=sum(s.total_rows for s in stats.values()),
        total_invoices=sum(s.total_invoices for s in stats.values()),
        total_taxable_value=sum(s.total_taxable_value for s in stats.values()),
        total_invoice_value=sum(s.total_invoice_value for s in stats.values()),
        total_suppliers=sum(s.total_suppliers for s in stats.values()),
        total_customers=sum(s.total_customers for s in stats.values()),
        total_eway_bills=sum(s.total_eway_bills for s in stats.values()),
        duplicate_records=sum(s.duplicate_records for s in stats.values()),
        unique_records=sum(s.unique_records for s in stats.values()),
        duplicate_percent=_pct(sum(s.duplicate_records for s in stats.values()), sum(s.total_rows for s in stats.values())),
        months_uploaded=sum(s.months_uploaded for s in stats.values()),
        months_total=12 * len(stats) if stats else 0,
    )

    gstr1_ready = session.datasets.get("gstr1") and session.datasets["gstr1"].merged
    gstr2a_ready = session.datasets.get("gstr2a") and session.datasets["gstr2a"].merged
    can_start = readiness.overall >= 75 and (gstr1_ready or gstr2a_ready)
    not_ready_reason = derive_audit_not_ready_reason(session, readiness, can_start)

    from services.comparison_store import get_result
    from services.investigation_service import build_summary, sync_cases_from_comparison
    from intelligence.intelligence_service import get_session_intelligence

    cmp_result = get_result(session.session_id)
    comparison_summary = cmp_result.summary.model_dump() if cmp_result else None
    cases = sync_cases_from_comparison(session.session_id) if session.session_id else []
    case_tracking = build_summary(cases)
    intel = get_session_intelligence(session.session_id) if session.session_id and cmp_result else None
    audit_intelligence = intel.summary.model_dump() if intel else None

    return DashboardResponse(
        session=session,
        dealer_name=session.dealer.display_name(),
        gstin=session.dealer.gstin,
        trade_name=session.dealer.trade_name or session.dealer.legal_name,
        financial_year=session.financial_year or session.dealer.financial_year,
        audit_status=session.audit_status,
        audit_readiness_percent=readiness.overall,
        readiness=readiness,
        dataset_cards=build_dataset_cards(session),
        month_coverage={k: v.model_dump() for k, v in coverage_map.items()},
        statistics={k: v.model_dump() for k, v in stats.items()},
        summary_statistics=summary,
        top_summary=build_top_summary(summary),
        comparison_status=session.comparison_status,
        discrepancies=session.discrepancies,
        upload_history=session.upload_history,
        merge_summaries=build_merge_summaries(session),
        upload_health=build_upload_health(session, readiness, can_start),
        duplicate_detection=build_duplicate_detection(session, summary),
        workbook_summaries=build_workbook_summaries(session),
        month_statistics=month_stats,
        can_start_audit=can_start,
        audit_not_ready_reason=not_ready_reason,
        warnings=build_warnings(session),
        dataset_keys=keys,
        comparison_summary=comparison_summary,
        case_tracking=case_tracking,
        audit_intelligence=audit_intelligence,
    )
