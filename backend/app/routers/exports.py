"""
exports.py
----------
Data export endpoints for clean datasets and rejected audit trails.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.export_service import export_clean_sales, export_rejected_sales

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get("/clean-sales")
def download_clean_sales(
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    db: Session = Depends(get_db)
):
    buffer = export_clean_sales(db=db, format=format)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    filename = f"clean_sales_export.{format}"

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/rejected-sales")
def download_rejected_sales(
    job_id: Optional[str] = Query(None),
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    db: Session = Depends(get_db)
):
    buffer = export_rejected_sales(db=db, job_id=job_id, format=format)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    filename = f"rejected_sales_export.{format}"

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
