"""Synthetic Purchase Register workbooks for plugin tests."""

from __future__ import annotations

import io
from typing import List, Optional

import pandas as pd

from tests.gstr2a_fixtures import SUPPLIER_GSTIN


def build_purchase_register_workbook(invoices: Optional[List[dict]] = None) -> bytes:
    rows = invoices or [
        {
            "Invoice Number": "PINV/001",
            "Invoice Date": "11/05/2023",
            "Supplier GSTIN": SUPPLIER_GSTIN,
            "Supplier Name": "Test Supplier Pvt Ltd",
            "Taxable Value": 10000,
            "IGST": 1800,
            "CGST": 0,
            "SGST": 0,
            "Invoice Value": 11800,
            "HSN": "8471",
        },
        {
            "Invoice Number": "PINV-002",
            "Invoice Date": "12/05/2023",
            "Supplier GSTIN": SUPPLIER_GSTIN,
            "Supplier Name": "Test Supplier Pvt Ltd",
            "Taxable Value": 5000,
            "IGST": 900,
            "CGST": 0,
            "SGST": 0,
            "Invoice Value": 5900,
            "HSN": "8471",
        },
        {
            "Invoice Number": "PINV-ONLY-PR",
            "Invoice Date": "15/05/2023",
            "Supplier GSTIN": SUPPLIER_GSTIN,
            "Supplier Name": "Test Supplier Pvt Ltd",
            "Taxable Value": 800,
            "IGST": 144,
            "CGST": 0,
            "SGST": 0,
            "Invoice Value": 944,
            "HSN": "8471",
        },
    ]
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Purchase Register", index=False)
    return buffer.getvalue()
