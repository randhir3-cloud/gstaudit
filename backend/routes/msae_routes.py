"""MSAE API routes — Multi-Source Audit Engine."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.msae_service import (
    build_consolidated_report,
    enqueue_msae_orchestration,
    get_master_case,
    get_session_msae,
    orchestrate_session,
)

router = APIRouter(prefix="/api/msae", tags=["msae"])


@router.get("")
async def msae_full(session_id: str = Query(...)):
    return get_session_msae(session_id).model_dump()


@router.get("/summary")
async def msae_summary(session_id: str = Query(...)):
    return get_session_msae(session_id).summary.model_dump()


@router.get("/cases")
async def msae_cases(
    session_id: str = Query(...),
    cross_plugin_only: bool = False,
    high_risk_only: bool = False,
    limit: int = 50,
    offset: int = 0,
):
    data = get_session_msae(session_id)
    cases = data.master_cases
    if cross_plugin_only:
        cases = [c for c in cases if c.source_count > 1]
    if high_risk_only:
        cases = [c for c in cases if c.risk_score >= 70]
    page = cases[offset : offset + limit]
    return {
        "session_id": session_id,
        "total": len(cases),
        "cases": [c.model_dump() for c in page],
    }


@router.get("/cases/{master_case_id}")
async def msae_case_detail(session_id: str = Query(...), master_case_id: str = ""):
    case = get_master_case(session_id, master_case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Master case not found")
    return case.model_dump()


@router.get("/patterns")
async def msae_patterns(session_id: str = Query(...)):
    data = get_session_msae(session_id)
    return {"session_id": session_id, "patterns": [p.model_dump() for p in data.patterns]}


@router.get("/scores")
async def msae_scores(session_id: str = Query(...)):
    data = get_session_msae(session_id)
    return {"session_id": session_id, "scores": data.summary.scores.model_dump()}


@router.get("/timeline")
async def msae_timeline(session_id: str = Query(...)):
    data = get_session_msae(session_id)
    return {"session_id": session_id, "timeline": [e.model_dump() for e in data.timeline]}


@router.get("/report")
async def msae_report(session_id: str = Query(...)):
    return build_consolidated_report(session_id).model_dump()


@router.post("/orchestrate", status_code=202)
async def msae_orchestrate(session_id: str = Query(...)):
    return enqueue_msae_orchestration(session_id)
