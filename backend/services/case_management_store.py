"""In-memory persistence for audit case management workflow."""

from __future__ import annotations

from typing import Dict, List, Optional

from models.case_management import (
    AuditCase,
    AuditNotice,
    CaseAssignment,
    CaseComment,
    CaseDocument,
    CaseTimelineEntry,
    DealerResponse,
    WorkflowHistoryEntry,
)


class CaseManagementStore:
    def __init__(self) -> None:
        self.cases: Dict[str, AuditCase] = {}
        self.assignments: Dict[str, CaseAssignment] = {}
        self.notices: Dict[str, AuditNotice] = {}
        self.documents: Dict[str, CaseDocument] = {}
        self.comments: Dict[str, CaseComment] = {}
        self.timeline: Dict[str, CaseTimelineEntry] = {}
        self.dealer_responses: Dict[str, DealerResponse] = {}
        self.workflow_history: Dict[str, WorkflowHistoryEntry] = {}

    def clear(self) -> None:
        self.__init__()

    def clear_session(self, session_id: str) -> None:
        case_ids = {c.audit_case_id for c in self.cases.values() if c.session_id == session_id}
        self.cases = {k: v for k, v in self.cases.items() if v.session_id != session_id}
        self.assignments = {k: v for k, v in self.assignments.items() if v.audit_case_id not in case_ids}
        self.notices = {k: v for k, v in self.notices.items() if v.audit_case_id not in case_ids}
        self.documents = {k: v for k, v in self.documents.items() if v.audit_case_id not in case_ids}
        self.comments = {k: v for k, v in self.comments.items() if v.audit_case_id not in case_ids}
        self.timeline = {k: v for k, v in self.timeline.items() if v.audit_case_id not in case_ids}
        self.dealer_responses = {k: v for k, v in self.dealer_responses.items() if v.audit_case_id not in case_ids}
        self.workflow_history = {k: v for k, v in self.workflow_history.items() if v.audit_case_id not in case_ids}


_store = CaseManagementStore()


def get_case_store() -> CaseManagementStore:
    return _store


def reset_case_store() -> None:
    _store.clear()
