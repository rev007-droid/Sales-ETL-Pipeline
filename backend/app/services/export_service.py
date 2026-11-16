"""
export_service.py
-----------------
Generates CSV and Excel exports of clean sales and rejected records.
"""

import io
from typing import Optional
import pandas as pd
from sqlalchemy.orm import Session
from backend.app.models import SalesTransaction, ETLRejection


def export_clean_sales(db: Session, format: str = "csv") -> io.BytesIO:
    query = db.query(SalesTransaction).order_by(SalesTransaction.id.asc())
    transactions = query.all()

    data = []
    for t in transactions:
        data.append({
            "TransactionKey": t.transaction_key,
            "OrderID": t.order_id,
            "OrderDate": t.order_date.isoformat(),
            "CustomerID": t.customer_id,
            "CustomerName": t.customer_name,
            "Region": t.region,
            "Category": t.category,
            "Product": t.product,
            "Quantity": t.quantity,
            "UnitPrice": t.unit_price,
            "CostPrice": t.cost_price,
            "Discount": t.discount,
            "GrossSales": t.gross_sales,
            "DiscountAmount": t.discount_amount,
            "NetSales": t.net_sales,
            "TotalCost": t.total_cost,
            "Profit": t.profit,
            "PaymentMethod": t.payment_method
        })

    df = pd.DataFrame(data)
    buffer = io.BytesIO()

    if format.lower() == "xlsx" or format.lower() == "excel":
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="CleanSales")
    else:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        buffer.write(csv_bytes)

    buffer.seek(0)
    return buffer


def export_rejected_sales(db: Session, job_id: Optional[str] = None, format: str = "csv") -> io.BytesIO:
    query = db.query(ETLRejection)
    if job_id:
        query = query.filter(ETLRejection.job_id == job_id)
    rejections = query.order_by(ETLRejection.row_number.asc()).all()

    data = []
    for r in rejections:
        data.append({
            "JobID": r.job_id,
            "RowNumber": r.row_number,
            "OrderID": r.order_id,
            "Product": r.product,
            "RejectionReason": r.rejection_reason,
            "RawData": r.raw_data,
            "Timestamp": r.created_at.isoformat() if r.created_at else ""
        })

    df = pd.DataFrame(data)
    buffer = io.BytesIO()

    if format.lower() == "xlsx" or format.lower() == "excel":
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="RejectedRecords")
    else:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        buffer.write(csv_bytes)

    buffer.seek(0)
    return buffer
