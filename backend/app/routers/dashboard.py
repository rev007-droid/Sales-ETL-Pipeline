"""
dashboard.py
------------
Analytical dashboard endpoints for KPIs, trends, and breakdown visualizations.
"""

# import type hints
from typing import List, Optional
# import date classes
from datetime import date
# import fastapi router
from fastapi import APIRouter, Depends, Query
# import session type
from sqlalchemy.orm import Session

# import database session
from backend.app.database import get_db
# import pydantic schemas
from backend.app.schemas import (
    SalesSummaryKPIs, # kpi summary
    SalesTrendItem, # trend item
    RegionPerformanceItem, # region metrics
    CategoryPerformanceItem, # category share
    TopProductItem # product rank
)
# import analytics service
from backend.app.services import analytics_service

# define dashboard router
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# helper resolve param
def resolve_param(val):
    # return none if query
    if hasattr(val, "default"):
        return None
    return val # return raw value


@router.get("/summary", response_model=SalesSummaryKPIs)
def get_dashboard_summary(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"), # start date filter
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"), # end date filter
    region: Optional[str] = Query(None, description="Region filter"), # region filter
    category: Optional[str] = Query(None, description="Category filter"), # category filter
    payment_method: Optional[str] = Query(None, description="Payment method filter"), # payment filter
    db: Session = Depends(get_db) # database session
):
    # compute summary kpis
    return analytics_service.get_summary_kpis(
        db=db, # db session
        start_date=resolve_param(start_date), # clean start
        end_date=resolve_param(end_date), # clean end
        region=resolve_param(region), # clean region
        category=resolve_param(category), # clean category
        payment_method=resolve_param(payment_method) # clean payment
    )


@router.get("/sales-trend", response_model=List[SalesTrendItem])
def get_dashboard_sales_trend(
    start_date: Optional[date] = Query(None), # start date
    end_date: Optional[date] = Query(None), # end date
    region: Optional[str] = Query(None), # region
    category: Optional[str] = Query(None), # category
    payment_method: Optional[str] = Query(None), # payment
    db: Session = Depends(get_db) # db session
):
    # compute sales trend
    return analytics_service.get_sales_trend(
        db=db, # db session
        start_date=resolve_param(start_date), # clean start
        end_date=resolve_param(end_date), # clean end
        region=resolve_param(region), # clean region
        category=resolve_param(category), # clean category
        payment_method=resolve_param(payment_method) # clean payment
    )


@router.get("/region-performance", response_model=List[RegionPerformanceItem])
def get_dashboard_region_performance(
    start_date: Optional[date] = Query(None), # start date
    end_date: Optional[date] = Query(None), # end date
    region: Optional[str] = Query(None), # region
    category: Optional[str] = Query(None), # category
    payment_method: Optional[str] = Query(None), # payment
    db: Session = Depends(get_db) # db session
):
    # compute regional performance
    return analytics_service.get_region_performance(
        db=db, # db session
        start_date=resolve_param(start_date), # clean start
        end_date=resolve_param(end_date), # clean end
        region=resolve_param(region), # clean region
        category=resolve_param(category), # clean category
        payment_method=resolve_param(payment_method) # clean payment
    )


@router.get("/category-performance", response_model=List[CategoryPerformanceItem])
def get_dashboard_category_performance(
    start_date: Optional[date] = Query(None), # start date
    end_date: Optional[date] = Query(None), # end date
    region: Optional[str] = Query(None), # region
    category: Optional[str] = Query(None), # category
    payment_method: Optional[str] = Query(None), # payment
    db: Session = Depends(get_db) # db session
):
    # compute category performance
    return analytics_service.get_category_performance(
        db=db, # db session
        start_date=resolve_param(start_date), # clean start
        end_date=resolve_param(end_date), # clean end
        region=resolve_param(region), # clean region
        category=resolve_param(category), # clean category
        payment_method=resolve_param(payment_method) # clean payment
    )


@router.get("/top-products", response_model=List[TopProductItem])
def get_dashboard_top_products(
    limit: int = Query(10, ge=1, le=50), # row limit
    start_date: Optional[date] = Query(None), # start date
    end_date: Optional[date] = Query(None), # end date
    region: Optional[str] = Query(None), # region
    category: Optional[str] = Query(None), # category
    payment_method: Optional[str] = Query(None), # payment
    db: Session = Depends(get_db) # db session
):
    # clean limit integer
    clean_limit = limit if isinstance(limit, int) else (getattr(limit, "default", 10) or 10)

    # compute top products
    return analytics_service.get_top_products(
        db=db, # db session
        limit=clean_limit, # clean limit
        start_date=resolve_param(start_date), # clean start
        end_date=resolve_param(end_date), # clean end
        region=resolve_param(region), # clean region
        category=resolve_param(category), # clean category
        payment_method=resolve_param(payment_method) # clean payment
    )
