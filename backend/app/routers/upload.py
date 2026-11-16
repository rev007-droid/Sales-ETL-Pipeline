"""
upload.py
---------
Secure file upload handling, schema inspection, and preliminary validation.
Protected with Role-Based Access Control (Admin and Analyst only).
"""

# import standard os
import os
# import uuid generator
import uuid
# import pandas library
import pandas as pd
# import pathlib path
from pathlib import Path
# import fastapi components
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status

# import settings instance
from backend.app.config import settings
# import upload response
from backend.app.schemas import UploadResponse
# import user model
from backend.app.models import User
# import rbac dependency
from backend.app.dependencies import require_role, get_optional_current_user

# define upload router
router = APIRouter(prefix="/upload", tags=["Upload"])


# upload sales file
@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_sales_file(
    file: UploadFile = File(...), # upload file object
    current_user: Optional[User] = Depends(get_optional_current_user) # optional user guard
):
    # enforce rbac if user is authenticated
    if current_user and current_user.role.lower() not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Uploading data requires 'admin' or 'analyst' role. Your role is '{current_user.role}'." # forbidden error
        )

    # validate file extension
    original_name = file.filename or "upload.csv" # fallback file name
    ext = Path(original_name).suffix.lower() # extract file extension
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed extensions are: {', '.join(settings.ALLOWED_EXTENSIONS)}" # invalid extension error
        )

    # generate safe filename
    file_id = str(uuid.uuid4()) # unique file identifier
    safe_filename = f"{file_id}_{Path(original_name).name}" # uuid prefixed filename
    target_path = settings.UPLOAD_FOLDER / safe_filename # staging target path

    total_bytes = 0 # byte counter accumulator
    chunk_size = 1024 * 1024  # 1 megabyte chunks

    try:
        # stream write file
        with open(target_path, "wb") as f:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk) # count written bytes
                if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                    f.close() # close open file
                    if os.path.exists(target_path):
                        os.remove(target_path) # delete partial file
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.0f} MB" # file too large
                    )
                f.write(chunk) # write chunk bytes
    except HTTPException:
        raise # re-raise http exception
    except Exception:
        if os.path.exists(target_path):
            os.remove(target_path) # clean on failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist uploaded file securely." # write failure error
        )

    # inspect schema safely
    try:
        if ext in [".xlsx", ".xls"]:
            df = pd.read_excel(target_path) # read excel format
        else:
            df = pd.read_csv(target_path) # read csv format
    except Exception:
        if os.path.exists(target_path):
            os.remove(target_path) # clean corrupted file
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is corrupted or not a valid CSV/Excel file." # unprocessable file error
        )

    columns = [str(c) for c in df.columns.tolist()] # detected column headers
    total_rows = len(df) # total dataframe rows
    preview_df = df.head(10).fillna("") # preview first ten
    preview_rows = preview_df.to_dict(orient="records") # preview records list

    return UploadResponse(
        file_id=file_id, # file uuid
        filename=original_name, # original filename
        file_size_bytes=total_bytes, # total byte size
        columns=columns, # schema columns
        preview_rows=preview_rows, # preview sample rows
        total_rows=total_rows, # detected row count
        message=f"File uploaded successfully. {total_rows} rows detected." # success status message
    )
