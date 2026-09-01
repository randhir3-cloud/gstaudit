"""Purchase Register plugin registration."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module(name: str, filename: str):
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def register(registry, ctx) -> None:
    comparison = _load_module("gais_plugin_purchase_comparison", "comparison.py")
    ctx.comparisons.register(
        comparison.COMPARISON_ID_GSTR2A,
        comparison.PURCHASE_GSTR2A_CONFIG,
        comparison.compare_purchase_vs_gstr2a,
    )
    ctx.comparisons.register(
        comparison.COMPARISON_ID_EWB,
        comparison.PURCHASE_EWB_CONFIG,
        comparison.compare_purchase_vs_ewb_inward,
    )
    registry.register_comparison_runner(
        comparison.COMPARISON_ID_GSTR2A,
        comparison.run_purchase_gstr2a_with_progress,
    )
    registry.register_comparison_runner(
        comparison.COMPARISON_ID_EWB,
        comparison.run_purchase_ewb_with_progress,
    )
    registry.add_router(_load_module("gais_plugin_purchase_routes", "routes.py").router)
