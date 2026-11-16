"""
schemas.py
----------
Pydantic response and request models for SalesPulse API.
Includes Authentication, RBAC, Analytics, ETL, and Transactions.
"""

# import date classes
from datetime import date, datetime
# import typing helpers
from typing import List, Optional, Dict, Any
# import pydantic base
from pydantic import BaseModel, Field, ConfigDict


# user registration schema
class UserRegisterRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Valid user email") # user email field
    username: str = Field(..., min_length=3, max_length=50, description="Unique username") # username field
    password: str = Field(..., min_length=6, max_length=128, description="User password") # password field
    full_name: Optional[str] = Field(None, description="Full name of user") # full name field
    role: Optional[str] = Field("analyst", description="Role: admin, analyst, or viewer") # rbac role


# user login schema
class UserLoginRequest(BaseModel):
    email_or_username: str = Field(..., description="Email address or username") # login identifier
    password: str = Field(..., description="User password") # login password


# user read schema
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True) # orm attributes mode

    id: int # user id
    email: str # email string
    username: str # username string
    full_name: Optional[str] = None # full name
    role: str # user role
    is_active: bool # active status
    created_at: Optional[datetime] = None # creation time


# token response schema
class TokenResponse(BaseModel):
    access_token: str # jwt access token
    refresh_token: str # opaque refresh token
    token_type: str = "bearer" # token type bearer
    expires_in: int # seconds to expire
    user: UserRead # current user profile


# refresh token request
class RefreshTokenRequest(BaseModel):
    refresh_token: str # refresh token string


# health schema
class HealthResponse(BaseModel):
    status: str # health status
    version: str # app version
    timestamp: str # check timestamp
    database: str # database status
    environment: str # active environment


# analytics summary schema
class SalesSummaryKPIs(BaseModel):
    total_revenue: float = Field(..., description="Sum of NetSales") # total net sales
    total_profit: float = Field(..., description="Sum of Profit") # total net profit
    total_orders: int = Field(..., description="Count of distinct OrderID") # distinct order count
    units_sold: int = Field(..., description="Sum of Quantity") # total units count
    average_order_value: float = Field(..., description="Total Revenue / Total Orders") # revenue per order
    profit_margin_pct: float = Field(..., description="(Total Profit / Total Revenue) * 100") # profit margin pct


# sales trend schema
class SalesTrendItem(BaseModel):
    period: str # period label
    revenue: float # period revenue
    profit: float # period profit
    units_sold: int # units count
    orders_count: int # orders count


# regional performance schema
class RegionPerformanceItem(BaseModel):
    region: str # region name
    revenue: float # region revenue
    profit: float # region profit
    orders_count: int # orders count
    profit_margin_pct: float # margin percent


# category performance schema
class CategoryPerformanceItem(BaseModel):
    category: str # category name
    revenue: float # category revenue
    profit: float # category profit
    units_sold: int # units sold
    revenue_share_pct: float # category share


# top product schema
class TopProductItem(BaseModel):
    product: str # product title
    category: str # product category
    units_sold: int # sold units
    revenue: float # total revenue
    profit: float # total profit
    profit_margin_pct: float # margin rate


# transaction read schema
class SalesTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True) # orm mode

    id: int # transaction id
    transaction_key: str # composite key
    order_id: str # order number
    order_date: date # order date
    customer_id: str # customer number
    customer_name: Optional[str] = None # customer name
    region: str # sales region
    category: str # product category
    product: str # product name
    quantity: int # sold quantity
    unit_price: float # unit price
    cost_price: float # unit cost
    discount: float # discount fraction
    gross_sales: float # gross sales
    discount_amount: float # discount value
    net_sales: float # net revenue
    total_cost: float # total cost
    profit: float # total profit
    payment_method: str # payment method
    job_id: Optional[str] = None # source job
    created_at: Optional[datetime] = None # inserted time


# sales list pagination
class SalesListResponse(BaseModel):
    items: List[SalesTransactionRead] # items page
    total: int # total count
    page: int # current page
    page_size: int # page size
    total_pages: int # pages count


# preview response schema
class SalesPreviewResponse(BaseModel):
    filename: str # source name
    file_size_bytes: int # file bytes
    total_rows: int # total rows
    columns: List[str] # schema columns
    preview_rows: List[Dict[str, Any]] # sample rows


# upload response schema
class UploadResponse(BaseModel):
    file_id: str # file uuid
    filename: str # file name
    file_size_bytes: int # byte size
    columns: List[str] # column headers
    preview_rows: List[Dict[str, Any]] # sample rows
    total_rows: int # row count
    message: str # status text


# etl run request
class ETLRunRequest(BaseModel):
    file_path: Optional[str] = None # optional path
    file_id: Optional[str] = None # optional id
    run_mode: Optional[str] = "sync" # sync or async


# etl job read
class ETLJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True) # orm mode

    id: str # job id
    job_name: str # job title
    file_name: str # file title
    file_size_bytes: int # file bytes
    status: str # job status
    total_rows: int # extracted rows
    valid_rows: int # accepted rows
    rejected_rows: int # rejected rows
    duplicate_rows: int # duplicate rows
    inserted_rows: int # inserted rows
    updated_rows: int # updated rows
    skipped_rows: int # skipped rows
    duration_seconds: float # duration float
    quality_score_pct: float # quality rate
    start_time: Optional[datetime] = None # start time
    end_time: Optional[datetime] = None # end time
    error_message: Optional[str] = None # error text
    created_at: Optional[datetime] = None # creation time


# etl job list
class ETLJobListResponse(BaseModel):
    jobs: List[ETLJobRead] # job items
    total: int # total jobs


# rejection detail schema
class RejectionDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True) # orm mode

    id: int # rejection id
    job_id: str # foreign job id
    row_number: int # row number
    order_id: Optional[str] = None # order id
    product: Optional[str] = None # product name
    rejection_reason: str # failure reason
    raw_data: Optional[str] = None # raw payload
    created_at: Optional[datetime] = None # logged time


# data quality summary
class DataQualitySummaryResponse(BaseModel):
    execution_timestamp: str # run timestamp
    total_extracted_rows: int # total extracted
    valid_rows_count: int # clean rows
    rejected_rows_count: int # rejected rows
    reconciliation_passed: bool # balance status
    data_quality_score_pct: float # quality score
    rejection_breakdown: Dict[str, int] # reasons count
    financial_aggregates: Dict[str, Any] # totals dict
    recent_rejections: List[RejectionDetailRead] = [] # audit rows
