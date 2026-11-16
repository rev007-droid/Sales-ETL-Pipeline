# SalesPulse — Technical Interview Guide & Two-Minute Pitch

## 1. Two-Minute Elevator Pitch

> "SalesPulse is a production-minded Sales Data ETL and Analytics platform engineered to solve a common enterprise bottleneck: messy, unvalidated transactional data entering business intelligence pipelines.
>
> In many organizations, dashboards fail or report misleading numbers because source CSVs or ERP exports contain corrupt dates, duplicate line items, negative quantities, or missing prices. SalesPulse addresses this with a resilient, decoupled architecture:
>
> 1. **Robust Python/Pandas Transformation Engine**: When raw datasets are ingested, SalesPulse normalizes diverse column aliases, strictly validates business rules, isolates corrupt records with explicit, auditable failure reasons, and synthesizes stable composite transaction keys `(OrderID + Product)` to prevent double-counting line items.
> 2. **Financial Precision**: Derived columns—Gross Sales, Discount Amount, Net Sales, Total Cost, and Profit—are calculated deterministically with proper fractional discount modeling and division-by-zero protection.
> 3. **High-Performance FastAPI & PostgreSQL Backend**: Provides ACID transaction safety, idempotent batch loading, and connection pooling. Re-running the pipeline on identical datasets safely skips existing records without corrupting primary keys or reporting false inserts.
> 4. **Enterprise React Dashboard**: Powered by Recharts and Lucide icons, business users can upload files, preview raw schemas, trigger pipeline runs, track job throughput, and filter KPIs dynamically across dates, sales regions, categories, and payment methods.
> 5. **Reconciliation & Auditing**: An auditable data quality report guarantees mathematical balance: `Extracted Rows (1,501) == Accepted Valid Rows (1,495) + Rejected Rows (6)`.
>
> The result is a verifiable, audit-proof sales intelligence platform ready for cloud deployment via Docker, PostgreSQL, and modern cloud hosts."

---

## 2. Technical Interview Questions & Answers

### Q1: Why did you choose composite transaction keys instead of relying solely on `OrderID` as unique?
**Answer:**
In real-world retail and B2B datasets, a single `OrderID` frequently contains multiple distinct line items or products (e.g., an order containing both a Laptop and a Mouse). Enforcing a unique constraint solely on `OrderID` would reject legitimate line items as duplicates. Conversely, having no unique constraint would permit duplicate submissions to double-count revenue. SalesPulse synthesizes a stable composite key `f"{order_id}_{slug(product)}"`, uniquely identifying each line item while strictly catching duplicate transactions.

### Q2: How does SalesPulse handle idempotency and transaction rollback?
**Answer:**
During batch loading in `backend/app/services/etl_service.py`, SalesPulse pre-queries existing transaction keys in the database. When an already processed dataset is re-run, duplicate keys are tracked in `skipped_rows` rather than triggering SQL constraint errors. Furthermore, all database operations are wrapped in an atomic SQLAlchemy session with rollback on failure. If any database exception occurs mid-batch, changes are rolled back, preserving database integrity, and the ETL job status is updated to `FAILED` with the exact error message recorded.

### Q3: How do you prevent division by zero in KPI calculations?
**Answer:**
KPIs such as Average Order Value (AOV) and Profit Margin are calculated as:
- $\text{AOV} = \frac{\text{Total Net Sales}}{\text{Distinct Orders}}$ (guarded: if $\text{Distinct Orders} = 0$, returns `0.00`).
- $\text{Profit Margin} = \frac{\text{Total Profit}}{\text{Total Net Sales}} \times 100$ (guarded: if $\text{Total Net Sales} = 0$, returns `0.00%`).
This guarantees that an empty database or heavily filtered query never throws `ZeroDivisionError` or returns `NaN`/`Infinity` to the frontend.

### Q4: Why isolate the ETL transformation logic into a standalone module (`src/transform.py`)?
**Answer:**
Decoupling the transformation logic from the web framework enables:
1. **Headless Execution**: Data engineers can run `python src/transform.py` from CLI or cron jobs without spinning up a web server.
2. **High Testability**: Core validation, data parsing, and financial math can be tested via pure unit tests (`pytest backend/tests/test_etl.py`) without HTTP mocks.
3. **Reusability**: The FastAPI `etl_service` imports `run_etl` directly, ensuring identical business logic regardless of whether the execution was triggered via CLI, background task, or web upload.

### Q5: How is security handled for file uploads?
**Answer:**
1. **Extension Whitelisting**: Strict validation allowing only `.csv`, `.xlsx`, and `.xls`.
2. **Size Enforcement**: Stream chunk counting with a hard 50MB ceiling (`HTTP 413 Entity Too Large`).
3. **Path Traversal Protection**: Uploaded files are assigned UUID-prefixed basenames and resolved strictly within the server's staging directory, preventing directory traversal (`../`).
4. **Error Masking**: In production mode (`ENVIRONMENT=production`), internal stack traces and database paths are hidden from API error responses.

### Q6: What was the reconciliation verification on the baseline dataset?
**Answer:**
The baseline dataset contains exactly 1,501 rows with 6 intentionally introduced anomalies:
1. Missing CustomerID (`missing_required_field`)
2. Missing UnitPrice (`missing_price`)
3. Invalid date format (`"2026-15-45"`)
4. Negative quantity (`-4`)
5. Invalid discount (`1.65`, > 1.0)
6. Duplicate record (exact duplicate of row #50)

Under our automated test suite (`backend/tests/test_reconciliation.py`), exactly 1,495 records are validated and accepted, and exactly 6 records are rejected, satisfying the balance condition:
$$\text{Total Extracted (1,501)} = \text{Clean Accepted (1,495)} + \text{Rejected (6)}$$
All 26 automated tests pass in under 4 seconds.
