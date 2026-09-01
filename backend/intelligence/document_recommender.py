"""Document recommendation engine per discrepancy type."""

from __future__ import annotations

from comparison.comparison_types import ComparisonResultType
from intelligence.models import DocumentRecommendation

DOCUMENT_MAP: dict[ComparisonResultType, list[str]] = {
    ComparisonResultType.MISSING_IN_GSTR1: [
        "Sales Register",
        "Tax Invoice",
        "E-Invoice (if applicable)",
        "Transport Documents / LR",
        "Bank Statement (receipt confirmation)",
    ],
    ComparisonResultType.MISSING_IN_EWAY: [
        "Sales Register",
        "Tax Invoice",
        "Dispatch Register",
        "E-Way Bill Portal Extract",
        "Delivery Challan",
    ],
    ComparisonResultType.GSTIN_MISMATCH: [
        "Tax Invoice",
        "E-Way Bill Printout",
        "Party Master / GSTIN Registration Certificate",
        "Contract / PO",
    ],
    ComparisonResultType.VALUE_MISMATCH: [
        "Tax Invoice",
        "Credit/Debit Note",
        "Sales Register",
        "E-Way Bill",
        "Books of Account",
    ],
    ComparisonResultType.DATE_MISMATCH: [
        "Tax Invoice",
        "E-Way Bill",
        "LR / Transport Document",
        "GSTR-1 Filing Acknowledgement",
    ],
    ComparisonResultType.DUPLICATE: [
        "Original Tax Invoice",
        "Amended Return Acknowledgement",
        "Sales Register",
        "Upload Source Files",
    ],
    ComparisonResultType.MULTIPLE_MATCHES: [
        "Tax Invoice",
        "E-Way Bill(s)",
        "Sales Register",
        "Dispatch Records",
    ],
}

PURCHASE_DOCS = [
    "Purchase Register",
    "Supplier Ledger",
    "GRN / Receipt Note",
    "Payment Proof / Bank Statement",
    "Supplier Tax Invoice",
]


def recommend_documents(result_type: ComparisonResultType | str) -> list[str]:
    if isinstance(result_type, str):
        try:
            result_type = ComparisonResultType(result_type)
        except ValueError:
            return ["Books of Account", "Source Workbooks"]
    return list(DOCUMENT_MAP.get(result_type, ["Books of Account", "Source Workbooks"]))


def build_document_catalog() -> list[DocumentRecommendation]:
    catalog = []
    for rtype, docs in DOCUMENT_MAP.items():
        catalog.append(DocumentRecommendation(discrepancy_type=rtype.value, documents=docs))
    catalog.append(DocumentRecommendation(discrepancy_type="PURCHASE_MISMATCH", documents=PURCHASE_DOCS))
    return catalog
