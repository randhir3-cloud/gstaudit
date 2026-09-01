"""Comparison configuration models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NormalizerConfig(BaseModel):
    amount_round_digits: int = 2
    amount_tolerance: float = 1.0
    date_tolerance_days: int = 1


class ComparisonConfig(BaseModel):
    comparison_id: str
    left_dataset: str
    right_dataset: str
    left_label: str
    right_label: str
    normalizer: NormalizerConfig = Field(default_factory=NormalizerConfig)


class ComparisonRunRequest(BaseModel):
    session_id: str
    gstr1_workbook_base64: str = ""
    ewb_outward_workbook_base64: str = ""


class WorkbookCacheRequest(BaseModel):
    session_id: str
    dataset_key: str
    workbook_base64: str
