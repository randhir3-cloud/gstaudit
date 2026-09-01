"""Shared E-Way Bill Excel loading utilities."""

from __future__ import annotations

import io
from typing import List

import pandas as pd

from services.eway_errors import EwayValidationError


def load_excel_file(filename: str, content: bytes) -> pd.ExcelFile:
    if filename.lower().endswith(".xls"):
        header = content[:500].lower()
        if b"<html" in header or b"<!doctype html" in header or b"<style" in header:
            tables = pd.read_html(io.BytesIO(content))
            if not tables:
                raise EwayValidationError(f"No tables found in HTML-xls file {filename}")
            xlsx_buffer = io.BytesIO()
            tables[0].to_excel(xlsx_buffer, index=False, engine="openpyxl")
            xlsx_buffer.seek(0)
            return pd.ExcelFile(xlsx_buffer, engine="openpyxl")
        return pd.ExcelFile(io.BytesIO(content), engine="xlrd")
    return pd.ExcelFile(io.BytesIO(content), engine="openpyxl")


def read_primary_dataframe(filename: str, content: bytes) -> pd.DataFrame:
    xls = load_excel_file(filename, content)
    frames: List[pd.DataFrame] = []
    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, engine="openpyxl")
        except Exception:
            df = pd.read_excel(xls, sheet_name=sheet_name)
        if not df.empty:
            frames.append(df)
    if not frames:
        raise EwayValidationError(f"No data found in {filename}")
    if len(frames) == 1:
        return frames[0]
    return pd.concat(frames, ignore_index=True)
