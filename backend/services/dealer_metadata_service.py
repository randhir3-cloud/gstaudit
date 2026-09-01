"""Extract dealer metadata from GSTR Read me worksheets."""

from __future__ import annotations

import io
import re
from typing import Dict, List, Optional, Tuple

import openpyxl

from models.dealer_metadata import DealerMetadata

README_SHEET_NAMES = {"read me"}

FIELD_ALIASES: Dict[str, Tuple[str, ...]] = {
    "gstin": ("gstin", "taxpayer's gstin", "taxpayers gstin"),
    "legal_name": ("legal name", "legal name of taxpayer"),
    "trade_name": ("trade name", "trade name (if any)"),
    "financial_year": ("financial year",),
    "tax_period": ("tax period", "tax period "),
    "arn": ("arn",),
    "arn_date": ("arn date",),
    "download_date": (
        "date and time of generation",
        "date of generation",
        "download date",
        "date of download",
    ),
}

# Known GST portal cell positions (1-based row, col) when label scan fails.
GSTR1_FALLBACK: Dict[str, Tuple[int, int]] = {
    "financial_year": (4, 3),
    "tax_period": (5, 3),
    "gstin": (6, 3),
    "legal_name": (7, 3),
    "trade_name": (8, 3),
    "arn": (9, 3),
    "arn_date": (10, 3),
    "download_date": (11, 3),
}

GSTR2A_FALLBACK: Dict[str, Tuple[int, int]] = {
    "gstin": (2, 3),
    "legal_name": (3, 3),
    "trade_name": (4, 3),
    "tax_period": (2, 5),
    "financial_year": (3, 5),
    "download_date": (4, 5),
    "arn": (0, 0),
    "arn_date": (0, 0),
}


def _normalize_label(text: object) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text).strip().lower())


def _clean_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def find_readme_sheet_name(sheet_names: List[str]) -> Optional[str]:
    for name in sheet_names:
        if name.strip().lower() in README_SHEET_NAMES:
            return name
    return None


def _match_field(label: str) -> Optional[str]:
    normalized = _normalize_label(label)
    if not normalized:
        return None
    for field, aliases in FIELD_ALIASES.items():
        if normalized in aliases:
            return field
        for alias in aliases:
            if alias in normalized or normalized in alias:
                return field
    return None


def _value_to_the_right(ws, row: int, start_col: int, max_col: int) -> str:
    """Pick the first meaningful value to the right of a label cell."""
    for col in range(start_col + 1, max_col + 1):
        raw = ws.cell(row=row, column=col).value
        if raw is None:
            continue
        text = _clean_value(raw)
        if not text:
            continue
        if _match_field(text):
            break
        return text
    return ""


def scan_readme_labels(ws, max_row: int = 20, max_col: int = 8) -> Dict[str, str]:
    """Dynamically map metadata fields by scanning label cells."""
    found: Dict[str, str] = {}
    scan_rows = min(max_row, ws.max_row or max_row)
    scan_cols = min(max_col, ws.max_column or max_col)

    for row in range(1, scan_rows + 1):
        for col in range(1, scan_cols + 1):
            label_cell = ws.cell(row=row, column=col).value
            field = _match_field(label_cell)
            if not field or field in found:
                continue
            value = _value_to_the_right(ws, row, col, scan_cols)
            if value:
                found[field] = value
    return found


def apply_fallback(
    ws,
    found: Dict[str, str],
    fallback: Dict[str, Tuple[int, int]],
) -> Dict[str, str]:
    result = dict(found)
    for field, (row, col) in fallback.items():
        if field in result and result[field]:
            continue
        if row <= 0 or col <= 0:
            continue
        value = _clean_value(ws.cell(row=row, column=col).value)
        if value:
            result[field] = value
    return result


def fields_to_dealer(fields: Dict[str, str]) -> DealerMetadata:
    return DealerMetadata(
        gstin=fields.get("gstin", ""),
        legal_name=fields.get("legal_name", ""),
        trade_name=fields.get("trade_name", ""),
        financial_year=fields.get("financial_year", ""),
        tax_period=fields.get("tax_period", ""),
        arn=fields.get("arn", ""),
        arn_date=fields.get("arn_date", ""),
        download_date=fields.get("download_date", ""),
    ).ensure_id()


def extract_from_workbook(wb, return_type: str) -> DealerMetadata:
    readme_name = find_readme_sheet_name(wb.sheetnames)
    if not readme_name:
        return DealerMetadata().ensure_id()

    ws = wb[readme_name]
    scanned = scan_readme_labels(ws)
    fallback = GSTR1_FALLBACK if return_type == "gstr1" else GSTR2A_FALLBACK
    merged = apply_fallback(ws, scanned, fallback)
    return fields_to_dealer(merged)


def extract_from_bytes(content: bytes, return_type: str) -> DealerMetadata:
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        return extract_from_workbook(wb, return_type)
    finally:
        wb.close()


def extract_from_files(
    files: List[Tuple[str, bytes]],
    return_type: str,
) -> List[Tuple[str, DealerMetadata]]:
    if return_type not in {"gstr1", "gstr2a"}:
        raise ValueError(f"Unsupported return type: {return_type}")

    results: List[Tuple[str, DealerMetadata]] = []
    for filename, content in files:
        dealer = extract_from_bytes(content, return_type)
        results.append((filename, dealer))
    return results
