"""Job repository — memory and PostgreSQL implementations."""

from __future__ import annotations

import threading
import uuid
from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import delete, select, update

from db.orm.models import JobLogORM, JobORM, JobProgressORM
from db.session import session_scope
from models.job import BackgroundJob, JobLogEntry, JobProgress, JobStatus, JobType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobRepository(ABC):
    @abstractmethod
    def create(self, job: BackgroundJob) -> BackgroundJob: ...

    @abstractmethod
    def update(self, job: BackgroundJob) -> BackgroundJob: ...

    @abstractmethod
    def get_by_id(self, job_id: str) -> Optional[BackgroundJob]: ...

    @abstractmethod
    def list_by_session(self, session_id: str, limit: int = 50) -> List[BackgroundJob]: ...

    @abstractmethod
    def list_all(self, limit: int = 100) -> List[BackgroundJob]: ...

    @abstractmethod
    def claim_next_queued(self) -> Optional[BackgroundJob]: ...

    @abstractmethod
    def append_log(self, job_id: str, entry: JobLogEntry) -> None: ...

    @abstractmethod
    def append_progress(self, job_id: str, progress: JobProgress) -> None: ...

    @abstractmethod
    def clear_all(self) -> None: ...


def _job_to_model(row: JobORM, logs: Optional[List[JobLogORM]] = None) -> BackgroundJob:
    return BackgroundJob(
        job_id=str(row.job_id),
        session_id=row.session_id,
        job_type=JobType(row.job_type),
        status=JobStatus(row.status),
        title=row.title,
        payload=row.payload or {},
        result_ref=row.result_ref or {},
        checkpoint=row.checkpoint or {},
        error=row.error or "",
        progress=JobProgress(
            percent=row.progress_percent,
            stage=row.progress_stage or "",
            rows_processed=row.rows_processed,
            rows_total=row.rows_total,
            eta_seconds=row.eta_seconds,
            started_at=row.started_at.isoformat() if row.started_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else "",
        ),
        logs=[
            JobLogEntry(level=l.level, message=l.message, created_at=l.created_at.isoformat())
            for l in (logs or [])
        ],
        retry_count=row.retry_count,
        max_retries=row.max_retries,
        created_at=row.created_at.isoformat() if row.created_at else "",
        started_at=row.started_at.isoformat() if row.started_at else None,
        completed_at=row.completed_at.isoformat() if row.completed_at else None,
        updated_at=row.updated_at.isoformat() if row.updated_at else "",
    )


def _model_to_row(job: BackgroundJob) -> JobORM:
    return JobORM(
        job_id=uuid.UUID(job.job_id),
        session_id=job.session_id,
        job_type=job.job_type.value,
        status=job.status.value,
        title=job.title,
        payload=job.payload,
        result_ref=job.result_ref,
        checkpoint=job.checkpoint,
        error=job.error,
        progress_percent=job.progress.percent,
        progress_stage=job.progress.stage,
        rows_processed=job.progress.rows_processed,
        rows_total=job.progress.rows_total,
        eta_seconds=job.progress.eta_seconds,
        retry_count=job.retry_count,
        max_retries=job.max_retries,
    )


class MemoryJobRepository(JobRepository):
    def __init__(self) -> None:
        self._jobs: dict[str, BackgroundJob] = {}
        self._lock = threading.Lock()

    def create(self, job: BackgroundJob) -> BackgroundJob:
        with self._lock:
            self._jobs[job.job_id] = deepcopy(job)
            return deepcopy(job)

    def update(self, job: BackgroundJob) -> BackgroundJob:
        with self._lock:
            job.updated_at = BackgroundJob.now_iso()
            self._jobs[job.job_id] = deepcopy(job)
            return deepcopy(job)

    def get_by_id(self, job_id: str) -> Optional[BackgroundJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            return deepcopy(job) if job else None

    def list_by_session(self, session_id: str, limit: int = 50) -> List[BackgroundJob]:
        with self._lock:
            items = [j for j in self._jobs.values() if j.session_id == session_id]
            items.sort(key=lambda j: j.created_at, reverse=True)
            return [deepcopy(j) for j in items[:limit]]

    def list_all(self, limit: int = 100) -> List[BackgroundJob]:
        with self._lock:
            items = list(self._jobs.values())
            items.sort(key=lambda j: j.created_at, reverse=True)
            return [deepcopy(j) for j in items[:limit]]

    def claim_next_queued(self) -> Optional[BackgroundJob]:
        with self._lock:
            for job in self._jobs.values():
                if job.status in (JobStatus.QUEUED, JobStatus.RETRYING):
                    job.status = JobStatus.RUNNING
                    job.started_at = job.started_at or BackgroundJob.now_iso()
                    job.progress.started_at = job.started_at
                    job.updated_at = BackgroundJob.now_iso()
                    self._jobs[job.job_id] = deepcopy(job)
                    return deepcopy(job)
            return None

    def append_log(self, job_id: str, entry: JobLogEntry) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.logs.append(entry)
                if len(job.logs) > 100:
                    job.logs = job.logs[-100:]

    def append_progress(self, job_id: str, progress: JobProgress) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.progress = progress
                job.updated_at = BackgroundJob.now_iso()

    def clear_all(self) -> None:
        with self._lock:
            self._jobs.clear()


class PostgresJobRepository(JobRepository):
    def create(self, job: BackgroundJob) -> BackgroundJob:
        row = _model_to_row(job)
        with session_scope() as db:
            db.merge(row)
        return job

    def update(self, job: BackgroundJob) -> BackgroundJob:
        with session_scope() as db:
            db.execute(
                update(JobORM)
                .where(JobORM.job_id == uuid.UUID(job.job_id))
                .values(
                    status=job.status.value,
                    title=job.title,
                    payload=job.payload,
                    result_ref=job.result_ref,
                    checkpoint=job.checkpoint,
                    error=job.error,
                    progress_percent=job.progress.percent,
                    progress_stage=job.progress.stage,
                    rows_processed=job.progress.rows_processed,
                    rows_total=job.progress.rows_total,
                    eta_seconds=job.progress.eta_seconds,
                    retry_count=job.retry_count,
                    started_at=datetime.fromisoformat(job.started_at) if job.started_at else None,
                    completed_at=datetime.fromisoformat(job.completed_at) if job.completed_at else None,
                    updated_at=_utcnow(),
                )
            )
        return job

    def get_by_id(self, job_id: str) -> Optional[BackgroundJob]:
        with session_scope() as db:
            row = db.get(JobORM, uuid.UUID(job_id))
            if not row:
                return None
            logs = db.scalars(select(JobLogORM).where(JobLogORM.job_id == row.job_id).order_by(JobLogORM.created_at.desc()).limit(50)).all()
            return _job_to_model(row, list(reversed(logs)))

    def list_by_session(self, session_id: str, limit: int = 50) -> List[BackgroundJob]:
        with session_scope() as db:
            rows = db.scalars(
                select(JobORM).where(JobORM.session_id == session_id).order_by(JobORM.created_at.desc()).limit(limit)
            ).all()
            return [_job_to_model(r) for r in rows]

    def list_all(self, limit: int = 100) -> List[BackgroundJob]:
        with session_scope() as db:
            rows = db.scalars(select(JobORM).order_by(JobORM.created_at.desc()).limit(limit)).all()
            return [_job_to_model(r) for r in rows]

    def claim_next_queued(self) -> Optional[BackgroundJob]:
        with session_scope() as db:
            row = db.scalar(
                select(JobORM)
                .where(JobORM.status.in_(["queued", "retrying"]))
                .order_by(JobORM.created_at.asc())
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if not row:
                return None
            row.status = "running"
            row.started_at = row.started_at or _utcnow()
            row.updated_at = _utcnow()
            db.flush()
            return _job_to_model(row)

    def append_log(self, job_id: str, entry: JobLogEntry) -> None:
        with session_scope() as db:
            db.add(
                JobLogORM(
                    job_id=uuid.UUID(job_id),
                    level=entry.level,
                    message=entry.message,
                )
            )

    def append_progress(self, job_id: str, progress: JobProgress) -> None:
        with session_scope() as db:
            db.add(
                JobProgressORM(
                    job_id=uuid.UUID(job_id),
                    percent=progress.percent,
                    stage=progress.stage,
                    rows_processed=progress.rows_processed,
                    rows_total=progress.rows_total,
                    eta_seconds=progress.eta_seconds,
                )
            )
            db.execute(
                update(JobORM)
                .where(JobORM.job_id == uuid.UUID(job_id))
                .values(
                    progress_percent=progress.percent,
                    progress_stage=progress.stage,
                    rows_processed=progress.rows_processed,
                    rows_total=progress.rows_total,
                    eta_seconds=progress.eta_seconds,
                    updated_at=_utcnow(),
                )
            )

    def clear_all(self) -> None:
        with session_scope() as db:
            db.execute(delete(JobProgressORM))
            db.execute(delete(JobLogORM))
            db.execute(delete(JobORM))


_job_repo: Optional[JobRepository] = None
_job_repo_lock = threading.Lock()


def get_job_repository() -> JobRepository:
    global _job_repo
    if _job_repo is None:
        with _job_repo_lock:
            if _job_repo is None:
                from config.settings import get_settings

                if get_settings().is_postgres:
                    _job_repo = PostgresJobRepository()
                else:
                    _job_repo = MemoryJobRepository()
    return _job_repo


def reset_job_repository() -> None:
    global _job_repo
    _job_repo = None
