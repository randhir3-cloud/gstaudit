"""Reference comparator: GSTR-1 vs EWB Outward."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Set

from comparison.comparators.date_matcher import compare_dates
from comparison.comparators.duplicate_matcher import find_duplicate_keys
from comparison.comparators.gstin_matcher import gstins_match
from comparison.comparators.invoice_matcher import build_invoice_index
from comparison.comparators.observation_generator import generate_observations
from comparison.comparators.risk_engine import overall_risk_level, score_result
from comparison.comparators.summary_builder import build_summary
from comparison.comparators.value_matcher import compare_values
from comparison.comparison_types import ComparisonResultType
from comparison.data_loader import load_eway_outward_records, load_gstr1_records
from comparison.models import ComparisonConfig
from comparison.result_models import ComparisonRecord, ComparisonResult


def compare_gstr1_vs_eway_outward(
    config: ComparisonConfig,
    gstr1_bytes: bytes,
    ewb_bytes: bytes,
    session_id: str,
    *,
    progress_callback=None,
    checkpoint: dict | None = None,
    cancel_check=None,
) -> ComparisonResult:
    gstr1_records = load_gstr1_records(gstr1_bytes)
    eway_records = load_eway_outward_records(ewb_bytes)

    total_rows = len(gstr1_records) + len(eway_records)
    if progress_callback:
        progress_callback(percent=10, stage="Building indexes", rows_processed=0, rows_total=total_rows)

    gstr1_dupes = find_duplicate_keys(gstr1_records)
    eway_dupes = find_duplicate_keys(eway_records)

    gstr1_index = build_invoice_index(gstr1_records)
    eway_index = build_invoice_index(eway_records)

    classified: List[ComparisonRecord] = []
    matched_gstr1_keys: Set[str] = set()
    if checkpoint:
        raw = checkpoint.get("classified", [])
        for item in raw:
            classified.append(item if isinstance(item, ComparisonRecord) else ComparisonRecord.model_validate(item))
        matched_gstr1_keys = set(checkpoint.get("matched_gstr1_keys", []))
    start_index = int(checkpoint.get("eway_index", 0)) if checkpoint else 0

    for i, eway_rec in enumerate(eway_records):
        if i < start_index:
            continue
        if cancel_check and cancel_check():
            raise InterruptedError("Job cancelled")

        key = eway_rec["normalized_invoice"]
        if not key:
            continue
        if key in eway_dupes:
            classified.append(_record_from_eway(eway_rec, ComparisonResultType.DUPLICATE, config))
            continue

        gstr1_matches = gstr1_index.get(key, [])
        if len(gstr1_matches) > 1:
            classified.append(_record_from_eway(eway_rec, ComparisonResultType.MULTIPLE_MATCHES, config))
            continue
        if not gstr1_matches:
            classified.append(_record_from_eway(eway_rec, ComparisonResultType.MISSING_IN_GSTR1, config))
            continue

        gstr1_rec = gstr1_matches[0]
        matched_gstr1_keys.add(key)
        if key in gstr1_dupes:
            classified.append(_merge_record(gstr1_rec, eway_rec, ComparisonResultType.DUPLICATE, config))
            continue

        result_type = ComparisonResultType.MATCHED
        diff = 0.0
        if not gstins_match(gstr1_rec.get("gstin", ""), eway_rec.get("gstin", "")):
            result_type = ComparisonResultType.GSTIN_MISMATCH
        elif not compare_dates(gstr1_rec.get("invoice_date"), eway_rec.get("invoice_date"), config.normalizer):
            result_type = ComparisonResultType.DATE_MISMATCH
        else:
            values_ok, diff = compare_values(gstr1_rec, eway_rec, config.normalizer)
            if not values_ok:
                result_type = ComparisonResultType.VALUE_MISMATCH

        classified.append(_merge_record(gstr1_rec, eway_rec, result_type, config, diff))

        if progress_callback and (i % 50 == 0 or i == len(eway_records) - 1):
            processed = i + 1
            pct = 10 + int((processed / max(len(eway_records), 1)) * 70)
            remaining = len(eway_records) - processed
            eta = int(remaining * 0.001) if remaining else 0
            progress_callback(
                percent=pct,
                stage="Invoice Matching",
                rows_processed=processed,
                rows_total=len(eway_records),
                eta_seconds=eta,
                checkpoint={
                    "eway_index": i + 1,
                    "classified": [c.model_dump(mode="json") for c in classified],
                    "matched_gstr1_keys": list(matched_gstr1_keys),
                },
            )

    if progress_callback:
        progress_callback(percent=85, stage="Finding missing EWB records", rows_processed=len(eway_records), rows_total=total_rows)

    for gstr1_rec in gstr1_records:
        key = gstr1_rec["normalized_invoice"]
        if not key or key in matched_gstr1_keys:
            continue
        if key in gstr1_dupes and not any(c.normalized_invoice == key for c in classified):
            classified.append(_record_from_gstr1(gstr1_rec, ComparisonResultType.DUPLICATE, config))
            continue
        if not any(c.normalized_invoice == key and c.result_type == ComparisonResultType.MISSING_IN_GSTR1 for c in classified):
            classified.append(_record_from_gstr1(gstr1_rec, ComparisonResultType.MISSING_IN_EWAY, config))

    summary = build_summary(
        classified,
        comparison_id=config.comparison_id,
        left_label=config.left_label,
        right_label=config.right_label,
        total_gstr1=len(gstr1_records),
        total_eway=len(eway_records),
    )
    summary.overall_risk_score = max((c.risk_score for c in classified), default=0)
    summary.risk_level = overall_risk_level([c.risk_score for c in classified])

    return ComparisonResult(
        session_id=session_id,
        comparison_id=config.comparison_id,
        status="completed",
        summary=summary,
        records=classified,
        observations=generate_observations(classified),
        completed_at=datetime.now(timezone.utc).isoformat(),
    )


def _merge_record(gstr1_rec: dict, eway_rec: dict, result_type: ComparisonResultType, config: ComparisonConfig, diff: float = 0.0) -> ComparisonRecord:
    rec = ComparisonRecord(
        result_type=result_type,
        invoice_number=gstr1_rec.get("invoice_number") or eway_rec.get("invoice_number", ""),
        normalized_invoice=gstr1_rec.get("normalized_invoice") or eway_rec.get("normalized_invoice", ""),
        gstin_gstr1=gstr1_rec.get("gstin", ""),
        gstin_eway=eway_rec.get("gstin", ""),
        date_gstr1=gstr1_rec.get("invoice_date", ""),
        date_eway=eway_rec.get("invoice_date", ""),
        taxable_value_gstr1=float(gstr1_rec.get("taxable_value", 0)),
        taxable_value_eway=float(eway_rec.get("taxable_value", 0)),
        invoice_value_gstr1=float(gstr1_rec.get("invoice_value", 0)),
        invoice_value_eway=float(eway_rec.get("invoice_value", 0)),
        igst_gstr1=float(gstr1_rec.get("igst", 0)),
        igst_eway=float(eway_rec.get("igst", 0)),
        cgst_gstr1=float(gstr1_rec.get("cgst", 0)),
        cgst_eway=float(eway_rec.get("cgst", 0)),
        sgst_gstr1=float(gstr1_rec.get("sgst", 0)),
        sgst_eway=float(eway_rec.get("sgst", 0)),
        difference_amount=diff,
        source_period=gstr1_rec.get("source_period") or eway_rec.get("source_period", ""),
        ewb_number=eway_rec.get("ewb_number", ""),
    )
    rec.risk_score = score_result(result_type, diff)
    return rec


def _record_from_eway(eway_rec: dict, result_type: ComparisonResultType, config: ComparisonConfig) -> ComparisonRecord:
    rec = ComparisonRecord(
        result_type=result_type,
        invoice_number=eway_rec.get("invoice_number", ""),
        normalized_invoice=eway_rec.get("normalized_invoice", ""),
        gstin_eway=eway_rec.get("gstin", ""),
        date_eway=eway_rec.get("invoice_date", ""),
        taxable_value_eway=float(eway_rec.get("taxable_value", 0)),
        invoice_value_eway=float(eway_rec.get("invoice_value", 0)),
        source_period=eway_rec.get("source_period", ""),
        ewb_number=eway_rec.get("ewb_number", ""),
    )
    rec.risk_score = score_result(result_type)
    return rec


def _record_from_gstr1(gstr1_rec: dict, result_type: ComparisonResultType, config: ComparisonConfig) -> ComparisonRecord:
    rec = ComparisonRecord(
        result_type=result_type,
        invoice_number=gstr1_rec.get("invoice_number", ""),
        normalized_invoice=gstr1_rec.get("normalized_invoice", ""),
        gstin_gstr1=gstr1_rec.get("gstin", ""),
        date_gstr1=gstr1_rec.get("invoice_date", ""),
        taxable_value_gstr1=float(gstr1_rec.get("taxable_value", 0)),
        invoice_value_gstr1=float(gstr1_rec.get("invoice_value", 0)),
        source_period=gstr1_rec.get("source_period", ""),
    )
    rec.risk_score = score_result(result_type)
    return rec
