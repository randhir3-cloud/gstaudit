"""Purchase Register plugin HTTP routes."""

from __future__ import annotations

import base64
import importlib.util
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["purchase-plugin"])
_PLUGIN_DIR = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _PLUGIN_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FilePreviewRequest(BaseModel):
    file_base64: str
    filename: str = "purchase.xlsx"


class ImportRequest(BaseModel):
    session_id: str
    file_base64: str
    filename: str = "purchase.xlsx"
    mapping: Optional[Dict[str, Any]] = None
    profile_id: str = ""


class MappingProfileRequest(BaseModel):
    profile_id: str
    mapping: Dict[str, Any]
    template: str = "generic"
    label: str = ""


class PurchaseComparisonRunRequest(BaseModel):
    session_id: str
    purchase_register_workbook_base64: str = ""
    gstr2a_workbook_base64: str = ""
    ewb_inward_workbook_base64: str = ""


@router.get("/api/purchase/ui", response_class=HTMLResponse)
async def purchase_import_ui():
    html_path = _PLUGIN_DIR / "static" / "import_workbench.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Import workbench not found")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@router.post("/api/purchase/import/preview")
async def purchase_import_preview(body: FilePreviewRequest):
    mapping = _load("purchase_mapping_route", "mapping.py")
    try:
        raw = base64.b64decode(body.file_base64)
        return mapping.preview_import(raw, body.filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/purchase/mapping-profiles")
async def list_mapping_profiles():
    mapping = _load("purchase_mapping_route", "mapping.py")
    return {"profiles": mapping.list_profiles(), "fields": mapping.MAPPING_FIELDS}


@router.post("/api/purchase/mapping-profiles")
async def save_mapping_profile(body: MappingProfileRequest):
    mapping = _load("purchase_mapping_route", "mapping.py")
    profile = mapping.save_profile(body.profile_id, body.mapping, body.template, body.label)
    return {"profile": profile}


@router.post("/api/purchase/import")
async def purchase_import(body: ImportRequest):
    from services.audit_session_store import get_session
    from services.comparison_store import cache_workbook

    mapping_mod = _load("purchase_mapping_route", "mapping.py")
    loader = _load("purchase_loader_route", "loader.py")

    if not get_session(body.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        raw = base64.b64decode(body.file_base64)
        col_map = body.mapping
        if not col_map and body.profile_id:
            profile = mapping_mod.get_profile(body.profile_id)
            if profile:
                col_map = profile.get("mapping")
        if not col_map:
            preview = mapping_mod.preview_import(raw, body.filename)
            col_map = preview["detected_mapping"]

        normalized = mapping_mod.apply_mapping_to_normalized_workbook(raw, col_map, body.filename)
        cache_workbook(body.session_id, "purchase_register", normalized)
        records = loader.load_purchase_register_records(normalized, mapping=col_map)

        columns = [v for v in col_map.values() if v]
        return {
            "status": "imported",
            "session_id": body.session_id,
            "row_count": len(records),
            "mapping": col_map,
            "template": mapping_mod.detect_template(columns),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/comparison/purchase-gstr2a", status_code=202)
async def api_comparison_purchase_gstr2a(body: PurchaseComparisonRunRequest):
    comparison = _load("purchase_comparison_route", "comparison.py")
    try:
        result = comparison.enqueue_purchase_gstr2a_comparison(
            body.session_id,
            purchase_register_workbook_base64=body.purchase_register_workbook_base64,
            gstr2a_workbook_base64=body.gstr2a_workbook_base64,
        )
        return JSONResponse(status_code=202, content=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/comparison/purchase-ewb", status_code=202)
async def api_comparison_purchase_ewb(body: PurchaseComparisonRunRequest):
    comparison = _load("purchase_comparison_route", "comparison.py")
    try:
        result = comparison.enqueue_purchase_ewb_comparison(
            body.session_id,
            purchase_register_workbook_base64=body.purchase_register_workbook_base64,
            ewb_inward_workbook_base64=body.ewb_inward_workbook_base64,
        )
        return JSONResponse(status_code=202, content=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/api/plugins/purchase/report-section")
async def purchase_report_section():
    report = _load("purchase_report_route", "report.py")
    return {
        "section": report.report_section_metadata(),
        "sample_highlights": report.build_report_highlights({}),
    }


for _model in (FilePreviewRequest, ImportRequest, MappingProfileRequest, PurchaseComparisonRunRequest):
    _model.model_rebuild()
