"""Financial-year month utilities — single source for coverage, duplicates, missing months."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from merger import (
    FULL_MONTH_MAP,
    MONTH_MAP,
    file_fy_key,
    find_missing_months,
    fy_key_to_label,
    fy_sort_key,
    next_fy_key,
)

# FY month order: April → March (keys 1..12 in fy_sort_key space)
FY_MONTH_SEQUENCE: List[Tuple[str, str]] = [
    ("04", "April"),
    ("05", "May"),
    ("06", "June"),
    ("07", "July"),
    ("08", "August"),
    ("09", "September"),
    ("10", "October"),
    ("11", "November"),
    ("12", "December"),
    ("01", "January"),
    ("02", "February"),
    ("03", "March"),
]

FY_MONTH_LABELS: List[str] = [label for _, label in FY_MONTH_SEQUENCE]
FY_MONTH_SHORT: List[str] = [MONTH_MAP[mm] for mm, _ in FY_MONTH_SEQUENCE]


def parse_month_from_filename(filename: str) -> Optional[Tuple[str, str, int]]:
    """Return (short_label, full_label, fy_key) or None."""
    match = re.search(r"_(\d{2})(\d{4})_", filename)
    if not match:
        return None
    mm, yyyy = match.group(1), match.group(2)
    key = fy_sort_key(mm, yyyy)
    short = MONTH_MAP.get(mm, mm)
    full = fy_key_to_label(key)
    return short, full, key


def month_coverage_from_filenames(filenames: List[str]) -> Dict:
    """Build month coverage grid, missing list, and duplicate groups."""
    present_keys: Dict[int, List[str]] = {}
    for name in filenames:
        parsed = parse_month_from_filename(name)
        if not parsed:
            continue
        _, _, key = parsed
        present_keys.setdefault(key, []).append(name)

    months = []
    for mm, full_name in FY_MONTH_SEQUENCE:
        short = MONTH_MAP[mm]
        matching_keys = [k for k in present_keys if _key_to_mm(k) == mm]
        uploaded = bool(matching_keys)
        files_for_month: List[str] = []
        for k in matching_keys:
            files_for_month.extend(present_keys.get(k, []))
        display_month = fy_key_to_label(matching_keys[0]) if matching_keys else full_name
        months.append(
            {
                "month": display_month,
                "short": short,
                "uploaded": uploaded,
                "file_count": len(files_for_month),
                "filenames": sorted(files_for_month),
            }
        )

    missing = find_missing_months(filenames) if filenames else []

    duplicates = []
    for month_entry in months:
        if month_entry["file_count"] > 1:
            duplicates.append(
                {
                    "month": month_entry["month"],
                    "short": month_entry["short"],
                    "file_count": month_entry["file_count"],
                    "filenames": month_entry["filenames"],
                }
            )

    uploaded_count = sum(1 for m in months if m["uploaded"])
    return {
        "months": months,
        "uploaded_count": uploaded_count,
        "total_months": len(FY_MONTH_SEQUENCE),
        "missing_months": missing,
        "duplicate_months": duplicates,
        "coverage_percent": round((uploaded_count / len(FY_MONTH_SEQUENCE)) * 100, 1),
    }


def _key_to_mm(fy_key: int) -> str:
    idx = fy_key % 100
    fy_year = fy_key // 100
    if idx <= 9:
        cal_month = idx + 3
    else:
        cal_month = idx - 9
    return f"{cal_month:02d}"


def infer_financial_year(filenames: List[str], fallback: str = "") -> str:
    years = set()
    for name in filenames:
        m = re.search(r"_(\d{2})(\d{4})_", name)
        if m:
            mm, yyyy = int(m.group(1)), int(m.group(2))
            fy_start = yyyy if mm >= 4 else yyyy - 1
            fy_end = (fy_start + 1) % 100
            years.add(f"{fy_start}-{fy_end:02d}")
    return sorted(years)[0] if years else fallback
