"""Officer guidance — possible causes and verification steps."""

from __future__ import annotations

from comparison.comparison_types import ComparisonResultType
from comparison.result_models import ComparisonRecord

CAUSES: dict[ComparisonResultType, list[str]] = {
    ComparisonResultType.MISSING_IN_GSTR1: [
        "Late filing / wrong tax period",
        "Suppressed turnover",
        "Wrong invoice number in GSTR-1",
        "Return amendment pending",
        "Cancelled invoice still in EWB",
    ],
    ComparisonResultType.MISSING_IN_EWAY: [
        "E-Way Bill not generated",
        "Exempt / non-EWB movement",
        "Wrong EWB upload period",
        "Consignment below EWB threshold",
        "Manual dispatch without EWB",
    ],
    ComparisonResultType.GSTIN_MISMATCH: [
        "Data entry error",
        "Wrong GSTIN mapped to party",
        "Branch / additional place of business",
        "B2C recorded as B2B",
    ],
    ComparisonResultType.VALUE_MISMATCH: [
        "Rounding difference",
        "Freight included in EWB value",
        "Amended invoice not updated",
        "Credit note not reflected",
        "Tax rate difference",
    ],
    ComparisonResultType.DATE_MISMATCH: [
        "Backdated invoice",
        "EWB generated on dispatch date",
        "Period-end cut-off difference",
        "Amendment with revised date",
    ],
    ComparisonResultType.DUPLICATE: [
        "Duplicate upload",
        "Amended return not removing old entry",
        "Revised invoice uploaded twice",
    ],
    ComparisonResultType.MULTIPLE_MATCHES: [
        "Split consignment / multiple EWBs",
        "Invoice amended with new EWB",
        "Partial dispatch",
    ],
}

VERIFICATIONS: dict[ComparisonResultType, list[str]] = {
    ComparisonResultType.MISSING_IN_GSTR1: [
        "Books of Account",
        "Sales Register",
        "Bank Statement",
        "E-Invoice Portal",
        "GSTR-1 Return (as filed)",
    ],
    ComparisonResultType.MISSING_IN_EWAY: [
        "Dispatch Register",
        "E-Way Bill Portal",
        "Stock Register",
        "Transport Documents",
    ],
    ComparisonResultType.GSTIN_MISMATCH: [
        "Tax Invoice",
        "Party Ledger",
        "GST Registration Certificate",
        "E-Way Bill Portal",
    ],
    ComparisonResultType.VALUE_MISMATCH: [
        "Books of Account",
        "Tax Invoice",
        "E-Way Bill",
        "Credit/Debit Notes",
    ],
    ComparisonResultType.DATE_MISMATCH: [
        "Tax Invoice",
        "LR / Transport Document",
        "GSTR-1 Filing Records",
    ],
    ComparisonResultType.DUPLICATE: [
        "Sales Register",
        "GSTR-1 Amendment Records",
        "Source Upload Files",
    ],
    ComparisonResultType.MULTIPLE_MATCHES: [
        "Dispatch Records",
        "E-Way Bill Portal",
        "Sales Register",
    ],
}

PROVISIONS: dict[ComparisonResultType, list[str]] = {
    ComparisonResultType.MISSING_IN_GSTR1: [
        "Section 73/74 — determination of tax not paid/short paid",
        "Rule 138 — E-Way Bill compliance",
    ],
    ComparisonResultType.MISSING_IN_EWAY: [
        "Section 122 — penalty for E-Way Bill contravention",
        "Rule 138 — E-Way Bill requirements",
    ],
    ComparisonResultType.GSTIN_MISMATCH: [
        "Section 31 — tax invoice requirements",
        "Rule 46 — invoice particulars",
    ],
    ComparisonResultType.VALUE_MISMATCH: [
        "Section 15 — value of supply",
        "Section 34 — credit/debit notes",
    ],
    ComparisonResultType.DATE_MISMATCH: [
        "Section 31 — time of supply / invoice date",
        "Rule 46 — invoice date requirements",
    ],
    ComparisonResultType.DUPLICATE: [
        "Section 37 — furnishing details of outward supplies",
        "Section 39 — return filing accuracy",
    ],
}


def _resolve_type(result_type: ComparisonResultType | str) -> ComparisonResultType:
    if isinstance(result_type, ComparisonResultType):
        return result_type
    try:
        return ComparisonResultType(result_type)
    except ValueError:
        return ComparisonResultType.UNKNOWN


def generate_guidance(record: ComparisonRecord, extra_patterns: list[str] | None = None) -> dict:
    rtype = _resolve_type(record.result_type)
    causes = list(CAUSES.get(rtype, ["Unclassified discrepancy — manual review required."]))
    verifications = list(VERIFICATIONS.get(rtype, ["Books of Account", "Source Workbooks"]))
    provisions = list(PROVISIONS.get(rtype, []))

    if extra_patterns:
        if any("round value" in p.lower() for p in extra_patterns):
            causes.append("Possible structured / round-value invoicing pattern.")
        if any("repeated missing" in p.lower() for p in extra_patterns):
            causes.append("Repeated omission pattern with same party — review turnover reporting.")
            verifications.append("Party-wise Ledger")

    return {
        "possible_causes": causes[:5],
        "suggested_verifications": verifications[:5],
        "gst_provisions": provisions,
    }
