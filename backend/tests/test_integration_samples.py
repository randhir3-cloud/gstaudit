"""Integration tests against real sample workbooks when available."""

from pathlib import Path

import pytest

from services.dealer_metadata_service import extract_from_bytes

SAMPLE_DIR = Path(r"E:/gstaudit/Ujjwal SMall bank/Ujwal small 2A 22-23")
GSTR1_SAMPLE = SAMPLE_DIR.parent / "Ujwal small 2A 22-23"  # may not have gstr1


@pytest.mark.skipif(not SAMPLE_DIR.exists(), reason="Sample workbook directory not available")
def test_extract_real_gstr2a_workbook():
    files = sorted(SAMPLE_DIR.glob("*.xlsx"))
    assert files, "Expected at least one GSTR-2A sample file"
    dealer = extract_from_bytes(files[0].read_bytes(), "gstr2a")
    assert dealer.gstin == "03AABCU9603R1ZX"
    assert dealer.financial_year == "2022-23"
    assert "UJJIVAN" in dealer.legal_name.upper()
