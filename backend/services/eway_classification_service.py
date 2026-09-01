"""Intelligent E-Way Bill outward/inward classification from Excel content."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

import pandas as pd

from merger import FULL_MONTH_MAP, extract_period, file_fy_key
from models.eway_classification import (
    DealerGstinResolution,
    EwayClassifyResponse,
    EwayDetectedType,
    EwayFileClassification,
    EwayValidateResponse,
    EwayValidationStatus,
)
from services.dealer_gstin_resolver import resolve_dealer_gstin
from services.eway_file_loader import read_primary_dataframe

GSTIN_PATTERN = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]$")
ROWS_TO_INSPECT = 100
MATCH_THRESHOLD = 0.80

FROM_GSTIN_ALIASES = (
    "from gstin",
    "from gstin & name",
    "from gstin and name",
    "from gstin/name",
    "consigner gstin",
    "consignor gstin",
    "supplier gstin",
    "seller gstin",
    "dispatch gstin",
)

TO_GSTIN_ALIASES = (
    "to gstin",
    "to gstin & name",
    "to gstin and name",
    "to gstin/name",
    "consignee gstin",
    "recipient gstin",
    "buyer gstin",
    "receiver gstin",
)


def _normalize_column_name(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("&", " and ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _find_gstin_in_value(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().upper()
    if GSTIN_PATTERN.match(text):
        return text
    match = re.search(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9])\b", text)
    return match.group(1) if match else ""


def _match_column(columns: List[str], aliases: Tuple[str, ...]) -> Optional[str]:
    normalized = {_normalize_column_name(col): col for col in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    for norm, original in normalized.items():
        for alias in aliases:
            if alias in norm or norm in alias:
                return original
    return None


def _column_match_rate(series: pd.Series, dealer_gstin: str, limit: int = ROWS_TO_INSPECT) -> Tuple[float, int]:
    dealer = dealer_gstin.upper()
    inspected = 0
    matches = 0
    for value in series.head(limit):
        inspected += 1
        gstin = _find_gstin_in_value(value)
        if gstin == dealer:
            matches += 1
    if inspected == 0:
        return 0.0, 0
    return matches / inspected, inspected


def _infer_month_and_fy(filename: str) -> Tuple[str, str]:
    match = re.search(r"_(\d{2})(\d{4})_", filename)
    if match:
        mm, yyyy = match.group(1), match.group(2)
        month = f"{FULL_MONTH_MAP.get(mm, mm)} {yyyy}"
        mm_int, yyyy_int = int(mm), int(yyyy)
        fy_start = yyyy_int if mm_int >= 4 else yyyy_int - 1
        fy_end = (fy_start + 1) % 100
        return month, f"{fy_start}-{fy_end:02d}"
    period = extract_period(filename)
    return period, ""


def classify_eway_file(
    filename: str,
    content: bytes,
    dealer_gstin: str,
    *,
    expected_direction: Optional[str] = None,
) -> EwayFileClassification:
    month, financial_year = _infer_month_and_fy(filename)
    dealer = dealer_gstin.strip().upper()

    if not dealer:
        return EwayFileClassification(
            filename=filename,
            detected_type="unknown",
            confidence=0,
            dealer_gstin="",
            month=month,
            financial_year=financial_year,
            status="pending_dealer_gstin",
            message="Dealer GSTIN is required for classification.",
        )

    df = read_primary_dataframe(filename, content)
    from_col = _match_column([str(c) for c in df.columns], FROM_GSTIN_ALIASES)
    to_col = _match_column([str(c) for c in df.columns], TO_GSTIN_ALIASES)

    if not from_col and not to_col:
        return EwayFileClassification(
            filename=filename,
            detected_type="unknown",
            confidence=0,
            dealer_gstin=dealer,
            month=month,
            financial_year=financial_year,
            status="unknown",
            message="Could not detect From GSTIN or To GSTIN columns.",
        )

    from_rate, from_rows = (0.0, 0)
    to_rate, to_rows = (0.0, 0)
    if from_col:
        from_rate, from_rows = _column_match_rate(df[from_col], dealer)
    if to_col:
        to_rate, to_rows = _column_match_rate(df[to_col], dealer)

    rows_inspected = max(from_rows, to_rows)
    detected_type: EwayDetectedType = "unknown"
    confidence = 0.0
    message = ""

    from_match = from_rate > MATCH_THRESHOLD
    to_match = to_rate > MATCH_THRESHOLD

    if from_match and to_match:
        detected_type = "unknown"
        confidence = 0.0
        message = "Dealer GSTIN appears in both From and To GSTIN columns."
    elif from_match:
        detected_type = "outward"
        confidence = 100.0
        message = "Dealer GSTIN predominantly in From GSTIN column."
    elif to_match:
        detected_type = "inward"
        confidence = 100.0
        message = "Dealer GSTIN predominantly in To GSTIN column."
    else:
        detected_type = "unknown"
        confidence = max(from_rate, to_rate) * 100
        message = "Could not classify with 80% confidence."

    status: EwayValidationStatus = "valid"
    if detected_type == "unknown":
        status = "unknown"
    elif expected_direction and detected_type != expected_direction:
        status = "wrong_section"

    return EwayFileClassification(
        filename=filename,
        detected_type=detected_type,
        confidence=round(confidence, 2),
        dealer_gstin=dealer,
        month=month,
        financial_year=financial_year,
        status=status,
        from_gstin_column=from_col,
        to_gstin_column=to_col,
        rows_inspected=rows_inspected,
        from_match_rate=round(from_rate * 100, 2),
        to_match_rate=round(to_rate * 100, 2),
        message=message,
    )


def classify_eway_files(
    ewb_files: List[Tuple[str, bytes]],
    *,
    user_gstin: Optional[str] = None,
    gstr1_files: Optional[List[Tuple[str, bytes]]] = None,
    gstr2a_files: Optional[List[Tuple[str, bytes]]] = None,
    expected_direction: Optional[str] = None,
) -> EwayClassifyResponse:
    dealer_resolution = resolve_dealer_gstin(
        user_gstin=user_gstin,
        gstr1_files=gstr1_files,
        gstr2a_files=gstr2a_files,
    )

    classifications: List[EwayFileClassification] = []
    for filename, content in ewb_files:
        classifications.append(
            classify_eway_file(
                filename,
                content,
                dealer_resolution.gstin,
                expected_direction=expected_direction,
            )
        )

    return EwayClassifyResponse(
        dealer_resolution=dealer_resolution,
        classifications=classifications,
    )


def validate_eway_batch(
    ewb_files: List[Tuple[str, bytes]],
    expected_direction: str,
    *,
    user_gstin: Optional[str] = None,
    gstr1_files: Optional[List[Tuple[str, bytes]]] = None,
    gstr2a_files: Optional[List[Tuple[str, bytes]]] = None,
) -> EwayValidateResponse:
    result = classify_eway_files(
        ewb_files,
        user_gstin=user_gstin,
        gstr1_files=gstr1_files,
        gstr2a_files=gstr2a_files,
        expected_direction=expected_direction,
    )

    blocking: List[str] = []
    can_merge = True

    if result.dealer_resolution.requires_user_input:
        can_merge = False
        blocking.append("Dealer GSTIN is required.")

    for item in result.classifications:
        if item.status == "wrong_section":
            can_merge = False
            blocking.append(
                f"{item.filename}: detected as {item.detected_type.upper()} but uploaded in {expected_direction.upper()} section."
            )
        elif item.status == "unknown":
            can_merge = False
            blocking.append(f"{item.filename}: classification unknown — {item.message}")
        elif item.status == "pending_dealer_gstin":
            can_merge = False
            blocking.append(f"{item.filename}: dealer GSTIN pending.")

    return EwayValidateResponse(
        dealer_resolution=result.dealer_resolution,
        expected_direction=expected_direction,
        validations=result.classifications,
        can_merge=can_merge,
        blocking_issues=blocking,
    )
