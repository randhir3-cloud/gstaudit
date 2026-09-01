"""Background job domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class JobType(str, Enum):
    MERGE = "merge"
    COMPARISON = "comparison"
    INTELLIGENCE = "intelligence"
    REPORT = "report"
    IMPORT = "import"
    AI = "ai"  # reserved


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobProgress(BaseModel):
    percent: int = 0
    stage: str = ""
    rows_processed: int = 0
    rows_total: int = 0
    eta_seconds: Optional[int] = None
    started_at: Optional[str] = None
    updated_at: str = ""

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


class JobLogEntry(BaseModel):
    level: Literal["info", "warning", "error"] = "info"
    message: str = ""
    created_at: str = ""

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


class BackgroundJob(BaseModel):
    job_id: str
    session_id: str
    job_type: JobType
    status: JobStatus = JobStatus.QUEUED
    title: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    result_ref: Dict[str, Any] = Field(default_factory=dict)
    checkpoint: Dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    progress: JobProgress = Field(default_factory=JobProgress)
    logs: List[JobLogEntry] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    updated_at: str = ""

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


class JobCreateRequest(BaseModel):
    session_id: str
    job_type: JobType
    title: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)


class JobListResponse(BaseModel):
    jobs: List[BackgroundJob] = Field(default_factory=list)
    total: int = 0
