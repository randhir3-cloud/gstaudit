"""E-Way Bill intelligent classification models."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

EwayDetectedType = Literal["outward", "inward", "unknown"]
EwayValidationStatus = Literal["valid", "wrong_section", "unknown", "pending_dealer_gstin"]


class DealerGstinResolution(BaseModel):
    gstin: str = ""
    source: Literal["gstr1", "gstr2a", "user", "none"] = "none"
    requires_user_input: bool = False
    legal_name: str = ""
    financial_year: str = ""


class EwayFileClassification(BaseModel):
    filename: str
    detected_type: EwayDetectedType
    confidence: float = Field(ge=0, le=100)
    dealer_gstin: str = ""
    month: str = ""
    financial_year: str = ""
    status: EwayValidationStatus = "valid"
    from_gstin_column: Optional[str] = None
    to_gstin_column: Optional[str] = None
    rows_inspected: int = 0
    from_match_rate: float = 0.0
    to_match_rate: float = 0.0
    message: str = ""


class EwayClassifyResponse(BaseModel):
    dealer_resolution: DealerGstinResolution
    classifications: List[EwayFileClassification] = Field(default_factory=list)


class EwayValidateResponse(BaseModel):
    dealer_resolution: DealerGstinResolution
    expected_direction: str
    validations: List[EwayFileClassification] = Field(default_factory=list)
    can_merge: bool = False
    blocking_issues: List[str] = Field(default_factory=list)
