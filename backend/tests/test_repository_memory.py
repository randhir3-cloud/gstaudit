"""Memory repository layer tests."""

from __future__ import annotations

from repositories.factory import get_repositories
from tests.repository_fixtures import (
    sample_case,
    sample_comparison_result,
    sample_intelligence,
    sample_session,
)


class TestMemoryRepositories:
    def test_audit_session_crud(self):
        repos = get_repositories()
        session = sample_session()
        repos.audit_session.create(session)
        loaded = repos.audit_session.get_by_id(session.session_id)
        assert loaded is not None
        assert loaded.dealer.gstin == "03AABCU9603R1ZX"
        repos.audit_session.set_active_session_id(session.session_id)
        assert repos.audit_session.get_active_session_id() == session.session_id
        found = repos.audit_session.search(gstin="03AABCU9603R1ZX", financial_year="2023-24")
        assert len(found) == 1
        repos.audit_session.delete(session.session_id)
        assert repos.audit_session.get_by_id(session.session_id) is None

    def test_workbook_cache(self):
        repos = get_repositories()
        sid = "session_wb_test"
        repos.workbook.cache_workbook(sid, "gstr1", b"excel-bytes")
        assert repos.workbook.get_workbook(sid, "gstr1") == b"excel-bytes"
        repos.workbook.delete_by_session(sid)
        assert repos.workbook.get_workbook(sid, "gstr1") is None

    def test_comparison_save_and_search(self):
        repos = get_repositories()
        result = sample_comparison_result("session_cmp_test")
        repos.comparison.save_result(result)
        loaded = repos.comparison.get_result("session_cmp_test")
        assert loaded is not None
        assert loaded.summary.matched_count == 5
        assert len(loaded.records) == 1
        assert len(loaded.observations) == 1
        assert repos.comparison.get_status("session_cmp_test") == "completed"
        page = repos.comparison.search_records("session_cmp_test", result_type="MISSING_IN_GSTR1")
        assert page.total == 1
        assert page.items[0].invoice_number == "INV-001"

    def test_investigation_crud_bulk_search(self):
        repos = get_repositories()
        sid = "session_inv_test"
        case1 = sample_case(sid, "case_a")
        case2 = sample_case(sid, "case_b")
        repos.investigation.create(case1)
        repos.investigation.create(case2)
        assert len(repos.investigation.get_by_session(sid)) == 2
        updated = repos.investigation.bulk_update(sid, ["case_a", "case_b"], {"status": "Verified"})
        assert updated == 2
        page = repos.investigation.search(sid, status="Verified", limit=10)
        assert page.total == 2
        repos.investigation.delete(sid, "case_a")
        assert repos.investigation.get_by_id(sid, "case_a") is None

    def test_intelligence_cache(self):
        repos = get_repositories()
        sid = "session_intel_test"
        data = sample_intelligence()
        data.session_id = sid
        repos.intelligence.save(sid, data)
        loaded = repos.intelligence.get(sid)
        assert loaded is not None
        assert loaded.summary.cards.high_risk_cases == 1
        repos.intelligence.delete(sid)
        assert repos.intelligence.get(sid) is None

    def test_store_delegation_unchanged_api(self):
        from services.audit_session_store import get_session, upsert_session, clear_sessions
        from services.comparison_store import cache_workbook, get_workbook, save_result, get_result, clear_session
        from services.investigation_store import save_case, get_case, list_cases, clear_session as clear_inv

        session = sample_session("session_delegate_test")
        upsert_session(session)
        assert get_session("session_delegate_test") is not None
        cache_workbook("session_delegate_test", "gstr1", b"data")
        assert get_workbook("session_delegate_test", "gstr1") == b"data"
        save_result(sample_comparison_result("session_delegate_test"))
        assert get_result("session_delegate_test") is not None
        case = sample_case("session_delegate_test", "case_delegate")
        save_case(case)
        assert get_case("session_delegate_test", "case_delegate") is not None
        assert len(list_cases("session_delegate_test")) == 1
        clear_session("session_delegate_test")
        clear_inv("session_delegate_test")
        clear_sessions()
