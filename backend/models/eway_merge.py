"""E-Way Bill merge response models — outward and inward workflows are independent."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from models.dealer_metadata import DealerMetadata

EwayDirection = Literal["outward", "inward"]


class EwaySheetPreview(BaseModel):
    name: str
    columns: List[str] = Field(default_factory=list)
    row_count: int = 0
    sample_rows: List[List[Optional[str]]] = Field(default_factory=list)


class EwayMergeSummary(BaseModel):
    direction: EwayDirection
    financial_year: str = ""
    uploaded_months: List[str] = Field(default_factory=list)
    missing_months: List[str] = Field(default_factory=list)
    sheet_list: List[str] = Field(default_factory=list)
    row_count: int = 0
    source_files: List[str] = Field(default_factory=list)
    compare_target: str = Field(
        description="Future comparison target: gstr1 for outward, gstr2a for inward"
    )


class EwayMergeResponse(BaseModel):
    workbook_id: str
    dealer: DealerMetadata
    financial_year: str = ""
    uploaded_months: List[str] = Field(default_factory=list)
    missing_months: List[str] = Field(default_factory=list)
    sheet_list: List[str] = Field(default_factory=list)
    row_count: int = 0
    suggested_filename: str
    summary: EwayMergeSummary
    preview: List[EwaySheetPreview] = Field(default_factory=list)
    workbook_base64: str = Field(description="Base64-encoded merged .xlsx workbook")
