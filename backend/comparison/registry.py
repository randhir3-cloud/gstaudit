"""Comparison registry — register comparators without changing the engine."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from comparison.models import ComparisonConfig
from comparison.result_models import ComparisonResult

ComparatorFn = Callable[[ComparisonConfig, bytes, bytes, str], ComparisonResult]


class ComparisonRegistry:
    def __init__(self) -> None:
        self._comparators: Dict[str, ComparatorFn] = {}
        self._configs: Dict[str, ComparisonConfig] = {}

    def register(self, comparison_id: str, config: ComparisonConfig, fn: ComparatorFn) -> None:
        self._comparators[comparison_id] = fn
        self._configs[comparison_id] = config

    def get(self, comparison_id: str) -> Optional[ComparatorFn]:
        return self._comparators.get(comparison_id)

    def get_config(self, comparison_id: str) -> Optional[ComparisonConfig]:
        return self._configs.get(comparison_id)

    def list_comparisons(self) -> List[str]:
        return list(self._comparators.keys())


comparison_registry = ComparisonRegistry()
