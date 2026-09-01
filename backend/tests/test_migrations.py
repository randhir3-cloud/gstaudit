"""Alembic migration script tests."""

from __future__ import annotations

from pathlib import Path


class TestMigrations:
    def test_initial_migration_file_exists(self):
        path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "001_initial_schema.py"
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "def upgrade()" in content
        assert "def downgrade()" in content
        assert "investigation_cases" in content
        assert "comparison_results" in content

    def test_migration_declares_indexes(self):
        path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "001_initial_schema.py"
        content = path.read_text(encoding="utf-8")
        assert "ix_investigation_cases_session_status" in content
        assert "ix_comparison_results_invoice" in content
        assert "uq_dealers_gstin_fy" in content

    def test_rollback_downgrade_order(self):
        path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "001_initial_schema.py"
        content = path.read_text(encoding="utf-8")
        downgrade = content.split("def downgrade")[1]
        assert downgrade.index("investigation_cases") < downgrade.index("audit_sessions")
        assert downgrade.index("audit_sessions") < downgrade.index("dealers")

    def test_jobs_migration_file_exists(self):
        path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "002_jobs_schema.py"
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "def upgrade()" in content
        assert "jobs" in content
        assert "job_logs" in content
        assert "job_progress" in content

    def test_security_migration_file_exists(self):
        path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "003_security_schema.py"
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "users" in content
        assert "audit_logs" in content
        assert "user_sessions" in content
        assert "department_settings" in content

    def test_case_management_migration_file_exists(self):
        path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "004_case_management_schema.py"
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "audit_cases" in content
        assert "case_assignments" in content
        assert "audit_notices" in content
        assert "workflow_history" in content
