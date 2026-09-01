import pytest

from services.eway_classification_service import classify_eway_file, classify_eway_files, validate_eway_batch
from tests.eway_fixtures import (
    DEALER_GSTIN,
    build_eway_workbook,
    inward_filename,
    outward_filename,
)


class TestEwayClassification:
    def test_classify_outward_with_dealer_in_from_column(self):
        content = build_eway_workbook(direction="outward")
        result = classify_eway_file(outward_filename(), content, DEALER_GSTIN)
        assert result.detected_type == "outward"
        assert result.confidence == 100.0
        assert result.status == "valid"

    def test_classify_inward_with_dealer_in_to_column(self):
        content = build_eway_workbook(direction="inward")
        result = classify_eway_file(inward_filename(), content, DEALER_GSTIN)
        assert result.detected_type == "inward"
        assert result.confidence == 100.0

    def test_unknown_when_dealer_in_both_columns(self):
        content = build_eway_workbook(direction="ambiguous")
        result = classify_eway_file("ambiguous.xlsx", content, DEALER_GSTIN)
        assert result.detected_type == "unknown"
        assert result.status == "unknown"

    def test_wrong_section_detection(self):
        content = build_eway_workbook(direction="outward")
        result = classify_eway_file(outward_filename(), content, DEALER_GSTIN, expected_direction="inward")
        assert result.detected_type == "outward"
        assert result.status == "wrong_section"

    def test_validate_batch_blocks_wrong_upload(self):
        files = [(outward_filename(), build_eway_workbook(direction="outward"))]
        validation = validate_eway_batch(files, "inward", user_gstin=DEALER_GSTIN)
        assert validation.can_merge is False
        assert validation.validations[0].status == "wrong_section"

    def test_classify_requires_dealer_gstin_without_context(self):
        content = build_eway_workbook(direction="outward")
        result = classify_eway_files([(outward_filename(), content)])
        assert result.dealer_resolution.requires_user_input is True
        assert result.classifications[0].status == "pending_dealer_gstin"

    def test_mixed_upload_unknown(self):
        content = build_eway_workbook(direction="mixed", row_count=50)
        result = classify_eway_file("mixed.xlsx", content, DEALER_GSTIN)
        assert result.detected_type == "unknown"
