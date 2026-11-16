"""
etl.py
------
ETL job execution, status monitoring, and run history.
Protected with Role-Based Access Control (Admin and Analyst only for execution).
"""

# import standard os
import os
# import typing helpers
from typing import Optional, List
# import fastapi components
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
# import query functions
from sqlalchemy import desc
# import session type
from sqlalchemy.orm import Session

# import settings instance
from backend.app.config import settings
# import database sessions
from backend.app.database import get_db, SessionLocal
# import models references
from backend.app.models import ETLJob, ETLRejection, User
# import pydantic schemas
from backend.app.schemas import ETLRunRequest, ETLJobRead, ETLJobListResponse, RejectionDetailRead
# import etl orchestrator
from backend.app.services.etl_service import execute_etl_pipeline
# import rbac dependencies
from backend.app.dependencies import require_role, get_optional_current_user

# define etl router
router = APIRouter(prefix="/etl", tags=["ETL"])


# background task runner
def run_pipeline_in_background(target_file_path: str, job_name: str):
    db: Session = SessionLocal() # open new session
    try:
        execute_etl_pipeline(db=db, file_path=target_file_path, job_name=job_name) # run pipeline function
    finally:
        db.close() # close session clean


# trigger etl execution
@router.post("/run", status_code=status.HTTP_200_OK)
def trigger_etl_run(
    payload: ETLRunRequest, # run request payload
    background_tasks: BackgroundTasks, # background task queue
    current_user: Optional[User] = Depends(get_optional_current_user), # rbac user guard
    db: Session = Depends(get_db) # database session
):
    # enforce rbac if authenticated
    if current_user and current_user.role.lower() not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Executing ETL pipeline requires 'admin' or 'analyst' role. Your role is '{current_user.role}'." # forbidden error
        )

    target_file: Optional[str] = None # resolved target file

    # resolve target file
    if payload.file_id:
        matches = list(settings.UPLOAD_FOLDER.glob(f"{payload.file_id}_*")) # match file prefix
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Uploaded file with ID '{payload.file_id}' not found." # file missing error
            )
        target_file = str(matches[0]) # set matched path
    elif payload.file_path:
        resolved_path = (settings.BASE_DIR / payload.file_path).resolve() # resolve path safe
        if not str(resolved_path).startswith(str(settings.BASE_DIR)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Illegal path traversal attempt." # traversal path error
            )
        if not resolved_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified data file not found." # not found error
            )
        target_file = str(resolved_path) # set resolved path
    else:
        default_raw = settings.BASE_DIR / "data" / "raw" / "sales_data.csv" # default raw path
        if not default_raw.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Default raw dataset 'data/raw/sales_data.csv' not found. Please upload a file first." # default missing error
            )
        target_file = str(default_raw) # set default path

    file_basename = os.path.basename(target_file) # extract base filename
    job_name = f"Job-{file_basename}" # generate job title

    # check execution mode
    if payload.run_mode == "async":
        background_tasks.add_task(run_pipeline_in_background, target_file, job_name) # queue background task
        return {
            "status": "ACCEPTED", # accepted status
            "message": "ETL job scheduled in background.", # schedule message
            "file": file_basename # scheduled filename
        }
    else:
        try:
            # execute pipeline synchronous
            result = execute_etl_pipeline(db=db, file_path=target_file, job_name=job_name)
            return {
                "status": "COMPLETED", # completed status
                "message": "ETL job completed successfully.", # success message
                "job_id": result["job_id"], # job uuid
                "reconciliation_passed": result["reconciliation_passed"], # balance flag
                "total_extracted": result["total_extracted"], # extracted count
                "valid_rows": result["valid_rows"], # valid count
                "rejected_rows": result["rejected_rows"], # rejected count
                "duplicate_rows": result["duplicate_rows"], # duplicate count
                "inserted_rows": result["inserted_rows"], # inserted count
                "skipped_rows": result["skipped_rows"], # skipped count
                "quality_score_pct": result["quality_score_pct"], # quality rate
                "duration_seconds": result["duration_seconds"] # duration seconds
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ETL Execution failed: {str(e)}" # failure error detail
            )


# list job runs
@router.get("/jobs", response_model=ETLJobListResponse)
def list_etl_jobs(
    limit: int = Query(20, ge=1, le=100), # jobs limit
    db: Session = Depends(get_db) # database session
):
    clean_limit = limit if isinstance(limit, int) else (getattr(limit, "default", 20) or 20) # safe limit int
    query = db.query(ETLJob).order_by(desc(ETLJob.created_at)) # query descending date
    total = query.count() # total job runs
    jobs = query.limit(clean_limit).all() # fetch limited items
    return ETLJobListResponse(jobs=jobs, total=total) # return job list


# get job detail
@router.get("/jobs/{job_id}")
def get_etl_job_details(
    job_id: str, # target job id
    db: Session = Depends(get_db) # database session
):
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first() # query job record
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ETL Job '{job_id}' not found." # job missing error
        )

    rejections = db.query(ETLRejection).filter(ETLRejection.job_id == job_id).all() # query job rejections
    return {
        "job": ETLJobRead.model_validate(job), # validated job schema
        "rejections": [RejectionDetailRead.model_validate(r) for r in rejections] # validated rejections
    }


# get latest results
@router.get("/results")
def get_latest_etl_results(db: Session = Depends(get_db)):
    latest_job = db.query(ETLJob).order_by(desc(ETLJob.created_at)).first() # query latest job
    if not latest_job:
        return {"message": "No ETL jobs have been executed yet.", "latest_job": None} # empty state

    rejections_count = db.query(ETLRejection).filter(ETLRejection.job_id == latest_job.id).count() # rejections count
    return {
        "latest_job": ETLJobRead.model_validate(latest_job), # latest job schema
        "rejections_count": rejections_count # count number
    }
