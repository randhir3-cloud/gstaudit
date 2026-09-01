"""Resolve dealer GSTIN for E-Way Bill classification."""

from __future__ import annotations

from typing import List, Optional, Tuple

from models.dealer_metadata import DealerMetadata
from models.eway_classification import DealerGstinResolution
from services.dealer_metadata_service import extract_from_bytes, extract_from_files


def resolve_dealer_gstin(
    *,
    user_gstin: Optional[str] = None,
    gstr1_files: Optional[List[Tuple[str, bytes]]] = None,
    gstr2a_files: Optional[List[Tuple[str, bytes]]] = None,
) -> DealerGstinResolution:
    """Priority: GSTR-1 Read me → GSTR-2A Read me → user-provided GSTIN."""
    if user_gstin and user_gstin.strip():
        return DealerGstinResolution(
            gstin=user_gstin.strip().upper(),
            source="user",
            requires_user_input=False,
        )

    if gstr1_files:
        dealer = _extract_first_gstin(gstr1_files, "gstr1")
        if dealer.gstin:
            return DealerGstinResolution(
                gstin=dealer.gstin,
                source="gstr1",
                requires_user_input=False,
                legal_name=dealer.legal_name,
                financial_year=dealer.financial_year,
            )

    if gstr2a_files:
        dealer = _extract_first_gstin(gstr2a_files, "gstr2a")
        if dealer.gstin:
            return DealerGstinResolution(
                gstin=dealer.gstin,
                source="gstr2a",
                requires_user_input=False,
                legal_name=dealer.legal_name,
                financial_year=dealer.financial_year,
            )

    return DealerGstinResolution(
        gstin="",
        source="none",
        requires_user_input=True,
    )


def _extract_first_gstin(files: List[Tuple[str, bytes]], return_type: str) -> DealerMetadata:
    for filename, content in files:
        dealer = extract_from_bytes(content, return_type)
        if dealer.gstin:
            return dealer
    return DealerMetadata()
