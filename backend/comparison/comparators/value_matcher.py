"""Value matching utilities."""

from __future__ import annotations

from typing import Optional, Tuple

from comparison.models import NormalizerConfig
from comparison.normalizer import amounts_match, normalize_amount


def compare_values(
    gstr1_rec: dict,
    eway_rec: dict,
    config: Optional[NormalizerConfig] = None,
) -> Tuple[bool, float]:
    cfg = config or NormalizerConfig()
    fields = [
        ("taxable_value", "taxable_value"),
        ("invoice_value", "invoice_value"),
        ("igst", "igst"),
        ("cgst", "cgst"),
        ("sgst", "sgst"),
    ]
    max_diff = 0.0
    for g_field, e_field in fields:
        left = normalize_amount(gstr1_rec.get(g_field), cfg)
        right = normalize_amount(eway_rec.get(e_field), cfg)
        diff = abs(left - right)
        max_diff = max(max_diff, diff)
        if not amounts_match(left, right, cfg):
            return False, max_diff
    return True, max_diff
