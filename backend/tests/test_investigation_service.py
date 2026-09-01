"""Tests for investigation service."""

import base64

import pytest

from models.audit_session import AuditSession
from models.dealer_metadata import DealerMetadata
from models.investigation import BulkCaseUpdateRequest, CaseUpdateRequest, InvestigationFilterParams
from services.audit_session_store import clear_sessions, upsert_session
from services.comparison_service import run_gstr1_eway_comparison
from services.investigation_service import (
    bulk_update_cases,
    get_investigation,
    sync_cases_from_comparison,
    update_case,
)
from services.investigation_store import clear_session as clear_inv
from services.comparison_store import clear_session as clear_cmp
from tests.comparison_fixtures import build_eway_comparison_workbook, build_gstr1_comparison_workbook

SESSION = "session_inv_test"
DEALER = DealerMetadata(gstin="03AABCU9603R1ZX", legal_name="TEST", financial_year="2023-24")


@pytest.fixture(autouse=True)
def clean():
    clear_sessions()
    clear_inv(SESSION)
    clear_cmp(SESSION)
    yield
    clear_sessions()
    clear_inv(SESSION)
    clear_cmp(SESSION)


def _setup_comparison():
    session = AuditSession(session_id=SESSION, dealer=DEALER, financial_year="2023-24")
    upsert_session(session)
    run_gstr1_eway_comparison(
        SESSION,
        gstr1_workbook_base64=base64.b64encode(build_gstr1_comparison_workbook()).decode(),
        ewb_outward_workbook_base64=base64.b64encode(build_eway_comparison_workbook()).decode(),
    )


class TestInvestigationService:
    def test_sync_creates_cases_from_comparison(self):
        _setup_comparison()
        cases = sync_cases_from_comparison(SESSION)
        assert len(cases) > 0
        assert cases[0].case_number.startswith("CASE-")

    def test_list_with_category_filter(self):
        _setup_comparison()
        resp = get_investigation(InvestigationFilterParams(session_id=SESSION, category="MISSING_IN_GSTR1"))
        assert resp.summary.total > 0
        assert all(c.result_type == "MISSING_IN_GSTR1" for c in resp.cases)

    def test_update_case_remarks_and_status(self):
        _setup_comparison()
        cases = sync_cases_from_comparison(SESSION)
        case = cases[0]
        updated = update_case(case.case_id, CaseUpdateRequest(session_id=SESSION, status="Verified", officer_remarks="Checked books"))
        assert updated.status == "Verified"
        assert updated.officer_remarks == "Checked books"

    def test_bulk_update(self):
        _setup_comparison()
        cases = sync_cases_from_comparison(SESSION)
        ids = [c.case_id for c in cases[:2]]
        result = bulk_update_cases(BulkCaseUpdateRequest(session_id=SESSION, case_ids=ids, status="Pending", officer_remarks="Bulk"))
        assert len(result) == 2
