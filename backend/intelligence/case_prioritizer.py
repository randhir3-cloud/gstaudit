"""Case prioritization — score, priority level, and reason."""

from __future__ import annotations

from comparison.comparison_types import ComparisonResultType
from comparison.result_models import ComparisonRecord
from intelligence.models import CaseIntelligence, CasePriorityResult
from intelligence.pattern_detector import patterns_for_record
from intelligence.risk_classifier import classify_record, score_to_priority
from intelligence.document_recommender import recommend_documents
from intelligence.recommendation_engine import generate_guidance


def prioritize_case(
    case_id: str,
    record: ComparisonRecord,
    pattern_findings: list,
    related_ids: list[str] | None = None,
) -> CaseIntelligence:
    score, _, base_reason = classify_record(record)
    patterns = patterns_for_record(record, pattern_findings)

    # Boost score for pattern involvement
    if patterns:
        score = min(100, score + len(patterns) * 5)
    if record.result_type == ComparisonResultType.MISSING_IN_GSTR1:
        score = min(100, score + 5)

    priority = score_to_priority(score)
    reason = base_reason
    if patterns:
        reason = f"{reason} Pattern: {patterns[0]}"

    guidance = generate_guidance(record, patterns)
    docs = recommend_documents(record.result_type)

    return CaseIntelligence(
        case_id=case_id,
        priority=priority,  # type: ignore[arg-type]
        priority_score=score,
        priority_reason=reason,
        patterns=patterns,
        recommended_documents=docs,
        possible_causes=guidance["possible_causes"],
        suggested_verifications=guidance["suggested_verifications"],
        gst_provisions=guidance["gst_provisions"],
        related_case_ids=related_ids or [],
    )


def priority_result(record: ComparisonRecord) -> CasePriorityResult:
    score, _, reason = classify_record(record)
    return CasePriorityResult(
        priority=score_to_priority(score),  # type: ignore[arg-type]
        score=score,
        reason=reason,
    )
