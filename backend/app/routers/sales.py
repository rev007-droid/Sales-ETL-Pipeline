"""
sales.py
--------
Endpoints for querying and exploring sales transactions.
"""

# import type hints
from typing import Optional
# import date classes
from datetime import date
# import fastapi router
from fastapi import APIRouter, Depends, Query, HTTPException
# import sqlalchemy clauses
from sqlalchemy import desc, asc, or_
# import session type
from sqlalchemy.orm import Session

# import database dependency
from backend.app.database import get_db
# import transaction model
from backend.app.models import SalesTransaction
# import pydantic models
from backend.app.schemas import SalesListResponse, SalesTransactionRead, SalesPreviewResponse
# import filter helper
from backend.app.services.analytics_service import apply_analytics_filters

# define sales router
router = APIRouter(prefix="/sales", tags=["Sales"])


# clean parameter helper
def resolve_val(v, default=None):
    if hasattr(v, "default"):
        return default # return default
    return v if v is not None else default # return valid


@router.get("", response_model=SalesListResponse)
def get_sales_transactions(
    page: int = Query(1, ge=1), # page number
    page_size: int = Query(25, ge=1, le=200), # items per page
    search: Optional[str] = Query(None, description="Search order ID, customer name, or product"), # search text
    region: Optional[str] = Query(None), # region filter
    category: Optional[str] = Query(None), # category filter
    payment_method: Optional[str] = Query(None), # payment filter
    start_date: Optional[date] = Query(None), # start date
    end_date: Optional[date] = Query(None), # end date
    sort_by: str = Query("order_date"), # sort column
    sort_desc: bool = Query(True), # sort order
    db: Session = Depends(get_db) # database session
):
    # clean pagination values
    c_page = page if isinstance(page, int) else resolve_val(page, 1) # safe page
    c_page_size = page_size if isinstance(page_size, int) else resolve_val(page_size, 25) # safe size
    c_sort_by = sort_by if isinstance(sort_by, str) else resolve_val(sort_by, "order_date") # safe sort
    c_sort_desc = sort_desc if isinstance(sort_desc, bool) else resolve_val(sort_desc, True) # safe desc
    c_search = search if isinstance(search, str) else resolve_val(search, None) # safe search

    # initialize transactions query
    query = db.query(SalesTransaction)
    # apply analytical filters
    query = apply_analytics_filters(
        query,
        start_date=resolve_val(start_date), # start date
        end_date=resolve_val(end_date), # end date
        region=resolve_val(region), # region
        category=resolve_val(category), # category
        payment_method=resolve_val(payment_method) # payment
    )

    # apply search filter
    if c_search:
        pattern = f"%{c_search.strip()}%" # search wildcard
        query = query.filter(
            or_(
                SalesTransaction.order_id.ilike(pattern), # match order id
                SalesTransaction.customer_name.ilike(pattern), # match customer name
                SalesTransaction.product.ilike(pattern), # match product name
                SalesTransaction.customer_id.ilike(pattern) # match customer id
            )
        )

    # count total matches
    total = query.count()

    # resolve sort column
    sort_col = getattr(SalesTransaction, c_sort_by, SalesTransaction.order_date)
    if c_sort_desc:
        query = query.order_by(desc(sort_col)) # descending order
    else:
        query = query.order_by(asc(sort_col)) # ascending order

    # calculate offset pagination
    offset = (c_page - 1) * c_page_size
    # fetch page records
    items = query.offset(offset).limit(c_page_size).all()
    # calculate total pages
    total_pages = (total + c_page_size - 1) // c_page_size if total > 0 else 1

    return SalesListResponse(
        items=items, # items list
        total=total, # total count
        page=c_page, # current page
        page_size=c_page_size, # page size
        total_pages=total_pages # page total
    )


@router.get("/preview", response_model=SalesPreviewResponse)
def get_sales_preview(
    limit: int = Query(10, ge=1, le=50), # preview limit
    db: Session = Depends(get_db) # database session
):
    # safe preview limit
    c_limit = limit if isinstance(limit, int) else resolve_val(limit, 10)

    # fetch preview rows
    rows = db.query(SalesTransaction).order_by(SalesTransaction.id.asc()).limit(c_limit).all()
    # count all records
    total_count = db.query(SalesTransaction).count()

    preview_rows = []
    # preview columns list
    columns = [
        "order_id", "order_date", "customer_name", "region", "category",
        "product", "quantity", "unit_price", "discount", "net_sales", "profit", "payment_method"
    ]
    # format preview records
    for r in rows:
        preview_rows.append({
            "order_id": r.order_id, # order id
            "order_date": r.order_date.isoformat(), # date string
            "customer_name": r.customer_name, # client name
            "region": r.region, # sales region
            "category": r.category, # item category
            "product": r.product, # product name
            "quantity": r.quantity, # quantity number
            "unit_price": r.unit_price, # price float
            "discount": r.discount, # discount rate
            "net_sales": r.net_sales, # net revenue
            "profit": r.profit, # profit value
            "payment_method": r.payment_method # payment type
        })

    return SalesPreviewResponse(
        filename="Database: sales_transactions", # source name
        file_size_bytes=0, # db size
        total_rows=total_count, # total rows
        columns=columns, # schema columns
        preview_rows=preview_rows # preview items
    )
