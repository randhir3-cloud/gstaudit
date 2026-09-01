"""GSTR-2A and EWB Inward workbook validation and record loading."""

from __future__ import annotations

import io
import re
from typing import List, Optional, Tuple

import pandas as pd

from comparison.normalizer import normalize_amount, normalize_date, normalize_gstin, normalize_invoice

GSTR2A_INVOICE_ALIASES = ["invoice number", "invoice no", "doc no", "document number"]
GSTR2A_DATE_ALIASES = ["invoice date", "date"]
GSTR2A_GSTIN_ALIASES = [
    "gstin/uin of supplier",
    "supplier gstin",
    "gstin of supplier",
    "gstin",
]
GSTR2A_TAXABLE_ALIASES = ["taxable value", "taxable amount"]
GSTR2A_INVOICE_VALUE_ALIASES = ["invoice value", "total invoice value", "value"]
GSTR2A_IGST_ALIASES = ["integrated tax", "igst"]
GSTR2A_CGST_ALIASES = ["central tax", "cgst"]
GSTR2A_SGST_ALIASES = ["state tax", "sgst"]
GSTR2A_HSN_ALIASES = ["hsn", "hsn/sac", "hsn code"]

EWB_INWARD_INVOICE_ALIASES = ["doc no", "document no", "invoice number"]
EWB_INWARD_GSTIN_ALIASES = ["from gstin & name", "from gstin", "supplier gstin"]
EWB_INWARD_DATE_ALIASES = ["ewb no & dt", "doc date", "invoice date"]
EWB_INWARD_TAXABLE_ALIASES = ["taxable value", "taxable amount"]
EWB_INWARD_INVOICE_VALUE_ALIASES = ["invoice value", "total value", "value"]
EWB_INWARD_IGST_ALIASES = ["igst amount", "igst"]
EWB_INWARD_CGST_ALIASES = ["cgst amount", "cgst"]
EWB_INWARD_SGST_ALIASES = ["sgst amount", "sgst"]
EWB_INWARD_HSN_ALIASES = ["hsn code", "hsn"]


def _norm_col(name: object) -> str:
    return re.sub(r"\s+", " ", str(name).strip().lower())


def _find_column(columns: List[str], aliases: List[str]) -> Optional[str]:
    normalized = {_norm_col(c): c for c in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    for col_norm, original in normalized.items():
        for alias in aliases:
            if alias in col_norm:
                return original
    return None


def _cell(row: pd.Series, col: Optional[str], default=""):
    if not col or col not in row.index:
        return default
    val = row[col]
    if pd.isna(val):
        return default
    return val


def _mapping_for_gstr2a(columns: List[str]) -> dict:
    return {
        "invoice": _find_column(columns, GSTR2A_INVOICE_ALIASES),
        "date": _find_column(columns, GSTR2A_DATE_ALIASES),
        "gstin": _find_column(columns, GSTR2A_GSTIN_ALIASES),
        "taxable": _find_column(columns, GSTR2A_TAXABLE_ALIASES),
        "invoice_value": _find_column(columns, GSTR2A_INVOICE_VALUE_ALIASES),
        "igst": _find_column(columns, GSTR2A_IGST_ALIASES),
        "cgst": _find_column(columns, GSTR2A_CGST_ALIASES),
        "sgst": _find_column(columns, GSTR2A_SGST_ALIASES),
        "hsn": _find_column(columns, GSTR2A_HSN_ALIASES),
        "source_period": _find_column(columns, ["source_period"]),
    }


def _mapping_for_ewb_inward(columns: List[str]) -> dict:
    return {
        "invoice": _find_column(columns, EWB_INWARD_INVOICE_ALIASES),
        "date": _find_column(columns, EWB_INWARD_DATE_ALIASES),
        "gstin": _find_column(columns, EWB_INWARD_GSTIN_ALIASES),
        "taxable": _find_column(columns, EWB_INWARD_TAXABLE_ALIASES),
        "invoice_value": _find_column(columns, EWB_INWARD_INVOICE_VALUE_ALIASES),
        "igst": _find_column(columns, EWB_INWARD_IGST_ALIASES),
        "cgst": _find_column(columns, EWB_INWARD_CGST_ALIASES),
        "sgst": _find_column(columns, EWB_INWARD_SGST_ALIASES),
        "hsn": _find_column(columns, EWB_INWARD_HSN_ALIASES),
        "source_period": _find_column(columns, ["source_period"]),
        "ewb_number": _find_column(columns, ["ewb no & dt", "ewb no"]),
    }


def _record_from_row(row: pd.Series, mapping: dict, source: str) -> dict:
    invoice_raw = _cell(row, mapping.get("invoice"))
    return {
        "source": source,
        "invoice_number": str(invoice_raw),
        "normalized_invoice": normalize_invoice(invoice_raw),
        "gstin": normalize_gstin(_cell(row, mapping.get("gstin"))),
        "invoice_date": normalize_date(_cell(row, mapping.get("date"))),
        "taxable_value": normalize_amount(_cell(row, mapping.get("taxable"), 0)),
        "invoice_value": normalize_amount(_cell(row, mapping.get("invoice_value"), 0)),
        "igst": normalize_amount(_cell(row, mapping.get("igst"), 0)),
        "cgst": normalize_amount(_cell(row, mapping.get("cgst"), 0)),
        "sgst": normalize_amount(_cell(row, mapping.get("sgst"), 0)),
        "hsn": str(_cell(row, mapping.get("hsn"), "")),
        "source_period": str(_cell(row, mapping.get("source_period"), "")),
        "ewb_number": str(_cell(row, mapping.get("ewb_number"), "")),
    }


def _detect_header_row(df: pd.DataFrame, invoice_aliases: List[str]) -> Optional[int]:
    for idx in range(min(12, len(df))):
        row_vals = [_norm_col(v) for v in df.iloc[idx].tolist() if str(v).strip()]
        joined = " ".join(row_vals)
        if any(alias in joined for alias in invoice_aliases):
            return idx
    return 0 if len(df) else None


def load_gstr2a_records(workbook_bytes: bytes) -> List[dict]:
    buffer = io.BytesIO(workbook_bytes)
    xl = pd.ExcelFile(buffer, engine="openpyxl")
    records: List[dict] = []
    for sheet in xl.sheet_names:
        if sheet.strip().lower() in {"read me", "readme"}:
            continue
        df = pd.read_excel(xl, sheet_name=sheet, header=None)
        header_row = _detect_header_row(df, GSTR2A_INVOICE_ALIASES)
        if header_row is None:
            continue
        df = pd.read_excel(xl, sheet_name=sheet, header=header_row)
        df = df.dropna(how="all")
        columns = [str(c) for c in df.columns]
        mapping = _mapping_for_gstr2a(columns)
        if not mapping.get("invoice"):
            continue
        for _, row in df.iterrows():
            rec = _record_from_row(row, mapping, "gstr2a")
            if rec["normalized_invoice"]:
                records.append(rec)
    return records


def load_eway_inward_records(workbook_bytes: bytes) -> List[dict]:
    buffer = io.BytesIO(workbook_bytes)
    df = pd.read_excel(buffer, engine="openpyxl")
    df = df.dropna(how="all")
    columns = [str(c) for c in df.columns]
    mapping = _mapping_for_ewb_inward(columns)
    records: List[dict] = []
    for _, row in df.iterrows():
        rec = _record_from_row(row, mapping, "ewb_inward")
        if rec["normalized_invoice"]:
            records.append(rec)
    return records


def validate_workbook_pair(gstr2a_bytes: Optional[bytes], ewb_bytes: Optional[bytes]) -> Tuple[bool, str]:
    if not gstr2a_bytes:
        return False, "Merged GSTR-2A workbook is required"
    if not ewb_bytes:
        return False, "Merged EWB Inward workbook is required"
    gstr2a_records = load_gstr2a_records(gstr2a_bytes)
    ewb_records = load_eway_inward_records(ewb_bytes)
    if not gstr2a_records:
        return False, "No invoice rows found in GSTR-2A workbook"
    if not ewb_records:
        return False, "No invoice rows found in EWB Inward workbook"
    return True, ""


def compare_tax_fields(left: dict, right: dict, tolerance: float = 1.0) -> Tuple[bool, float]:
    max_diff = 0.0
    for field in ("igst", "cgst", "sgst"):
        diff = abs(float(left.get(field, 0)) - float(right.get(field, 0)))
        max_diff = max(max_diff, diff)
        if diff > tolerance:
            return False, max_diff
    return True, max_diff


def compare_invoice_values(left: dict, right: dict, tolerance: float = 1.0) -> Tuple[bool, float]:
    left_val = float(left.get("invoice_value", 0))
    right_val = float(right.get("invoice_value", 0))
    diff = abs(left_val - right_val)
    return diff <= tolerance, diff
