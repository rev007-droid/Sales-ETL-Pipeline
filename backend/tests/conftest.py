"""
conftest.py
-----------
Pytest fixtures for SalesPulse backend testing.
Uses an isolated in-memory SQLite database.
"""

# import standard os
import os
# import pytest module
import pytest
# import sqlalchemy engine
from sqlalchemy import create_engine
# import session maker
from sqlalchemy.orm import sessionmaker
# import static pool
from sqlalchemy.pool import StaticPool

# import settings instance
from backend.app.config import settings
# import database objects
from backend.app.database import Base, get_db
# import etl runner
from backend.app.services.etl_service import execute_etl_pipeline

# in-memory db uri
TEST_DATABASE_URL = "sqlite:///:memory:"

# create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}, # allow thread sharing
    poolclass=StaticPool # shared test memory
)
# create session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # build test tables
    Base.metadata.create_all(bind=test_engine)
    # open db session
    db = TestingSessionLocal()
    # path raw dataset
    raw_csv = settings.BASE_DIR / "data" / "raw" / "sales_data.csv"
    if raw_csv.exists():
        try:
            # seed initial records
            execute_etl_pipeline(db=db, file_path=str(raw_csv), job_name="Test-Seed-ETL")
        except Exception:
            pass # ignore seed error
    db.close() # close session clean
    yield
    # drop test tables
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    # open test session
    db = TestingSessionLocal()
    try:
        yield db # yield active session
    finally:
        db.close() # close session clean
