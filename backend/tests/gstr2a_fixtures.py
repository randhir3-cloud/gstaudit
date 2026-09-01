"""Synthetic GSTR-2A and EWB inward workbooks for plugin tests."""

from __future__ import annotations

import io
from typing import List, Optional

import pandas as pd

SUPPLIER_GSTIN = "29AABCT1332L000"
DEALER_GSTIN = "03AABCU9603R1ZX"


def build_gstr2a_comparison_workbook(invoices: Optional[List[dict]] = None) -> bytes:
    rows = invoices or [
        {
            "Invoice Number": "PINV/001",
            "Invoice Date": "11/05/2023",
            "GSTIN/UIN of Supplier": SUPPLIER_GSTIN,
            "Taxable Value": 10000,
            "Invoice Value": 11800,
            "Integrated Tax": 1800,
            "Central Tax": 0,
            "State Tax": 0,
            "HSN/SAC": "8471",
        },
        {
            "Invoice Number": "PINV-002",
            "Invoice Date": "12/05/2023",
            "GSTIN/UIN of Supplier": SUPPLIER_GSTIN,
            "Taxable Value": 5000,
            "Invoice Value": 5900,
            "Integrated Tax": 900,
            "Central Tax": 0,
            "State Tax": 0,
            "HSN/SAC": "8471",
        },
        {
            "Invoice Number": "PINV-ONLY-2A",
            "Invoice Date": "13/05/2023",
            "GSTIN/UIN of Supplier": SUPPLIER_GSTIN,
            "Taxable Value": 1500,
            "Invoice Value": 1770,
            "Integrated Tax": 270,
            "Central Tax": 0,
            "State Tax": 0,
            "HSN/SAC": "8471",
        },
    ]
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="B2B", index=False, startrow=0)
    return buffer.getvalue()


def build_ewb_inward_comparison_workbook(invoices: Optional[List[dict]] = None) -> bytes:
    rows = invoices or [
        {
            "EWB No & Dt": "201581579001 - 11/05/2023 10:29:00",
            "From GSTIN & Name": SUPPLIER_GSTIN,
            "To GSTIN & Name": DEALER_GSTIN,
            "Doc No": "PINV 001",
            "Taxable Value": 10000,
            "Invoice Value": 11800,
            "IGST Amount": 1800,
            "CGST Amount": 0,
            "SGST Amount": 0,
        },
        {
            "EWB No & Dt": "201581579002 - 12/05/2023 10:29:00",
            "From GSTIN & Name": SUPPLIER_GSTIN,
            "To GSTIN & Name": DEALER_GSTIN,
            "Doc No": "PINV002",
            "Taxable Value": 5000,
            "Invoice Value": 5900,
            "IGST Amount": 900,
            "CGST Amount": 0,
            "SGST Amount": 0,
        },
        {
            "EWB No & Dt": "201581579003 - 14/05/2023 10:29:00",
            "From GSTIN & Name": SUPPLIER_GSTIN,
            "To GSTIN & Name": DEALER_GSTIN,
            "Doc No": "PINV-ONLY-EWB",
            "Taxable Value": 2500,
            "Invoice Value": 2950,
            "IGST Amount": 450,
            "CGST Amount": 0,
            "SGST Amount": 0,
        },
    ]
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()
