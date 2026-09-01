"""GSTIN matching utilities."""

from __future__ import annotations

from comparison.normalizer import normalize_gstin


def gstins_match(gstr1_gstin: str, eway_gstin: str) -> bool:
    left = normalize_gstin(gstr1_gstin)
    right = normalize_gstin(eway_gstin)
    if not left or not right:
        return True
    return left == right
