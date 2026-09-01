"""GSTR-1 plugin HTTP routes — identical paths to pre-plugin platform."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from comparison.models import ComparisonRunRequest
from gais_platform.http_helpers import read_upload_files, workbook_metadata_header
from merger import find_missing_months, merge_gstr1_files
from services.dealer_validation import DealerValidationError

router = APIRouter(tags=["gstr1-plugin"])


@router.post("/api/merge/gstr1")
async def api_merge_gstr1(
    files: List[UploadFile] = File(...),
    ignore_missing: bool = Query(False),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    try:
        file_data = await read_upload_files(files)

        if not ignore_missing:
            filenames = [f[0] for f in file_data]
            missing = find_missing_months(filenames)
            if missing:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "warning",
                        "error_type": "missing_months",
                        "missing": missing,
                        "message": "Missing months detected between selected files.",
                    },
                )

        output_buffer, auto_name, _, dealer, workbook_id = merge_gstr1_files(file_data)
        filenames = [f[0] for f in file_data]

        headers = {
            "Content-Disposition": f'attachment; filename="{auto_name}"',
            "X-Suggested-Filename": auto_name,
            **workbook_metadata_header(
                workbook_id,
                dealer,
                "gstr1",
                filenames,
                current_dataset=auto_name,
            ),
        }
        return StreamingResponse(
            output_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )
    except DealerValidationError as exc:
        return JSONResponse(status_code=400, content=exc.to_dict())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/comparison/gstr1-eway", status_code=202)
async def api_comparison_gstr1_eway(body: ComparisonRunRequest):
    from services.comparison_service import enqueue_gstr1_eway_comparison

    try:
        result = enqueue_gstr1_eway_comparison(
            body.session_id,
            gstr1_workbook_base64=body.gstr1_workbook_base64,
            ewb_outward_workbook_base64=body.ewb_outward_workbook_base64,
        )
        return JSONResponse(status_code=202, content=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
