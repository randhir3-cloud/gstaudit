"""Load normalized invoice records from merged workbooks."""

from __future__ import annotations

import io
import re
from typing import Dict, List, Tuple

import pandas as pd

from comparison.normalizer import normalize_amount, normalize_date, normalize_gstin, normalize_invoice

GSTR1_INVOICE_ALIASES = ["invoice number", "invoice no", "doc no", "document number"]
GSTR1_DATE_ALIASES = ["invoice date", "date"]
GSTR1_GSTIN_ALIASES = ["gstin/uin of recipient", "recipient gstin", "gstin of recipient", "gstin"]
GSTR1_TAXABLE_ALIASES = ["taxable value", "taxable amount"]
GSTR1_INVOICE_VALUE_ALIASES = ["invoice value", "total invoice value", "value"]
GSTR1_IGST_ALIASES = ["integrated tax", "igst"]
GSTR1_CGST_ALIASES = ["central tax", "cgst"]
GSTR1_SGST_ALIASES = ["state tax", "sgst"]

EWB_INVOICE_ALIASES = ["doc no", "document no", "invoice number"]
EWB_GSTIN_ALIASES = ["to gstin & name", "to gstin", "consignee gstin"]
EWB_DATE_ALIASES = ["ewb no & dt", "doc date", "invoice date"]
EWB_TAXABLE_ALIASES = ["taxable value", "taxable amount"]
EWB_INVOICE_VALUE_ALIASES = ["invoice value", "total value", "value"]
EWB_IGST_ALIASES = ["igst amount", "igst"]
EWB_CGST_ALIASES = ["cgst amount", "cgst"]
EWB_SGST_ALIASES = ["sgst amount", "sgst"]


def _norm_col(name: object) -> str:
    return re.sub(r"\s+", " ", str(name).strip().lower())


def _find_column(columns: List[str], aliases: List[str]) -> str | None:
    normalized = {_norm_col(c): c for c in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    for col_norm, original in normalized.items():
        for alias in aliases:
            if alias in col_norm:
                return original
    return None


def _cell(row: pd.Series, col: str | None, default=""):
    if not col or col not in row.index:
        return default
    val = row[col]
    if pd.isna(val):
        return default
    return val


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
        "source_period": str(_cell(row, mapping.get("source_period"), "")),
        "ewb_number": str(_cell(row, mapping.get("ewb_number"), "")),
    }


def _mapping_for_columns(columns: List[str], source: str) -> dict:
    if source == "gstr1":
        return {
            "invoice": _find_column(columns, GSTR1_INVOICE_ALIASES),
            "date": _find_column(columns, GSTR1_DATE_ALIASES),
            "gstin": _find_column(columns, GSTR1_GSTIN_ALIASES),
            "taxable": _find_column(columns, GSTR1_TAXABLE_ALIASES),
            "invoice_value": _find_column(columns, GSTR1_INVOICE_VALUE_ALIASES),
            "igst": _find_column(columns, GSTR1_IGST_ALIASES),
            "cgst": _find_column(columns, GSTR1_CGST_ALIASES),
            "sgst": _find_column(columns, GSTR1_SGST_ALIASES),
            "source_period": _find_column(columns, ["source_period"]),
        }
    return {
        "invoice": _find_column(columns, EWB_INVOICE_ALIASES),
        "date": _find_column(columns, EWB_DATE_ALIASES),
        "gstin": _find_column(columns, EWB_GSTIN_ALIASES),
        "taxable": _find_column(columns, EWB_TAXABLE_ALIASES),
        "invoice_value": _find_column(columns, EWB_INVOICE_VALUE_ALIASES),
        "igst": _find_column(columns, EWB_IGST_ALIASES),
        "cgst": _find_column(columns, EWB_CGST_ALIASES),
        "sgst": _find_column(columns, EWB_SGST_ALIASES),
        "source_period": _find_column(columns, ["source_period"]),
        "ewb_number": _find_column(columns, ["ewb no & dt", "ewb no"]),
    }


def load_gstr1_records(workbook_bytes: bytes) -> List[dict]:
    buffer = io.BytesIO(workbook_bytes)
    xl = pd.ExcelFile(buffer, engine="openpyxl")
    records: List[dict] = []
    for sheet in xl.sheet_names:
        if sheet.strip().lower() == "read me":
            continue
        df = pd.read_excel(xl, sheet_name=sheet, header=None)
        header_row = _detect_header_row(df)
        if header_row is None:
            continue
        df = pd.read_excel(xl, sheet_name=sheet, header=header_row)
        df = df.dropna(how="all")
        columns = [str(c) for c in df.columns]
        mapping = _mapping_for_columns(columns, "gstr1")
        if not mapping.get("invoice"):
            continue
        for _, row in df.iterrows():
            rec = _record_from_row(row, mapping, "gstr1")
            if rec["normalized_invoice"]:
                records.append(rec)
    return records


def load_eway_outward_records(workbook_bytes: bytes) -> List[dict]:
    buffer = io.BytesIO(workbook_bytes)
    df = pd.read_excel(buffer, engine="openpyxl")
    df = df.dropna(how="all")
    columns = [str(c) for c in df.columns]
    mapping = _mapping_for_columns(columns, "ewb")
    records: List[dict] = []
    for _, row in df.iterrows():
        rec = _record_from_row(row, mapping, "ewb")
        if rec["normalized_invoice"]:
            records.append(rec)
    return records


def _detect_header_row(df: pd.DataFrame) -> int | None:
    for idx in range(min(10, len(df))):
        row_vals = [_norm_col(v) for v in df.iloc[idx].tolist() if str(v).strip()]
        joined = " ".join(row_vals)
        if any(alias in joined for alias in GSTR1_INVOICE_ALIASES):
            return idx
    return 0 if len(df) else None
