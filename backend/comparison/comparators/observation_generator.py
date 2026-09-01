"""Rule-based audit observation generator."""

from __future__ import annotations

from typing import List

from comparison.comparison_types import ComparisonResultType
from comparison.result_models import AuditObservation, ComparisonRecord


def generate_observations(records: List[ComparisonRecord], limit: int = 50) -> List[AuditObservation]:
    observations: List[AuditObservation] = []
    for rec in records:
        if rec.result_type == ComparisonResultType.MATCHED:
            continue
        obs = _observation_for(rec)
        if obs:
            observations.append(obs)
        if len(observations) >= limit:
            break
    return observations


def _observation_for(rec: ComparisonRecord) -> AuditObservation | None:
    inv = rec.invoice_number or rec.normalized_invoice or "Unknown"
    if rec.result_type == ComparisonResultType.MISSING_IN_GSTR1:
        return AuditObservation(
            invoice_number=inv,
            result_type=rec.result_type,
            observation=f"Invoice {inv} exists in E-Way Bill but is missing in GSTR-1.",
            possible_reasons=[
                "Invoice omitted from GSTR-1",
                "Wrong upload period",
                "Return amendment pending",
            ],
            officer_action="Verify Books, Sales Register, and supporting documents.",
        )
    if rec.result_type == ComparisonResultType.MISSING_IN_EWAY:
        return AuditObservation(
            invoice_number=inv,
            result_type=rec.result_type,
            observation=f"Invoice {inv} exists in GSTR-1 but is missing in E-Way Bill outward register.",
            possible_reasons=[
                "E-Way Bill not generated",
                "Exempt / non-EWB movement",
                "Wrong EWB upload",
            ],
            officer_action="Verify dispatch records and E-Way Bill portal.",
        )
    if rec.result_type == ComparisonResultType.GSTIN_MISMATCH:
        return AuditObservation(
            invoice_number=inv,
            result_type=rec.result_type,
            observation=f"Invoice {inv} has GSTIN mismatch between GSTR-1 ({rec.gstin_gstr1}) and EWB ({rec.gstin_eway}).",
            possible_reasons=["Data entry error", "Wrong party mapped", "Branch transfer"],
            officer_action="Verify recipient GSTIN in invoice and E-Way Bill.",
        )
    if rec.result_type == ComparisonResultType.VALUE_MISMATCH:
        return AuditObservation(
            invoice_number=inv,
            result_type=rec.result_type,
            observation=f"Invoice {inv} has value difference of {rec.difference_amount:.2f} between GSTR-1 and EWB.",
            possible_reasons=["Rounding difference", "Amended invoice", "Freight included in EWB"],
            officer_action="Verify taxable value and invoice value in both records.",
        )
    if rec.result_type == ComparisonResultType.DATE_MISMATCH:
        return AuditObservation(
            invoice_number=inv,
            result_type=rec.result_type,
            observation=f"Invoice {inv} has date mismatch: GSTR-1 ({rec.date_gstr1}) vs EWB ({rec.date_eway}).",
            possible_reasons=["Backdated invoice", "EWB generated on different date"],
            officer_action="Verify invoice date and E-Way Bill date.",
        )
    if rec.result_type == ComparisonResultType.DUPLICATE:
        return AuditObservation(
            invoice_number=inv,
            result_type=rec.result_type,
            observation=f"Invoice {inv} appears more than once in uploaded data.",
            possible_reasons=["Duplicate upload", "Amended return not removed"],
            officer_action="Verify duplicate entries and retain latest record.",
        )
    return AuditObservation(
        invoice_number=inv,
        result_type=rec.result_type,
        observation=f"Invoice {inv} requires manual review ({rec.result_type.value}).",
        possible_reasons=["Unclassified discrepancy"],
        officer_action="Review source workbooks.",
    )
