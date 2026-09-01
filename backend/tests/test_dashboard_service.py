"""Tests for dashboard service and month coverage."""

import pytest

from models.audit_session import AuditSession, UploadHistoryEntry
from models.dealer_metadata import DealerMetadata
from services.dashboard_service import (
    build_dashboard,
    build_dataset_record,
    compute_readiness,
)
from services.fy_months import month_coverage_from_filenames


DEALER = DealerMetadata(
    gstin="03AABFP3268J1ZB",
    legal_name="PERFECT FORGINGS",
    trade_name="PERFECT FORGINGS",
    financial_year="2024-25",
)


def _session_with_gstr1_files(filenames, rows=12548):
    session = AuditSession(
        session_id=AuditSession.build_session_id(DEALER.gstin, DEALER.financial_year),
        dealer=DEALER,
        financial_year="2024-25",
    )
    session.datasets["gstr1"] = build_dataset_record(
        "gstr1",
        source_files=filenames,
        dealer_gstin=DEALER.gstin,
        financial_year="2024-25",
        row_count=rows * len(filenames),
    )
    session.upload_history = [
        UploadHistoryEntry(
            timestamp="2026-07-09T10:00:00Z",
            dataset="gstr1",
            dataset_label="GSTR-1",
            filename=f,
            rows=rows,
            status="uploaded",
        )
        for f in filenames
    ]
    return session


class TestMonthCoverage:
    def test_twelve_month_grid(self):
        files = [
            "GSTR1_03AABFP3268J1ZB_042024_R1.xlsx",
            "GSTR1_03AABFP3268J1ZB_052024_R1.xlsx",
        ]
        coverage = month_coverage_from_filenames(files)
        assert len(coverage["months"]) == 12
        assert coverage["uploaded_count"] == 2

    def test_detects_duplicate_month(self):
        files = [
            "GSTR1_03AABFP3268J1ZB_042024_R1.xlsx",
            "GSTR1_03AABFP3268J1ZB_042024_R1_v2.xlsx",
        ]
        coverage = month_coverage_from_filenames(files)
        assert len(coverage["duplicate_months"]) == 1
        assert coverage["duplicate_months"][0]["month"] == "April 2024"
        assert coverage["duplicate_months"][0]["file_count"] == 2

    def test_detects_missing_months_in_range(self):
        files = [
            "GSTR1_03AABFP3268J1ZB_042024_R1.xlsx",
            "GSTR1_03AABFP3268J1ZB_062024_R1.xlsx",
        ]
        coverage = month_coverage_from_filenames(files)
        assert "May 2024" in coverage["missing_months"]


class TestDashboardService:
    def test_empty_dashboard(self):
        dash = build_dashboard(None)
        assert dash.audit_readiness_percent == 0.0
        assert dash.can_start_audit is False
        assert len(dash.dataset_cards) == 4

    def test_readiness_increases_with_uploads(self):
        session = _session_with_gstr1_files(
            [f"GSTR1_03AABFP3268J1ZB_{mm}2024_R1.xlsx" for mm in ("04", "05", "06", "07", "08", "09", "10", "11", "12", "01", "02", "03")]
        )
        session.datasets["gstr1"].merged = True
        session.datasets["gstr1"].row_count = 1200
        readiness = compute_readiness(session)
        assert readiness.gstr1 == 100.0

    def test_dashboard_shows_dealer_header(self):
        session = _session_with_gstr1_files(["GSTR1_03AABFP3268J1ZB_042024_R1.xlsx"])
        dash = build_dashboard(session)
        assert dash.gstin == DEALER.gstin
        assert "PERFECT FORGINGS" in dash.dealer_name
        assert dash.financial_year == "2024-25"

    def test_comparison_ready_when_pairs_merged(self):
        session = AuditSession(
            session_id="session_test",
            dealer=DEALER,
            financial_year="2024-25",
        )
        session.datasets["gstr1"] = build_dataset_record("gstr1", source_files=["a.xlsx"], merged=True)
        session.datasets["ewb_outward"] = build_dataset_record("ewb_outward", source_files=["b.xlsx"], merged=True)
        dash = build_dashboard(session)
        pair = next(c for c in dash.comparison_status if c.id == "gstr1_ewb_outward")
        assert pair.status == "ready"

    def test_discrepancies_zero_initially(self):
        dash = build_dashboard(_session_with_gstr1_files(["GSTR1_03AABFP3268J1ZB_042024_R1.xlsx"]))
        assert dash.discrepancies.total == 0

    def test_top_summary_includes_duplicate_stats(self):
        session = _session_with_gstr1_files(
            ["GSTR1_03AABFP3268J1ZB_042024_R1.xlsx", "GSTR1_03AABFP3268J1ZB_042024_R1_v2.xlsx"],
        )
        dash = build_dashboard(session)
        assert dash.top_summary.files_uploaded >= 2
        assert dash.top_summary.rows_imported > 0
        assert dash.duplicate_detection.duplicate_months >= 1

    def test_month_coverage_enriched_with_row_counts(self):
        session = _session_with_gstr1_files(["GSTR1_03AABFP3268J1ZB_042024_R1.xlsx"])
        dash = build_dashboard(session)
        apr = dash.month_coverage["gstr1"].months[0]
        assert apr.short == "Apr"
        assert apr.row_count == 12548
        assert apr.status in ("uploaded", "processing")

    def test_upload_health_and_workbook_summaries(self):
        session = _session_with_gstr1_files(["GSTR1_03AABFP3268J1ZB_042024_R1.xlsx"])
        dash = build_dashboard(session)
        assert dash.upload_health.score_percent > 0
        assert len(dash.upload_health.checks) >= 5
        assert len(dash.workbook_summaries) >= 1
        assert dash.dataset_keys == ["gstr1", "gstr2a", "ewb_outward", "ewb_inward"]

    def test_audit_not_ready_reason_when_incomplete(self):
        dash = build_dashboard(_session_with_gstr1_files(["GSTR1_03AABFP3268J1ZB_042024_R1.xlsx"]))
        assert dash.can_start_audit is False
        assert dash.audit_not_ready_reason
