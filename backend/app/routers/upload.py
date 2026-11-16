"""
upload.py
---------
Secure file upload handling, schema inspection, and preliminary validation.
"""

import os
import uuid
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status

from backend.app.config import settings
from backend.app.schemas import UploadResponse

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_sales_file(file: UploadFile = File(...)):
    # 1. Validate file extension
    original_name = file.filename or "upload.csv"
    ext = Path(original_name).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed extensions are: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. Secure file writing & Size check
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{Path(original_name).name}"
    target_path = settings.UPLOAD_FOLDER / safe_filename

    total_bytes = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    try:
        with open(target_path, "wb") as f:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                    # Remove partial file
                    f.close()
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.0f} MB"
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(target_path):
            os.remove(target_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist uploaded file securely."
        )

    # 3. Inspect schema and parse preview safely
    try:
        if ext in [".xlsx", ".xls"]:
            df = pd.read_excel(target_path)
        else:
            df = pd.read_csv(target_path)
    except Exception:
        if os.path.exists(target_path):
            os.remove(target_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is corrupted or not a valid CSV/Excel file."
        )

    columns = [str(c) for c in df.columns.tolist()]
    total_rows = len(df)
    preview_df = df.head(10).fillna("")
    preview_rows = preview_df.to_dict(orient="records")

    return UploadResponse(
        file_id=file_id,
        filename=original_name,
        file_size_bytes=total_bytes,
        columns=columns,
        preview_rows=preview_rows,
        total_rows=total_rows,
        message=f"File uploaded successfully. {total_rows} rows detected."
    )
