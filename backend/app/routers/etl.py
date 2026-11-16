"""
etl.py
------
ETL job execution, status monitoring, and run history.
"""

import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db, SessionLocal
from backend.app.models import ETLJob, ETLRejection
from backend.app.schemas import ETLRunRequest, ETLJobRead, ETLJobListResponse, RejectionDetailRead
from backend.app.services.etl_service import execute_etl_pipeline

router = APIRouter(prefix="/etl", tags=["ETL"])


def run_pipeline_in_background(target_file_path: str, job_name: str):
    db: Session = SessionLocal()
    try:
        execute_etl_pipeline(db=db, file_path=target_file_path, job_name=job_name)
    finally:
        db.close()


@router.post("/run", status_code=status.HTTP_200_OK)
def trigger_etl_run(
    payload: ETLRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    target_file: Optional[str] = None

    # 1. Resolve target file safely
    if payload.file_id:
        # Search for file starting with file_id in upload folder
        matches = list(settings.UPLOAD_FOLDER.glob(f"{payload.file_id}_*"))
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Uploaded file with ID '{payload.file_id}' not found."
            )
        target_file = str(matches[0])
    elif payload.file_path:
        # Prevent path traversal outside allowed data directory
        resolved_path = (settings.BASE_DIR / payload.file_path).resolve()
        if not str(resolved_path).startswith(str(settings.BASE_DIR)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Illegal path traversal attempt."
            )
        if not resolved_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified data file not found."
            )
        target_file = str(resolved_path)
    else:
        # Default to raw sales data
        default_raw = settings.BASE_DIR / "data" / "raw" / "sales_data.csv"
        if not default_raw.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Default raw dataset 'data/raw/sales_data.csv' not found. Please upload a file first."
            )
        target_file = str(default_raw)

    file_basename = os.path.basename(target_file)
    job_name = f"Job-{file_basename}"

    # 2. Asynchronous vs Synchronous Execution
    if payload.run_mode == "async":
        background_tasks.add_task(run_pipeline_in_background, target_file, job_name)
        return {
            "status": "ACCEPTED",
            "message": "ETL job scheduled in background.",
            "file": file_basename
        }
    else:
        try:
            result = execute_etl_pipeline(db=db, file_path=target_file, job_name=job_name)
            return {
                "status": "COMPLETED",
                "message": "ETL job completed successfully.",
                "job_id": result["job_id"],
                "reconciliation_passed": result["reconciliation_passed"],
                "total_extracted": result["total_extracted"],
                "valid_rows": result["valid_rows"],
                "rejected_rows": result["rejected_rows"],
                "duplicate_rows": result["duplicate_rows"],
                "inserted_rows": result["inserted_rows"],
                "skipped_rows": result["skipped_rows"],
                "quality_score_pct": result["quality_score_pct"],
                "duration_seconds": result["duration_seconds"]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ETL Execution failed: {str(e)}"
            )


@router.get("/jobs", response_model=ETLJobListResponse)
def list_etl_jobs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(ETLJob).order_by(desc(ETLJob.created_at))
    total = query.count()
    jobs = query.limit(limit).all()
    return ETLJobListResponse(jobs=jobs, total=total)


@router.get("/jobs/{job_id}")
def get_etl_job_details(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ETL Job '{job_id}' not found."
        )

    rejections = db.query(ETLRejection).filter(ETLRejection.job_id == job_id).all()
    return {
        "job": ETLJobRead.model_validate(job),
        "rejections": [RejectionDetailRead.model_validate(r) for r in rejections]
    }


@router.get("/results")
def get_latest_etl_results(db: Session = Depends(get_db)):
    latest_job = db.query(ETLJob).order_by(desc(ETLJob.created_at)).first()
    if not latest_job:
        return {"message": "No ETL jobs have been executed yet.", "latest_job": None}

    rejections_count = db.query(ETLRejection).filter(ETLRejection.job_id == latest_job.id).count()
    return {
        "latest_job": ETLJobRead.model_validate(latest_job),
        "rejections_count": rejections_count
    }
