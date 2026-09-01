"""Report section for Purchase Register reconciliation."""

from __future__ import annotations

from typing import Any, Dict, List

SECTION_ID = "purchase_register_reconciliation"
SECTION_TITLE = "Purchase Register Reconciliation"


def report_section_metadata() -> Dict[str, Any]:
    return {
        "section_id": SECTION_ID,
        "title": SECTION_TITLE,
        "description": "Purchase Register vs GSTR-2A and EWB Inward verification summary",
        "comparison_ids": ["purchase_register_vs_gstr2a", "purchase_register_vs_ewb_inward"],
        "datasets": ["purchase_register", "gstr2a", "ewb_inward"],
    }


def build_report_highlights(summary: Dict[str, Any]) -> List[str]:
    if not summary:
        return []
    return [
        f"Matched invoices: {summary.get('matched_count', 0)}",
        f"Missing in Purchase Register: {summary.get('missing_in_gstr1_count', 0)}",
        f"Missing in counterparty: {summary.get('missing_in_eway_count', 0)}",
        f"Tax/value mismatches: {summary.get('value_mismatch_count', 0)}",
        f"Risk level: {summary.get('risk_level', 'LOW')}",
    ]
