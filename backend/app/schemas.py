"""
schemas.py
----------
Pydantic response and request models for SalesPulse API.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# Health Schema
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    database: str
    environment: str


# Analytics Schemas
class SalesSummaryKPIs(BaseModel):
    total_revenue: float = Field(..., description="Sum of NetSales")
    total_profit: float = Field(..., description="Sum of Profit")
    total_orders: int = Field(..., description="Count of distinct OrderID")
    units_sold: int = Field(..., description="Sum of Quantity")
    average_order_value: float = Field(..., description="Total Revenue / Total Orders")
    profit_margin_pct: float = Field(..., description="(Total Profit / Total Revenue) * 100")


class SalesTrendItem(BaseModel):
    period: str
    revenue: float
    profit: float
    units_sold: int
    orders_count: int


class RegionPerformanceItem(BaseModel):
    region: str
    revenue: float
    profit: float
    orders_count: int
    profit_margin_pct: float


class CategoryPerformanceItem(BaseModel):
    category: str
    revenue: float
    profit: float
    units_sold: int
    revenue_share_pct: float


class TopProductItem(BaseModel):
    product: str
    category: str
    units_sold: int
    revenue: float
    profit: float
    profit_margin_pct: float


# Transaction Schemas
class SalesTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_key: str
    order_id: str
    order_date: date
    customer_id: str
    customer_name: Optional[str] = None
    region: str
    category: str
    product: str
    quantity: int
    unit_price: float
    cost_price: float
    discount: float
    gross_sales: float
    discount_amount: float
    net_sales: float
    total_cost: float
    profit: float
    payment_method: str
    job_id: Optional[str] = None
    created_at: Optional[datetime] = None


class SalesListResponse(BaseModel):
    items: List[SalesTransactionRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class SalesPreviewResponse(BaseModel):
    filename: str
    file_size_bytes: int
    total_rows: int
    columns: List[str]
    preview_rows: List[Dict[str, Any]]


# Upload & ETL Schemas
class UploadResponse(BaseModel):
    file_id: str
    filename: str
    file_size_bytes: int
    columns: List[str]
    preview_rows: List[Dict[str, Any]]
    total_rows: int
    message: str


class ETLRunRequest(BaseModel):
    file_path: Optional[str] = None
    file_id: Optional[str] = None
    run_mode: Optional[str] = "sync"  # "sync" or "async"


class ETLJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_name: str
    file_name: str
    file_size_bytes: int
    status: str
    total_rows: int
    valid_rows: int
    rejected_rows: int
    duplicate_rows: int
    inserted_rows: int
    updated_rows: int
    skipped_rows: int
    duration_seconds: float
    quality_score_pct: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class ETLJobListResponse(BaseModel):
    jobs: List[ETLJobRead]
    total: int


class RejectionDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: str
    row_number: int
    order_id: Optional[str] = None
    product: Optional[str] = None
    rejection_reason: str
    raw_data: Optional[str] = None
    created_at: Optional[datetime] = None


class DataQualitySummaryResponse(BaseModel):
    execution_timestamp: str
    total_extracted_rows: int
    valid_rows_count: int
    rejected_rows_count: int
    reconciliation_passed: bool
    data_quality_score_pct: float
    rejection_breakdown: Dict[str, int]
    financial_aggregates: Dict[str, Any]
    recent_rejections: List[RejectionDetailRead] = []
