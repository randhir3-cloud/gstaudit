"""GSTR-2A ↔ EWB Inward plugin registration."""

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


def _load_routes_module():
    return _load_module("gais_plugin_gstr2a_routes", "routes.py")


def register(registry, ctx) -> None:
    comparison = _load_module("gais_plugin_gstr2a_comparison", "comparison.py")
    ctx.comparisons.register(
        comparison.COMPARISON_ID,
        comparison.GSTR2A_EWB_INWARD_CONFIG,
        comparison.compare_gstr2a_vs_eway_inward,
    )
    registry.register_comparison_runner(comparison.COMPARISON_ID, comparison.run_gstr2a_eway_comparison_with_progress)
    registry.add_router(_load_routes_module().router)
