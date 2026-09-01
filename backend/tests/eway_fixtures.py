"""Create synthetic E-Way Bill workbooks for classification tests."""

from __future__ import annotations

import io
from typing import List

import pandas as pd

DEALER_GSTIN = "03AABCU9603R1ZX"
OTHER_GSTIN = "29AABCT1332L000"


def build_eway_workbook(
    *,
    direction: str,
    filename_tag: str = "042023",
    row_count: int = 20,
) -> bytes:
    rows: List[dict] = []
    for i in range(row_count):
        if direction == "outward":
            from_gstin = DEALER_GSTIN
            to_gstin = OTHER_GSTIN
        elif direction == "inward":
            from_gstin = OTHER_GSTIN
            to_gstin = DEALER_GSTIN
        elif direction == "mixed":
            from_gstin = DEALER_GSTIN if i % 2 == 0 else OTHER_GSTIN
            to_gstin = DEALER_GSTIN if i % 2 == 1 else OTHER_GSTIN
        else:  # unknown / ambiguous both
            from_gstin = DEALER_GSTIN
            to_gstin = DEALER_GSTIN

        rows.append(
            {
                "EWB No & Dt": f"10158157903{i} - 11/04/2023 10:29:00",
                "From GSTIN & Name": from_gstin,
                "To GSTIN & Name": to_gstin,
                "Doc No": f"INV-{i:03d}",
            }
        )

    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


def outward_filename() -> str:
    return f"ewb_outward_{DEALER_GSTIN[:5]}_{'042023'}_report.xlsx"


def inward_filename() -> str:
    return f"ewb_inward_{DEALER_GSTIN[:5]}_{'052023'}_report.xlsx"
