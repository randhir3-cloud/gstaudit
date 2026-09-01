"""Normalization engine for invoice, GSTIN, date, and amount fields."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from comparison.models import NormalizerConfig

_INVOICE_CLEAN_RE = re.compile(r"[^A-Z0-9]")
_GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


def normalize_invoice(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().upper()
    return _INVOICE_CLEAN_RE.sub("", text)


def normalize_gstin(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().upper()
    match = re.search(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]", text)
    return match.group(0) if match else text.replace(" ", "")


def normalize_date(value: object) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", text)
    if match:
        d, m, y = match.groups()
        year = int(y)
        if year < 100:
            year += 2000
        try:
            return datetime(year, int(m), int(d)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return text


def normalize_amount(value: object, config: Optional[NormalizerConfig] = None) -> float:
    cfg = config or NormalizerConfig()
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return round(float(value), cfg.amount_round_digits)
    text = str(value).strip().replace(",", "").replace(" ", "")
    try:
        return round(float(text), cfg.amount_round_digits)
    except ValueError:
        return 0.0


def amounts_match(left: float, right: float, config: Optional[NormalizerConfig] = None) -> bool:
    cfg = config or NormalizerConfig()
    return abs(left - right) <= cfg.amount_tolerance


def dates_match(left: str, right: str, config: Optional[NormalizerConfig] = None) -> bool:
    cfg = config or NormalizerConfig()
    if not left or not right:
        return left == right
    try:
        d1 = datetime.strptime(left, "%Y-%m-%d")
        d2 = datetime.strptime(right, "%Y-%m-%d")
        return abs((d1 - d2).days) <= cfg.date_tolerance_days
    except ValueError:
        return left == right


def is_valid_gstin(value: str) -> bool:
    return bool(_GSTIN_RE.match(value))
