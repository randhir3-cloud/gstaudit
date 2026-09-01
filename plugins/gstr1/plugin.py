"""GSTR-1 reference plugin — routes and job runner registration."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from services.comparison_service import run_gstr1_eway_comparison_with_progress


def _load_routes_module():
    routes_path = Path(__file__).resolve().parent / "routes.py"
    module_name = "gais_plugin_gstr1_routes"
    spec = importlib.util.spec_from_file_location(module_name, routes_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load GSTR-1 routes from {routes_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def register(registry, ctx) -> None:
    registry.register_comparison_runner("gstr1_ewb_outward", run_gstr1_eway_comparison_with_progress)
    routes = _load_routes_module()
    registry.add_router(routes.router)
