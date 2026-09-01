"""Shared HTTP helpers for plugin routes."""

from __future__ import annotations

from typing import List

from fastapi import UploadFile

from models.dealer_metadata import DealerMetadata, WorkbookMetadataResponse


def workbook_metadata_header(
    workbook_id: str,
    dealer: DealerMetadata,
    return_type: str,
    source_files: List[str],
    current_dataset: str = "",
) -> dict:
    payload = WorkbookMetadataResponse(
        workbook_id=workbook_id,
        dealer=dealer,
        return_type=return_type,
        source_files=source_files,
        current_dataset=current_dataset,
    )
    return {"X-Workbook-Metadata": payload.model_dump_json()}


async def read_upload_files(files: List[UploadFile]) -> List[tuple[str, bytes]]:
    file_data = []
    for file in files:
        content = await file.read()
        file_data.append((file.filename, content))
    return file_data
