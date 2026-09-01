"""Intelligence cache store — delegates to repository layer."""

from __future__ import annotations

from typing import Optional

from intelligence.models import IntelligenceFullResponse
from repositories.factory import get_repositories


def save_intelligence(session_id: str, data: IntelligenceFullResponse) -> None:
    get_repositories().intelligence.save(session_id, data)


def get_intelligence(session_id: str) -> Optional[IntelligenceFullResponse]:
    return get_repositories().intelligence.get(session_id)


def clear_intelligence(session_id: str) -> None:
    get_repositories().intelligence.delete(session_id)
