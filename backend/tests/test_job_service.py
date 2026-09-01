"""Background job service tests."""

from __future__ import annotations

import pytest

from jobs.worker import JobWorker
from models.job import JobCreateRequest, JobStatus, JobType
from repositories.job_repository import get_job_repository, reset_job_repository
from services.job_service import cancel_job, create_job, get_job, retry_job


@pytest.fixture(autouse=True)
def clean_jobs(monkeypatch):
    monkeypatch.setenv("DATABASE_PROVIDER", "memory")
    from config.settings import get_settings
    from services.audit_session_store import clear_sessions
    from services.comparison_store import clear_session as clear_cmp

    get_settings.cache_clear()
    reset_job_repository()
    get_job_repository().clear_all()
    clear_sessions()
    clear_cmp("session_worker_test")
    yield
    get_job_repository().clear_all()
    clear_sessions()
    clear_cmp("session_worker_test")


class TestJobService:
    def test_create_and_get_job(self):
        job = create_job(JobCreateRequest(session_id="session_job_test", job_type=JobType.COMPARISON, title="Test Comparison"))
        loaded = get_job(job.job_id)
        assert loaded is not None
        assert loaded.status == JobStatus.QUEUED
        assert loaded.job_type == JobType.COMPARISON

    def test_cancel_job(self):
        job = create_job(JobCreateRequest(session_id="session_job_test", job_type=JobType.REPORT))
        cancelled = cancel_job(job.job_id)
        assert cancelled.status == JobStatus.CANCELLED

    def test_worker_executes_comparison_job(self):
        from models.audit_session import AuditSession
        from models.dealer_metadata import DealerMetadata
        from services.audit_session_store import upsert_session
        from services.comparison_store import cache_workbook
        from tests.comparison_fixtures import build_eway_comparison_workbook, build_gstr1_comparison_workbook

        session = AuditSession(session_id="session_worker_test", dealer=DealerMetadata(gstin="03AABCU9603R1ZX", financial_year="2023-24"), financial_year="2023-24")
        upsert_session(session)
        cache_workbook("session_worker_test", "gstr1", build_gstr1_comparison_workbook())
        cache_workbook("session_worker_test", "ewb_outward", build_eway_comparison_workbook())

        import base64

        job = create_job(
            JobCreateRequest(
                session_id="session_worker_test",
                job_type=JobType.COMPARISON,
                payload={
                    "gstr1_workbook_base64": base64.b64encode(build_gstr1_comparison_workbook()).decode(),
                    "ewb_outward_workbook_base64": base64.b64encode(build_eway_comparison_workbook()).decode(),
                },
            )
        )
        worker = JobWorker(worker_count=1)
        worker.start()
        import time

        deadline = time.time() + 30
        while time.time() < deadline:
            current = get_job(job.job_id)
            if current and current.status == JobStatus.COMPLETED:
                break
            time.sleep(0.3)
        worker.stop()
        final = get_job(job.job_id)
        assert final is not None
        assert final.status == JobStatus.COMPLETED
        assert final.progress.percent == 100

    def test_retry_failed_job(self):
        job = create_job(JobCreateRequest(session_id="session_retry", job_type=JobType.INTELLIGENCE))
        from services.job_service import mark_failed

        mark_failed(job, "simulated failure")
        retried = retry_job(job.job_id)
        assert retried.status == JobStatus.RETRYING
