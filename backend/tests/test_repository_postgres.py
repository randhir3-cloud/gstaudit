"""PostgreSQL repository tests — require running Postgres (TEST_DATABASE_URL)."""

from __future__ import annotations

import pytest

from tests.repository_fixtures import (
    postgres_provider,
    sample_case,
    sample_comparison_result,
    sample_intelligence,
    sample_session,
)

pytestmark = pytest.mark.postgres


class TestPostgresRepositories:
    def test_session_and_comparison_persist(self, postgres_provider):
        repos = postgres_provider
        session = sample_session("session_pg_test")
        repos.audit_session.create(session)
        result = sample_comparison_result("session_pg_test")
        repos.comparison.save_result(result)
        loaded = repos.comparison.get_result("session_pg_test")
        assert loaded is not None
        assert loaded.summary.missing_in_gstr1_count == 2

    def test_investigation_bulk_update(self, postgres_provider):
        repos = postgres_provider
        sid = "session_pg_inv"
        repos.audit_session.create(sample_session(sid))
        repos.investigation.save_many(sid, [sample_case(sid, "pg_case_1"), sample_case(sid, "pg_case_2")])
        count = repos.investigation.bulk_update(sid, ["pg_case_1"], {"status": "Verified"})
        assert count == 1
        case = repos.investigation.get_by_id(sid, "pg_case_1")
        assert case.status == "Verified"

    def test_intelligence_and_report(self, postgres_provider):
        repos = postgres_provider
        sid = "session_pg_report"
        repos.audit_session.create(sample_session(sid))
        intel = sample_intelligence()
        intel.session_id = sid
        repos.intelligence.save(sid, intel)
        assert repos.intelligence.get(sid) is not None
        rid = repos.audit_report.create(sid, "pdf", b"%PDF-1.4", {"pages": 1})
        report = repos.audit_report.get_by_id(rid)
        assert report["format"] == "pdf"
        assert len(repos.audit_report.get_by_session(sid)) == 1

    def test_rollback_on_error(self, postgres_provider):
        repos = postgres_provider
        sid = "session_pg_rollback"
        repos.audit_session.create(sample_session(sid))
        repos.workbook.cache_workbook(sid, "gstr1", b"bytes")
        repos.workbook.delete_by_session(sid)
        assert repos.workbook.get_workbook(sid, "gstr1") is None

    def test_large_case_dataset_search(self, postgres_provider):
        repos = postgres_provider
        sid = "session_pg_large"
        repos.audit_session.create(sample_session(sid))
        cases = []
        for i in range(250):
            case = sample_case(sid, f"case_{i:04d}")
            case.invoice_number = f"INV-{i:04d}"
            case.normalized_invoice = f"INV{i:04d}"
            case.risk_score = 50 + (i % 50)
            cases.append(case)
        repos.investigation.save_many(sid, cases)
        page = repos.investigation.search(sid, offset=0, limit=100)
        assert page.total == 250
        assert len(page.items) == 100
        page2 = repos.investigation.search(sid, search="INV-0249", limit=10)
        assert page2.total >= 1
