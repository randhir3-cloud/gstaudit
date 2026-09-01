"""Purchase-specific intelligence and officer observations for GSTR-2A plugin."""

from __future__ import annotations

from typing import List

from comparison.comparators.observation_generator import generate_observations
from comparison.comparison_types import ComparisonResultType
from comparison.result_models import AuditObservation, ComparisonRecord

PURCHASE_DOCUMENTS = {
    ComparisonResultType.MISSING_IN_GSTR1: [
        "Purchase register",
        "Supplier tax invoice",
        "E-Way Bill inward copy",
        "GSTR-2A download",
    ],
    ComparisonResultType.MISSING_IN_EWAY: [
        "GSTR-2A B2B sheet",
        "Supplier invoice",
        "Delivery challan",
        "Books of account",
    ],
    ComparisonResultType.GSTIN_MISMATCH: [
        "Supplier GST registration certificate",
        "Purchase invoice",
        "E-Way Bill",
    ],
    ComparisonResultType.VALUE_MISMATCH: [
        "Purchase invoice",
        "Debit/credit note",
        "ITC ledger",
        "E-Way Bill tax breakup",
    ],
    ComparisonResultType.DATE_MISMATCH: [
        "Invoice date proof",
        "E-Way Bill validity record",
        "Goods receipt note",
    ],
}


def _priority_hint(risk_score: int) -> str:
    if risk_score >= 95:
        return "Critical"
    if risk_score >= 70:
        return "High"
    if risk_score >= 40:
        return "Medium"
    return "Low"


def generate_purchase_observations(records: List[ComparisonRecord], limit: int = 100) -> List[AuditObservation]:
    base = generate_observations(records, limit=limit)
    enriched: List[AuditObservation] = []
    rec_map = {r.normalized_invoice: r for r in records if r.normalized_invoice}

    for obs in base:
        rec = rec_map.get(obs.invoice_number) or next((r for r in records if r.invoice_number == obs.invoice_number), None)
        docs = PURCHASE_DOCUMENTS.get(obs.result_type, ["Purchase invoice", "E-Way Bill inward", "GSTR-2A"])
        causes = list(obs.possible_reasons)
        if rec and rec.details.get("mismatch_kind") == "tax":
            causes.insert(0, "IGST/CGST/SGST breakup differs between GSTR-2A and inward EWB")
        if rec and rec.details.get("mismatch_kind") == "invoice_value":
            causes.insert(0, "Invoice value differs though taxable value may match")
        if obs.result_type == ComparisonResultType.MISSING_IN_GSTR1:
            observation = obs.observation.replace("GSTR-1", "GSTR-2A").replace("E-Way Bill", "E-Way Bill inward")
            action = "Verify purchase register, supplier invoice, and inward movement records."
        elif obs.result_type == ComparisonResultType.MISSING_IN_EWAY:
            observation = obs.observation.replace("GSTR-1", "GSTR-2A").replace("outward", "inward")
            action = "Verify inward E-Way Bill generation and supplier dispatch records."
        else:
            observation = obs.observation.replace("GSTR-1", "GSTR-2A")
            action = obs.officer_action

        enriched.append(
            AuditObservation(
                invoice_number=obs.invoice_number,
                result_type=obs.result_type,
                observation=observation,
                possible_reasons=causes[:4],
                officer_action=f"{action} Priority: {_priority_hint(rec.risk_score if rec else 0)}. Documents: {', '.join(docs[:3])}.",
            )
        )
    return enriched
