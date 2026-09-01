"""Alembic migration — background jobs tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_jobs"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("job_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), server_default="queued"),
        sa.Column("title", sa.String(256), server_default=""),
        sa.Column("payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result_ref", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("checkpoint", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error", sa.Text, server_default=""),
        sa.Column("progress_percent", sa.Integer, server_default="0"),
        sa.Column("progress_stage", sa.String(128), server_default=""),
        sa.Column("rows_processed", sa.Integer, server_default="0"),
        sa.Column("rows_total", sa.Integer, server_default="0"),
        sa.Column("eta_seconds", sa.Integer, nullable=True),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("max_retries", sa.Integer, server_default="2"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_jobs_session_id", "jobs", ["session_id"])
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_session_status", "jobs", ["session_id", "status"])
    op.create_index("ix_jobs_type_status", "jobs", ["job_type", "status"])

    op.create_table(
        "job_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.String(16), server_default="info"),
        sa.Column("message", sa.Text, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_job_logs_job_id", "job_logs", ["job_id"])

    op.create_table(
        "job_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False),
        sa.Column("percent", sa.Integer, server_default="0"),
        sa.Column("stage", sa.String(128), server_default=""),
        sa.Column("rows_processed", sa.Integer, server_default="0"),
        sa.Column("rows_total", sa.Integer, server_default="0"),
        sa.Column("eta_seconds", sa.Integer, nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_job_progress_job_id", "job_progress", ["job_id"])


def downgrade() -> None:
    op.drop_table("job_progress")
    op.drop_table("job_logs")
    op.drop_table("jobs")
