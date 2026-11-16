"""
test_etl.py
-----------
Tests for SalesPulse ETL transformation logic, calculations, and data-quality rules.
"""

import pandas as pd
import pytest
from src.transform import run_etl, normalize_column_name, generate_transaction_key


def test_column_normalization():
    assert normalize_column_name("Order ID") == "order_id"
    assert normalize_column_name("Order_Date") == "order_date"
    assert normalize_column_name("Customer Name") == "customer_name"
    assert normalize_column_name("UnitPrice") == "unit_price"
    assert normalize_column_name("Unit_Cost") == "cost_price"
    assert normalize_column_name("Discount_Rate") == "discount"


def test_transaction_key_generation():
    key1 = generate_transaction_key("ORD-101", "Wireless Mouse")
    key2 = generate_transaction_key("ord-101", "wireless mouse")
    key3 = generate_transaction_key("ORD-101", "Laptop Pro 15")

    assert key1 == key2
    assert key1 != key3
    assert key1 == "ORD-101_wirelessmouse"


def test_etl_financial_calculations():
    # Construct a sample single-row DataFrame
    data = [{
        "OrderID": "ORD-TEST-1",
        "OrderDate": "2025-04-10",
        "CustomerID": "CUST-100",
        "CustomerName": "Test Customer",
        "Region": "North",
        "Category": "Electronics",
        "Product": "Mechanical Keyboard",
        "Quantity": 5,
        "UnitPrice": 100.00,
        "CostPrice": 60.00,
        "Discount": 0.10,  # 10%
        "PaymentMethod": "Credit Card"
    }]
    df = pd.DataFrame(data)

    result = run_etl(df, clean_output_path=None, rejected_output_path=None, report_output_path=None)
    clean_df = result["clean_df"]
    summary = result["summary"]

    assert len(clean_df) == 1
    assert summary["rejected_rows_count"] == 0

    row = clean_df.iloc[0]
    # GrossSales = 5 * 100 = 500.00
    assert row["gross_sales"] == 500.00
    # DiscountAmount = 500 * 0.10 = 50.00
    assert row["discount_amount"] == 50.00
    # NetSales = 500 - 50 = 450.00
    assert row["net_sales"] == 450.00
    # TotalCost = 5 * 60 = 300.00
    assert row["total_cost"] == 300.00
    # Profit = 450 - 300 = 150.00
    assert row["profit"] == 150.00


def test_etl_missing_required_fields():
    data = [
        # Missing CustomerID
        {
            "OrderID": "ORD-M1",
            "OrderDate": "2025-01-01",
            "CustomerID": "",
            "CustomerName": "No Customer",
            "Region": "North",
            "Category": "Electronics",
            "Product": "Mouse",
            "Quantity": 1,
            "UnitPrice": 20.00,
            "CostPrice": 10.00,
            "Discount": 0.0,
            "PaymentMethod": "Credit Card"
        },
        # Missing UnitPrice
        {
            "OrderID": "ORD-M2",
            "OrderDate": "2025-01-01",
            "CustomerID": "CUST-M2",
            "CustomerName": "No Price",
            "Region": "North",
            "Category": "Electronics",
            "Product": "Mouse",
            "Quantity": 1,
            "UnitPrice": None,
            "CostPrice": 10.00,
            "Discount": 0.0,
            "PaymentMethod": "Credit Card"
        }
    ]
    df = pd.DataFrame(data)
    result = run_etl(df, clean_output_path=None, rejected_output_path=None, report_output_path=None)

    assert result["summary"]["valid_rows_count"] == 0
    assert result["summary"]["rejected_rows_count"] == 2
    assert result["summary"]["rejection_breakdown"]["missing_required_field"] == 1
    assert result["summary"]["rejection_breakdown"]["missing_price"] == 1


def test_etl_invalid_date():
    data = [{
        "OrderID": "ORD-D1",
        "OrderDate": "2026-15-45",
        "CustomerID": "CUST-D1",
        "CustomerName": "Invalid Date",
        "Region": "South",
        "Category": "Furniture",
        "Product": "Chair",
        "Quantity": 1,
        "UnitPrice": 50.00,
        "CostPrice": 25.00,
        "Discount": 0.0,
        "PaymentMethod": "PayPal"
    }]
    df = pd.DataFrame(data)
    result = run_etl(df, clean_output_path=None, rejected_output_path=None, report_output_path=None)

    assert result["summary"]["valid_rows_count"] == 0
    assert result["summary"]["rejected_rows_count"] == 1
    assert result["summary"]["rejection_breakdown"]["invalid_date_format"] == 1


def test_etl_negative_quantity():
    data = [{
        "OrderID": "ORD-Q1",
        "OrderDate": "2025-05-01",
        "CustomerID": "CUST-Q1",
        "CustomerName": "Negative Qty",
        "Region": "West",
        "Category": "Apparel",
        "Product": "Shirt",
        "Quantity": -3,
        "UnitPrice": 30.00,
        "CostPrice": 12.00,
        "Discount": 0.0,
        "PaymentMethod": "Debit Card"
    }]
    df = pd.DataFrame(data)
    result = run_etl(df, clean_output_path=None, rejected_output_path=None, report_output_path=None)

    assert result["summary"]["valid_rows_count"] == 0
    assert result["summary"]["rejected_rows_count"] == 1
    assert result["summary"]["rejection_breakdown"]["invalid_quantity"] == 1


def test_etl_invalid_discount():
    data = [{
        "OrderID": "ORD-DISC1",
        "OrderDate": "2025-05-01",
        "CustomerID": "CUST-DISC1",
        "CustomerName": "Over 100% Discount",
        "Region": "Central",
        "Category": "Office Supplies",
        "Product": "Paper",
        "Quantity": 2,
        "UnitPrice": 40.00,
        "CostPrice": 20.00,
        "Discount": 1.50,  # 150% discount invalid
        "PaymentMethod": "Bank Transfer"
    }]
    df = pd.DataFrame(data)
    result = run_etl(df, clean_output_path=None, rejected_output_path=None, report_output_path=None)

    assert result["summary"]["valid_rows_count"] == 0
    assert result["summary"]["rejected_rows_count"] == 1
    assert result["summary"]["rejection_breakdown"]["invalid_discount"] == 1


def test_etl_duplicate_transaction():
    row = {
        "OrderID": "ORD-DUP1",
        "OrderDate": "2025-03-15",
        "CustomerID": "CUST-DUP1",
        "CustomerName": "Duplicate Tester",
        "Region": "North",
        "Category": "Electronics",
        "Product": "Smartwatch",
        "Quantity": 1,
        "UnitPrice": 200.00,
        "CostPrice": 120.00,
        "Discount": 0.05,
        "PaymentMethod": "Credit Card"
    }
    df = pd.DataFrame([row, dict(row)])
    result = run_etl(df, clean_output_path=None, rejected_output_path=None, report_output_path=None)

    assert result["summary"]["total_extracted_rows"] == 2
    assert result["summary"]["valid_rows_count"] == 1
    assert result["summary"]["rejected_rows_count"] == 1
    assert result["summary"]["rejection_breakdown"]["duplicate_transaction"] == 1


def test_baseline_raw_sales_dataset():
    """
    Validates that the generated raw CSV has exactly 1,501 rows,
    producing 1,495 valid records and 6 rejected records under the intended rules.
    """
    raw_path = "data/raw/sales_data.csv"
    result = run_etl(raw_path, clean_output_path=None, rejected_output_path=None, report_output_path=None)
    summary = result["summary"]

    assert summary["total_extracted_rows"] == 1501
    assert summary["valid_rows_count"] == 1495
    assert summary["rejected_rows_count"] == 6
    assert summary["reconciliation_passed"] is True
    assert summary["rejection_breakdown"]["missing_required_field"] == 1
    assert summary["rejection_breakdown"]["missing_price"] == 1
    assert summary["rejection_breakdown"]["invalid_date_format"] == 1
    assert summary["rejection_breakdown"]["invalid_quantity"] == 1
    assert summary["rejection_breakdown"]["invalid_discount"] == 1
    assert summary["rejection_breakdown"]["duplicate_transaction"] == 1
