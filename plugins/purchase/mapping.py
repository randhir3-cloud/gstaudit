"""Column mapping, template detection, and profile storage for Purchase Register."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

MAPPING_FIELDS = [
    "invoice_number",
    "invoice_date",
    "supplier_gstin",
    "supplier_name",
    "taxable_value",
    "cgst",
    "sgst",
    "igst",
    "cess",
    "hsn",
    "quantity",
    "invoice_value",
]

FIELD_ALIASES: Dict[str, List[str]] = {
    "invoice_number": [
        "invoice number", "invoice no", "bill no", "voucher no", "doc no",
        "document number", "purc no", "purchase invoice no",
    ],
    "invoice_date": ["invoice date", "bill date", "date", "voucher date", "purc date"],
    "supplier_gstin": [
        "supplier gstin", "gstin", "gstin/uin of supplier", "party gstin",
        "vendor gstin", "from gstin",
    ],
    "supplier_name": ["supplier name", "party name", "vendor name", "supplier", "party"],
    "taxable_value": ["taxable value", "taxable amount", "assessable value", "taxable val"],
    "cgst": ["cgst", "central tax", "cgst amount"],
    "sgst": ["sgst", "state tax", "sgst amount"],
    "igst": ["igst", "integrated tax", "igst amount"],
    "cess": ["cess", "cess amount"],
    "hsn": ["hsn", "hsn/sac", "hsn code", "sac"],
    "quantity": ["quantity", "qty", "qnty"],
    "invoice_value": ["invoice value", "total value", "bill amount", "total invoice value", "gross total"],
}

TEMPLATE_SIGNATURES = {
    "tally": ["tally", "voucher type", "party ledger name"],
    "busy": ["busy", "material centre", " vch type"],
    "marg": ["marg", "pur bill", "purc"],
    "generic_gst": ["purchase register", "gst purchase", "b2b purchase"],
}

_profiles: Dict[str, dict] = {}


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


def detect_mapping(columns: List[str]) -> Dict[str, Optional[str]]:
    normalized = {_norm_col(c): c for c in columns}
    result: Dict[str, Optional[str]] = {}
    for field in MAPPING_FIELDS:
        if field in normalized:
            result[field] = normalized[field]
        else:
            result[field] = _find_column(columns, FIELD_ALIASES.get(field, []))
    return result


def detect_template(columns: List[str], sample_text: str = "") -> str:
    joined = " ".join(_norm_col(c) for c in columns) + " " + sample_text.lower()
    for template, markers in TEMPLATE_SIGNATURES.items():
        if any(m in joined for m in markers):
            return template
    return "generic"


def _detect_header_row(df: pd.DataFrame) -> int:
    for idx in range(min(15, len(df))):
        row_vals = [_norm_col(v) for v in df.iloc[idx].tolist() if str(v).strip()]
        joined = " ".join(row_vals)
        if any(alias in joined for alias in FIELD_ALIASES["invoice_number"]):
            return idx
    return 0


def read_raw_table(file_bytes: bytes, filename: str = "") -> Tuple[pd.DataFrame, List[str]]:
    name = filename.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
        df = df.dropna(how="all")
        return df, [str(c) for c in df.columns]

    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
    sheet = xl.sheet_names[0]
    raw = pd.read_excel(xl, sheet_name=sheet, header=None)
    header_row = _detect_header_row(raw)
    df = pd.read_excel(xl, sheet_name=sheet, header=header_row)
    df = df.dropna(how="all")
    return df, [str(c) for c in df.columns]


def preview_import(file_bytes: bytes, filename: str = "") -> dict:
    df, columns = read_raw_table(file_bytes, filename)
    detected = detect_mapping(columns)
    template = detect_template(columns)
    sample = df.head(5).fillna("").astype(str).to_dict(orient="records")
    return {
        "columns": columns,
        "detected_mapping": detected,
        "template": template,
        "row_count": len(df),
        "sample_rows": sample,
        "fields": MAPPING_FIELDS,
    }


def save_profile(profile_id: str, mapping: dict, template: str = "generic", label: str = "") -> dict:
    profile = {
        "profile_id": profile_id,
        "mapping": mapping,
        "template": template,
        "label": label or profile_id,
    }
    _profiles[profile_id] = profile
    return profile


def list_profiles() -> List[dict]:
    return list(_profiles.values())


def get_profile(profile_id: str) -> Optional[dict]:
    return _profiles.get(profile_id)


def clear_profiles() -> None:
    _profiles.clear()


def apply_mapping_to_normalized_workbook(
    file_bytes: bytes,
    mapping: Dict[str, Optional[str]],
    filename: str = "",
) -> bytes:
    """Normalize source file to standard column names for downstream comparison."""
    df, _ = read_raw_table(file_bytes, filename)
    out = pd.DataFrame()
    for field in MAPPING_FIELDS:
        col = mapping.get(field)
        if col and col in df.columns:
            out[field] = df[col]
        else:
            out[field] = ""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        out.to_excel(writer, sheet_name="PurchaseRegister", index=False)
    return buffer.getvalue()
