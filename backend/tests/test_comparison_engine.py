"""Tests for comparison registry and engine."""

import pytest

from comparison.engine import ComparisonEngine
from comparison.registry import comparison_registry
import comparison.bootstrap  # noqa: F401
from tests.comparison_fixtures import build_eway_comparison_workbook, build_gstr1_comparison_workbook


class TestRegistry:
    def test_gstr1_eway_registered(self):
        assert "gstr1_ewb_outward" in comparison_registry.list_comparisons()
        config = comparison_registry.get_config("gstr1_ewb_outward")
        assert config.left_dataset == "gstr1"


class TestEngine:
    def test_perfect_and_mismatch_scenarios(self):
        engine = ComparisonEngine()
        result = engine.run(
            "gstr1_ewb_outward",
            build_gstr1_comparison_workbook(),
            build_eway_comparison_workbook(),
            "session_test",
        )
        assert result.summary.matched_count >= 3
        assert result.summary.missing_in_gstr1_count >= 1
        assert result.summary.missing_in_eway_count >= 1
        assert result.summary.gstin_mismatch_count >= 0
        assert result.summary.value_mismatch_count >= 1
        assert result.summary.date_mismatch_count >= 1
        assert result.summary.duplicate_count + result.summary.multiple_matches_count >= 1
        assert len(result.observations) >= 1

    def test_unknown_comparison_raises(self):
        engine = ComparisonEngine()
        with pytest.raises(ValueError):
            engine.run("unknown", b"", b"", "s")
