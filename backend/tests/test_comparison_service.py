"""Integration tests for comparison API service."""

import base64

import pytest

from models.audit_session import AuditSession
from models.dealer_metadata import DealerMetadata
from services.audit_session_store import clear_sessions, upsert_session
from services.comparison_service import (
    get_comparison_details,
    get_full_comparison,
    get_observations,
    get_risk,
    run_gstr1_eway_comparison,
)
from services.dashboard_service import build_dashboard, ensure_session_datasets
from tests.comparison_fixtures import build_eway_comparison_workbook, build_gstr1_comparison_workbook

DEALER = DealerMetadata(gstin="03AABCU9603R1ZX", legal_name="TEST", financial_year="2023-24")


@pytest.fixture(autouse=True)
def _clean():
    clear_sessions()
    yield
    clear_sessions()


def _merged_session():
    session = AuditSession(
        session_id="session_cmp_test",
        dealer=DEALER,
        financial_year="2023-24",
    )
    ensure_session_datasets(session)
    session.datasets["gstr1"].merged = True
    session.datasets["gstr1"].source_files = ["gstr1.xlsx"]
    session.datasets["ewb_outward"].merged = True
    session.datasets["ewb_outward"].source_files = ["ewb.xlsx"]
    upsert_session(session)
    return session


class TestComparisonService:
    def test_run_updates_dashboard(self):
        session = _merged_session()
        gstr1_b64 = base64.b64encode(build_gstr1_comparison_workbook()).decode()
        ewb_b64 = base64.b64encode(build_eway_comparison_workbook()).decode()

        result = run_gstr1_eway_comparison(
            session.session_id,
            gstr1_workbook_base64=gstr1_b64,
            ewb_outward_workbook_base64=ewb_b64,
        )
        assert result.status == "completed"
        dash = build_dashboard(session)
        assert dash.discrepancies.missing_invoice >= 1
        assert dash.discrepancies.risk_score > 0
        pair = next(c for c in dash.comparison_status if c.id == "gstr1_ewb_outward")
        assert pair.status == "completed"

    def test_detail_and_risk_endpoints(self):
        session = _merged_session()
        run_gstr1_eway_comparison(
            session.session_id,
            gstr1_workbook_base64=base64.b64encode(build_gstr1_comparison_workbook()).decode(),
            ewb_outward_workbook_base64=base64.b64encode(build_eway_comparison_workbook()).decode(),
        )
        full = get_full_comparison(session.session_id)
        assert full["status"] == "completed"
        details = get_comparison_details(session.session_id, result_type="MISSING_IN_GSTR1")
        assert details.total >= 1
        risk = get_risk(session.session_id)
        assert risk["overall_risk_score"] > 0
        obs = get_observations(session.session_id)
        assert len(obs) >= 1
