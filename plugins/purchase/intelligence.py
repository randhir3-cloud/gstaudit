"""Purchase Register intelligence — risk, priority, documents, officer observations."""

from __future__ import annotations

from typing import List

from comparison.comparators.observation_generator import generate_observations
from comparison.comparison_types import ComparisonResultType
from comparison.result_models import AuditObservation, ComparisonRecord

PURCHASE_REGISTER_DOCUMENTS = {
    ComparisonResultType.MISSING_IN_GSTR1: [
        "Purchase register",
        "Supplier tax invoice",
        "GSTR-2A download",
        "E-Way Bill inward copy",
    ],
    ComparisonResultType.MISSING_IN_EWAY: [
        "Purchase register",
        "GSTR-2A B2B sheet",
        "Supplier invoice",
        "Inward E-Way Bill",
    ],
    ComparisonResultType.GSTIN_MISMATCH: [
        "Supplier GST registration certificate",
        "Purchase invoice",
        "GSTR-2A supplier column",
    ],
    ComparisonResultType.VALUE_MISMATCH: [
        "Purchase invoice",
        "Debit/credit note",
        "ITC ledger",
        "GSTR-2A tax breakup",
    ],
    ComparisonResultType.DATE_MISMATCH: [
        "Invoice date proof",
        "Goods receipt note",
        "GSTR-2A filing period",
    ],
    ComparisonResultType.DUPLICATE: [
        "Purchase register duplicate rows",
        "Supplier invoice copies",
    ],
    ComparisonResultType.MULTIPLE_MATCHES: [
        "Purchase register",
        "Invoice numbering policy",
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


def _label_for_source(right_source: str) -> str:
    if right_source == "gstr2a":
        return "GSTR-2A"
    if right_source == "ewb_inward":
        return "EWB Inward"
    return right_source.replace("_", " ").upper()


def generate_purchase_register_observations(
    records: List[ComparisonRecord],
    right_source: str = "gstr2a",
    limit: int = 100,
) -> List[AuditObservation]:
    base = generate_observations(records, limit=limit)
    enriched: List[AuditObservation] = []
    rec_map = {r.normalized_invoice: r for r in records if r.normalized_invoice}
    counterparty = _label_for_source(right_source)

    for obs in base:
        rec = rec_map.get(obs.invoice_number) or next((r for r in records if r.invoice_number == obs.invoice_number), None)
        docs = PURCHASE_REGISTER_DOCUMENTS.get(obs.result_type, ["Purchase register", counterparty, "Supplier invoice"])
        causes = list(obs.possible_reasons)
        label = rec.details.get("result_label") if rec else ""

        if rec and rec.details.get("mismatch_kind") == "tax":
            causes.insert(0, f"IGST/CGST/SGST breakup differs between Purchase Register and {counterparty}")
        if rec and rec.details.get("mismatch_kind") == "invoice_value":
            causes.insert(0, "Invoice value differs though taxable value may match")
        if obs.result_type == ComparisonResultType.MISSING_IN_GSTR1:
            observation = f"Invoice {obs.invoice_number} appears in {counterparty} but not in Purchase Register."
            action = "Verify books of account and supplier invoice for unrecorded purchase."
        elif obs.result_type == ComparisonResultType.MISSING_IN_EWAY:
            observation = f"Invoice {obs.invoice_number} is in Purchase Register but missing in {counterparty}."
            action = f"Verify {counterparty} filing and supplier compliance."
        elif label:
            observation = f"Invoice {obs.invoice_number}: {label}."
            action = obs.officer_action
        else:
            observation = obs.observation.replace("GSTR-1", "Purchase Register").replace("E-Way Bill", counterparty)
            action = obs.officer_action

        enriched.append(
            AuditObservation(
                invoice_number=obs.invoice_number,
                result_type=obs.result_type,
                observation=observation,
                possible_reasons=causes[:4],
                officer_action=(
                    f"{action} Priority: {_priority_hint(rec.risk_score if rec else 0)}. "
                    f"Documents: {', '.join(docs[:3])}."
                ),
            )
        )
    return enriched
