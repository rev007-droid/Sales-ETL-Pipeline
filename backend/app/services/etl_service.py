"""
etl_service.py
--------------
Service layer for orchestrating the SalesPulse ETL pipeline,
database batch loading, idempotent transactions, and error auditing.
"""

import os
import sys
import uuid
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.config import settings
from backend.app.models import ETLJob, ETLRejection, SalesTransaction
from src.transform import run_etl


def execute_etl_pipeline(
    db: Session,
    file_path: str,
    job_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes the ETL process on a specified file, loads clean records into the database
    with transaction rollback safety, records rejected rows, and updates job metadata.
    """
    start_time = datetime.now(timezone.utc)
    start_perf = time.perf_counter()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source file does not exist: {file_path}")

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    job_id = str(uuid.uuid4())
    resolved_job_name = job_name or f"ETL-{file_name}-{start_time.strftime('%Y%m%d%H%M%S')}"

    # 1. Initialize ETL Job record in DB
    job = ETLJob(
        id=job_id,
        job_name=resolved_job_name,
        file_name=file_name,
        file_size_bytes=file_size,
        status="PROCESSING",
        start_time=start_time
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        # 2. Execute Transformation & Data Quality Rules
        etl_result = run_etl(
            input_source=file_path,
            clean_output_path=str(settings.CLEAN_DATA_FILE),
            rejected_output_path=str(settings.REJECTED_DATA_FILE),
            report_output_path=str(settings.DATA_QUALITY_REPORT_FILE)
        )

        clean_df = etl_result["clean_df"]
        rejected_df = etl_result["rejected_df"]
        summary = etl_result["summary"]

        total_extracted = summary["total_extracted_rows"]
        valid_count = summary["valid_rows_count"]
        rejected_count = summary["rejected_rows_count"]
        quality_score = summary["data_quality_score_pct"]
        duplicate_count = summary["rejection_breakdown"].get("duplicate_transaction", 0)

        # 3. Batch insert Rejections into DB
        rejection_records = []
        for _, rej_row in rejected_df.iterrows():
            rejection_records.append(
                ETLRejection(
                    job_id=job_id,
                    row_number=int(rej_row["row_number"]),
                    order_id=str(rej_row.get("order_id", "")),
                    product=str(rej_row.get("product", "")),
                    rejection_reason=str(rej_row["rejection_reason"]),
                    raw_data=str(rej_row.get("raw_data", ""))
                )
            )
        if rejection_records:
            db.bulk_save_objects(rejection_records)

        # 4. Idempotent Database Loading for Clean Records
        # Query existing keys to prevent primary/unique key collisions across repeated runs
        existing_keys = set(
            k[0] for k in db.query(SalesTransaction.transaction_key).all()
        )

        inserted_count = 0
        skipped_count = 0
        transactions_to_insert = []

        for _, row in clean_df.iterrows():
            tx_key = row["transaction_key"]
            if tx_key in existing_keys:
                skipped_count += 1
                continue

            order_date_val = datetime.strptime(str(row["order_date"]), "%Y-%m-%d").date()
            transactions_to_insert.append(
                SalesTransaction(
                    transaction_key=tx_key,
                    order_id=str(row["order_id"]),
                    order_date=order_date_val,
                    customer_id=str(row["customer_id"]),
                    customer_name=str(row["customer_name"]),
                    region=str(row["region"]),
                    category=str(row["category"]),
                    product=str(row["product"]),
                    quantity=int(row["quantity"]),
                    unit_price=float(row["unit_price"]),
                    cost_price=float(row["cost_price"]),
                    discount=float(row["discount"]),
                    gross_sales=float(row["gross_sales"]),
                    discount_amount=float(row["discount_amount"]),
                    net_sales=float(row["net_sales"]),
                    total_cost=float(row["total_cost"]),
                    profit=float(row["profit"]),
                    payment_method=str(row["payment_method"]),
                    job_id=job_id
                )
            )
            existing_keys.add(tx_key)
            inserted_count += 1

        if transactions_to_insert:
            db.bulk_save_objects(transactions_to_insert)

        end_time = datetime.now(timezone.utc)
        duration = round(time.perf_counter() - start_perf, 2)

        # 5. Finalize Job Details
        job.status = "COMPLETED"
        job.total_rows = total_extracted
        job.valid_rows = valid_count
        job.rejected_rows = rejected_count
        job.duplicate_rows = duplicate_count
        job.inserted_rows = inserted_count
        job.skipped_rows = skipped_count
        job.quality_score_pct = quality_score
        job.end_time = end_time
        job.duration_seconds = duration

        db.commit()
        db.refresh(job)

        return {
            "job_id": job.id,
            "job_name": job.job_name,
            "status": "COMPLETED",
            "total_extracted": total_extracted,
            "valid_rows": valid_count,
            "rejected_rows": rejected_count,
            "duplicate_rows": duplicate_count,
            "inserted_rows": inserted_count,
            "skipped_rows": skipped_count,
            "duration_seconds": duration,
            "quality_score_pct": quality_score,
            "reconciliation_passed": (total_extracted == valid_count + rejected_count),
            "summary": summary
        }

    except Exception as e:
        db.rollback()
        end_time = datetime.now(timezone.utc)
        duration = round(time.perf_counter() - start_perf, 2)

        job.status = "FAILED"
        job.error_message = str(e)
        job.end_time = end_time
        job.duration_seconds = duration
        db.commit()
        raise e
