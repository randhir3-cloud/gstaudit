"""Tests for audit intelligence module."""

import base64

import pytest

from intelligence.intelligence_service import analyze_session, get_case_intelligence
from intelligence.document_recommender import recommend_documents
from intelligence.intelligence_store import clear_intelligence
from models.audit_session import AuditSession
from models.dealer_metadata import DealerMetadata
from services.audit_session_store import clear_sessions, upsert_session
from services.comparison_service import run_gstr1_eway_comparison
from services.comparison_store import clear_session as clear_cmp
from services.investigation_store import clear_session as clear_inv
from services.investigation_service import sync_cases_from_comparison
from tests.comparison_fixtures import build_eway_comparison_workbook, build_gstr1_comparison_workbook

SESSION = "session_intel_test"
DEALER = DealerMetadata(gstin="03AABCU9603R1ZX", legal_name="TEST", financial_year="2023-24")


@pytest.fixture(autouse=True)
def clean():
    clear_sessions()
    clear_inv(SESSION)
    clear_cmp(SESSION)
    clear_intelligence(SESSION)
    yield
    clear_sessions()
    clear_inv(SESSION)
    clear_cmp(SESSION)
    clear_intelligence(SESSION)


def _setup():
    session = AuditSession(session_id=SESSION, dealer=DEALER, financial_year="2023-24")
    upsert_session(session)
    run_gstr1_eway_comparison(
        SESSION,
        gstr1_workbook_base64=base64.b64encode(build_gstr1_comparison_workbook()).decode(),
        ewb_outward_workbook_base64=base64.b64encode(build_eway_comparison_workbook()).decode(),
    )
    sync_cases_from_comparison(SESSION)


class TestIntelligenceService:
    def test_analyze_session_returns_summary(self):
        _setup()
        data = analyze_session(SESSION)
        assert data.session_id == SESSION
        assert len(data.cases) > 0

    def test_case_intelligence_has_documents(self):
        _setup()
        data = analyze_session(SESSION)
        case = data.cases[0]
        assert case.recommended_documents
        assert case.priority in {"Critical", "High", "Medium", "Low"}
        assert 0 <= case.priority_score <= 100

    def test_get_case_intelligence(self):
        _setup()
        cases = sync_cases_from_comparison(SESSION)
        intel = get_case_intelligence(SESSION, cases[0].case_id)
        assert intel is not None

    def test_month_and_supplier_analysis(self):
        _setup()
        data = analyze_session(SESSION)
        assert isinstance(data.months, list)
        assert isinstance(data.suppliers, list)

    def test_document_recommender_missing_gstr1(self):
        docs = recommend_documents("MISSING_IN_GSTR1")
        assert "Sales Register" in docs

    def test_heatmaps_populated(self):
        _setup()
        data = analyze_session(SESSION)
        assert data.summary.heatmaps.categories
