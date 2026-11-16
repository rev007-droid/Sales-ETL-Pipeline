"""
reports.py
----------
Endpoints for fetching comprehensive Data Quality audit reports.
"""

import os
import json
from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import ETLRejection, ETLJob
from backend.app.schemas import DataQualitySummaryResponse, RejectionDetailRead

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/data-quality", response_model=DataQualitySummaryResponse)
def get_data_quality_report(db: Session = Depends(get_db)):
    summary_path = settings.DATA_QUALITY_REPORT_FILE

    # Fetch recent rejections from database
    recent_rejections_query = db.query(ETLRejection).order_by(desc(ETLRejection.created_at)).limit(50).all()
    recent_rejections = [RejectionDetailRead.model_validate(r) for r in recent_rejections_query]

    # Load from persistent JSON summary if available
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DataQualitySummaryResponse(
                execution_timestamp=data.get("execution_timestamp", ""),
                total_extracted_rows=data.get("total_extracted_rows", 0),
                valid_rows_count=data.get("valid_rows_count", 0),
                rejected_rows_count=data.get("rejected_rows_count", 0),
                reconciliation_passed=data.get("reconciliation_passed", True),
                data_quality_score_pct=data.get("data_quality_score_pct", 0.0),
                rejection_breakdown=data.get("rejection_breakdown", {}),
                financial_aggregates=data.get("financial_aggregates", {}),
                recent_rejections=recent_rejections
            )
        except Exception:
            pass

    # Fallback to database aggregations if report file is not yet generated
    latest_job = db.query(ETLJob).filter(ETLJob.status == "COMPLETED").order_by(desc(ETLJob.created_at)).first()
    if latest_job:
        total = latest_job.total_rows
        valid = latest_job.valid_rows
        rejected = latest_job.rejected_rows
        return DataQualitySummaryResponse(
            execution_timestamp=latest_job.end_time.isoformat() if latest_job.end_time else "",
            total_extracted_rows=total,
            valid_rows_count=valid,
            rejected_rows_count=rejected,
            reconciliation_passed=(total == valid + rejected),
            data_quality_score_pct=latest_job.quality_score_pct,
            rejection_breakdown={"rejections": rejected},
            financial_aggregates={},
            recent_rejections=recent_rejections
        )

    return DataQualitySummaryResponse(
        execution_timestamp="",
        total_extracted_rows=0,
        valid_rows_count=0,
        rejected_rows_count=0,
        reconciliation_passed=True,
        data_quality_score_pct=100.0,
        rejection_breakdown={},
        financial_aggregates={},
        recent_rejections=[]
    )
