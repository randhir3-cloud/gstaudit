"""GSTR-2A vs EWB Inward comparator and job orchestration."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Callable, List, Optional, Set

from comparison.comparators.date_matcher import compare_dates
from comparison.comparators.duplicate_matcher import find_duplicate_keys
from comparison.comparators.gstin_matcher import gstins_match
from comparison.comparators.invoice_matcher import build_invoice_index
from comparison.comparators.risk_engine import overall_risk_level, score_result
from comparison.comparators.summary_builder import build_summary
from comparison.comparators.value_matcher import compare_values
from comparison.comparison_types import ComparisonResultType
from comparison.engine import ComparisonEngine
from comparison.models import ComparisonConfig, NormalizerConfig
from comparison.result_models import ComparisonRecord, ComparisonResult
from models.job import JobCreateRequest, JobType
from services.comparison_store import cache_workbook, get_workbook, save_result, set_comparison_status
from services.comparison_service import apply_result_to_session
from services.audit_session_store import get_session, upsert_session
from services.job_service import create_job

_COMPARISON_DIR = __import__("pathlib").Path(__file__).resolve().parent


def _load_intelligence():
    import importlib.util

    spec = importlib.util.spec_from_file_location("gais_gstr2a_intelligence", _COMPARISON_DIR / "intelligence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_validators():
    import importlib.util

    spec = importlib.util.spec_from_file_location("gais_gstr2a_validators", _COMPARISON_DIR / "validators.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_validators = _load_validators()
load_gstr2a_records = _validators.load_gstr2a_records
load_eway_inward_records = _validators.load_eway_inward_records
validate_workbook_pair = _validators.validate_workbook_pair
compare_tax_fields = _validators.compare_tax_fields
compare_invoice_values = _validators.compare_invoice_values


def generate_purchase_observations(records, limit=100):
    return _load_intelligence().generate_purchase_observations(records, limit=limit)

COMPARISON_ID = "gstr2a_ewb_inward"

GSTR2A_EWB_INWARD_CONFIG = ComparisonConfig(
    comparison_id=COMPARISON_ID,
    left_dataset="gstr2a",
    right_dataset="ewb_inward",
    left_label="GSTR-2A",
    right_label="EWB INWARD",
    normalizer=NormalizerConfig(amount_tolerance=1.0, date_tolerance_days=1),
)

_engine = ComparisonEngine()


def _decode_b64(data: str) -> bytes:
    return base64.b64decode(data)


def _resolve_workbooks(
    session_id: str,
    *,
    gstr2a_workbook_base64: str = "",
    ewb_inward_workbook_base64: str = "",
    job_id: Optional[str] = None,
) -> tuple[bytes, bytes]:
    gstr2a_bytes = get_workbook(session_id, "gstr2a")
    ewb_bytes = get_workbook(session_id, "ewb_inward")

    if job_id:
        from services.job_service import get_job

        job = get_job(job_id)
        if job and job.payload:
            gstr2a_workbook_base64 = gstr2a_workbook_base64 or job.payload.get("gstr2a_workbook_base64", "")
            ewb_inward_workbook_base64 = ewb_inward_workbook_base64 or job.payload.get("ewb_inward_workbook_base64", "")

    if gstr2a_workbook_base64:
        gstr2a_bytes = _decode_b64(gstr2a_workbook_base64)
        cache_workbook(session_id, "gstr2a", gstr2a_bytes)
    if ewb_inward_workbook_base64:
        ewb_bytes = _decode_b64(ewb_inward_workbook_base64)
        cache_workbook(session_id, "ewb_inward", ewb_bytes)

    return gstr2a_bytes, ewb_bytes


def compare_gstr2a_vs_eway_inward(
    config: ComparisonConfig,
    gstr2a_bytes: bytes,
    ewb_bytes: bytes,
    session_id: str,
    *,
    progress_callback=None,
    checkpoint: dict | None = None,
    cancel_check=None,
) -> ComparisonResult:
    gstr2a_records = load_gstr2a_records(gstr2a_bytes)
    ewb_records = load_eway_inward_records(ewb_bytes)

    total_rows = len(gstr2a_records) + len(ewb_records)
    if progress_callback:
        progress_callback(percent=10, stage="Building purchase indexes", rows_processed=0, rows_total=total_rows)

    gstr2a_dupes = find_duplicate_keys(gstr2a_records)
    ewb_dupes = find_duplicate_keys(ewb_records)
    gstr2a_index = build_invoice_index(gstr2a_records)
    ewb_index = build_invoice_index(ewb_records)

    classified: List[ComparisonRecord] = []
    matched_gstr2a_keys: Set[str] = set()
    if checkpoint:
        raw = checkpoint.get("classified", [])
        for item in raw:
            classified.append(item if isinstance(item, ComparisonRecord) else ComparisonRecord.model_validate(item))
        matched_gstr2a_keys = set(checkpoint.get("matched_gstr2a_keys", []))
    start_index = int(checkpoint.get("ewb_index", 0)) if checkpoint else 0

    for i, ewb_rec in enumerate(ewb_records):
        if i < start_index:
            continue
        if cancel_check and cancel_check():
            raise InterruptedError("Job cancelled")

        key = ewb_rec["normalized_invoice"]
        if not key:
            classified.append(_record_from_ewb(ewb_rec, ComparisonResultType.UNKNOWN, config, reason="missing_invoice"))
            continue
        if key in ewb_dupes:
            classified.append(_record_from_ewb(ewb_rec, ComparisonResultType.DUPLICATE, config))
            continue

        gstr2a_matches = gstr2a_index.get(key, [])
        if len(gstr2a_matches) > 1:
            classified.append(_record_from_ewb(ewb_rec, ComparisonResultType.MULTIPLE_MATCHES, config, reason="invoice_mismatch"))
            continue
        if not gstr2a_matches:
            classified.append(_record_from_ewb(ewb_rec, ComparisonResultType.MISSING_IN_GSTR1, config))
            continue

        gstr2a_rec = gstr2a_matches[0]
        matched_gstr2a_keys.add(key)
        if key in gstr2a_dupes:
            classified.append(_merge_record(gstr2a_rec, ewb_rec, ComparisonResultType.DUPLICATE, config))
            continue

        result_type = ComparisonResultType.MATCHED
        diff = 0.0
        details: dict = {}

        if not gstins_match(gstr2a_rec.get("gstin", ""), ewb_rec.get("gstin", "")):
            result_type = ComparisonResultType.GSTIN_MISMATCH
        elif not compare_dates(gstr2a_rec.get("invoice_date"), ewb_rec.get("invoice_date"), config.normalizer):
            result_type = ComparisonResultType.DATE_MISMATCH
        else:
            taxable_ok, diff = compare_values(
                {**gstr2a_rec, "igst": 0, "cgst": 0, "sgst": 0, "invoice_value": gstr2a_rec.get("taxable_value", 0)},
                {**ewb_rec, "igst": 0, "cgst": 0, "sgst": 0, "invoice_value": ewb_rec.get("taxable_value", 0)},
                config.normalizer,
            )
            if not taxable_ok:
                result_type = ComparisonResultType.VALUE_MISMATCH
                details["mismatch_kind"] = "taxable_value"
            else:
                tax_ok, tax_diff = compare_tax_fields(gstr2a_rec, ewb_rec, config.normalizer.amount_tolerance)
                diff = max(diff, tax_diff)
                if not tax_ok:
                    result_type = ComparisonResultType.VALUE_MISMATCH
                    details["mismatch_kind"] = "tax"
                else:
                    inv_ok, inv_diff = compare_invoice_values(gstr2a_rec, ewb_rec, config.normalizer.amount_tolerance)
                    diff = max(diff, inv_diff)
                    if not inv_ok:
                        result_type = ComparisonResultType.VALUE_MISMATCH
                        details["mismatch_kind"] = "invoice_value"
                    elif gstr2a_rec.get("hsn") and ewb_rec.get("hsn") and gstr2a_rec["hsn"] != ewb_rec["hsn"]:
                        details["hsn_mismatch"] = True

        classified.append(_merge_record(gstr2a_rec, ewb_rec, result_type, config, diff, details))

        if progress_callback and (i % 50 == 0 or i == len(ewb_records) - 1):
            processed = i + 1
            pct = 10 + int((processed / max(len(ewb_records), 1)) * 70)
            progress_callback(
                percent=pct,
                stage="Purchase invoice matching",
                rows_processed=processed,
                rows_total=len(ewb_records),
                eta_seconds=int((len(ewb_records) - processed) * 0.001),
                checkpoint={
                    "ewb_index": i + 1,
                    "classified": [c.model_dump(mode="json") for c in classified],
                    "matched_gstr2a_keys": list(matched_gstr2a_keys),
                },
            )

    if progress_callback:
        progress_callback(percent=85, stage="Finding missing EWB inward records", rows_processed=len(ewb_records), rows_total=total_rows)

    for gstr2a_rec in gstr2a_records:
        key = gstr2a_rec["normalized_invoice"]
        if not key or key in matched_gstr2a_keys:
            continue
        if key in gstr2a_dupes and not any(c.normalized_invoice == key for c in classified):
            classified.append(_record_from_gstr2a(gstr2a_rec, ComparisonResultType.DUPLICATE, config))
            continue
        classified.append(_record_from_gstr2a(gstr2a_rec, ComparisonResultType.MISSING_IN_EWAY, config))

    summary = build_summary(
        classified,
        comparison_id=config.comparison_id,
        left_label=config.left_label,
        right_label=config.right_label,
        total_gstr1=len(gstr2a_records),
        total_eway=len(ewb_records),
    )
    summary.overall_risk_score = max((c.risk_score for c in classified), default=0)
    summary.risk_level = overall_risk_level([c.risk_score for c in classified])

    return ComparisonResult(
        session_id=session_id,
        comparison_id=config.comparison_id,
        status="completed",
        summary=summary,
        records=classified,
        observations=generate_purchase_observations(classified),
        completed_at=datetime.now(timezone.utc).isoformat(),
    )


def enqueue_gstr2a_eway_comparison(
    session_id: str,
    *,
    gstr2a_workbook_base64: str = "",
    ewb_inward_workbook_base64: str = "",
) -> dict:
    session = get_session(session_id)
    if not session:
        raise ValueError("Session not found")
    job = create_job(
        JobCreateRequest(
            session_id=session_id,
            job_type=JobType.COMPARISON,
            title="GSTR-2A ↔ EWB Inward Comparison",
            payload={
                "comparison_id": COMPARISON_ID,
                "gstr2a_workbook_base64": gstr2a_workbook_base64,
                "ewb_inward_workbook_base64": ewb_inward_workbook_base64,
            },
        )
    )
    set_comparison_status(session_id, "running")
    return {"job_id": job.job_id, "status": job.status.value, "session_id": session_id, "comparison_id": COMPARISON_ID}


def run_gstr2a_eway_comparison_with_progress(
    session_id: str,
    *,
    gstr1_workbook_base64: str = "",
    ewb_outward_workbook_base64: str = "",
    progress_callback: Optional[Callable] = None,
    checkpoint: Optional[dict] = None,
    job_id: Optional[str] = None,
    **kwargs,
) -> ComparisonResult:
    """Background job entry point — reads GSTR-2A payload via job_id when needed."""
    from services.job_service import _is_cancelled

    session = get_session(session_id)
    if not session:
        raise ValueError("Session not found")

    gstr2a_bytes, ewb_bytes = _resolve_workbooks(
        session_id,
        gstr2a_workbook_base64=kwargs.get("gstr2a_workbook_base64", ""),
        ewb_inward_workbook_base64=kwargs.get("ewb_inward_workbook_base64", ""),
        job_id=job_id,
    )

    ok, message = validate_workbook_pair(gstr2a_bytes, ewb_bytes)
    if not ok:
        set_comparison_status(session_id, "ready")
        raise ValueError(message)

    restored_checkpoint = None
    if checkpoint and checkpoint.get("classified"):
        restored_checkpoint = {
            "ewb_index": checkpoint.get("ewb_index", 0),
            "matched_gstr2a_keys": checkpoint.get("matched_gstr2a_keys", []),
            "classified": [ComparisonRecord.model_validate(c) for c in checkpoint["classified"]],
        }

    def cancel_check() -> bool:
        return bool(job_id and _is_cancelled(job_id))

    result = _engine.run(
        COMPARISON_ID,
        gstr2a_bytes,
        ewb_bytes,
        session_id,
        progress_callback=progress_callback,
        checkpoint=restored_checkpoint,
        cancel_check=cancel_check,
    )
    save_result(result)
    return result


def run_gstr2a_eway_comparison_sync(session_id: str, **kwargs) -> ComparisonResult:
    result = run_gstr2a_eway_comparison_with_progress(session_id, **kwargs)
    from intelligence.intelligence_service import analyze_session
    from services.investigation_service import enrich_cases_from_intelligence, sync_cases_from_comparison

    sync_cases_from_comparison(session_id)
    analyze_session(session_id, force=True)
    enrich_cases_from_intelligence(session_id)
    session = get_session(session_id)
    if session:
        session = apply_result_to_session(session, result)
        upsert_session(session)
    return result


def _merge_record(
    gstr2a_rec: dict,
    ewb_rec: dict,
    result_type: ComparisonResultType,
    config: ComparisonConfig,
    diff: float = 0.0,
    details: Optional[dict] = None,
) -> ComparisonRecord:
    rec = ComparisonRecord(
        result_type=result_type,
        invoice_number=gstr2a_rec.get("invoice_number") or ewb_rec.get("invoice_number", ""),
        normalized_invoice=gstr2a_rec.get("normalized_invoice") or ewb_rec.get("normalized_invoice", ""),
        gstin_gstr1=gstr2a_rec.get("gstin", ""),
        gstin_eway=ewb_rec.get("gstin", ""),
        date_gstr1=gstr2a_rec.get("invoice_date", ""),
        date_eway=ewb_rec.get("invoice_date", ""),
        taxable_value_gstr1=float(gstr2a_rec.get("taxable_value", 0)),
        taxable_value_eway=float(ewb_rec.get("taxable_value", 0)),
        invoice_value_gstr1=float(gstr2a_rec.get("invoice_value", 0)),
        invoice_value_eway=float(ewb_rec.get("invoice_value", 0)),
        igst_gstr1=float(gstr2a_rec.get("igst", 0)),
        igst_eway=float(ewb_rec.get("igst", 0)),
        cgst_gstr1=float(gstr2a_rec.get("cgst", 0)),
        cgst_eway=float(ewb_rec.get("cgst", 0)),
        sgst_gstr1=float(gstr2a_rec.get("sgst", 0)),
        sgst_eway=float(ewb_rec.get("sgst", 0)),
        difference_amount=diff,
        source_period=gstr2a_rec.get("source_period") or ewb_rec.get("source_period", ""),
        ewb_number=ewb_rec.get("ewb_number", ""),
        details=details or {},
    )
    rec.risk_score = score_result(result_type, diff)
    return rec


def _record_from_ewb(
    ewb_rec: dict,
    result_type: ComparisonResultType,
    config: ComparisonConfig,
    reason: str = "",
) -> ComparisonRecord:
    details = {"reason": reason} if reason else {}
    rec = ComparisonRecord(
        result_type=result_type,
        invoice_number=ewb_rec.get("invoice_number", ""),
        normalized_invoice=ewb_rec.get("normalized_invoice", ""),
        gstin_eway=ewb_rec.get("gstin", ""),
        date_eway=ewb_rec.get("invoice_date", ""),
        taxable_value_eway=float(ewb_rec.get("taxable_value", 0)),
        invoice_value_eway=float(ewb_rec.get("invoice_value", 0)),
        source_period=ewb_rec.get("source_period", ""),
        ewb_number=ewb_rec.get("ewb_number", ""),
        details=details,
    )
    rec.risk_score = score_result(result_type)
    return rec


def _record_from_gstr2a(gstr2a_rec: dict, result_type: ComparisonResultType, config: ComparisonConfig) -> ComparisonRecord:
    rec = ComparisonRecord(
        result_type=result_type,
        invoice_number=gstr2a_rec.get("invoice_number", ""),
        normalized_invoice=gstr2a_rec.get("normalized_invoice", ""),
        gstin_gstr1=gstr2a_rec.get("gstin", ""),
        date_gstr1=gstr2a_rec.get("invoice_date", ""),
        taxable_value_gstr1=float(gstr2a_rec.get("taxable_value", 0)),
        invoice_value_gstr1=float(gstr2a_rec.get("invoice_value", 0)),
        source_period=gstr2a_rec.get("source_period", ""),
        details={"purchase_record": True},
    )
    rec.risk_score = score_result(result_type)
    return rec
