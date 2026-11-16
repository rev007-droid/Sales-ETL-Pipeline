"""
config.py
---------
SalesPulse backend configuration settings.
Loads from environment variables with safe defaults.
"""

# import standard os
import os
# import type hint
from typing import List
# import filesystem path
from pathlib import Path

# define base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# define data directory
DATA_DIR = BASE_DIR / "data"
# define upload directory
UPLOAD_DIR = DATA_DIR / "uploads"
# define processed directory
PROCESSED_DIR = DATA_DIR / "processed"
# define reports directory
REPORTS_DIR = BASE_DIR / "reports"
# define logs directory
LOGS_DIR = BASE_DIR / "logs"

# create required folders
for directory in [DATA_DIR, UPLOAD_DIR, PROCESSED_DIR, REPORTS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True) # create folder safe


class Settings:
    # app project name
    PROJECT_NAME: str = "SalesPulse — Sales Data ETL & Reporting Platform"
    # app api version
    VERSION: str = "1.0.0"
    # base api route
    API_PREFIX: str = "/api"
    # runtime environment flag
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    # project root path
    BASE_DIR: Path = BASE_DIR

    # database connection url
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'data' / 'salespulse.db'}"
    )

    # raw cors string
    _raw_cors = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    )
    # parsed cors list
    CORS_ORIGINS: List[str] = [origin.strip() for origin in _raw_cors.split(",") if origin.strip()]

    # upload size limit
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 megabytes
    # allowed file types
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]

    # folder upload target
    UPLOAD_FOLDER: Path = UPLOAD_DIR
    # clean csv path
    CLEAN_DATA_FILE: Path = PROCESSED_DIR / "clean_sales.csv"
    # rejected csv path
    REJECTED_DATA_FILE: Path = PROCESSED_DIR / "rejected_sales.csv"
    # json summary path
    DATA_QUALITY_REPORT_FILE: Path = REPORTS_DIR / "data_quality_summary.json"


# export settings instance
settings = Settings()
