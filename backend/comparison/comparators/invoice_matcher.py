"""Invoice number matching utilities."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from comparison.normalizer import normalize_invoice


def build_invoice_index(records: List[dict], invoice_field: str = "normalized_invoice") -> Dict[str, List[dict]]:
    index: Dict[str, List[dict]] = defaultdict(list)
    for rec in records:
        key = rec.get(invoice_field) or normalize_invoice(rec.get("invoice_number", ""))
        if key:
            index[key].append(rec)
    return index


def find_matches(
    invoice_key: str,
    left_index: Dict[str, List[dict]],
    right_index: Dict[str, List[dict]],
) -> Tuple[List[dict], List[dict]]:
    return left_index.get(invoice_key, []), right_index.get(invoice_key, [])
