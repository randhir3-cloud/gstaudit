"""GSTR-2A plugin HTTP routes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(tags=["gstr2a-plugin"])


class Gstr2aComparisonRunRequest(BaseModel):
    session_id: str
    gstr2a_workbook_base64: str = ""
    ewb_inward_workbook_base64: str = ""


@router.post("/api/comparison/gstr2a-eway", status_code=202)
async def api_comparison_gstr2a_eway(body: Gstr2aComparisonRunRequest):
    import importlib.util
    from pathlib import Path

    comp_path = Path(__file__).resolve().parent / "comparison.py"
    spec = importlib.util.spec_from_file_location("gais_gstr2a_comparison_route", comp_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    try:
        result = module.enqueue_gstr2a_eway_comparison(
            body.session_id,
            gstr2a_workbook_base64=body.gstr2a_workbook_base64,
            ewb_inward_workbook_base64=body.ewb_inward_workbook_base64,
        )
        return JSONResponse(status_code=202, content=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/api/plugins/gstr2a/report-section")
async def gstr2a_report_section():
    import importlib.util
    from pathlib import Path

    report_path = Path(__file__).resolve().parent / "report.py"
    spec = importlib.util.spec_from_file_location("gais_gstr2a_report_route", report_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return {
        "section": module.report_section_metadata(),
        "sample_highlights": module.build_report_highlights({}),
    }
