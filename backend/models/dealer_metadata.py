"""Dealer metadata models — reusable for API responses and future DB persistence."""

from __future__ import annotations

import hashlib
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


def _clean_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


class DealerMetadata(BaseModel):
    """Dealer identity extracted from a GST return workbook Read me sheet."""

    gstin: str = ""
    legal_name: str = ""
    trade_name: str = ""
    financial_year: str = ""
    tax_period: str = ""
    arn: str = ""
    arn_date: str = ""
    download_date: str = ""

    # Future-ready primary key for audit-session persistence.
    id: Optional[str] = Field(default=None, description="Stable UUID for DB storage")

    @field_validator(
        "gstin",
        "legal_name",
        "trade_name",
        "financial_year",
        "tax_period",
        "arn",
        "arn_date",
        "download_date",
        mode="before",
    )
    @classmethod
    def normalize_fields(cls, value: object) -> str:
        return _clean_str(value)

    def ensure_id(self) -> "DealerMetadata":
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    def normalized_gstin(self) -> str:
        return self.gstin.upper()

    def normalized_financial_year(self) -> str:
        return self.financial_year.replace(" ", "")

    def display_name(self) -> str:
        return self.legal_name or self.trade_name or self.gstin or "Unknown Dealer"

    def to_db_dict(self) -> dict:
        """Shape suitable for future ORM / audit-session tables."""
        data = self.model_dump()
        data.setdefault("id", str(uuid.uuid4()))
        return data


class DealerMismatchDetail(BaseModel):
    field: str
    expected: str
    found: str
    source_file: str


class WorkbookMetadataResponse(BaseModel):
    workbook_id: str
    dealer: DealerMetadata
    return_type: str = Field(description="gstr1 | gstr2a")
    source_files: List[str] = Field(default_factory=list)
    current_dataset: str = ""

    @staticmethod
    def build_workbook_id(
        return_type: str,
        dealer: DealerMetadata,
        source_files: Optional[List[str]] = None,
    ) -> str:
        """Deterministic workbook id from dealer + return type (+ optional files)."""
        parts = [
            return_type.lower(),
            dealer.normalized_gstin(),
            dealer.normalized_financial_year(),
        ]
        if source_files:
            parts.append("|".join(sorted(source_files)))
        digest = hashlib.sha256(":".join(parts).encode()).hexdigest()[:16]
        return f"wb_{return_type}_{digest}"
