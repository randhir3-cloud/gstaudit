"""Tests for comparison normalizer."""

import pytest

from comparison.normalizer import (
    amounts_match,
    dates_match,
    normalize_amount,
    normalize_date,
    normalize_gstin,
    normalize_invoice,
)


class TestNormalizer:
    def test_normalize_invoice_variants(self):
        assert normalize_invoice("INV/001") == "INV001"
        assert normalize_invoice("inv-001") == "INV001"
        assert normalize_invoice("INV 001") == "INV001"

    def test_normalize_gstin(self):
        assert normalize_gstin(" 03aabfp3268j1zb ") == "03AABFP3268J1ZB"
        assert normalize_gstin("Name 03AABFP3268J1ZB Trade") == "03AABFP3268J1ZB"

    def test_normalize_date(self):
        assert normalize_date("11/04/2023") == "2023-04-11"
        assert normalize_date("2023-04-11") == "2023-04-11"

    def test_normalize_amount(self):
        assert normalize_amount("10,000.50") == 10000.5
        assert normalize_amount(" 5000 ") == 5000.0

    def test_amounts_match_tolerance(self):
        assert amounts_match(100.0, 100.5)
        assert not amounts_match(100.0, 102.0)

    def test_dates_match_tolerance(self):
        assert dates_match("2023-04-11", "2023-04-12")
        assert not dates_match("2023-04-11", "2023-04-15")
