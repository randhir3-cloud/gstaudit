"""Shared fixtures for repository tests."""

from __future__ import annotations

import os

import pytest

from comparison.comparison_types import ComparisonResultType, RiskLevel
from comparison.result_models import AuditObservation, ComparisonRecord, ComparisonSummary, ComparisonResult
from config.settings import get_settings
from db.base import Base
from db.session import get_engine, reset_engine
from intelligence.models import IntelligenceFullResponse, IntelligenceSummary, AuditIntelligenceCards
from models.audit_session import AuditSession, DiscrepancySummary
from models.dealer_metadata import DealerMetadata
from models.investigation import InvestigationCase
from repositories.factory import get_repositories, reset_repositories
from services import audit_session_store, comparison_store, investigation_store
from intelligence import intelligence_store


@pytest.fixture(autouse=True)
def memory_provider(monkeypatch):
    monkeypatch.setenv("DATABASE_PROVIDER", "memory")
    get_settings.cache_clear()
    reset_repositories()
    reset_engine()
    yield
    audit_session_store.clear_sessions()


def sample_session(session_id: str = "session_repo_test") -> AuditSession:
    dealer = DealerMetadata(
        gstin="03AABCU9603R1ZX",
        legal_name="PERFECT FORGINGS",
        trade_name="PERFECT FORGINGS",
        financial_year="2023-24",
    )
    return AuditSession(
        session_id=session_id,
        dealer=dealer,
        financial_year="2023-24",
        audit_status="in_progress",
        discrepancies=DiscrepancySummary(total=0),
        created_at=AuditSession.now_iso(),
        updated_at=AuditSession.now_iso(),
    )


def sample_comparison_result(session_id: str = "session_repo_test") -> ComparisonResult:
    summary = ComparisonSummary(
        matched_count=5,
        missing_in_gstr1_count=2,
        overall_risk_score=42,
        risk_level=RiskLevel.MEDIUM,
    )
    records = [
        ComparisonRecord(
            result_type=ComparisonResultType.MISSING_IN_GSTR1,
            invoice_number="INV-001",
            normalized_invoice="INV001",
            gstin_gstr1="03AABCU9603R1ZX",
            risk_score=80,
            source_period="Apr-2023",
        )
    ]
    observations = [
        AuditObservation(
            invoice_number="INV-001",
            result_type=ComparisonResultType.MISSING_IN_GSTR1,
            observation="Invoice missing in GSTR-1",
            officer_action="Verify sales register",
        )
    ]
    return ComparisonResult(
        session_id=session_id,
        comparison_id="gstr1_ewb_outward",
        status="completed",
        summary=summary,
        records=records,
        observations=observations,
        completed_at=AuditSession.now_iso(),
    )


def sample_case(session_id: str = "session_repo_test", case_id: str = "case_001") -> InvestigationCase:
    return InvestigationCase(
        case_id=case_id,
        case_number="CASE-001",
        session_id=session_id,
        result_type="MISSING_IN_GSTR1",
        invoice_number="INV-001",
        normalized_invoice="INV001",
        supplier_gstin="03AABCU9603R1ZX",
        status="Pending",
        priority="High",
        priority_score=85,
        risk_score=80,
        source_period="Apr-2023",
        created_at=InvestigationCase.now_iso(),
        updated_at=InvestigationCase.now_iso(),
    )


def sample_intelligence() -> IntelligenceFullResponse:
    return IntelligenceFullResponse(
        session_id="session_repo_test",
        summary=IntelligenceSummary(
            cards=AuditIntelligenceCards(high_risk_cases=1),
        ),
    )


def postgres_available() -> bool:
    url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        return False
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


@pytest.fixture
def postgres_provider(monkeypatch):
    if not postgres_available():
        pytest.skip("PostgreSQL not available for repository tests")
    url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    monkeypatch.setenv("DATABASE_PROVIDER", "postgres")
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    reset_repositories()
    reset_engine()
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield get_repositories()
    Base.metadata.drop_all(engine)
    reset_engine()
    reset_repositories()
