"""
models.py
---------
SQLAlchemy ORM models for SalesPulse.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Date, DateTime, Text, ForeignKey, Numeric, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ETLJob(Base):
    __tablename__ = "etl_jobs"

    id = Column(String(36), primary_key=True, index=True)
    job_name = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger, default=0, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, PROCESSING, COMPLETED, FAILED

    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    rejected_rows = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)
    inserted_rows = Column(Integer, default=0)
    updated_rows = Column(Integer, default=0)
    skipped_rows = Column(Integer, default=0)

    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    quality_score_pct = Column(Float, default=0.0)

    created_at = Column(DateTime, default=utc_now, index=True)

    # Relationships
    rejections = relationship("ETLRejection", back_populates="job", cascade="all, delete-orphan")
    transactions = relationship("SalesTransaction", back_populates="job")


class ETLRejection(Base):
    __tablename__ = "etl_rejections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("etl_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    order_id = Column(String(100), nullable=True, index=True)
    product = Column(String(255), nullable=True)
    rejection_reason = Column(Text, nullable=False)
    raw_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    job = relationship("ETLJob", back_populates="rejections")


class SalesTransaction(Base):
    __tablename__ = "sales_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_key = Column(String(255), unique=True, nullable=False, index=True)
    order_id = Column(String(100), nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    customer_id = Column(String(100), nullable=False, index=True)
    customer_name = Column(String(255), nullable=True)
    region = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    product = Column(String(255), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, default=0.0, nullable=False)
    discount = Column(Float, default=0.0, nullable=False)

    gross_sales = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False)
    net_sales = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)

    payment_method = Column(String(100), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("etl_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now)

    job = relationship("ETLJob", back_populates="transactions")
