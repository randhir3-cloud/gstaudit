"""Background job orchestration service."""

from __future__ import annotations

import uuid
from typing import Callable, List, Optional

from jobs.broadcaster import job_broadcaster
from models.job import BackgroundJob, JobCreateRequest, JobLogEntry, JobProgress, JobStatus, JobType
from repositories.job_repository import get_job_repository


class JobCancelledError(Exception):
    pass


def _repo():
    return get_job_repository()


def is_job_cancelled(job_id: str) -> bool:
    job = _repo().get_by_id(job_id)
    return job is not None and job.status == JobStatus.CANCELLED


def _is_cancelled(job_id: str) -> bool:
    return is_job_cancelled(job_id)


def create_job(request: JobCreateRequest) -> BackgroundJob:
    job = BackgroundJob(
        job_id=str(uuid.uuid4()),
        session_id=request.session_id,
        job_type=request.job_type,
        title=request.title or _default_title(request.job_type),
        payload=request.payload,
        status=JobStatus.QUEUED,
        created_at=BackgroundJob.now_iso(),
        updated_at=BackgroundJob.now_iso(),
    )
    saved = _repo().create(job)
    _log(saved.job_id, "info", f"Job queued: {saved.title}")
    job_broadcaster.publish(saved.session_id, saved)
    return saved


def _default_title(job_type: JobType) -> str:
    return {
        JobType.MERGE: "Merge Workbooks",
        JobType.COMPARISON: "GSTR-1 ↔ EWB Comparison",
        JobType.INTELLIGENCE: "Audit Intelligence Analysis",
        JobType.REPORT: "Audit Report Generation",
        JobType.IMPORT: "Workbook Import",
        JobType.AI: "AI Analysis",
    }.get(job_type, "Background Job")


def get_job(job_id: str) -> Optional[BackgroundJob]:
    return _repo().get_by_id(job_id)


def list_jobs(session_id: Optional[str] = None, limit: int = 50) -> List[BackgroundJob]:
    if session_id:
        return _repo().list_by_session(session_id, limit=limit)
    return _repo().list_all(limit=limit)


def cancel_job(job_id: str) -> BackgroundJob:
    job = _repo().get_by_id(job_id)
    if not job:
        raise ValueError("Job not found")
    if job.status in (JobStatus.COMPLETED, JobStatus.CANCELLED):
        return job
    job.status = JobStatus.CANCELLED
    job.completed_at = BackgroundJob.now_iso()
    job.updated_at = BackgroundJob.now_iso()
    _log(job_id, "warning", "Job cancelled by user")
    updated = _repo().update(job)
    job_broadcaster.publish(updated.session_id, updated)
    return updated


def retry_job(job_id: str) -> BackgroundJob:
    job = _repo().get_by_id(job_id)
    if not job:
        raise ValueError("Job not found")
    if job.status not in (JobStatus.FAILED, JobStatus.CANCELLED):
        raise ValueError("Only failed or cancelled jobs can be retried")
    job.status = JobStatus.RETRYING
    job.error = ""
    job.retry_count += 1
    job.completed_at = None
    job.progress = JobProgress(started_at=None, updated_at=JobProgress.now_iso())
    job.updated_at = BackgroundJob.now_iso()
    _log(job_id, "info", f"Job retry #{job.retry_count}")
    updated = _repo().update(job)
    job_broadcaster.publish(updated.session_id, updated)
    return updated


def mark_running(job: BackgroundJob) -> BackgroundJob:
    job.status = JobStatus.RUNNING
    job.started_at = job.started_at or BackgroundJob.now_iso()
    job.progress.started_at = job.started_at
    job.updated_at = BackgroundJob.now_iso()
    updated = _repo().update(job)
    job_broadcaster.publish(updated.session_id, updated)
    return updated


def mark_completed(job: BackgroundJob, result_ref: Optional[dict] = None) -> BackgroundJob:
    job.status = JobStatus.COMPLETED
    job.completed_at = BackgroundJob.now_iso()
    job.updated_at = BackgroundJob.now_iso()
    job.progress.percent = 100
    job.progress.updated_at = JobProgress.now_iso()
    if result_ref:
        job.result_ref = result_ref
    _log(job.job_id, "info", "Job completed successfully")
    updated = _repo().update(job)
    job_broadcaster.publish(updated.session_id, updated)
    return updated


def mark_failed(job: BackgroundJob, error: str) -> BackgroundJob:
    job.status = JobStatus.FAILED
    job.error = error
    job.completed_at = BackgroundJob.now_iso()
    job.updated_at = BackgroundJob.now_iso()
    _log(job.job_id, "error", error)
    updated = _repo().update(job)
    job_broadcaster.publish(updated.session_id, updated)
    return updated


def update_progress(
    job_id: str,
    *,
    percent: int,
    stage: str,
    rows_processed: int = 0,
    rows_total: int = 0,
    eta_seconds: Optional[int] = None,
    checkpoint: Optional[dict] = None,
) -> None:
    if _is_cancelled(job_id):
        raise JobCancelledError("Job cancelled")
    progress = JobProgress(
        percent=min(100, max(0, percent)),
        stage=stage,
        rows_processed=rows_processed,
        rows_total=rows_total,
        eta_seconds=eta_seconds,
        updated_at=JobProgress.now_iso(),
    )
    job = _repo().get_by_id(job_id)
    if not job:
        return
    job.progress = progress
    if checkpoint is not None:
        job.checkpoint = checkpoint
    job.updated_at = BackgroundJob.now_iso()
    _repo().update(job)
    _repo().append_progress(job_id, progress)
    job_broadcaster.publish(job.session_id, job)


def make_progress_callback(job_id: str) -> Callable[..., None]:
    def callback(*, percent: int, stage: str, rows_processed: int = 0, rows_total: int = 0, eta_seconds: Optional[int] = None, checkpoint: Optional[dict] = None) -> None:
        update_progress(
            job_id,
            percent=percent,
            stage=stage,
            rows_processed=rows_processed,
            rows_total=rows_total,
            eta_seconds=eta_seconds,
            checkpoint=checkpoint,
        )

    return callback


def _log(job_id: str, level: str, message: str) -> None:
    entry = JobLogEntry(level=level, message=message, created_at=JobLogEntry.now_iso())
    _repo().append_log(job_id, entry)


def clear_jobs() -> None:
    _repo().clear_all()
