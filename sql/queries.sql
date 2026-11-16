-- =============================================================================
-- SalesPulse Analytical SQL Queries
-- =============================================================================

-- 1. Executive Summary KPIs
SELECT
    COALESCE(SUM(net_sales), 0.00) AS total_revenue,
    COALESCE(SUM(profit), 0.00) AS total_profit,
    COUNT(DISTINCT order_id) AS total_orders,
    COALESCE(SUM(quantity), 0) AS units_sold,
    CASE 
        WHEN COUNT(DISTINCT order_id) > 0 THEN ROUND(SUM(net_sales) / COUNT(DISTINCT order_id), 2)
        ELSE 0.00 
    END AS average_order_value,
    CASE 
        WHEN SUM(net_sales) > 0 THEN ROUND((SUM(profit) / SUM(net_sales)) * 100, 2)
        ELSE 0.00 
    END AS profit_margin_pct
FROM sales_transactions;

-- 2. Sales & Profit Trend by Month
SELECT
    TO_CHAR(order_date, 'YYYY-MM') AS month,
    ROUND(SUM(net_sales), 2) AS revenue,
    ROUND(SUM(profit), 2) AS profit,
    SUM(quantity) AS units_sold,
    COUNT(DISTINCT order_id) AS order_count
FROM sales_transactions
GROUP BY TO_CHAR(order_date, 'YYYY-MM')
ORDER BY month ASC;

-- 3. Regional Performance Breakdown
SELECT
    region,
    ROUND(SUM(net_sales), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    COUNT(DISTINCT order_id) AS orders_count,
    ROUND(AVG(net_sales), 2) AS avg_transaction_value,
    CASE 
        WHEN SUM(net_sales) > 0 THEN ROUND((SUM(profit) / SUM(net_sales)) * 100, 2)
        ELSE 0.00 
    END AS profit_margin_pct
FROM sales_transactions
GROUP BY region
ORDER BY total_revenue DESC;

-- 4. Category Performance & Share
SELECT
    category,
    ROUND(SUM(net_sales), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(net_sales) * 100.0 / NULLIF((SELECT SUM(net_sales) FROM sales_transactions), 0), 2) AS revenue_share_pct
FROM sales_transactions
GROUP BY category
ORDER BY total_revenue DESC;

-- 5. Top 10 Best-Selling Products by Revenue
SELECT
    product,
    category,
    SUM(quantity) AS units_sold,
    ROUND(SUM(net_sales), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    CASE 
        WHEN SUM(net_sales) > 0 THEN ROUND((SUM(profit) / SUM(net_sales)) * 100, 2)
        ELSE 0.00 
    END AS profit_margin_pct
FROM sales_transactions
GROUP BY product, category
ORDER BY total_revenue DESC
LIMIT 10;

-- 6. Payment Method Distribution
SELECT
    payment_method,
    COUNT(*) AS transaction_count,
    ROUND(SUM(net_sales), 2) AS total_revenue,
    ROUND(AVG(net_sales), 2) AS avg_order_value
FROM sales_transactions
GROUP BY payment_method
ORDER BY total_revenue DESC;
