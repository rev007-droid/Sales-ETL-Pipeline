"""
test_database.py
----------------
Tests for database transactions, idempotency, duplicate protection, and rollback on error.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models import SalesTransaction, ETLJob, ETLRejection
from backend.app.services.etl_service import execute_etl_pipeline


@pytest.fixture
def isolated_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_idempotent_loading(isolated_db):
    """
    Test that re-running the ETL on the same dataset does not duplicate sales transactions.
    """
    raw_path = "data/raw/sales_data.csv"
    res1 = execute_etl_pipeline(isolated_db, raw_path, job_name="Run-1")
    count1 = isolated_db.query(SalesTransaction).count()
    assert count1 == 1495
    assert res1["inserted_rows"] == 1495
    assert res1["skipped_rows"] == 0

    # Second run of same dataset
    res2 = execute_etl_pipeline(isolated_db, raw_path, job_name="Run-2")
    count2 = isolated_db.query(SalesTransaction).count()
    assert count2 == 1495  # No duplicate rows inserted into DB
    assert res2["inserted_rows"] == 0
    assert res2["skipped_rows"] == 1495


def test_transaction_rollback_on_failure(isolated_db, monkeypatch):
    """
    Test that if an unexpected exception occurs during loading, the transaction is rolled back
    and the ETL job is marked as FAILED.
    """
    import backend.app.services.etl_service as etl_mod

    # Intentionally cause a failure during saving
    def mock_bulk_save_objects(*args, **kwargs):
        raise RuntimeError("Database forced error during batch insert")

    monkeypatch.setattr(isolated_db, "bulk_save_objects", mock_bulk_save_objects)

    raw_path = "data/raw/sales_data.csv"
    with pytest.raises(RuntimeError):
        execute_etl_pipeline(isolated_db, raw_path, job_name="Failing-Run")

    failed_job = isolated_db.query(ETLJob).filter(ETLJob.status == "FAILED").first()
    assert failed_job is not None
    assert "Database forced error" in failed_job.error_message
