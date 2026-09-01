"""E-Way Bill merge service — independent outward and inward workflows."""

from __future__ import annotations

import base64
import io
import re
from typing import List, Optional, Tuple

import numpy as np
import openpyxl
import pandas as pd

from merger import (
    find_eway_date_column,
    find_missing_months,
    parse_eway_source_period,
    extract_period,
    file_fy_key,
    fy_key_to_label,
    MONTH_MAP,
    FULL_MONTH_MAP,
)
from models.dealer_metadata import DealerMetadata, WorkbookMetadataResponse
from models.eway_merge import EwayDirection, EwayMergeResponse, EwayMergeSummary, EwaySheetPreview

from services.eway_classification_service import validate_eway_batch
from services.eway_errors import EwayValidationError
from services.eway_file_loader import load_excel_file

PREVIEW_ROW_LIMIT = 5

COMPARE_TARGETS: dict[EwayDirection, str] = {
    "outward": "gstr1",
    "inward": "gstr2a",
}

DEFAULT_FILENAMES: dict[EwayDirection, str] = {
    "outward": "EWB_Outward_Merged.xlsx",
    "inward": "EWB_Inward_Merged.xlsx",
}

GSTIN_PATTERN = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]$")


def _read_file_frames(filename: str, content: bytes, direction: EwayDirection) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    period_from_name = extract_period(filename)
    xls = load_excel_file(filename, content)

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, engine="openpyxl")
        except Exception:
            df = pd.read_excel(xls, sheet_name=sheet_name)

        if df.empty:
            continue

        date_col = find_eway_date_column(df)
        if date_col is not None:
            df["Source_Period"] = df[date_col].apply(parse_eway_source_period)
        else:
            df["Source_Period"] = period_from_name if period_from_name else ""

        df["Source_File"] = filename
        df["Source_Sheet"] = sheet_name
        df["EWB_Direction"] = direction.capitalize()
        frames.append(df)

    return frames


def _extract_months_from_files(filenames: List[str]) -> List[str]:
    months: List[str] = []
    seen = set()
    for name in sorted(filenames, key=file_fy_key):
        m = re.search(r"_(\d{2})(\d{4})_", name)
        if m:
            mm, yyyy = m.group(1), m.group(2)
            label = f"{FULL_MONTH_MAP.get(mm, mm)} {yyyy}"
        else:
            label = extract_period(name)
        if label and label not in seen:
            seen.add(label)
            months.append(label)
    return months


def _infer_financial_year(filenames: List[str], frames: List[pd.DataFrame]) -> str:
    years = set()
    for name in filenames:
        m = re.search(r"_(\d{2})(\d{4})_", name)
        if m:
            mm, yyyy = int(m.group(1)), int(m.group(2))
            fy_start = yyyy if mm >= 4 else yyyy - 1
            fy_end = (fy_start + 1) % 100
            years.add(f"{fy_start}-{fy_end:02d}")

    if years:
        return sorted(years)[0]

    for df in frames:
        if "Source_Period" not in df.columns:
            continue
        for value in df["Source_Period"].dropna().unique():
            m = re.match(r"([A-Za-z]+)-(\d{4})", str(value))
            if m:
                month_name, year = m.group(1), int(m.group(2))
                month_num = next(
                    (k for k, v in MONTH_MAP.items() if v.lower() == month_name.lower()),
                    None,
                )
                if month_num:
                    mm = int(month_num)
                    fy_start = year if mm >= 4 else year - 1
                    fy_end = (fy_start + 1) % 100
                    years.add(f"{fy_start}-{fy_end:02d}")

    return sorted(years)[0] if years else ""


def _find_gstin_in_value(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().upper()
    if GSTIN_PATTERN.match(text):
        return text
    match = re.search(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9])\b", text)
    return match.group(1) if match else ""


def _extract_dealer_from_frames(frames: List[pd.DataFrame]) -> DealerMetadata:
    gstin = ""
    legal_name = ""
    trade_name = ""

    gstin_columns = (
        "gstin",
        "from gstin",
        "to gstin",
        "gstin of supplier",
        "gstin of recipient",
        "taxpayer gstin",
        "user gstin",
    )
    name_columns = (
        "legal name",
        "trade name",
        "from trade name",
        "to trade name",
        "company name",
        "name",
    )

    for df in frames:
        normalized_cols = {str(c).strip().lower(): c for c in df.columns}
        for alias in gstin_columns:
            if alias in normalized_cols and not gstin:
                col = normalized_cols[alias]
                for value in df[col].dropna().head(20):
                    gstin = _find_gstin_in_value(value)
                    if gstin:
                        break
        for alias in name_columns:
            if alias in normalized_cols and not legal_name:
                col = normalized_cols[alias]
                for value in df[col].dropna().head(5):
                    text = str(value).strip()
                    if text and not _find_gstin_in_value(text):
                        legal_name = text
                        break

        if not gstin:
            sample = df.head(10)
            for _, row in sample.iterrows():
                for value in row.values:
                    gstin = _find_gstin_in_value(value)
                    if gstin:
                        break
                if gstin:
                    break

    return DealerMetadata(
        gstin=gstin,
        legal_name=legal_name,
        trade_name=trade_name or legal_name,
    ).ensure_id()


def _build_suggested_filename(direction: EwayDirection, dealer: DealerMetadata, fy: str) -> str:
    safe = lambda s: re.sub(r'[\\/:*?"<>|]', "_", s.strip()) or "UNKNOWN"
    gstin = safe(dealer.gstin) if dealer.gstin else "UNKNOWN"
    financial_year = safe(fy) if fy else "UNKNOWN"
    prefix = "EWB_Outward" if direction == "outward" else "EWB_Inward"
    return f"{prefix}_{gstin}_{financial_year}_Merged.xlsx"


def _build_preview(combined: pd.DataFrame, sheet_list: List[str]) -> List[EwaySheetPreview]:
    previews: List[EwaySheetPreview] = []

    if "Source_Sheet" in combined.columns:
        groups = combined.groupby("Source_Sheet", sort=False)
        for sheet_name, df in groups:
            columns = [str(c) for c in df.columns.tolist()]
            sample_df = df.head(PREVIEW_ROW_LIMIT).replace({np.nan: None})
            sample_rows = [
                [None if v is None else str(v) for v in row]
                for row in sample_df.values.tolist()
            ]
            previews.append(
                EwaySheetPreview(
                    name=str(sheet_name),
                    columns=columns,
                    row_count=len(df),
                    sample_rows=sample_rows,
                )
            )
    elif not combined.empty:
        columns = [str(c) for c in combined.columns.tolist()]
        sample_df = combined.head(PREVIEW_ROW_LIMIT).replace({np.nan: None})
        previews.append(
            EwaySheetPreview(
                name=sheet_list[0] if sheet_list else "Merged",
                columns=columns,
                row_count=len(combined),
                sample_rows=[
                    [None if v is None else str(v) for v in row]
                    for row in sample_df.values.tolist()
                ],
            )
        )
    return previews


def merge_eway_workflow(
    files: List[Tuple[str, bytes]],
    direction: EwayDirection,
    *,
    ignore_missing: bool = False,
    dealer_gstin: Optional[str] = None,
    gstr1_context: Optional[List[Tuple[str, bytes]]] = None,
    gstr2a_context: Optional[List[Tuple[str, bytes]]] = None,
    skip_classification: bool = False,
) -> EwayMergeResponse:
    if not files:
        raise EwayValidationError("No files provided for merging.")

    filenames = [name for name, _ in files]
    resolved_gstin = (dealer_gstin or "").strip().upper()

    if not skip_classification:
        validation = validate_eway_batch(
            files,
            direction,
            user_gstin=dealer_gstin,
            gstr1_files=gstr1_context,
            gstr2a_files=gstr2a_context,
        )
        if not validation.can_merge:
            raise EwayValidationError(
                message="; ".join(validation.blocking_issues),
                error_type="classification_blocked",
            )
        if validation.dealer_resolution.gstin:
            resolved_gstin = validation.dealer_resolution.gstin

    missing_months = find_missing_months(filenames)
    if missing_months and not ignore_missing:
        raise EwayValidationError(
            message="Missing months detected between selected files.",
            error_type="missing_months",
            missing=missing_months,
        )

    sorted_files = sorted(files, key=lambda item: file_fy_key(item[0]))
    all_frames: List[pd.DataFrame] = []

    for filename, content in sorted_files:
        try:
            frames = _read_file_frames(filename, content, direction)
            all_frames.extend(frames)
        except EwayValidationError:
            raise
        except Exception as exc:
            raise EwayValidationError(f"Error processing {filename}: {exc}") from exc

    if not all_frames:
        raise EwayValidationError("No data found to merge.")

    combined = pd.concat(all_frames, ignore_index=True)
    dealer = _extract_dealer_from_frames(all_frames)
    if resolved_gstin:
        dealer.gstin = resolved_gstin
    financial_year = _infer_financial_year(filenames, all_frames)
    uploaded_months = _extract_months_from_files(filenames)
    sheet_list = sorted({str(name) for frame in all_frames for name in frame.get("Source_Sheet", pd.Series()).dropna().unique()})
    if not sheet_list:
        sheet_list = ["Merged"]

    suggested_filename = _build_suggested_filename(direction, dealer, financial_year)
    workbook_id = WorkbookMetadataResponse.build_workbook_id(
        f"eway_{direction}",
        dealer,
        filenames,
    )

    output_buffer = io.BytesIO()
    combined.to_excel(output_buffer, index=False, engine="openpyxl")
    output_buffer.seek(0)
    workbook_base64 = base64.b64encode(output_buffer.getvalue()).decode("ascii")

    summary = EwayMergeSummary(
        direction=direction,
        financial_year=financial_year,
        uploaded_months=uploaded_months,
        missing_months=missing_months,
        sheet_list=sheet_list,
        row_count=len(combined),
        source_files=filenames,
        compare_target=COMPARE_TARGETS[direction],
    )

    return EwayMergeResponse(
        workbook_id=workbook_id,
        dealer=dealer,
        financial_year=financial_year,
        uploaded_months=uploaded_months,
        missing_months=missing_months,
        sheet_list=sheet_list,
        row_count=len(combined),
        suggested_filename=suggested_filename,
        summary=summary,
        preview=_build_preview(combined, sheet_list),
        workbook_base64=workbook_base64,
    )


def merge_eway_bills_legacy(files: List[Tuple[str, bytes]]) -> io.BytesIO:
    """Backward-compatible merge used by deprecated /api/merge/eway endpoint."""
    result = merge_eway_workflow(files, "outward", ignore_missing=True)
    return io.BytesIO(base64.b64decode(result.workbook_base64))
