"""Report section registration for GSTR-2A purchase reconciliation."""

from __future__ import annotations

from typing import Any, Dict, List

SECTION_ID = "purchase_reconciliation"
SECTION_TITLE = "Purchase Reconciliation"


def report_section_metadata() -> Dict[str, Any]:
    return {
        "section_id": SECTION_ID,
        "title": SECTION_TITLE,
        "description": "GSTR-2A vs EWB Inward purchase verification summary",
        "comparison_id": "gstr2a_ewb_inward",
        "datasets": ["gstr2a", "ewb_inward"],
    }


def build_report_highlights(summary: Dict[str, Any]) -> List[str]:
    if not summary:
        return []
    return [
        f"Matched purchases: {summary.get('matched_count', 0)}",
        f"Missing in GSTR-2A: {summary.get('missing_in_gstr1_count', 0)}",
        f"Missing in EWB Inward: {summary.get('missing_in_eway_count', 0)}",
        f"Tax/value mismatches: {summary.get('value_mismatch_count', 0)}",
        f"Risk level: {summary.get('risk_level', 'LOW')}",
    ]
