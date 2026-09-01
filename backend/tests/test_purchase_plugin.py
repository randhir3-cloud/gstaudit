"""Purchase Register plugin tests."""

from __future__ import annotations

import base64
import importlib.util
from pathlib import Path

import pytest

from comparison.registry import comparison_registry
from plugins.sdk.loader import ensure_plugins_loaded, reset_plugins_for_tests
from services.comparison_store import cache_workbook, clear_session, get_result
from services.audit_session_store import clear_sessions, upsert_session
from tests.gstr2a_fixtures import build_ewb_inward_comparison_workbook, build_gstr2a_comparison_workbook
from tests.purchase_fixtures import build_purchase_register_workbook
from tests.repository_fixtures import sample_session

PLUGIN_DIR = Path(__file__).resolve().parents[2] / "plugins" / "purchase"
SESSION = "session_purchase_plugin_test"


def _load_plugin_module(name: str):
    path = PLUGIN_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_purchase_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _reset():
    reset_plugins_for_tests()
    clear_sessions()
    clear_session(SESSION)
    mapping = _load_plugin_module("mapping")
    mapping.clear_profiles()
    yield
    clear_sessions()
    clear_session(SESSION)
    mapping.clear_profiles()


def test_plugin_registers_on_startup():
    ensure_plugins_loaded()
    ids = comparison_registry.list_comparisons()
    assert "purchase_register_vs_gstr2a" in ids
    assert "purchase_register_vs_ewb_inward" in ids


def test_mapping_detects_tally_like_columns():
    mapping = _load_plugin_module("mapping")
    columns = [
        "Invoice Number",
        "Invoice Date",
        "Supplier GSTIN",
        "Supplier Name",
        "Taxable Value",
        "IGST",
        "CGST",
        "SGST",
        "Invoice Value",
    ]
    detected = mapping.detect_mapping(columns)
    assert detected["invoice_number"] == "Invoice Number"
    assert detected["supplier_gstin"] == "Supplier GSTIN"


def test_purchase_gstr2a_comparator_matches_and_finds_missing():
    ensure_plugins_loaded()
    comparison = _load_plugin_module("comparison")
    purchase = build_purchase_register_workbook()
    gstr2a = build_gstr2a_comparison_workbook()
    result = comparison.compare_purchase_vs_gstr2a(
        comparison.PURCHASE_GSTR2A_CONFIG,
        purchase,
        gstr2a,
        SESSION,
    )
    assert result.comparison_id == "purchase_register_vs_gstr2a"
    assert result.summary.matched_count >= 2
    assert result.summary.missing_in_gstr1_count >= 1
    assert result.summary.missing_in_eway_count >= 1
    assert len(result.observations) >= 1


def test_purchase_ewb_comparator_matches_and_finds_missing():
    ensure_plugins_loaded()
    comparison = _load_plugin_module("comparison")
    purchase = build_purchase_register_workbook()
    ewb = build_ewb_inward_comparison_workbook()
    result = comparison.compare_purchase_vs_ewb_inward(
        comparison.PURCHASE_EWB_CONFIG,
        purchase,
        ewb,
        SESSION,
    )
    assert result.comparison_id == "purchase_register_vs_ewb_inward"
    assert result.summary.matched_count >= 2
    assert result.summary.missing_in_eway_count >= 1


def test_purchase_sync_run_creates_investigation_cases():
    ensure_plugins_loaded()
    comparison = _load_plugin_module("comparison")
    session = sample_session(SESSION)
    upsert_session(session)
    cache_workbook(SESSION, "purchase_register", build_purchase_register_workbook())
    cache_workbook(SESSION, "gstr2a", build_gstr2a_comparison_workbook())

    result = comparison.run_purchase_gstr2a_sync(SESSION)
    assert result.status == "completed"

    from services.investigation_service import sync_cases_from_comparison

    cases = sync_cases_from_comparison(SESSION)
    assert len(cases) >= 2
    assert get_result(SESSION) is not None


def test_import_preview_and_profile():
    mapping = _load_plugin_module("mapping")
    raw = build_purchase_register_workbook()
    preview = mapping.preview_import(raw, "purchase.xlsx")
    assert preview["row_count"] == 3
    assert preview["detected_mapping"]["invoice_number"]
    profile = mapping.save_profile("test-profile", preview["detected_mapping"], preview["template"])
    assert mapping.get_profile("test-profile") == profile


def test_purchase_report_section_metadata():
    report = _load_plugin_module("report")
    meta = report.report_section_metadata()
    assert meta["section_id"] == "purchase_register_reconciliation"
    assert "purchase_register_vs_gstr2a" in meta["comparison_ids"]
