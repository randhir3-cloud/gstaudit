"""Synthetic comparison results for MSAE tests."""

from __future__ import annotations

from comparison.comparison_types import ComparisonResultType, RiskLevel
from comparison.result_models import ComparisonRecord, ComparisonResult, ComparisonSummary

SESSION = "session_msae_test"


def build_gstr1_result(session_id: str = SESSION) -> ComparisonResult:
    records = [
        ComparisonRecord(
            result_type=ComparisonResultType.MATCHED,
            invoice_number="INV-1045",
            normalized_invoice="INV1045",
            gstin_gstr1="03AABCU9603R1ZX",
            gstin_eway="29AABCT1332L000",
            source_period="May 2023",
        ),
        ComparisonRecord(
            result_type=ComparisonResultType.MISSING_IN_GSTR1,
            invoice_number="INV-1045",
            normalized_invoice="INV1045",
            gstin_gstr1="",
            gstin_eway="29AABCT1332L000",
            invoice_value_eway=118000,
            taxable_value_eway=100000,
            difference_amount=118000,
            risk_score=85,
            source_period="May 2023",
            ewb_number="201581579045",
        ),
        ComparisonRecord(
            result_type=ComparisonResultType.MISSING_IN_EWAY,
            invoice_number="INV-2001",
            normalized_invoice="INV2001",
            gstin_gstr1="03AABCU9603R1ZX",
            invoice_value_gstr1=50000,
            taxable_value_gstr1=42373,
            difference_amount=50000,
            risk_score=60,
            source_period="June 2023",
        ),
    ]
    return ComparisonResult(
        session_id=session_id,
        comparison_id="gstr1_ewb_outward",
        status="completed",
        summary=ComparisonSummary(
            comparison_id="gstr1_ewb_outward",
            matched_count=1,
            missing_in_gstr1_count=1,
            missing_in_eway_count=1,
            overall_risk_score=75,
            risk_level=RiskLevel.HIGH,
            total_gstr1_records=2,
            total_eway_records=2,
        ),
        records=records,
    )


def build_gstr2a_result(session_id: str = SESSION) -> ComparisonResult:
    records = [
        ComparisonRecord(
            result_type=ComparisonResultType.MISSING_IN_GSTR1,
            invoice_number="PINV-1045",
            normalized_invoice="PINV1045",
            gstin_gstr1="29AABCT1332L000",
            gstin_eway="03AABCU9603R1ZX",
            invoice_value_eway=118000,
            taxable_value_eway=100000,
            difference_amount=118000,
            risk_score=80,
            source_period="May 2023",
            ewb_number="201581579045",
        ),
        ComparisonRecord(
            result_type=ComparisonResultType.GSTIN_MISMATCH,
            invoice_number="PINV-300",
            normalized_invoice="PINV300",
            gstin_gstr1="29AABCT1332L000",
            gstin_eway="29AABCT9999L999",
            difference_amount=5000,
            risk_score=55,
            source_period="May 2023",
        ),
        ComparisonRecord(
            result_type=ComparisonResultType.GSTIN_MISMATCH,
            invoice_number="PINV-301",
            normalized_invoice="PINV301",
            gstin_gstr1="29AABCT1332L000",
            gstin_eway="29AABCT9999L999",
            difference_amount=3000,
            risk_score=50,
            source_period="May 2023",
        ),
    ]
    return ComparisonResult(
        session_id=session_id,
        comparison_id="gstr2a_ewb_inward",
        status="completed",
        summary=ComparisonSummary(
            comparison_id="gstr2a_ewb_inward",
            left_label="GSTR-2A",
            right_label="EWB INWARD",
            missing_in_gstr1_count=1,
            gstin_mismatch_count=2,
            overall_risk_score=70,
            risk_level=RiskLevel.HIGH,
            total_gstr1_records=3,
            total_eway_records=2,
        ),
        records=records,
    )
