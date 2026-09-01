"""Generate E-Way Bill Excel fixtures for Playwright E2E tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from tests.eway_fixtures import (  # noqa: E402
    DEALER_GSTIN,
    build_eway_workbook,
    inward_filename,
    outward_filename,
)

OUT_DIR = ROOT / "e2e" / "fixtures"


def write_fixture(path: Path, content: bytes) -> None:
    path.write_bytes(content)
    print(f"Wrote {path.name}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = [
        (outward_filename(), build_eway_workbook(direction="outward"), "outward_correct.xlsx"),
        (inward_filename(), build_eway_workbook(direction="inward"), "inward_correct.xlsx"),
        (outward_filename(), build_eway_workbook(direction="outward"), "outward_for_wrong_section.xlsx"),
        ("mixed_042023_ewb.xlsx", build_eway_workbook(direction="mixed", row_count=50), "mixed_unknown.xlsx"),
        ("ambiguous_042023_ewb.xlsx", build_eway_workbook(direction="ambiguous", row_count=50), "ambiguous_unknown.xlsx"),
    ]

    for _, content, alias in fixtures:
        write_fixture(OUT_DIR / alias, content)

    (OUT_DIR / "dealer_gstin.txt").write_text(DEALER_GSTIN, encoding="utf-8")
    print(f"Dealer GSTIN: {DEALER_GSTIN}")


if __name__ == "__main__":
    main()
