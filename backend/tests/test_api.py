"""
test_api.py
-----------
Tests for all SalesPulse FastAPI endpoints.
Validates business logic, schemas, filtering, pagination, and error handling.
"""

# import io stream
import io
# import pytest module
import pytest
# import http exceptions
from fastapi import HTTPException

# import health endpoint
from backend.app.routers.health import check_health
# import dashboard endpoints
from backend.app.routers.dashboard import (
    get_dashboard_summary, # summary kpis
    get_dashboard_sales_trend, # trend series
    get_dashboard_region_performance, # regional metrics
    get_dashboard_category_performance, # category metrics
    get_dashboard_top_products # top products
)
# import sales endpoints
from backend.app.routers.sales import get_sales_transactions, get_sales_preview
# import etl router
from backend.app.routers.etl import list_etl_jobs, get_latest_etl_results
# import export services
from backend.app.services.export_service import export_clean_sales, export_rejected_sales


def test_health_endpoint(db_session):
    # execute health check
    res = check_health(db=db_session)
    assert res.status in ["healthy", "degraded"] # check status field
    assert res.version == "1.0.0" # check app version
    assert res.database == "connected" # check db connectivity


def test_dashboard_summary_endpoint(db_session):
    # execute summary query
    data = get_dashboard_summary(db=db_session)
    assert data["total_revenue"] > 0 # check positive revenue
    assert data["total_profit"] > 0 # check positive profit
    assert data["total_orders"] > 0 # check positive orders
    assert data["units_sold"] > 0 # check units sold
    assert data["average_order_value"] > 0 # check aov metric
    assert 0 <= data["profit_margin_pct"] <= 100 # check margin range


def test_dashboard_filtered_summary(db_session):
    # filter by North
    data_north = get_dashboard_summary(region="North", db=db_session)
    # filter by South
    data_south = get_dashboard_summary(region="South", db=db_session)

    assert data_north["total_revenue"] > 0 # check north revenue
    assert data_south["total_revenue"] > 0 # check south revenue
    assert data_north["total_revenue"] != data_south["total_revenue"] # check distinct regional


def test_dashboard_sales_trend_endpoint(db_session):
    # fetch monthly trend
    trend = get_dashboard_sales_trend(db=db_session)
    assert isinstance(trend, list) # check list type
    assert len(trend) > 0 # check non empty
    item = trend[0] # first trend month
    assert "period" in item # check period label
    assert "revenue" in item # check revenue metric
    assert "profit" in item # check profit metric
    assert "units_sold" in item # check units metric
    assert "orders_count" in item # check orders count


def test_dashboard_region_performance_endpoint(db_session):
    # fetch region list
    regions = get_dashboard_region_performance(db=db_session)
    assert isinstance(regions, list) # check list type
    assert len(regions) >= 4 # check all regions
    reg = regions[0] # top region item
    assert "region" in reg # check region name
    assert "revenue" in reg # check revenue value
    assert "profit_margin_pct" in reg # check margin rate


def test_dashboard_category_performance_endpoint(db_session):
    # fetch category breakdown
    categories = get_dashboard_category_performance(db=db_session)
    assert isinstance(categories, list) # check list type
    assert len(categories) >= 3 # check categories count
    cat = categories[0] # top category item
    assert "category" in cat # check category name
    assert "revenue_share_pct" in cat # check share percentage


def test_dashboard_top_products_endpoint(db_session):
    # fetch top 5
    top5 = get_dashboard_top_products(limit=5, db=db_session)
    assert isinstance(top5, list) # check list type
    assert len(top5) <= 5 # check max limit
    prod = top5[0] # top product item
    assert "product" in prod # check product name
    assert "revenue" in prod # check product revenue


def test_sales_pagination_and_sorting(db_session):
    # fetch first page
    p1 = get_sales_transactions(page=1, page_size=10, sort_by="order_date", sort_desc=True, db=db_session)
    assert p1.page == 1 # check current page
    assert p1.page_size == 10 # check requested size
    assert len(p1.items) == 10 # check items length
    assert p1.total == 1495 # check total records
    assert p1.total_pages == 150 # check calculated pages


def test_sales_search_filtering(db_session):
    # search for Mouse
    res = get_sales_transactions(search="Mouse", db=db_session)
    assert res.total > 0 # check found matches
    for item in res.items:
        # verify match criteria
        assert "mouse" in item.product.lower() or "mouse" in (item.customer_name or "").lower()


def test_sales_preview_endpoint(db_session):
    # fetch table preview
    preview = get_sales_preview(limit=10, db=db_session)
    assert len(preview.preview_rows) == 10 # check preview count
    assert "order_id" in preview.columns # check order column
    assert "net_sales" in preview.columns # check sales column


def test_etl_jobs_list_endpoint(db_session):
    # list job history
    jobs_res = list_etl_jobs(limit=10, db=db_session)
    assert jobs_res.total >= 1 # check seeded job
    first_job = jobs_res.jobs[0] # latest job item
    assert first_job.status in ["COMPLETED", "PROCESSING"] # check valid status
    assert first_job.valid_rows == 1495 # check clean rows
    assert first_job.rejected_rows == 6 # check rejected rows


def test_exports_clean_sales_buffer(db_session):
    # export csv buffer
    csv_buf = export_clean_sales(db=db_session, format="csv")
    csv_content = csv_buf.getvalue().decode("utf-8") # decode csv bytes
    assert "TransactionKey,OrderID,OrderDate" in csv_content # check csv headers
    assert len(csv_content.splitlines()) > 1000 # check data rows


def test_exports_rejected_sales_buffer(db_session):
    # export rejected buffer
    csv_buf = export_rejected_sales(db=db_session, format="csv")
    csv_content = csv_buf.getvalue().decode("utf-8") # decode csv bytes
    assert "JobID,RowNumber,OrderID,Product,RejectionReason" in csv_content # check rejection headers
    assert len(csv_content.splitlines()) >= 6 # check 6 rejected
