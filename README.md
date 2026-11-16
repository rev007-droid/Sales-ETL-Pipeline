# SalesPulse — Sales Data ETL & Reporting Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB?logo=react)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4+-646CFF?logo=vite)](https://vitejs.dev/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?logo=sqlalchemy)](https://www.sqlalchemy.org/)
[![JWT & RBAC](https://img.shields.io/badge/Auth-JWT%20%7C%20RBAC-teal?logo=jsonwebtokens)](backend/app/routers/auth.py)
[![Tests](https://img.shields.io/badge/Tests-35%20Passed-success?logo=pytest)](backend/tests/)

**SalesPulse** is an enterprise-grade, full-stack Sales Data ETL and Analytics platform. It automates raw sales transaction ingestion (CSV/Excel), enforces strict data validation and deduplication rules, calculates derived financial KPIs, stores auditable records in PostgreSQL / SQLite, protects access with JWT authentication and Role-Based Access Control (RBAC), and visualizes metrics through a modern, responsive React/Vite analytics dashboard.

---

## 1. System Architecture

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React 18 + Vite)"]
        UI["SalesPulse UI (Recharts & Lucide)"]
        AuthModal["Auth Modal (Login/Register/Demo)"]
        ApiSvc["Centralized API Client (api.js)"]
    end

    subgraph API["FastAPI Backend Application"]
        Router["API Routers (/api/v1)"]
        AuthGuard["JWT & RBAC Guard (Admin/Analyst/Viewer)"]
        ETLService["ETL Ingestion Service"]
        AnalyticsService["Analytics & Aggregation Engine"]
        ExportService["Export Streaming Engine"]
        AuthService["Auth & Crypto Service"]
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
    AuthModal --> ApiSvc
    ApiSvc --> Router
    Router --> AuthGuard
    AuthGuard --> AuthService
    AuthGuard --> ETLService
    AuthGuard --> AnalyticsService
    AuthGuard --> ExportService

    ETLService --> CoreETL
    CoreETL --> Validator
    CoreETL --> Deduplicator
    CoreETL --> CalcEngine
    CoreETL --> DiskArtifacts

    AuthService --> Postgres
    AuthService --> SQLite
    ETLService --> Postgres
    ETLService --> SQLite
    AnalyticsService --> Postgres
    AnalyticsService --> SQLite
    ExportService --> Postgres
    ExportService --> SQLite
```

---

## 2. Core Features

### A. Authentication & Role-Based Access Control (RBAC)
- **User Registration & Login**: Validates unique emails and usernames with constant-time password verification.
- **Salted Password Hashing**: Cryptographic PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte random salts.
- **JWT Access Tokens**: Signed with `HS256`, 60-minute expiration, and unique `jti` identifier.
- **Refresh Token Rotation**: 7-day refresh tokens; requesting a new access token invalidates the old refresh token to prevent replay attacks.
- **Instant Logout & Revocation**: Blacklists the token's `jti` in a `revoked_tokens` table and invalidates active refresh tokens.
- **Role-Based Access Control (RBAC)**:
  - **`Admin`**: Full rights (execute ETL, upload data, manage users).
  - **`Analyst`**: Data ingestion, pipeline execution, sales analytics, and exports.
  - **`Viewer`**: Read-only analytics (blocked with `HTTP 403 Forbidden` if attempting file upload or pipeline execution).

### B. Automated ETL & Data Quality Pipeline
- **Dual Format Support**: Ingests both CSV and Excel (`.xlsx`, `.xls`) datasets up to 50MB.
- **Strict Validation Rules**:
  - Mandatory fields check (`OrderID`, `OrderDate`, `CustomerID`, `Product`, `Quantity`, `UnitPrice`).
  - Safe date parsing with out-of-bounds protection (`2000` to `2100`).
  - Numeric validation: integer quantities $> 0$, non-negative unit prices, fractional discounts $\in [0, 1.0]$.
  - Composite transaction deduplication (`OrderID + Product`), preventing line-item collisions.
- **Deterministic Financial Math**:
  - $\text{GrossSales} = \text{Quantity} \times \text{UnitPrice}$
  - $\text{DiscountAmount} = \text{GrossSales} \times \text{Discount}$
  - $\text{NetSales} = \text{GrossSales} - \text{DiscountAmount}$
  - $\text{TotalCost} = \text{Quantity} \times \text{CostPrice}$
  - $\text{Profit} = \text{NetSales} - \text{TotalCost}$
- **Mathematical Reconciliation**:
  $$\text{Total Extracted (1,501)} = \text{Clean Accepted (1,495)} + \text{Disqualified (6)} \implies \mathbf{PASSED}$$
- **Idempotent Loading & ACID Safety**: Re-running the pipeline skips previously loaded transactions without primary key conflicts. Exceptions automatically trigger transaction rollbacks and tag the job as `FAILED`.

### C. SaaS Analytics & Explorer UI
- **Executive Dashboard**: KPI metric cards (Revenue, Profit, Orders, Units Sold, AOV, Margin), monthly revenue & profit trajectory (Area Chart), regional breakdown (Bar Chart), category share (Donut Chart), and top 10 products table.
- **Multi-Dimensional Filters**: Filter all dashboard charts and metrics simultaneously by Date Range, Region, Category, and Payment Method.
- **Sales Explorer**: Searchable, sortable, and paginated data table with instant CSV and Excel exports.
- **Data Quality Audit**: Health score gauge, rejection reason distribution chart, and auditable row-level violation logs.

---

## 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite 5, Recharts, Lucide React, Modern CSS Variables |
| **Backend** | Python 3.11+ / 3.14, FastAPI, Pydantic v2, Uvicorn |
| **Security & Auth** | PyJWT (HS256), PBKDF2-HMAC-SHA256, HTTPBearer, RBAC |
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
│   │   ├── main.py               # FastAPI entry point & lifespan initialization
│   │   ├── config.py             # Typed environment settings & path resolution
│   │   ├── database.py           # Engine pooling & session management
│   │   ├── models.py             # Models: Users, RefreshTokens, RevokedTokens, Jobs, Sales
│   │   ├── schemas.py            # Pydantic v2 schemas for Auth, Analytics, Sales, and ETL
│   │   ├── dependencies.py       # JWT verification & RBAC role guards
│   │   ├── routers/              # Modular REST API endpoints
│   │   │   ├── auth.py           # Register, login, refresh, logout, profile (/api/auth/*)
│   │   │   ├── dashboard.py      # Summary KPIs, trend, regions, categories, top products
│   │   │   ├── sales.py          # Paginated, sortable sales explorer & preview
│   │   │   ├── upload.py         # File upload & schema inspection (Admin/Analyst)
│   │   │   ├── etl.py            # Pipeline execution & job history (Admin/Analyst)
│   │   │   ├── reports.py        # Data quality audit summary report
│   │   │   └── exports.py        # Clean & rejected CSV/Excel streaming downloads
│   │   └── services/             # Core business & persistence services
│   │       ├── auth_service.py   # Password hashing, JWT creation/decoding & revocation
│   │       ├── etl_service.py    # Batch load, idempotency & transaction rollback
│   │       ├── analytics_service.py # Filtered SQL aggregations & KPI computation
│   │       └── export_service.py # Streaming CSV/XLSX buffer generator
│   ├── tests/
│   │   ├── conftest.py           # Test fixtures & isolated in-memory test database
│   │   ├── test_auth.py          # Authentication, password hashing, JWT & RBAC tests
│   │   ├── test_etl.py           # Calculations & validation rules unit tests
│   │   ├── test_database.py      # Idempotent loading & rollback unit tests
│   │   ├── test_api.py           # Router endpoints integration tests
│   │   └── test_reconciliation.py# Row balance & audit trail verification
│   └── requirements.txt          # Python production dependencies
├── frontend/
│   ├── src/
│   │   ├── components/           # Sidebar, Navbar, MetricCard, FilterBar, StatusBadge, AuthModal
│   │   ├── layouts/              # MainLayout container
│   │   ├── pages/                # DashboardPage, UploadPage, MonitoringPage, Explorer, Quality
│   │   ├── services/             # api.js centralized REST client with JWT interceptor
│   │   ├── utils/                # formatters.js (currency, dates, numbers, bytes)
│   │   ├── App.jsx               # Application root
│   │   ├── main.jsx              # DOM entrypoint
│   │   └── index.css             # Enterprise dark navy & teal design system
│   ├── package.json              # Node dependencies (React, Recharts, Lucide)
│   ├── vite.config.js            # Vite build configuration & proxy
│   └── vercel.json               # SPA routing rewrite rules
├── src/
│   ├── generate_sales_data.py    # Synthetic raw generator (1,501 rows with 6 anomalies)
│   └── transform.py              # Standalone reusable ETL transformation script
├── data/
│   ├── raw/                      # sales_data.csv (baseline raw dataset)
│   ├── processed/                # clean_sales.csv, rejected_sales.csv
│   └── uploads/                  # Safe temporary file upload staging
├── sql/
│   ├── schema.sql                # PostgreSQL DDL script with indexes & constraints
│   └── queries.sql               # Analytical SQL queries reference
├── reports/
│   └── data_quality_summary.json # Auditable quality summary report
├── docs/
│   └── INTERVIEW_AND_PITCH.md    # 2-minute elevator pitch & technical interview Q&A
├── Dockerfile.backend            # Container build for FastAPI
├── Dockerfile.frontend           # Multi-stage container build for React/Nginx
├── docker-compose.yml            # Production stack orchestration (Postgres, API, Web)
├── render.yaml                   # Render cloud deployment blueprint
├── .env.example                  # Environment variable template
├── .gitignore                    # Git exclusions
└── README.md                     # Project documentation
```

---

## 5. Local Setup & Quickstart (Windows 10/11)

### Prerequisites
- Python 3.11+ (Python 3.14 compatible)
- Node.js v18+ & npm
- Git

### Step 1: Clone Repository
```powershell
# clone project repository
git clone https://github.com/rev007-droid/Sales-ETL-Pipeline.git
# navigate into directory
cd Sales-ETL-Pipeline
```

### Step 2: Set Up Environment & Baseline Data
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

### Step 3: Run Automated Test Suite
```powershell
# execute all 35 unit and integration tests
python -m pytest backend/tests -v
```
*Expected result: 35 passed in ~4.1 seconds.*

### Step 4: Start Backend API Server
```powershell
# run via python module (recommended on windows)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Root: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### Step 5: Start Frontend Development Server
In a separate terminal:
```powershell
# navigate to frontend
cd frontend

# install frontend dependencies (if not already installed)
npm.cmd install

# launch vite dev server
npm.cmd run dev
```
Open your browser at: **[http://localhost:5173/](http://localhost:5173/)**

---

## 6. Pre-Seeded Demo Accounts

The application automatically seeds three demo accounts for instant evaluation:

| Role | Username | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full access (Upload files, Run ETL, User control) |
| **Analyst** | `analyst` | `analyst123` | Upload datasets, Run ETL, Explore & Export |
| **Viewer** | `viewer` | `viewer123` | Read-only analytics (blocked from running ETL) |

---

## 7. Data Quality & Reconciliation Audit

The generated raw dataset (`data/raw/sales_data.csv`) contains exactly **1,501 rows** and **12 columns**. Under SalesPulse's transformation rules:

| Row Number | Detected Value | Failure Reason | Pipeline Action |
| :--- | :--- | :--- | :--- |
| **Row 1496** | `CustomerID = ""` | Missing required identifier | Disqualified: `missing_required_field` |
| **Row 1497** | `UnitPrice = null` | Missing price | Disqualified: `missing_price` |
| **Row 1498** | `OrderDate = "2026-15-45"` | Out-of-bounds date | Disqualified: `invalid_date_format` |
| **Row 1499** | `Quantity = -4` | Negative integer sold | Disqualified: `invalid_quantity` |
| **Row 1500** | `Discount = 1.65` | Discount rate $> 1.0$ (165%) | Disqualified: `invalid_discount` |
| **Row 1501** | Duplicate of row 50 | Repeated composite key | Disqualified: `duplicate_transaction` |

### Reconciliation Mathematical Balance:
$$\text{Total Extracted Records} = 1,501$$
$$\text{Clean Accepted Records} = 1,495$$
$$\text{Disqualified Records} = 6$$
$$\text{Reconciliation Check: } 1,501 = 1,495 + 6 \implies \mathbf{PASSED}$$

---

## 8. Running with Docker Compose (PostgreSQL Production Stack)

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

## 9. Cloud Deployment Guide

### A. Deploy Database (Neon / Supabase / Render PostgreSQL)
1. Provision a PostgreSQL 15+ database instance.
2. Execute `sql/schema.sql` via the provider's SQL editor or let SQLAlchemy automatically create tables upon startup.
3. Obtain your connection URI: `postgresql+psycopg2://user:password@host:port/dbname`.

### B. Deploy Backend (Render / Railway / Fly.io)
1. Link your GitHub repository.
2. Build command: `pip install -r backend/requirements.txt`
3. Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables:
   - `DATABASE_URL`: Hosted PostgreSQL connection string.
   - `ENVIRONMENT`: `production`
   - `JWT_SECRET_KEY`: A strong 64-character secret.
   - `CORS_ORIGINS`: `https://your-frontend-app.vercel.app`

### C. Deploy Frontend (Vercel / Netlify)
1. Import repository and set root directory to `frontend`.
2. Framework preset: `Vite`.
3. Build command: `npm run build`
4. Output directory: `dist`
5. Set environment variable:
   - `VITE_API_BASE_URL`: `https://your-backend-api.onrender.com/api`
6. Deploy!

---

## 10. Interview Guide & Technical Deep-Dive

For a 2-minute elevator pitch and technical interview questions regarding composite key selection, ACID transaction rollback, division-by-zero protection, and performance considerations, please review:
👉 **[`docs/INTERVIEW_AND_PITCH.md`](docs/INTERVIEW_AND_PITCH.md)**

---

## 11. License

This project is licensed under the MIT License — free for educational, portfolio, and commercial use.
