"""Investigation case store — delegates to repository layer."""

from __future__ import annotations

from typing import Dict, List, Optional

from models.investigation import InvestigationCase
from repositories.factory import get_repositories


def get_session_cases(session_id: str) -> Dict[str, InvestigationCase]:
    cases = get_repositories().investigation.get_by_session(session_id)
    return {c.case_id: c for c in cases}


def save_case(case: InvestigationCase) -> InvestigationCase:
    repos = get_repositories()
    existing = repos.investigation.get_by_id(case.session_id, case.case_id)
    if existing:
        return repos.investigation.update(case)
    return repos.investigation.create(case)


def get_case(session_id: str, case_id: str) -> Optional[InvestigationCase]:
    return get_repositories().investigation.get_by_id(session_id, case_id)


def list_cases(session_id: str) -> List[InvestigationCase]:
    return get_repositories().investigation.get_by_session(session_id)


def save_cases(session_id: str, cases: List[InvestigationCase]) -> None:
    get_repositories().investigation.save_many(session_id, cases)


def clear_session(session_id: str) -> None:
    get_repositories().investigation.delete_by_session(session_id)
