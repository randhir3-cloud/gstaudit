"""Synthetic GSTR-1 and EWB workbooks for comparison tests."""

from __future__ import annotations

import io
from typing import List, Optional

import pandas as pd

DEALER_GSTIN = "03AABCU9603R1ZX"
RECIPIENT_GSTIN = "29AABCT1332L000"


def build_gstr1_comparison_workbook(invoices: Optional[List[dict]] = None) -> bytes:
    rows = invoices or [
        {"Invoice Number": "INV/001", "Invoice Date": "11/04/2023", "GSTIN/UIN of Recipient": RECIPIENT_GSTIN,
         "Taxable Value": 10000, "Invoice Value": 11800, "Integrated Tax": 1800, "Central Tax": 0, "State Tax": 0},
        {"Invoice Number": "INV-002", "Invoice Date": "12/04/2023", "GSTIN/UIN of Recipient": RECIPIENT_GSTIN,
         "Taxable Value": 5000, "Invoice Value": 5900, "Integrated Tax": 900, "Central Tax": 0, "State Tax": 0},
        {"Invoice Number": "INV003", "Invoice Date": "13/04/2023", "GSTIN/UIN of Recipient": RECIPIENT_GSTIN,
         "Taxable Value": 8000, "Invoice Value": 9440, "Integrated Tax": 1440, "Central Tax": 0, "State Tax": 0},
        {"Invoice Number": "INV-GSTIN", "Invoice Date": "14/04/2023", "GSTIN/UIN of Recipient": "07AABCS1429B1Z5",
         "Taxable Value": 2000, "Invoice Value": 2360, "Integrated Tax": 360, "Central Tax": 0, "State Tax": 0},
        {"Invoice Number": "INV-DATE", "Invoice Date": "01/05/2023", "GSTIN/UIN of Recipient": RECIPIENT_GSTIN,
         "Taxable Value": 3000, "Invoice Value": 3540, "Integrated Tax": 540, "Central Tax": 0, "State Tax": 0},
        {"Invoice Number": "INV-VAL", "Invoice Date": "15/04/2023", "GSTIN/UIN of Recipient": RECIPIENT_GSTIN,
         "Taxable Value": 4000, "Invoice Value": 4720, "Integrated Tax": 720, "Central Tax": 0, "State Tax": 0},
        {"Invoice Number": "INV-DUP", "Invoice Date": "16/04/2023", "GSTIN/UIN of Recipient": RECIPIENT_GSTIN,
         "Taxable Value": 1000, "Invoice Value": 1180, "Integrated Tax": 180, "Central Tax": 0, "State Tax": 0},
        {"Invoice Number": "INV-DUP", "Invoice Date": "16/04/2023", "GSTIN/UIN of Recipient": RECIPIENT_GSTIN,
         "Taxable Value": 1000, "Invoice Value": 1180, "Integrated Tax": 180, "Central Tax": 0, "State Tax": 0},
        {"Invoice Number": "INV-ONLY-GSTR1", "Invoice Date": "17/04/2023", "GSTIN/UIN of Recipient": RECIPIENT_GSTIN,
         "Taxable Value": 1500, "Invoice Value": 1770, "Integrated Tax": 270, "Central Tax": 0, "State Tax": 0},
    ]
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="B2B", index=False, startrow=0)
    return buffer.getvalue()


def build_eway_comparison_workbook(invoices: Optional[List[dict]] = None) -> bytes:
    rows = invoices or [
        {"EWB No & Dt": "101581579001 - 11/04/2023 10:29:00", "From GSTIN & Name": DEALER_GSTIN,
         "To GSTIN & Name": RECIPIENT_GSTIN, "Doc No": "INV 001", "Taxable Value": 10000, "Invoice Value": 11800,
         "IGST Amount": 1800, "CGST Amount": 0, "SGST Amount": 0},
        {"EWB No & Dt": "101581579002 - 12/04/2023 10:29:00", "From GSTIN & Name": DEALER_GSTIN,
         "To GSTIN & Name": RECIPIENT_GSTIN, "Doc No": "INV002", "Taxable Value": 5000, "Invoice Value": 5900,
         "IGST Amount": 900, "CGST Amount": 0, "SGST Amount": 0},
        {"EWB No & Dt": "101581579003 - 13/04/2023 10:29:00", "From GSTIN & Name": DEALER_GSTIN,
         "To GSTIN & Name": RECIPIENT_GSTIN, "Doc No": "INV003", "Taxable Value": 8000, "Invoice Value": 9440,
         "IGST Amount": 1440, "CGST Amount": 0, "SGST Amount": 0},
        {"EWB No & Dt": "101581579004 - 14/04/2023 10:29:00", "From GSTIN & Name": DEALER_GSTIN,
         "To GSTIN & Name": RECIPIENT_GSTIN, "Doc No": "INV-GSTIN", "Taxable Value": 2000, "Invoice Value": 2360,
         "IGST Amount": 360, "CGST Amount": 0, "SGST Amount": 0},
        {"EWB No & Dt": "101581579005 - 20/04/2023 10:29:00", "From GSTIN & Name": DEALER_GSTIN,
         "To GSTIN & Name": RECIPIENT_GSTIN, "Doc No": "INV-DATE", "Taxable Value": 3000, "Invoice Value": 3540,
         "IGST Amount": 540, "CGST Amount": 0, "SGST Amount": 0},
        {"EWB No & Dt": "101581579006 - 15/04/2023 10:29:00", "From GSTIN & Name": DEALER_GSTIN,
         "To GSTIN & Name": RECIPIENT_GSTIN, "Doc No": "INV-VAL", "Taxable Value": 4500, "Invoice Value": 5310,
         "IGST Amount": 810, "CGST Amount": 0, "SGST Amount": 0},
        {"EWB No & Dt": "101581579007 - 16/04/2023 10:29:00", "From GSTIN & Name": DEALER_GSTIN,
         "To GSTIN & Name": RECIPIENT_GSTIN, "Doc No": "INV-DUP", "Taxable Value": 1000, "Invoice Value": 1180,
         "IGST Amount": 180, "CGST Amount": 0, "SGST Amount": 0},
        {"EWB No & Dt": "101581579008 - 18/04/2023 10:29:00", "From GSTIN & Name": DEALER_GSTIN,
         "To GSTIN & Name": RECIPIENT_GSTIN, "Doc No": "INV-ONLY-EWB", "Taxable Value": 2500, "Invoice Value": 2950,
         "IGST Amount": 450, "CGST Amount": 0, "SGST Amount": 0},
    ]
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()
