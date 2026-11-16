-- =============================================================================
-- SalesPulse Database Schema (PostgreSQL & ANSI SQL Compatible)
-- =============================================================================

CREATE TABLE IF NOT EXISTS etl_jobs (
    id VARCHAR(36) PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    total_rows INTEGER DEFAULT 0,
    valid_rows INTEGER DEFAULT 0,
    rejected_rows INTEGER DEFAULT 0,
    duplicate_rows INTEGER DEFAULT 0,
    inserted_rows INTEGER DEFAULT 0,
    updated_rows INTEGER DEFAULT 0,
    skipped_rows INTEGER DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds NUMERIC(10, 2) DEFAULT 0.0,
    error_message TEXT,
    quality_score_pct NUMERIC(5, 2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_etl_jobs_status ON etl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_etl_jobs_created_at ON etl_jobs(created_at DESC);


CREATE TABLE IF NOT EXISTS etl_rejections (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(36) REFERENCES etl_jobs(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    order_id VARCHAR(100),
    product VARCHAR(255),
    rejection_reason TEXT NOT NULL,
    raw_data TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_etl_rejections_job_id ON etl_rejections(job_id);
CREATE INDEX IF NOT EXISTS idx_etl_rejections_order_id ON etl_rejections(order_id);


CREATE TABLE IF NOT EXISTS sales_transactions (
    id BIGSERIAL PRIMARY KEY,
    transaction_key VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    order_date DATE NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    customer_name VARCHAR(255),
    region VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    product VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    cost_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (cost_price >= 0),
    discount NUMERIC(5, 4) NOT NULL DEFAULT 0.0000 CHECK (discount >= 0.0000 AND discount <= 1.0000),
    gross_sales NUMERIC(12, 2) NOT NULL,
    discount_amount NUMERIC(12, 2) NOT NULL,
    net_sales NUMERIC(12, 2) NOT NULL,
    total_cost NUMERIC(12, 2) NOT NULL,
    profit NUMERIC(12, 2) NOT NULL,
    payment_method VARCHAR(100) NOT NULL,
    job_id VARCHAR(36) REFERENCES etl_jobs(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sales_order_date ON sales_transactions(order_date);
CREATE INDEX IF NOT EXISTS idx_sales_region ON sales_transactions(region);
CREATE INDEX IF NOT EXISTS idx_sales_category ON sales_transactions(category);
CREATE INDEX IF NOT EXISTS idx_sales_payment_method ON sales_transactions(payment_method);
CREATE INDEX IF NOT EXISTS idx_sales_order_id ON sales_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales_transactions(product);
