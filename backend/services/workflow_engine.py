"""Workflow engine — enforces valid audit case status transitions."""

from __future__ import annotations

from models.case_management import CaseWorkflowStatus

VALID_TRANSITIONS: dict[str, list[str]] = {
    "Draft": ["Assigned"],
    "Assigned": ["Under Investigation"],
    "Under Investigation": ["Notice Issued", "Verification Pending"],
    "Notice Issued": ["Dealer Response Received"],
    "Dealer Response Received": ["Verification Pending"],
    "Verification Pending": ["Supervisor Review"],
    "Supervisor Review": ["Approved", "Under Investigation"],
    "Approved": ["Closed"],
    "Closed": ["Archived"],
    "Archived": [],
}

TERMINAL_STATUSES = {"Archived"}
SUPERVISOR_REQUIRED = {"Supervisor Review", "Approved"}
NOTICE_STATUSES = {"Notice Issued", "Dealer Response Received"}


class WorkflowTransitionError(ValueError):
    def __init__(self, from_status: str, to_status: str, allowed: list[str]):
        self.from_status = from_status
        self.to_status = to_status
        self.allowed = allowed
        super().__init__(
            f"Invalid transition from '{from_status}' to '{to_status}'. "
            f"Allowed: {', '.join(allowed) or 'none'}"
        )


def allowed_transitions(current: str) -> list[str]:
    return list(VALID_TRANSITIONS.get(current, []))


def can_transition(current: str, target: str) -> bool:
    return target in VALID_TRANSITIONS.get(current, [])


def validate_transition(current: CaseWorkflowStatus | str, target: CaseWorkflowStatus | str) -> None:
    current_s = str(current)
    target_s = str(target)
    if current_s == target_s:
        return
    allowed = allowed_transitions(current_s)
    if target_s not in allowed:
        raise WorkflowTransitionError(current_s, target_s, allowed)


def is_editable(status: str) -> bool:
    return status not in TERMINAL_STATUSES


def requires_supervisor(status: str) -> bool:
    return status in SUPERVISOR_REQUIRED
