"""Date matching utilities."""

from __future__ import annotations

from typing import Optional

from comparison.models import NormalizerConfig
from comparison.normalizer import dates_match, normalize_date


def compare_dates(gstr1_date: object, eway_date: object, config: Optional[NormalizerConfig] = None) -> bool:
    left = normalize_date(gstr1_date)
    right = normalize_date(eway_date)
    return dates_match(left, right, config)
