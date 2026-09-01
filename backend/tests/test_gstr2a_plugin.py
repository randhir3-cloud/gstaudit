"""GSTR-2A plugin tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from comparison.registry import comparison_registry
from plugins.sdk.loader import ensure_plugins_loaded, reset_plugins_for_tests
from services.comparison_store import cache_workbook, clear_session, get_result
from services.audit_session_store import clear_sessions, get_session, upsert_session
from tests.gstr2a_fixtures import build_ewb_inward_comparison_workbook, build_gstr2a_comparison_workbook
from tests.repository_fixtures import sample_session

PLUGIN_DIR = Path(__file__).resolve().parents[2] / "plugins" / "gstr2a"
SESSION = "session_gstr2a_plugin_test"


def _load_plugin_module(name: str):
    path = PLUGIN_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_gstr2a_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _reset():
    reset_plugins_for_tests()
    clear_sessions()
    clear_session(SESSION)
    yield
    clear_sessions()
    clear_session(SESSION)


def test_plugin_registers_on_startup():
    ensure_plugins_loaded()
    assert "gstr2a_ewb_inward" in comparison_registry.list_comparisons()


def test_gstr2a_comparator_matches_and_finds_missing():
    ensure_plugins_loaded()
    comparison = _load_plugin_module("comparison")
    gstr2a = build_gstr2a_comparison_workbook()
    ewb = build_ewb_inward_comparison_workbook()
    result = comparison.compare_gstr2a_vs_eway_inward(
        comparison.GSTR2A_EWB_INWARD_CONFIG,
        gstr2a,
        ewb,
        SESSION,
    )
    assert result.comparison_id == "gstr2a_ewb_inward"
    assert result.summary.matched_count >= 2
    assert result.summary.missing_in_gstr1_count >= 1
    assert result.summary.missing_in_eway_count >= 1
    assert len(result.observations) >= 1


def test_gstr2a_sync_run_creates_investigation_cases():
    ensure_plugins_loaded()
    comparison = _load_plugin_module("comparison")
    session = sample_session(SESSION)
    upsert_session(session)
    cache_workbook(SESSION, "gstr2a", build_gstr2a_comparison_workbook())
    cache_workbook(SESSION, "ewb_inward", build_ewb_inward_comparison_workbook())

    result = comparison.run_gstr2a_eway_comparison_sync(SESSION)
    assert result.status == "completed"

    from services.investigation_service import sync_cases_from_comparison

    cases = sync_cases_from_comparison(SESSION)
    assert len(cases) >= 2
    assert get_result(SESSION) is not None


def test_gstr2a_validators_reject_empty_workbooks():
    validators = _load_plugin_module("validators")
    ok, msg = validators.validate_workbook_pair(None, b"data")
    assert not ok
    assert "GSTR-2A" in msg


def test_gstr2a_report_section_metadata():
    report = _load_plugin_module("report")
    meta = report.report_section_metadata()
    assert meta["section_id"] == "purchase_reconciliation"
    assert meta["comparison_id"] == "gstr2a_ewb_inward"
