import io
import base64

import pandas as pd
import pytest

from services.eway_errors import EwayValidationError
from services.eway_merge_service import (
    merge_eway_workflow,
    _build_suggested_filename,
)
from models.dealer_metadata import DealerMetadata

DEALER_GSTIN = "03AABCU9603R1ZX"
OTHER_GSTIN = "29AABCT1332L000"


def _build_sample_eway_workbook(direction: str = "outward") -> bytes:
    if direction == "inward":
        from_gstin, to_gstin = OTHER_GSTIN, DEALER_GSTIN
    else:
        from_gstin, to_gstin = DEALER_GSTIN, OTHER_GSTIN

    df = pd.DataFrame(
        {
            "EWB No & Dt": [
                "101581579034 - 11/04/2023 10:29:00",
                "101581579035 - 15/04/2023 11:00:00",
            ],
            "From GSTIN & Name": [from_gstin, from_gstin],
            "To GSTIN & Name": [to_gstin, to_gstin],
            "Doc No": ["INV-001", "INV-002"],
        }
    )
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


class TestEwayMergeService:
    def test_merge_outward_returns_full_payload(self):
        files = [
            ("outward_042023_ewb.xlsx", _build_sample_eway_workbook("outward")),
            ("outward_052023_ewb.xlsx", _build_sample_eway_workbook("outward")),
        ]
        result = merge_eway_workflow(files, "outward", ignore_missing=True, dealer_gstin=DEALER_GSTIN)

        assert result.workbook_id.startswith("wb_eway_outward_")
        assert result.row_count == 4
        assert len(result.sheet_list) >= 1
        assert result.suggested_filename.startswith("EWB_Outward_")
        assert result.summary.direction == "outward"
        assert result.summary.compare_target == "gstr1"
        assert result.workbook_base64
        assert len(result.preview) >= 1

    def test_merge_inward_is_independent(self):
        files = [("inward_042023_ewb.xlsx", _build_sample_eway_workbook("inward"))]
        result = merge_eway_workflow(files, "inward", ignore_missing=True, dealer_gstin=DEALER_GSTIN)

        assert result.summary.direction == "inward"
        assert result.summary.compare_target == "gstr2a"
        assert result.suggested_filename.startswith("EWB_Inward_")

    def test_missing_months_raises_warning_error(self):
        files = [
            ("outward_042023_ewb.xlsx", _build_sample_eway_workbook("outward")),
            ("outward_062023_ewb.xlsx", _build_sample_eway_workbook("outward")),
        ]
        with pytest.raises(EwayValidationError) as exc:
            merge_eway_workflow(files, "outward", ignore_missing=False, dealer_gstin=DEALER_GSTIN)
        assert exc.value.error_type == "missing_months"
        assert exc.value.missing

    def test_suggested_filename_uses_dealer_and_fy(self):
        dealer = DealerMetadata(gstin="03AABCU9603R1ZX", financial_year="2022-23")
        name = _build_suggested_filename("outward", dealer, "2022-23")
        assert name == "EWB_Outward_03AABCU9603R1ZX_2022-23_Merged.xlsx"
