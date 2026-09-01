"""Audit Case Management workflow tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app
from services.case_management_store import get_case_store, reset_case_store
from services.comparison_store import clear_session, save_result
from services.msae_store import clear_msae
from services.msae_service import orchestrate_session
from services.case_management_service import (
    assign_case,
    approve_case,
    create_notice,
    get_audit_case,
    get_officer_tasks,
    get_supervisor_dashboard,
    issue_notice,
    list_audit_cases,
    record_dealer_response,
    sync_cases_from_msae,
    transition_case,
    upload_document,
)
from services.workflow_engine import WorkflowTransitionError, validate_transition
from models.case_management import CaseAssignmentRequest, CommentCreateRequest, DealerResponseRequest, NoticeCreateRequest, StatusTransitionRequest
from tests.msae_fixtures import SESSION, build_gstr1_result, build_gstr2a_result
from services.audit_session_store import clear_sessions, upsert_session
from tests.repository_fixtures import sample_session

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset():
    reset_case_store()
    clear_sessions()
    clear_session(SESSION)
    clear_msae(SESSION)
    upsert_session(sample_session(SESSION))
    save_result(build_gstr1_result())
    save_result(build_gstr2a_result())
    orchestrate_session(SESSION, force=True)
    yield
    reset_case_store()
    clear_sessions()
    clear_session(SESSION)
    clear_msae(SESSION)


class TestWorkflowEngine:
    def test_valid_transition_draft_to_assigned(self):
        validate_transition("Draft", "Assigned")

    def test_invalid_transition_draft_to_closed(self):
        with pytest.raises(WorkflowTransitionError):
            validate_transition("Draft", "Closed")

    def test_full_lifecycle_transitions(self):
        path = [
            ("Draft", "Assigned"),
            ("Assigned", "Under Investigation"),
            ("Under Investigation", "Notice Issued"),
            ("Notice Issued", "Dealer Response Received"),
            ("Dealer Response Received", "Verification Pending"),
            ("Verification Pending", "Supervisor Review"),
            ("Supervisor Review", "Approved"),
            ("Approved", "Closed"),
            ("Closed", "Archived"),
        ]
        for frm, to in path:
            validate_transition(frm, to)


class TestCaseManagementService:
    def test_sync_from_msae(self):
        cases = sync_cases_from_msae(SESSION)
        assert len(cases) >= 3
        assert all(c.workflow_status == "Draft" for c in cases)

    def test_assign_case(self):
        cases = sync_cases_from_msae(SESSION)
        case_id = cases[0].audit_case_id
        updated = assign_case(
            case_id,
            CaseAssignmentRequest(
                session_id=SESSION,
                assigned_officer="officer1",
                assigned_supervisor="supervisor1",
                due_date="2026-12-31",
                circle="Circle-A",
                ward="Ward-1",
            ),
            assigned_by="admin",
        )
        assert updated.workflow_status == "Assigned"
        assert updated.assigned_officer == "officer1"

    def test_workflow_lifecycle(self):
        cases = sync_cases_from_msae(SESSION)
        case_id = cases[0].audit_case_id
        assign_case(case_id, CaseAssignmentRequest(session_id=SESSION, assigned_officer="off1", due_date="2026-12-31"))
        transition_case(case_id, StatusTransitionRequest(session_id=SESSION, to_status="Under Investigation", actor="off1"))
        notice = create_notice(case_id, NoticeCreateRequest(session_id=SESSION, notice_content="Show cause"))
        issue_notice(case_id, notice.notice_id, SESSION, "off1")
        record_dealer_response(
            case_id,
            DealerResponseRequest(session_id=SESSION, notice_id=notice.notice_id, response_summary="Dealer explanation"),
            received_by="off1",
        )
        transition_case(case_id, StatusTransitionRequest(session_id=SESSION, to_status="Verification Pending", actor="off1"))
        transition_case(case_id, StatusTransitionRequest(session_id=SESSION, to_status="Supervisor Review", actor="off1"))
        approve_case(case_id, SESSION, "supervisor1")
        transition_case(case_id, StatusTransitionRequest(session_id=SESSION, to_status="Closed", actor="supervisor1"))

        detail = get_audit_case(SESSION, case_id)
        assert detail.workflow_status == "Closed"
        assert len(detail.timeline) >= 5
        assert len(detail.workflow_history) >= 5

    def test_document_upload(self):
        cases = sync_cases_from_msae(SESSION)
        doc = upload_document(
            cases[0].audit_case_id,
            SESSION,
            category="invoice",
            filename="inv.pdf",
            content_type="application/pdf",
            file_size=1024,
            uploaded_by="off1",
        )
        assert doc.document_id
        detail = get_audit_case(SESSION, cases[0].audit_case_id)
        assert len(detail.documents) == 1

    def test_officer_tasks(self):
        sync_cases_from_msae(SESSION)
        tasks = get_officer_tasks(SESSION)
        assert "counts" in tasks.model_dump()

    def test_supervisor_dashboard(self):
        sync_cases_from_msae(SESSION)
        dash = get_supervisor_dashboard(SESSION)
        assert dash.total_open >= 0


class TestCaseManagementAPI:
    def test_list_and_detail(self):
        sync_cases_from_msae(SESSION)
        r = client.get(f"/api/audit-cases?session_id={SESSION}")
        assert r.status_code == 200
        assert r.json()["total"] >= 3
        case_id = r.json()["cases"][0]["audit_case_id"]
        r2 = client.get(f"/api/audit-cases/{case_id}?session_id={SESSION}")
        assert r2.status_code == 200

    def test_assign_and_transition_api(self):
        sync_cases_from_msae(SESSION)
        case_id = list_audit_cases(SESSION)[0].audit_case_id
        r = client.post(
            f"/api/audit-cases/{case_id}/assign",
            json={"session_id": SESSION, "assigned_officer": "api_officer", "due_date": "2026-12-31"},
        )
        assert r.status_code == 200
        assert r.json()["workflow_status"] == "Assigned"

    def test_tasks_and_supervisor_endpoints(self):
        sync_cases_from_msae(SESSION)
        assert client.get(f"/api/audit-cases/tasks?session_id={SESSION}").status_code == 200
        assert client.get(f"/api/audit-cases/supervisor?session_id={SESSION}").status_code == 200
