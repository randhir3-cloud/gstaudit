"""Tests for risk and observation engines."""

from comparison.comparators.observation_generator import generate_observations
from comparison.comparators.risk_engine import overall_risk_level, score_result
from comparison.comparison_types import ComparisonResultType, RiskLevel
from comparison.result_models import ComparisonRecord


class TestRiskEngine:
    def test_scores(self):
        assert score_result(ComparisonResultType.MISSING_IN_GSTR1) == 100
        assert score_result(ComparisonResultType.MISSING_IN_EWAY) == 95
        assert score_result(ComparisonResultType.VALUE_MISMATCH, 0.5) == 10

    def test_risk_levels(self):
        assert overall_risk_level([100]) == RiskLevel.CRITICAL
        assert overall_risk_level([80]) == RiskLevel.HIGH
        assert overall_risk_level([40]) == RiskLevel.MEDIUM
        assert overall_risk_level([10]) == RiskLevel.LOW


class TestObservations:
    def test_generates_observation(self):
        rec = ComparisonRecord(
            result_type=ComparisonResultType.MISSING_IN_GSTR1,
            invoice_number="INV458",
            normalized_invoice="INV458",
        )
        obs = generate_observations([rec])
        assert len(obs) == 1
        assert "INV458" in obs[0].observation
        assert obs[0].possible_reasons
