"""Duplicate detection within a dataset."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set


def find_duplicate_keys(records: List[dict], key_field: str = "normalized_invoice") -> Set[str]:
    counts: Dict[str, int] = defaultdict(int)
    for rec in records:
        key = rec.get(key_field, "")
        if key:
            counts[key] += 1
    return {k for k, v in counts.items() if v > 1}
