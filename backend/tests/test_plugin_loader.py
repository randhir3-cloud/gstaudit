"""Plugin loader and registry tests."""

from __future__ import annotations

import pytest

from comparison.registry import comparison_registry
from plugins.sdk.loader import ensure_plugins_loaded, plugins_root, reset_plugins_for_tests
from plugins.sdk.registry import plugin_registry


@pytest.fixture(autouse=True)
def reset_plugins(monkeypatch):
    reset_plugins_for_tests()
    plugin_registry._manifests.clear()
    plugin_registry._routers.clear()
    plugin_registry._comparison_runners.clear()
    plugin_registry._datasets.clear()
    plugin_registry._comparison_pairs.clear()
    yield
    reset_plugins_for_tests()


def test_plugins_root_points_to_repo_plugins():
    root = plugins_root()
    assert root.name == "plugins"
    assert (root / "gstr1" / "manifest.json").exists()


def test_gstr1_plugin_registers_comparator_and_runner():
    import comparison.bootstrap  # noqa: F401
    ensure_plugins_loaded()
    assert "gstr1_ewb_outward" in comparison_registry.list_comparisons()
    assert plugin_registry.get_comparison_runner("gstr1_ewb_outward") is not None


def test_gstr1_manifest_loaded():
    ensure_plugins_loaded()
    manifest = plugin_registry.get_manifest("gstr1")
    assert manifest is not None
    assert manifest.name == "GSTR-1"
    assert manifest.datasets.get("gstr1") == "GSTR-1"


def test_plugin_catalog_includes_gstr1():
    ensure_plugins_loaded()
    catalog = plugin_registry.public_catalog()
    ids = [p["id"] for p in catalog["plugins"]]
    assert "gstr1" in ids
    assert "gstr2a" in ids
    assert catalog["datasets"].get("gstr1") == "GSTR-1"
    assert catalog["datasets"].get("gstr2a") == "GSTR-2A"
