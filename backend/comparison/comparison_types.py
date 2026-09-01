"""Comparison result type constants."""

from enum import Enum


class ComparisonResultType(str, Enum):
    MATCHED = "MATCHED"
    MISSING_IN_GSTR1 = "MISSING_IN_GSTR1"
    MISSING_IN_EWAY = "MISSING_IN_EWAY"
    GSTIN_MISMATCH = "GSTIN_MISMATCH"
    VALUE_MISMATCH = "VALUE_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    DUPLICATE = "DUPLICATE"
    MULTIPLE_MATCHES = "MULTIPLE_MATCHES"
    UNKNOWN = "UNKNOWN"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
