"""
models.py
---------
SQLAlchemy ORM models for SalesPulse.
Includes Sales Transactions, ETL Jobs, Rejections, Users, Tokens, and RBAC.
"""

# import datetime timezone
from datetime import datetime, timezone
# import sqlalchemy datatypes
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Date, DateTime, Text, ForeignKey, Boolean
)
# import orm relationship
from sqlalchemy.orm import relationship
# import database base
from backend.app.database import Base


# get current utc
def utc_now():
    return datetime.now(timezone.utc) # current utc timestamp


class User(Base):
    # table user name
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True) # user primary key
    email = Column(String(255), unique=True, nullable=False, index=True) # unique user email
    username = Column(String(100), unique=True, nullable=False, index=True) # unique username
    hashed_password = Column(String(255), nullable=False) # salted hashed password
    full_name = Column(String(255), nullable=True) # user display name
    role = Column(String(50), default="analyst", nullable=False) # rbac role: admin, analyst, viewer
    is_active = Column(Boolean, default=True, nullable=False) # active account flag
    created_at = Column(DateTime, default=utc_now) # user creation timestamp

    # user refresh tokens
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    # table refresh tokens
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True) # token primary key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True) # parent user id
    token = Column(String(255), unique=True, nullable=False, index=True) # unique refresh token
    expires_at = Column(DateTime, nullable=False) # token expiration time
    revoked = Column(Boolean, default=False, nullable=False) # token revocation status
    created_at = Column(DateTime, default=utc_now) # token creation timestamp

    # parent user relation
    user = relationship("User", back_populates="refresh_tokens")


class RevokedToken(Base):
    # table revoked tokens
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True) # primary key id
    jti = Column(String(255), unique=True, nullable=False, index=True) # jwt token identifier
    expires_at = Column(DateTime, nullable=False) # token expiration date
    revoked_at = Column(DateTime, default=utc_now) # revocation timestamp


class ETLJob(Base):
    # table etl jobs
    __tablename__ = "etl_jobs"

    id = Column(String(36), primary_key=True, index=True) # uuid job id
    job_name = Column(String(255), nullable=False) # job display name
    file_name = Column(String(255), nullable=False) # source file name
    file_size_bytes = Column(BigInteger, default=0, nullable=False) # file byte size
    status = Column(String(50), default="PENDING", nullable=False, index=True) # PENDING, PROCESSING, COMPLETED, FAILED

    total_rows = Column(Integer, default=0) # extracted rows count
    valid_rows = Column(Integer, default=0) # clean rows count
    rejected_rows = Column(Integer, default=0) # rejected rows count
    duplicate_rows = Column(Integer, default=0) # duplicate rows count
    inserted_rows = Column(Integer, default=0) # database inserted count
    updated_rows = Column(Integer, default=0) # database updated count
    skipped_rows = Column(Integer, default=0) # database skipped count

    start_time = Column(DateTime, nullable=True) # execution start time
    end_time = Column(DateTime, nullable=True) # execution end time
    duration_seconds = Column(Float, default=0.0) # execution duration seconds
    error_message = Column(Text, nullable=True) # error log message
    quality_score_pct = Column(Float, default=0.0) # quality score percent

    created_at = Column(DateTime, default=utc_now, index=True) # record creation time

    # job relationship mappings
    rejections = relationship("ETLRejection", back_populates="job", cascade="all, delete-orphan")
    transactions = relationship("SalesTransaction", back_populates="job")


class ETLRejection(Base):
    # table etl rejections
    __tablename__ = "etl_rejections"

    id = Column(Integer, primary_key=True, autoincrement=True) # rejection primary key
    job_id = Column(String(36), ForeignKey("etl_jobs.id", ondelete="CASCADE"), nullable=False, index=True) # foreign job id
    row_number = Column(Integer, nullable=False) # original file row
    order_id = Column(String(100), nullable=True, index=True) # order id reference
    product = Column(String(255), nullable=True) # product name reference
    rejection_reason = Column(Text, nullable=False) # validation failure reason
    raw_data = Column(Text, nullable=True) # json raw payload
    created_at = Column(DateTime, default=utc_now) # rejection logged time

    # parent job relation
    job = relationship("ETLJob", back_populates="rejections")


class SalesTransaction(Base):
    # table sales transactions
    __tablename__ = "sales_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True) # transaction primary key
    transaction_key = Column(String(255), unique=True, nullable=False, index=True) # composite unique key
    order_id = Column(String(100), nullable=False, index=True) # order id string
    order_date = Column(Date, nullable=False, index=True) # transaction order date
    customer_id = Column(String(100), nullable=False, index=True) # customer id string
    customer_name = Column(String(255), nullable=True) # customer full name
    region = Column(String(100), nullable=False, index=True) # geographical sales region
    category = Column(String(100), nullable=False, index=True) # product main category
    product = Column(String(255), nullable=False, index=True) # product item name
    quantity = Column(Integer, nullable=False) # item unit quantity
    unit_price = Column(Float, nullable=False) # item unit price
    cost_price = Column(Float, default=0.0, nullable=False) # item cost price
    discount = Column(Float, default=0.0, nullable=False) # discount fraction rate

    gross_sales = Column(Float, nullable=False) # quantity * unit price
    discount_amount = Column(Float, nullable=False) # gross sales * discount
    net_sales = Column(Float, nullable=False) # gross sales - discount
    total_cost = Column(Float, nullable=False) # quantity * cost price
    profit = Column(Float, nullable=False) # net sales - cost

    payment_method = Column(String(100), nullable=False, index=True) # payment method type
    job_id = Column(String(36), ForeignKey("etl_jobs.id", ondelete="SET NULL"), nullable=True, index=True) # source etl job
    created_at = Column(DateTime, default=utc_now) # database inserted time

    # parent job relation
    job = relationship("ETLJob", back_populates="transactions")
