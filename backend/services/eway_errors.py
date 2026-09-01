"""E-Way Bill service exceptions."""

from __future__ import annotations

from typing import List, Optional


class EwayValidationError(Exception):
    def __init__(
        self,
        message: str,
        error_type: str = "eway_validation",
        missing: Optional[List[str]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.missing = missing or []

    def to_dict(self) -> dict:
        payload = {
            "status": "error" if self.error_type != "missing_months" else "warning",
            "error_type": self.error_type,
            "message": self.message,
        }
        if self.missing:
            payload["missing"] = self.missing
        return payload
