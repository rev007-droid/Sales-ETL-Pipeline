# SalesPulse — Sales Data ETL & Reporting Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB?logo=react)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4+-646CFF?logo=vite)](https://vitejs.dev/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?logo=sqlalchemy)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/Tests-26%20Passed-success?logo=pytest)](backend/tests/)

SalesPulse is a production-grade, full-stack Sales ETL and Analytics web application. It automates raw sales transaction ingestion (CSV/Excel), enforces strict business validation and deduplication rules, calculates derived financial metrics, stores auditable records in PostgreSQL / SQLite, and visualizes KPIs through a modern, responsive enterprise analytics dashboard.

---

## 1. System Architecture

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React + Vite)"]
        UI["SalesPulse UI (Recharts & Lucide)"]
        ApiSvc["Centralized API Client (api.js)"]
    end

    subgraph API["FastAPI Backend Application"]
        Router["API Routers (/api/v1)"]
        AuthMiddleware["CORS & Upload Validation Guard"]
        ETLService["ETL Ingestion Service"]
        AnalyticsService["Analytics & Aggregation Engine"]
        ExportService["Export Streaming Engine"]
    end

    subgraph Processing["Data Pipeline & Transformation"]
        CoreETL["src/transform.py Engine"]
        Validator["Schema & Constraint Validator"]
        CalcEngine["Financial Calculations Engine"]
        Deduplicator["Composite Key Deduplicator"]
    end

    subgraph Persistence["Database & Storage"]
        Postgres[("PostgreSQL Database (Prod)")]
        SQLite[("SQLite Engine (Dev/Demo)")]
        DiskArtifacts[("CSV & JSON Audit Reports")]
    end

    UI --> ApiSvc
    ApiSvc --> Router
    Router --> AuthMiddleware
    AuthMiddleware --> ETLService
    AuthMiddleware --> AnalyticsService
    AuthMiddleware --> ExportService

    ETLService --> CoreETL
    CoreETL --> Validator
    CoreETL --> Deduplicator
    CoreETL --> CalcEngine
    CoreETL --> DiskArtifacts

    ETLService --> Postgres
    ETLService --> SQLite
    AnalyticsService --> Postgres
    AnalyticsService --> SQLite
    ExportService --> Postgres
    ExportService --> SQLite
```

---

## 2. Core Features

- **Automated Data Ingestion**: Drag-and-drop or upload CSV and Excel datasets up to 50MB with instant column detection and first-10-row preview.
- **Strict Data Quality Validation**:
  - Validates mandatory fields (`OrderID`, `OrderDate`, `CustomerID`, `Product`, `Quantity`, `UnitPrice`).
  - Safe date parsing with boundary validation.
  - Numeric integrity: integer quantities $> 0$, non-negative unit prices, fractional discounts $\in [0, 1.0]$.
  - Composite transaction deduplication (`OrderID + Product`) avoiding line-item collisions.
- **Deterministic Financial Math**:
  - $\text{GrossSales} = \text{Quantity} \times \text{UnitPrice}$
  - $\text{DiscountAmount} = \text{GrossSales} \times \text{Discount}$
  - $\text{NetSales} = \text{GrossSales} - \text{DiscountAmount}$
  - $\text{TotalCost} = \text{Quantity} \times \text{CostPrice}$
  - $\text{Profit} = \text{NetSales} - \text{TotalCost}$
- **Mathematical Reconciliation**:
  $$\text{Total Extracted (1,501)} = \text{Accepted Clean (1,495)} + \text{Rejected (6)}$$
  Row reconciliation is automatically verified, balanced, and stored in auditable JSON and database records.
- **Idempotent Loading & ACID Safety**: Re-running identical datasets skips previously loaded transactions without primary key conflicts. Database failures automatically rollback transactions and tag the job as `FAILED`.
- **Interactive SaaS Analytics**:
  - Dynamic KPI cards (Revenue, Profit, Orders, Units Sold, Average Order Value, Profit Margin).
  - Monthly revenue & profit trajectory (Area Chart).
  - Regional comparison (Bar Chart).
  - Category revenue share (Donut Chart).
  - Top 10 best-selling products table.
  - Multi-dimensional filters (Date range, Region, Category, Payment method).
- **Sales Explorer**: Paginated, sortable, and searchable table with instant CSV / Excel exports.
- **Data Quality Audit**: Visual breakdown of rejection categories and downloadable audit log.

---

## 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite 5, Recharts, Lucide React, Modern CSS Variables |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| **Data Processing** | Pandas 2+, NumPy, OpenPyXL |
| **ORM & Database** | SQLAlchemy 2+, PostgreSQL 16 (production), SQLite (local demo) |
| **Testing** | Pytest 9+, FastAPI TestClient, In-memory SQLite |
| **DevOps & Cloud** | Docker, Docker Compose, Nginx, Render, Vercel |

---

## 4. Project Monorepo Structure

```text
Sales-ETL-Pipeline/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI application entry point & lifespan
│   │   ├── config.py             # Typed environment settings & path resolution
│   │   ├── database.py           # Engine pooling & session dependencies
│   │   ├── models.py             # SQLAlchemy models (Jobs, Rejections, Sales)
│   │   ├── schemas.py            # Pydantic v2 request/response schemas
│   │   ├── dependencies.py       # Reusable session dependencies
│   │   ├── routers/              # Modular API endpoints
│   │   │   ├── health.py         # /api/health
│   │   │   ├── dashboard.py      # /api/dashboard/* (summary, trend, regions, categories, top products)
│   │   │   ├── sales.py          # /api/sales, /api/sales/preview
│   │   │   ├── upload.py         # /api/upload (schema check & safe staging)
│   │   │   ├── etl.py            # /api/etl/* (run, jobs, detail, results)
│   │   │   ├── reports.py        # /api/reports/data-quality
│   │   │   └── exports.py        # /api/exports/* (clean & rejected CSV/Excel)
│   │   └── services/             # Core business & database services
│   │       ├── etl_service.py    # Batch load, idempotency & transaction rollback
│   │       ├── analytics_service.py # Filtered SQL aggregations & KPI computation
│   │       └── export_service.py # Dynamic CSV/XLSX buffer generator
│   ├── tests/
│   │   ├── conftest.py           # Test fixtures & isolated in-memory DB
│   │   ├── test_etl.py           # Calculations & validation rules unit tests
│   │   ├── test_database.py      # Idempotent loading & rollback unit tests
│   │   ├── test_api.py           # Router endpoints integration tests
│   │   └── test_reconciliation.py# Row balance & audit trail verification
│   └── requirements.txt          # Python production dependencies
├── frontend/
│   ├── src/
│   │   ├── components/           # Sidebar, Navbar, MetricCard, FilterBar, StatusBadge
│   │   ├── layouts/              # MainLayout wrapper
│   │   ├── pages/                # DashboardPage, UploadPage, MonitoringPage, Explorer, Quality
│   │   ├── services/             # api.js centralized REST client
│   │   ├── utils/                # formatters.js (currency, dates, numbers, bytes)
│   │   ├── App.jsx               # Application root
│   │   ├── main.jsx              # DOM entrypoint
│   │   └── index.css             # Enterprise navy/teal design system
│   ├── package.json              # Node dependencies
│   ├── vite.config.js            # Vite configuration & proxy
│   └── vercel.json               # SPA routing rewrite rule
├── src/
│   ├── generate_sales_data.py    # Synthetic raw generator (1,501 rows with 6 anomalies)
│   └── transform.py              # Standalone reusable ETL transformation script
├── data/
│   ├── raw/                      # sales_data.csv (original source data)
│   ├── processed/                # clean_sales.csv, rejected_sales.csv
│   └── uploads/                  # Safe staging directory for user uploads
├── sql/
│   ├── schema.sql                # PostgreSQL DDL script with indexes & constraints
│   └── queries.sql               # Analytical SQL queries reference
├── reports/
│   └── data_quality_summary.json # Auditable quality summary report
├── docs/
│   └── INTERVIEW_AND_PITCH.md    # 2-minute elevator pitch & technical interview Q&A
├── Dockerfile.backend            # Container build for FastAPI
├── Dockerfile.frontend           # Multi-stage container build for React/Nginx
├── docker-compose.yml            # Multi-container orchestration (DB, API, Web)
├── render.yaml                   # Cloud deployment blueprint
├── .env.example                  # Environment variable template
├── .gitignore                    # Git exclusions
└── README.md                     # Complete project documentation
```

---

## 5. Local Setup & Installation (Windows 10/11)

### Prerequisites
- Python 3.11+ (Python 3.14 compatible)
- Node.js v18+ (Node v24 tested) & npm
- Git

### Step 1: Clone Repository & Open Folder
```powershell
# clone project repository
git clone https://github.com/revanth/SalesPulse.git
# navigate into directory
cd SalesPulse
```

### Step 2: Set Up Backend
```powershell
# copy environment settings
Copy-Item .env.example .env

# generate synthetic sales dataset (1,501 rows with 6 anomalies)
python src/generate_sales_data.py

# execute core transformation to produce baseline clean/rejected data
python src/transform.py

# install dependencies if in virtual environment
pip install -r backend/requirements.txt
```

### Step 3: Run Automated Tests
```powershell
# execute all 26 automated unit and integration tests
python -m pytest backend/tests -v
```
*Expected result: 26 passed in ~3.8 seconds.*

### Step 4: Start Backend API Server
```powershell
# launch uvicorn development server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Root: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- API Health Probe: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### Step 5: Start Frontend Application
In a separate terminal:
```powershell
# navigate to frontend
cd frontend

# install frontend dependencies (if not already installed)
npm install

# launch vite dev server
npm run dev
```
Open your browser at: **[http://localhost:5173/](http://localhost:5173/)**

---

## 6. Running with Docker Compose (PostgreSQL Production Stack)

To run the complete production stack (PostgreSQL + FastAPI + React/Nginx) with a single command:

```powershell
# build and start all containers
docker-compose up --build -d

# view running services
docker-compose ps

# stop containers
docker-compose down
```
- Web Application: [http://localhost:80](http://localhost:80)
- Backend API: [http://localhost:8000](http://localhost:8000)
- PostgreSQL Port: `5432`

---

## 7. Data Quality & Reconciliation Audit

The generated raw dataset (`data/raw/sales_data.csv`) contains exactly **1,501 rows** and **12 columns**. Under SalesPulse's transformation rules:

| Category | Input Value | Detected Anomaly | Pipeline Decision |
| :--- | :--- | :--- | :--- |
| **Row 1496** | `CustomerID = ""` | Missing required identifier | Disqualified: `missing_required_field` |
| **Row 1497** | `UnitPrice = null` | Missing price | Disqualified: `missing_price` |
| **Row 1498** | `OrderDate = "2026-15-45"` | Out-of-bounds month/day | Disqualified: `invalid_date_format` |
| **Row 1499** | `Quantity = -4` | Negative integer sold | Disqualified: `invalid_quantity` |
| **Row 1500** | `Discount = 1.65` | Discount rate $> 1.0$ (165%) | Disqualified: `invalid_discount` |
| **Row 1501** | Duplicate of row 50 | Repeated composite key | Disqualified: `duplicate_transaction` |

### Reconciliation Mathematical Proof:
$$\text{Total Extracted Records} = 1,501$$
$$\text{Clean Accepted Records} = 1,495$$
$$\text{Rejected Records} = 6$$
$$\text{Reconciliation Check: } 1,501 = 1,495 + 6 \implies \mathbf{PASSED}$$

---

## 8. Cloud Deployment Guide

### A. Deploy Database (Neon / Supabase / Render PostgreSQL)
1. Provision a PostgreSQL 15+ database.
2. Execute `sql/schema.sql` via the provider's SQL editor or let SQLAlchemy automatically create tables upon startup.
3. Obtain the connection string: `postgresql+psycopg2://user:password@host:port/dbname`.

### B. Deploy Backend (Render / Railway / Fly.io)
1. Link your GitHub repository.
2. Set root directory: `./`
3. Environment: `Python 3`
4. Build command: `pip install -r backend/requirements.txt`
5. Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables:
   - `DATABASE_URL`: Your hosted PostgreSQL connection string.
   - `ENVIRONMENT`: `production`
   - `CORS_ORIGINS`: `https://your-frontend-app.vercel.app`

### C. Deploy Frontend (Vercel / Netlify)
1. Import repository and set root directory to `frontend`.
2. Framework preset: `Vite`.
3. Build command: `npm run build`
4. Output directory: `dist`
5. Add environment variable:
   - `VITE_API_BASE_URL`: `https://your-backend-api.onrender.com/api`
6. Deploy!

---

## 9. Interview Guide & Technical Deep-Dive

For a 2-minute elevator pitch and technical interview questions regarding composite key selection, ACID transaction rollback, division-by-zero protection, and performance considerations, please review:
👉 **[`docs/INTERVIEW_AND_PITCH.md`](docs/INTERVIEW_AND_PITCH.md)**

---

## 10. Known Limitations & Future Improvements

### Limitations
- File upload staging uses local disk storage (`data/uploads/`). In a multi-instance container cluster, a shared object store (AWS S3 or Google Cloud Storage) should be utilized.
- Background asynchronous tasks use FastAPI's built-in `BackgroundTasks`. For workloads exceeding 500,000 rows, a distributed queue like Celery or Redis RQ is recommended.

### Planned Enhancements
- Multi-tenant role-based access control (RBAC).
- Webhook notifications for completed or failed ETL pipeline runs.
- Machine-learning anomaly detection for unusual discount-to-profit ratios.
- Automated Parquet data lake exports for Apache Iceberg / Snowflake querying.

---

## 11. License

This project is licensed under the MIT License — free for educational, portfolio, and commercial use.
