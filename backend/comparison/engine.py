"""Comparison engine — runs registered comparators."""

from __future__ import annotations

from comparison.models import ComparisonConfig
from comparison.registry import comparison_registry
from comparison.result_models import ComparisonResult


class ComparisonEngine:
    def run(
        self,
        comparison_id: str,
        left_bytes: bytes,
        right_bytes: bytes,
        session_id: str,
        *,
        progress_callback=None,
        checkpoint: dict | None = None,
        cancel_check=None,
    ) -> ComparisonResult:
        fn = comparison_registry.get(comparison_id)
        if not fn:
            raise ValueError(f"Unknown comparison: {comparison_id}")
        config = comparison_registry.get_config(comparison_id) or ComparisonConfig(
            comparison_id=comparison_id,
            left_dataset="left",
            right_dataset="right",
            left_label="Left",
            right_label="Right",
        )
        return fn(
            config,
            left_bytes,
            right_bytes,
            session_id,
            progress_callback=progress_callback,
            checkpoint=checkpoint,
            cancel_check=cancel_check,
        )
