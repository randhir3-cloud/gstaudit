import io
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List

from merger import merge_eway_bills, merge_gstr1_files, merge_gstr2a_files, find_missing_months

app = FastAPI(title="Excel Merger API", version="1.0")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Suggested-Filename"]
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Excel Merger API"}

@app.post("/api/merge/eway")
async def api_merge_eway(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    
    try:
        # Read files into memory
        file_data = []
        for file in files:
            content = await file.read()
            file_data.append((file.filename, content))
        
        # Merge
        output_buffer = merge_eway_bills(file_data)
        
        headers = {
            'Content-Disposition': 'attachment; filename="eway_merged_output.xlsx"',
            'X-Suggested-Filename': 'eway_merged_output.xlsx'
        }
        return StreamingResponse(
            output_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/merge/gstr1")
async def api_merge_gstr1(
    files: List[UploadFile] = File(...),
    ignore_missing: bool = Query(False)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    
    try:
        # Read files into memory
        file_data = []
        for file in files:
            content = await file.read()
            file_data.append((file.filename, content))
        
        # If ignore_missing is False, check for missing months first
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
                        "message": "Missing months detected between selected files."
                    }
                )
        
        # Merge GSTR-1 files
        output_buffer, auto_name, missing_months = merge_gstr1_files(file_data)
        
        headers = {
            'Content-Disposition': f'attachment; filename="{auto_name}"',
            'X-Suggested-Filename': auto_name
        }
        return StreamingResponse(
            output_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/merge/gstr2a")
async def api_merge_gstr2a(
    files: List[UploadFile] = File(...),
    ignore_missing: bool = Query(False)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    try:
        file_data = []
        for file in files:
            content = await file.read()
            file_data.append((file.filename, content))

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
                        "message": "Missing months detected between selected files."
                    }
                )

        output_buffer, auto_name, missing_months = merge_gstr2a_files(file_data)

        headers = {
            'Content-Disposition': f'attachment; filename="{auto_name}"',
            'X-Suggested-Filename': auto_name
        }
        return StreamingResponse(
            output_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
