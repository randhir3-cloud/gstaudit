"""Purchase Register record loading and validation."""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from comparison.normalizer import normalize_amount, normalize_date, normalize_gstin, normalize_invoice

PLUGIN_DIR = Path(__file__).resolve().parent
GSTR2A_DIR = PLUGIN_DIR.parent / "gstr2a"


def _load_gstr2a_validators():
    spec = importlib.util.spec_from_file_location("purchase_gstr2a_validators", GSTR2A_DIR / "validators.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_gstr2a = _load_gstr2a_validators()
load_gstr2a_records = _gstr2a.load_gstr2a_records
load_eway_inward_records = _gstr2a.load_eway_inward_records


def _load_mapping():
    spec = importlib.util.spec_from_file_location("purchase_mapping", PLUGIN_DIR / "mapping.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_purchase_register_records(
    workbook_bytes: bytes,
    mapping: Optional[dict] = None,
) -> List[dict]:
    buffer = io.BytesIO(workbook_bytes)
    df = pd.read_excel(buffer, engine="openpyxl")
    df = df.dropna(how="all")
    columns = [str(c) for c in df.columns]

    mapping_mod = _load_mapping()
    col_map = mapping or mapping_mod.detect_mapping(columns)
    records: List[dict] = []

    def _cell(row, field):
        col = col_map.get(field)
        if not col or col not in row.index:
            if field in row.index:
                val = row[field]
            else:
                return ""
        else:
            val = row[col]
        if pd.isna(val):
            return ""
        return val

    for _, row in df.iterrows():
        invoice_raw = _cell(row, "invoice_number")
        normalized = normalize_invoice(invoice_raw)
        if not normalized:
            continue
        records.append({
            "source": "purchase_register",
            "invoice_number": str(invoice_raw),
            "normalized_invoice": normalized,
            "gstin": normalize_gstin(_cell(row, "supplier_gstin")),
            "supplier_name": str(_cell(row, "supplier_name")),
            "invoice_date": normalize_date(_cell(row, "invoice_date")),
            "taxable_value": normalize_amount(_cell(row, "taxable_value"), 0),
            "invoice_value": normalize_amount(_cell(row, "invoice_value"), 0),
            "igst": normalize_amount(_cell(row, "igst"), 0),
            "cgst": normalize_amount(_cell(row, "cgst"), 0),
            "sgst": normalize_amount(_cell(row, "sgst"), 0),
            "cess": normalize_amount(_cell(row, "cess"), 0),
            "hsn": str(_cell(row, "hsn")),
            "quantity": normalize_amount(_cell(row, "quantity"), 0),
            "source_period": str(_cell(row, "source_period") if "source_period" in col_map else ""),
        })
    return records


def validate_purchase_gstr2a_pair(
    purchase_bytes: Optional[bytes],
    gstr2a_bytes: Optional[bytes],
) -> Tuple[bool, str]:
    if not purchase_bytes:
        return False, "Purchase Register workbook is required"
    if not gstr2a_bytes:
        return False, "Merged GSTR-2A workbook is required"
    pr = load_purchase_register_records(purchase_bytes)
    g2a = load_gstr2a_records(gstr2a_bytes)
    if not pr:
        return False, "No invoice rows found in Purchase Register"
    if not g2a:
        return False, "No invoice rows found in GSTR-2A workbook"
    return True, ""


def validate_purchase_ewb_pair(
    purchase_bytes: Optional[bytes],
    ewb_bytes: Optional[bytes],
) -> Tuple[bool, str]:
    if not purchase_bytes:
        return False, "Purchase Register workbook is required"
    if not ewb_bytes:
        return False, "Merged EWB Inward workbook is required"
    pr = load_purchase_register_records(purchase_bytes)
    ewb = load_eway_inward_records(ewb_bytes)
    if not pr:
        return False, "No invoice rows found in Purchase Register"
    if not ewb:
        return False, "No invoice rows found in EWB Inward workbook"
    return True, ""
