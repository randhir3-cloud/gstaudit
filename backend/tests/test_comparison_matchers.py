"""Tests for comparison matchers."""

from comparison.comparators.date_matcher import compare_dates
from comparison.comparators.duplicate_matcher import find_duplicate_keys
from comparison.comparators.gstin_matcher import gstins_match
from comparison.comparators.invoice_matcher import build_invoice_index
from comparison.comparators.value_matcher import compare_values
from comparison.normalizer import normalize_invoice


class TestMatchers:
    def test_invoice_index(self):
        records = [{"normalized_invoice": normalize_invoice("INV-1")}, {"normalized_invoice": normalize_invoice("INV-2")}]
        index = build_invoice_index(records)
        assert len(index[normalize_invoice("INV-1")]) == 1

    def test_gstin_match(self):
        assert gstins_match("03AABFP3268J1ZB", "03AABFP3268J1ZB")
        assert not gstins_match("03AABFP3268J1ZB", "07AABCS1429B1Z5")

    def test_value_match(self):
        ok, diff = compare_values(
            {"taxable_value": 100, "invoice_value": 118, "igst": 18, "cgst": 0, "sgst": 0},
            {"taxable_value": 100, "invoice_value": 118, "igst": 18, "cgst": 0, "sgst": 0},
        )
        assert ok
        assert diff == 0

    def test_date_match(self):
        assert compare_dates("11/04/2023", "2023-04-11")

    def test_duplicate_keys(self):
        records = [{"normalized_invoice": "A"}, {"normalized_invoice": "A"}, {"normalized_invoice": "B"}]
        dupes = find_duplicate_keys(records)
        assert "A" in dupes
        assert "B" not in dupes
