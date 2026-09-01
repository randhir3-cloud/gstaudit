"""Workbook and comparison result store — delegates to repository layer."""

from __future__ import annotations

from typing import Optional

from comparison.result_models import ComparisonResult
from repositories.factory import get_repositories


def cache_workbook(session_id: str, dataset_key: str, workbook_bytes: bytes) -> None:
    get_repositories().workbook.cache_workbook(session_id, dataset_key, workbook_bytes)


def get_workbook(session_id: str, dataset_key: str) -> Optional[bytes]:
    return get_repositories().workbook.get_workbook(session_id, dataset_key)


def set_comparison_status(session_id: str, status: str) -> None:
    get_repositories().comparison.set_status(session_id, status)


def get_comparison_status(session_id: str) -> str:
    return get_repositories().comparison.get_status(session_id)


def save_result(result: ComparisonResult) -> None:
    get_repositories().comparison.save_result(result)


def get_result(session_id: str, comparison_id: Optional[str] = None) -> Optional[ComparisonResult]:
    return get_repositories().comparison.get_result(session_id, comparison_id)


def list_results(session_id: str) -> list[ComparisonResult]:
    return get_repositories().comparison.list_results(session_id)


def clear_session(session_id: str) -> None:
    repos = get_repositories()
    repos.workbook.delete_by_session(session_id)
    repos.comparison.delete_by_session(session_id)
