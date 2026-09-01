"""Purchase Register comparison engine — GSTR-2A and EWB Inward."""

from __future__ import annotations

import base64
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
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

_PLUGIN_DIR = Path(__file__).resolve().parent


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _PLUGIN_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_loader = _load_module("purchase_loader", "loader.py")
_intelligence = _load_module("purchase_intelligence", "intelligence.py")

load_purchase_register_records = _loader.load_purchase_register_records
load_gstr2a_records = _loader.load_gstr2a_records
load_eway_inward_records = _loader.load_eway_inward_records
validate_purchase_gstr2a_pair = _loader.validate_purchase_gstr2a_pair
validate_purchase_ewb_pair = _loader.validate_purchase_ewb_pair
compare_tax_fields = _load_module("purchase_gstr2a_v", str(_PLUGIN_DIR.parent / "gstr2a" / "validators.py")).compare_tax_fields
compare_invoice_values = _load_module("purchase_gstr2a_v2", str(_PLUGIN_DIR.parent / "gstr2a" / "validators.py")).compare_invoice_values
generate_purchase_register_observations = _intelligence.generate_purchase_register_observations

COMPARISON_ID_GSTR2A = "purchase_register_vs_gstr2a"
COMPARISON_ID_EWB = "purchase_register_vs_ewb_inward"

PURCHASE_GSTR2A_CONFIG = ComparisonConfig(
    comparison_id=COMPARISON_ID_GSTR2A,
    left_dataset="purchase_register",
    right_dataset="gstr2a",
    left_label="PURCHASE REGISTER",
    right_label="GSTR-2A",
    normalizer=NormalizerConfig(amount_tolerance=1.0, date_tolerance_days=1),
)

PURCHASE_EWB_CONFIG = ComparisonConfig(
    comparison_id=COMPARISON_ID_EWB,
    left_dataset="purchase_register",
    right_dataset="ewb_inward",
    left_label="PURCHASE REGISTER",
    right_label="EWB INWARD",
    normalizer=NormalizerConfig(amount_tolerance=1.0, date_tolerance_days=1),
)

_engine = ComparisonEngine()

RESULT_LABELS = {
    ComparisonResultType.MISSING_IN_GSTR1: "Missing in Purchase Register",
    ComparisonResultType.MISSING_IN_EWAY: "Missing in counterparty",
    ComparisonResultType.GSTIN_MISMATCH: "Supplier GSTIN mismatch",
    ComparisonResultType.VALUE_MISMATCH: "Tax/Value mismatch",
    ComparisonResultType.DATE_MISMATCH: "Date mismatch",
    ComparisonResultType.DUPLICATE: "Duplicate",
    ComparisonResultType.MULTIPLE_MATCHES: "Multiple matches",
}


def _decode_b64(data: str) -> bytes:
    return base64.b64decode(data)


def _resolve_workbooks(
    session_id: str,
    *,
    right_key: str = "gstr2a",
    job_id: Optional[str] = None,
    purchase_b64_key: str = "purchase_register_workbook_base64",
    right_b64_key: str = "gstr2a_workbook_base64",
    purchase_register_workbook_base64: str = "",
    right_workbook_base64: str = "",
) -> tuple[bytes, bytes]:
    purchase_bytes = get_workbook(session_id, "purchase_register")
    right_bytes = get_workbook(session_id, right_key)

    if job_id:
        from services.job_service import get_job

        job = get_job(job_id)
        if job and job.payload:
            purchase_register_workbook_base64 = purchase_register_workbook_base64 or job.payload.get(purchase_b64_key, "")
            right_workbook_base64 = right_workbook_base64 or job.payload.get(right_b64_key, "")

    if purchase_register_workbook_base64:
        purchase_bytes = _decode_b64(purchase_register_workbook_base64)
        cache_workbook(session_id, "purchase_register", purchase_bytes)
    if right_workbook_base64:
        right_bytes = _decode_b64(right_workbook_base64)
        cache_workbook(session_id, right_key, right_bytes)

    return purchase_bytes, right_bytes


def compare_purchase_vs_gstr2a(
    config: ComparisonConfig,
    purchase_bytes: bytes,
    gstr2a_bytes: bytes,
    session_id: str,
    *,
    progress_callback=None,
    checkpoint: dict | None = None,
    cancel_check=None,
) -> ComparisonResult:
    return _compare_purchase_vs_right(
        config,
        purchase_bytes,
        gstr2a_bytes,
        session_id,
        load_purchase_register_records,
        load_gstr2a_records,
        right_source="gstr2a",
        missing_right_label="Missing in GSTR-2A",
        progress_callback=progress_callback,
        checkpoint=checkpoint,
        cancel_check=cancel_check,
    )


def compare_purchase_vs_ewb_inward(
    config: ComparisonConfig,
    purchase_bytes: bytes,
    ewb_bytes: bytes,
    session_id: str,
    *,
    progress_callback=None,
    checkpoint: dict | None = None,
    cancel_check=None,
) -> ComparisonResult:
    return _compare_purchase_vs_right(
        config,
        purchase_bytes,
        ewb_bytes,
        session_id,
        load_purchase_register_records,
        load_eway_inward_records,
        right_source="ewb_inward",
        missing_right_label="Missing in EWB",
        progress_callback=progress_callback,
        checkpoint=checkpoint,
        cancel_check=cancel_check,
    )


def _compare_purchase_vs_right(
    config: ComparisonConfig,
    purchase_bytes: bytes,
    right_bytes: bytes,
    session_id: str,
    load_left_fn,
    load_right_fn,
    *,
    right_source: str,
    missing_right_label: str,
    progress_callback=None,
    checkpoint: dict | None = None,
    cancel_check=None,
) -> ComparisonResult:
    left_records = load_left_fn(purchase_bytes)
    right_records = load_right_fn(right_bytes)

    left_dupes = find_duplicate_keys(left_records)
    right_dupes = find_duplicate_keys(right_records)
    left_index = build_invoice_index(left_records)
    right_index = build_invoice_index(right_records)

    classified: List[ComparisonRecord] = []
    matched_left_keys: Set[str] = set()

    for right_rec in right_records:
        if cancel_check and cancel_check():
            raise InterruptedError("Job cancelled")

        key = right_rec["normalized_invoice"]
        if not key:
            classified.append(_record_from_right(right_rec, ComparisonResultType.UNKNOWN, right_source, reason="missing_invoice"))
            continue
        if key in right_dupes:
            classified.append(_record_from_right(right_rec, ComparisonResultType.DUPLICATE, right_source))
            continue

        left_matches = left_index.get(key, [])
        if len(left_matches) > 1:
            classified.append(_record_from_right(right_rec, ComparisonResultType.MULTIPLE_MATCHES, right_source))
            continue
        if not left_matches:
            rec = _record_from_right(right_rec, ComparisonResultType.MISSING_IN_GSTR1, right_source)
            rec.details["result_label"] = "Missing in Purchase Register"
            classified.append(rec)
            continue

        left_rec = left_matches[0]
        matched_left_keys.add(key)
        result_type = ComparisonResultType.MATCHED
        diff = 0.0
        details: dict = {"left_source": "purchase_register", "right_source": right_source}

        if not gstins_match(left_rec.get("gstin", ""), right_rec.get("gstin", "")):
            result_type = ComparisonResultType.GSTIN_MISMATCH
            details["result_label"] = "Supplier GSTIN mismatch"
        elif not compare_dates(left_rec.get("invoice_date"), right_rec.get("invoice_date"), config.normalizer):
            result_type = ComparisonResultType.DATE_MISMATCH
            details["result_label"] = "Date mismatch"
        else:
            taxable_ok, diff = compare_values(
                {**left_rec, "invoice_value": left_rec.get("taxable_value", 0)},
                {**right_rec, "invoice_value": right_rec.get("taxable_value", 0)},
                config.normalizer,
            )
            if not taxable_ok:
                result_type = ComparisonResultType.VALUE_MISMATCH
                details["mismatch_kind"] = "taxable_value"
                details["result_label"] = "Value mismatch"
            else:
                tax_ok, tax_diff = compare_tax_fields(left_rec, right_rec, config.normalizer.amount_tolerance)
                diff = max(diff, tax_diff)
                if not tax_ok:
                    result_type = ComparisonResultType.VALUE_MISMATCH
                    details["mismatch_kind"] = "tax"
                    details["result_label"] = "Tax mismatch"
                else:
                    inv_ok, inv_diff = compare_invoice_values(left_rec, right_rec, config.normalizer.amount_tolerance)
                    diff = max(diff, inv_diff)
                    if not inv_ok:
                        result_type = ComparisonResultType.VALUE_MISMATCH
                        details["mismatch_kind"] = "invoice_value"
                        details["result_label"] = "Value mismatch"

        classified.append(_merge_record(left_rec, right_rec, result_type, config, diff, details, right_source))

    for left_rec in left_records:
        key = left_rec["normalized_invoice"]
        if not key or key in matched_left_keys:
            continue
        rec = _record_from_left(left_rec, ComparisonResultType.MISSING_IN_EWAY, config, right_source)
        rec.details["result_label"] = missing_right_label
        classified.append(rec)

    summary = build_summary(
        classified,
        comparison_id=config.comparison_id,
        left_label=config.left_label,
        right_label=config.right_label,
        total_gstr1=len(left_records),
        total_eway=len(right_records),
    )
    summary.overall_risk_score = max((c.risk_score for c in classified), default=0)
    summary.risk_level = overall_risk_level([c.risk_score for c in classified])

    return ComparisonResult(
        session_id=session_id,
        comparison_id=config.comparison_id,
        status="completed",
        summary=summary,
        records=classified,
        observations=generate_purchase_register_observations(classified, right_source),
        completed_at=datetime.now(timezone.utc).isoformat(),
    )


def _merge_record(left, right, result_type, config, diff, details, right_source) -> ComparisonRecord:
    rec = ComparisonRecord(
        result_type=result_type,
        invoice_number=left.get("invoice_number") or right.get("invoice_number", ""),
        normalized_invoice=left.get("normalized_invoice") or right.get("normalized_invoice", ""),
        gstin_gstr1=left.get("gstin", ""),
        gstin_eway=right.get("gstin", ""),
        date_gstr1=left.get("invoice_date", ""),
        date_eway=right.get("invoice_date", ""),
        taxable_value_gstr1=float(left.get("taxable_value", 0)),
        taxable_value_eway=float(right.get("taxable_value", 0)),
        invoice_value_gstr1=float(left.get("invoice_value", 0)),
        invoice_value_eway=float(right.get("invoice_value", 0)),
        igst_gstr1=float(left.get("igst", 0)),
        igst_eway=float(right.get("igst", 0)),
        cgst_gstr1=float(left.get("cgst", 0)),
        cgst_eway=float(right.get("cgst", 0)),
        sgst_gstr1=float(left.get("sgst", 0)),
        sgst_eway=float(right.get("sgst", 0)),
        difference_amount=diff,
        source_period=left.get("source_period") or right.get("source_period", ""),
        ewb_number=right.get("ewb_number", ""),
        details={**details, "supplier_name": left.get("supplier_name", ""), "plugin": "purchase"},
    )
    rec.risk_score = score_result(result_type, diff)
    return rec


def _record_from_right(right, result_type, right_source, reason="") -> ComparisonRecord:
    details = {"right_source": right_source, "left_source": "purchase_register", "plugin": "purchase"}
    if reason:
        details["reason"] = reason
    rec = ComparisonRecord(
        result_type=result_type,
        invoice_number=right.get("invoice_number", ""),
        normalized_invoice=right.get("normalized_invoice", ""),
        gstin_eway=right.get("gstin", ""),
        date_eway=right.get("invoice_date", ""),
        taxable_value_eway=float(right.get("taxable_value", 0)),
        invoice_value_eway=float(right.get("invoice_value", 0)),
        ewb_number=right.get("ewb_number", ""),
        details=details,
    )
    rec.risk_score = score_result(result_type)
    return rec


def _record_from_left(left, result_type, config, right_source) -> ComparisonRecord:
    rec = ComparisonRecord(
        result_type=result_type,
        invoice_number=left.get("invoice_number", ""),
        normalized_invoice=left.get("normalized_invoice", ""),
        gstin_gstr1=left.get("gstin", ""),
        date_gstr1=left.get("invoice_date", ""),
        taxable_value_gstr1=float(left.get("taxable_value", 0)),
        invoice_value_gstr1=float(left.get("invoice_value", 0)),
        details={"left_source": "purchase_register", "right_source": right_source, "plugin": "purchase"},
    )
    rec.risk_score = score_result(result_type)
    return rec


def enqueue_purchase_gstr2a_comparison(session_id: str, **payload) -> dict:
    return _enqueue(session_id, COMPARISON_ID_GSTR2A, "Purchase Register ↔ GSTR-2A Comparison", payload)


def enqueue_purchase_ewb_comparison(session_id: str, **payload) -> dict:
    return _enqueue(session_id, COMPARISON_ID_EWB, "Purchase Register ↔ EWB Inward Comparison", payload)


def _enqueue(session_id: str, comparison_id: str, title: str, payload: dict) -> dict:
    if not get_session(session_id):
        raise ValueError("Session not found")
    job = create_job(
        JobCreateRequest(
            session_id=session_id,
            job_type=JobType.COMPARISON,
            title=title,
            payload={"comparison_id": comparison_id, **payload},
        )
    )
    set_comparison_status(session_id, "running")
    return {"job_id": job.job_id, "status": job.status.value, "session_id": session_id, "comparison_id": comparison_id}


def run_purchase_gstr2a_with_progress(
    session_id: str,
    *,
    gstr1_workbook_base64: str = "",
    ewb_outward_workbook_base64: str = "",
    progress_callback: Optional[Callable] = None,
    checkpoint: Optional[dict] = None,
    job_id: Optional[str] = None,
    **kwargs,
) -> ComparisonResult:
    return _run_with_progress(
        session_id,
        COMPARISON_ID_GSTR2A,
        "gstr2a",
        validate_purchase_gstr2a_pair,
        progress_callback=progress_callback,
        checkpoint=checkpoint,
        job_id=job_id,
        right_b64_key="gstr2a_workbook_base64",
        purchase_register_workbook_base64=kwargs.get("purchase_register_workbook_base64", ""),
        right_workbook_base64=kwargs.get("gstr2a_workbook_base64", ""),
    )


def run_purchase_ewb_with_progress(
    session_id: str,
    *,
    gstr1_workbook_base64: str = "",
    ewb_outward_workbook_base64: str = "",
    progress_callback: Optional[Callable] = None,
    checkpoint: Optional[dict] = None,
    job_id: Optional[str] = None,
    **kwargs,
) -> ComparisonResult:
    return _run_with_progress(
        session_id,
        COMPARISON_ID_EWB,
        "ewb_inward",
        validate_purchase_ewb_pair,
        progress_callback=progress_callback,
        checkpoint=checkpoint,
        job_id=job_id,
        right_b64_key="ewb_inward_workbook_base64",
        purchase_register_workbook_base64=kwargs.get("purchase_register_workbook_base64", ""),
        right_workbook_base64=kwargs.get("ewb_inward_workbook_base64", ""),
    )


def _run_with_progress(
    session_id: str,
    comparison_id: str,
    right_key: str,
    validator,
    *,
    progress_callback=None,
    checkpoint=None,
    job_id=None,
    right_b64_key: str = "gstr2a_workbook_base64",
    purchase_register_workbook_base64: str = "",
    right_workbook_base64: str = "",
) -> ComparisonResult:
    purchase_bytes, right_bytes = _resolve_workbooks(
        session_id,
        right_key=right_key,
        job_id=job_id,
        right_b64_key=right_b64_key,
        purchase_register_workbook_base64=purchase_register_workbook_base64,
        right_workbook_base64=right_workbook_base64,
    )
    ok, message = validator(purchase_bytes, right_bytes)
    if not ok:
        set_comparison_status(session_id, "ready")
        raise ValueError(message)

    result = _engine.run(
        comparison_id,
        purchase_bytes,
        right_bytes,
        session_id,
        progress_callback=progress_callback,
        checkpoint=checkpoint,
    )
    save_result(result)

    session = get_session(session_id)
    if session:
        session = apply_result_to_session(session, result)
        upsert_session(session)

    return result


def run_purchase_gstr2a_sync(session_id: str, **kwargs) -> ComparisonResult:
    result = run_purchase_gstr2a_with_progress(session_id, **kwargs)
    from intelligence.intelligence_service import analyze_session
    from services.investigation_service import enrich_cases_from_intelligence, sync_cases_from_comparison

    sync_cases_from_comparison(session_id)
    analyze_session(session_id, force=True)
    enrich_cases_from_intelligence(session_id)
    return result
