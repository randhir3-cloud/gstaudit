"""Multi-Source Audit Engine (MSAE) tests."""

from __future__ import annotations

import time

import pytest

from services.comparison_store import clear_session, list_results, save_result
from services.msae_store import clear_all, clear_msae
from services.msae_service import (
    build_consolidated_report,
    correlate_findings,
    extract_plugin_findings,
    get_master_case,
    orchestrate_session,
)
from tests.msae_fixtures import SESSION, build_gstr1_result, build_gstr2a_result
from tests.repository_fixtures import sample_session
from services.audit_session_store import clear_sessions, upsert_session


@pytest.fixture(autouse=True)
def _reset():
    clear_sessions()
    clear_session(SESSION)
    clear_msae(SESSION)
    clear_all()
    yield
    clear_sessions()
    clear_session(SESSION)
    clear_msae(SESSION)
    clear_all()


class TestComparisonMultiSource:
    def test_list_results_returns_both_plugins(self):
        save_result(build_gstr1_result())
        save_result(build_gstr2a_result())
        results = list_results(SESSION)
        assert len(results) == 2
        ids = {r.comparison_id for r in results}
        assert "gstr1_ewb_outward" in ids
        assert "gstr2a_ewb_inward" in ids


class TestMSAEService:
    def test_extract_plugin_findings_from_multiple_sources(self):
        save_result(build_gstr1_result())
        save_result(build_gstr2a_result())
        findings = extract_plugin_findings(SESSION)
        assert len(findings) >= 4
        sources = {f.comparison_id for f in findings}
        assert len(sources) == 2

    def test_correlate_creates_master_cases_by_invoice(self):
        findings = extract_plugin_findings(SESSION, [build_gstr1_result(), build_gstr2a_result()])
        cases = correlate_findings(SESSION, findings, financial_year="2023-24")
        assert len(cases) >= 3
        inv1045 = next((c for c in cases if "1045" in c.normalized_invoice), None)
        assert inv1045 is not None
        assert inv1045.source_count >= 1

    def test_orchestrate_full_pipeline(self):
        session = sample_session(SESSION)
        upsert_session(session)
        save_result(build_gstr1_result())
        save_result(build_gstr2a_result())

        data = orchestrate_session(SESSION, force=True)
        assert data.summary.master_case_count >= 3
        assert data.summary.total_findings >= 4
        assert "gstr1_ewb_outward" in data.summary.sources_analyzed
        assert "gstr2a_ewb_inward" in data.summary.sources_analyzed
        assert data.summary.scores.dealer_risk_score > 0
        assert len(data.patterns) >= 1
        assert len(data.timeline) >= 1

    def test_master_case_detail_with_child_findings(self):
        save_result(build_gstr1_result())
        save_result(build_gstr2a_result())
        data = orchestrate_session(SESSION, force=True)
        case = data.master_cases[0]
        detail = get_master_case(SESSION, case.master_case_id)
        assert detail is not None
        assert len(detail.child_findings) >= 1

    def test_consolidated_report(self):
        save_result(build_gstr1_result())
        save_result(build_gstr2a_result())
        orchestrate_session(SESSION, force=True)
        report = build_consolidated_report(SESSION)
        assert "Consolidated audit" in report.executive_summary
        assert len(report.sources) == 2

    def test_performance_orchestration_under_one_second(self):
        save_result(build_gstr1_result())
        save_result(build_gstr2a_result())
        start = time.perf_counter()
        orchestrate_session(SESSION, force=True)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0


class TestMSAEAPI:
    def test_msae_endpoints(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        save_result(build_gstr1_result())
        save_result(build_gstr2a_result())
        qs = f"session_id={SESSION}"

        r = client.get(f"/api/msae?{qs}")
        assert r.status_code == 200
        body = r.json()
        assert body["summary"]["master_case_count"] >= 3

        r = client.get(f"/api/msae/summary?{qs}")
        assert r.status_code == 200

        r = client.get(f"/api/msae/cases?{qs}")
        assert r.status_code == 200
        assert r.json()["total"] >= 3

        r = client.get(f"/api/msae/patterns?{qs}")
        assert r.status_code == 200

        r = client.get(f"/api/msae/scores?{qs}")
        assert r.status_code == 200
        assert "dealer_risk_score" in r.json()["scores"]

        r = client.get(f"/api/msae/timeline?{qs}")
        assert r.status_code == 200

        r = client.get(f"/api/msae/report?{qs}")
        assert r.status_code == 200
        assert "executive_summary" in r.json()

        r = client.post(f"/api/msae/orchestrate?{qs}")
        assert r.status_code == 202
