"""
analytics_service.py
--------------------
SQLAlchemy-based analytics service for computing sales KPIs, trend aggregations,
regional breakdown, category analysis, and product rankings.
"""

# import type annotations
from typing import Dict, Any, List, Optional
# import date utilities
from datetime import date, datetime
# import query functions
from sqlalchemy import func, desc, asc, distinct
# import session type
from sqlalchemy.orm import Session

# import transaction model
from backend.app.models import SalesTransaction


def apply_analytics_filters(query, start_date=None, end_date=None, region=None, category=None, payment_method=None):
    # filter start date
    if start_date and not hasattr(start_date, "default") and str(start_date).lower() != "none" and start_date != "all":
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date() # parse start string
        query = query.filter(SalesTransaction.order_date >= start_date) # apply gte filter

    # filter end date
    if end_date and not hasattr(end_date, "default") and str(end_date).lower() != "none" and end_date != "all":
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date() # parse end string
        query = query.filter(SalesTransaction.order_date <= end_date) # apply lte filter

    # filter sales region
    if region and not hasattr(region, "default") and region != "all":
        query = query.filter(SalesTransaction.region == str(region)) # match region filter

    # filter sales category
    if category and not hasattr(category, "default") and category != "all":
        query = query.filter(SalesTransaction.category == str(category)) # match category filter

    # filter payment type
    if payment_method and not hasattr(payment_method, "default") and payment_method != "all":
        query = query.filter(SalesTransaction.payment_method == str(payment_method)) # match payment filter

    return query # return filtered query


def get_summary_kpis(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None
) -> Dict[str, Any]:
    # build summary aggregates
    query = db.query(
        func.coalesce(func.sum(SalesTransaction.net_sales), 0.0).label("total_revenue"), # total net sales
        func.coalesce(func.sum(SalesTransaction.profit), 0.0).label("total_profit"), # total profit sum
        func.count(distinct(SalesTransaction.order_id)).label("total_orders"), # distinct order count
        func.coalesce(func.sum(SalesTransaction.quantity), 0).label("units_sold") # total units count
    )
    # apply active filters
    query = apply_analytics_filters(query, start_date, end_date, region, category, payment_method)
    # fetch first row
    result = query.first()

    # cast financial numbers
    total_revenue = round(float(result.total_revenue), 2) # round total revenue
    total_profit = round(float(result.total_profit), 2) # round total profit
    total_orders = int(result.total_orders) # cast total orders
    units_sold = int(result.units_sold) # cast units sold

    # calculate average order
    aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0 # revenue per order
    # calculate profit margin
    profit_margin = round((total_profit / total_revenue) * 100, 2) if total_revenue > 0 else 0.0 # profit margin pct

    return {
        "total_revenue": total_revenue, # total revenue
        "total_profit": total_profit, # total profit
        "total_orders": total_orders, # order count
        "units_sold": units_sold, # quantity count
        "average_order_value": aov, # avg order val
        "profit_margin_pct": profit_margin # margin percent
    }


def get_sales_trend(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None
) -> List[Dict[str, Any]]:
    # select trend fields
    query = db.query(
        SalesTransaction.order_date.label("order_date"), # transaction date
        SalesTransaction.net_sales.label("net_sales"), # line net sales
        SalesTransaction.profit.label("profit"), # line profit
        SalesTransaction.quantity.label("quantity"), # line quantity
        SalesTransaction.order_id.label("order_id") # order identifier
    )
    # apply active filters
    query = apply_analytics_filters(query, start_date, end_date, region, category, payment_method)
    # execute database fetch
    rows = query.all()

    # aggregate by month
    monthly_data: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        month_key = r.order_date.strftime("%Y-%m") # format YYYY-MM
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "period": month_key, # period label
                "revenue": 0.0, # revenue accumulator
                "profit": 0.0, # profit accumulator
                "units_sold": 0, # units accumulator
                "orders": set() # unique orders
            }
        monthly_data[month_key]["revenue"] += r.net_sales # add revenue
        monthly_data[month_key]["profit"] += r.profit # add profit
        monthly_data[month_key]["units_sold"] += r.quantity # add units
        monthly_data[month_key]["orders"].add(r.order_id) # track order

    trend_list = []
    # format sorted periods
    for month_key in sorted(monthly_data.keys()):
        d = monthly_data[month_key] # month item
        trend_list.append({
            "period": d["period"], # period string
            "revenue": round(d["revenue"], 2), # rounded revenue
            "profit": round(d["profit"], 2), # rounded profit
            "units_sold": d["units_sold"], # units sum
            "orders_count": len(d["orders"]) # distinct orders
        })
    return trend_list # return trend points


def get_region_performance(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None
) -> List[Dict[str, Any]]:
    # group by region
    query = db.query(
        SalesTransaction.region.label("region"), # sales region
        func.coalesce(func.sum(SalesTransaction.net_sales), 0.0).label("revenue"), # region revenue
        func.coalesce(func.sum(SalesTransaction.profit), 0.0).label("profit"), # region profit
        func.count(distinct(SalesTransaction.order_id)).label("orders_count") # distinct orders
    ).group_by(SalesTransaction.region)
    # apply active filters
    query = apply_analytics_filters(query, start_date, end_date, region, category, payment_method)
    # sort highest revenue
    query = query.order_by(desc("revenue"))

    # fetch region list
    results = query.all()
    region_items = []
    for r in results:
        rev = round(float(r.revenue), 2) # revenue float
        prof = round(float(r.profit), 2) # profit float
        margin = round((prof / rev) * 100, 2) if rev > 0 else 0.0 # margin percent
        region_items.append({
            "region": r.region, # region label
            "revenue": rev, # revenue total
            "profit": prof, # profit total
            "orders_count": int(r.orders_count), # orders count
            "profit_margin_pct": margin # margin rate
        })
    return region_items # return regions


def get_category_performance(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None
) -> List[Dict[str, Any]]:
    # group by category
    query = db.query(
        SalesTransaction.category.label("category"), # product category
        func.coalesce(func.sum(SalesTransaction.net_sales), 0.0).label("revenue"), # category revenue
        func.coalesce(func.sum(SalesTransaction.profit), 0.0).label("profit"), # category profit
        func.coalesce(func.sum(SalesTransaction.quantity), 0).label("units_sold") # total quantity
    ).group_by(SalesTransaction.category)
    # apply active filters
    query = apply_analytics_filters(query, start_date, end_date, region, category, payment_method)
    # sort descending revenue
    query = query.order_by(desc("revenue"))

    # fetch category list
    results = query.all()
    # sum overall revenue
    total_rev = sum(float(r.revenue) for r in results)

    cat_items = []
    for r in results:
        rev = round(float(r.revenue), 2) # category revenue
        prof = round(float(r.profit), 2) # category profit
        share = round((rev / total_rev) * 100, 2) if total_rev > 0 else 0.0 # revenue share
        cat_items.append({
            "category": r.category, # category name
            "revenue": rev, # total revenue
            "profit": prof, # total profit
            "units_sold": int(r.units_sold), # total units
            "revenue_share_pct": share # share pct
        })
    return cat_items # return categories


def get_top_products(
    db: Session,
    limit: int = 10,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None
) -> List[Dict[str, Any]]:
    # query top products
    query = db.query(
        SalesTransaction.product.label("product"), # product name
        SalesTransaction.category.label("category"), # category name
        func.coalesce(func.sum(SalesTransaction.quantity), 0).label("units_sold"), # sold units
        func.coalesce(func.sum(SalesTransaction.net_sales), 0.0).label("revenue"), # product revenue
        func.coalesce(func.sum(SalesTransaction.profit), 0.0).label("profit") # product profit
    ).group_by(SalesTransaction.product, SalesTransaction.category)
    # apply active filters
    query = apply_analytics_filters(query, start_date, end_date, region, category, payment_method)
    # limit top rows
    query = query.order_by(desc("revenue")).limit(limit)

    # fetch top items
    results = query.all()
    top_items = []
    for r in results:
        rev = round(float(r.revenue), 2) # revenue amount
        prof = round(float(r.profit), 2) # profit amount
        margin = round((prof / rev) * 100, 2) if rev > 0 else 0.0 # margin percent
        top_items.append({
            "product": r.product, # product title
            "category": r.category, # category name
            "units_sold": int(r.units_sold), # total units
            "revenue": rev, # revenue value
            "profit": prof, # profit value
            "profit_margin_pct": margin # margin value
        })
    return top_items # return top items
