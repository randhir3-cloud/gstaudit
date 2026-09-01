"""Validate dealer metadata consistency across uploaded workbooks."""

from __future__ import annotations

from typing import List, Tuple

from models.dealer_metadata import DealerMetadata, DealerMismatchDetail


class DealerValidationError(Exception):
    def __init__(
        self,
        message: str,
        mismatches: List[DealerMismatchDetail],
        error_type: str = "dealer_mismatch",
    ):
        super().__init__(message)
        self.message = message
        self.mismatches = mismatches
        self.error_type = error_type

    def to_dict(self) -> dict:
        return {
            "status": "error",
            "error_type": self.error_type,
            "message": self.message,
            "mismatches": [m.model_dump() for m in self.mismatches],
        }


def _require_field(dealer: DealerMetadata, field: str, source_file: str) -> None:
    value = getattr(dealer, field, "")
    if not value:
        raise DealerValidationError(
            message=f"Missing {field.replace('_', ' ')} in Read me sheet of {source_file}.",
            mismatches=[
                DealerMismatchDetail(
                    field=field,
                    expected="non-empty value",
                    found="",
                    source_file=source_file,
                )
            ],
            error_type="dealer_metadata_missing",
        )


def validate_dealer_consistency(
    records: List[Tuple[str, DealerMetadata]],
    *,
    require_fields: bool = True,
) -> DealerMetadata:
    """
    Ensure all uploaded workbooks share the same GSTIN and Financial Year.
    Returns the canonical dealer metadata (from the first sorted file).
    """
    if not records:
        raise DealerValidationError(
            message="No files provided for dealer validation.",
            mismatches=[],
        )

    canonical_file, canonical = records[0]
    if require_fields:
        _require_field(canonical, "gstin", canonical_file)
        _require_field(canonical, "financial_year", canonical_file)

    mismatches: List[DealerMismatchDetail] = []

    for source_file, dealer in records[1:]:
        if dealer.normalized_gstin() != canonical.normalized_gstin():
            mismatches.append(
                DealerMismatchDetail(
                    field="gstin",
                    expected=canonical.gstin,
                    found=dealer.gstin,
                    source_file=source_file,
                )
            )
        if dealer.normalized_financial_year() != canonical.normalized_financial_year():
            mismatches.append(
                DealerMismatchDetail(
                    field="financial_year",
                    expected=canonical.financial_year,
                    found=dealer.financial_year,
                    source_file=source_file,
                )
            )

    if mismatches:
        gstin_issues = [m for m in mismatches if m.field == "gstin"]
        fy_issues = [m for m in mismatches if m.field == "financial_year"]
        parts = []
        if gstin_issues:
            parts.append(
                "GSTIN mismatch: expected "
                f"{canonical.gstin} but found different values in "
                f"{', '.join(m.source_file for m in gstin_issues)}"
            )
        if fy_issues:
            parts.append(
                "Financial Year mismatch: expected "
                f"{canonical.financial_year} but found different values in "
                f"{', '.join(m.source_file for m in fy_issues)}"
            )
        raise DealerValidationError(
            message="; ".join(parts),
            mismatches=mismatches,
        )

    return canonical
