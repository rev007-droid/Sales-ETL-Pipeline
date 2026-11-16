"""
test_reconciliation.py
----------------------
Validates strict row-level and financial reconciliation across the ETL lifecycle.
"""

from src.transform import run_etl


def test_row_count_reconciliation():
    raw_path = "data/raw/sales_data.csv"
    result = run_etl(raw_path, clean_output_path=None, rejected_output_path=None, report_output_path=None)
    summary = result["summary"]

    extracted = summary["total_extracted_rows"]
    valid = summary["valid_rows_count"]
    rejected = summary["rejected_rows_count"]

    # Reconciliation rule: Extracted == Valid + Rejected
    assert extracted == valid + rejected
    assert summary["reconciliation_passed"] is True
    assert extracted == 1501
    assert valid == 1495
    assert rejected == 6


def test_rejection_reasons_audit():
    raw_path = "data/raw/sales_data.csv"
    result = run_etl(raw_path, clean_output_path=None, rejected_output_path=None, report_output_path=None)
    rejected_df = result["rejected_df"]

    assert len(rejected_df) == 6
    reasons = rejected_df["rejection_reason"].tolist()

    # Verify each expected rejection reason is detected
    assert any("Missing required field(s): customer_id" in r for r in reasons)
    assert any("Missing required price: unit_price" in r for r in reasons)
    assert any("Invalid date format" in r for r in reasons)
    assert any("Invalid quantity" in r for r in reasons)
    assert any("Invalid discount" in r for r in reasons)
    assert any("Duplicate transaction detected" in r for r in reasons)
