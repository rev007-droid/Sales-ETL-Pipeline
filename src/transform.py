"""
transform.py
------------
Core SalesPulse ETL Transformation Module.
Can be executed as a standalone CLI script or imported as a backend service.

Operations:
- Extracts CSV or Excel datasets
- Normalizes and validates column names
- Validates required fields, date formats, quantities, prices, and discounts
- Detects duplicate transactions using a stable transaction key
- Calculates derived financial metrics:
    GrossSales = Quantity * UnitPrice
    DiscountAmount = GrossSales * Discount
    NetSales = GrossSales - DiscountAmount
    TotalCost = Quantity * CostPrice
    Profit = NetSales - TotalCost
- Segregates valid and rejected records with detailed rejection reasons
- Generates an auditable Data Quality Summary JSON report
"""

import os
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np

# Canonical schema mapping
COLUMN_ALIASES = {
    "order_id": ["orderid", "order_id", "order id", "order no", "orderno"],
    "order_date": ["orderdate", "order_date", "order date", "date"],
    "customer_id": ["customerid", "customer_id", "customer id", "cust_id", "custid"],
    "customer_name": ["customername", "customer_name", "customer name", "client_name"],
    "region": ["region", "sales_region", "territory"],
    "category": ["category", "product_category", "productcategory"],
    "product": ["product", "product_name", "productname", "item_name", "item"],
    "quantity": ["quantity", "qty", "units", "quantity_sold"],
    "unit_price": ["unitprice", "unit_price", "unit price", "price"],
    "cost_price": ["costprice", "cost_price", "cost price", "unit_cost", "cost"],
    "discount": ["discount", "discount_rate", "discount_pct", "discount_percent"],
    "payment_method": ["paymentmethod", "payment_method", "payment method", "payment_type"]
}

REQUIRED_COLUMNS = ["order_id", "order_date", "customer_id", "product", "quantity", "unit_price"]


def normalize_column_name(col: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]", "_", str(col).strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")

    for canonical, aliases in COLUMN_ALIASES.items():
        clean_aliases = [re.sub(r"[^a-zA-Z0-9]", "_", a.strip().lower()).strip("_") for a in aliases]
        if cleaned in clean_aliases:
            return canonical
    return cleaned


def standardize_dataframe_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    rename_map = {col: normalize_column_name(col) for col in df.columns}
    standardized_df = df.rename(columns=rename_map)
    return standardized_df, rename_map


def generate_transaction_key(order_id: Any, product: Any) -> str:
    clean_ord = str(order_id).strip().upper()
    clean_prod = re.sub(r"[^a-zA-Z0-9]", "", str(product).strip().lower())
    return f"{clean_ord}_{clean_prod}"


def run_etl(
    input_source: Any,
    clean_output_path: Optional[str] = "data/processed/clean_sales.csv",
    rejected_output_path: Optional[str] = "data/processed/rejected_sales.csv",
    report_output_path: Optional[str] = "reports/data_quality_summary.json"
) -> Dict[str, Any]:
    """
    Executes the SalesPulse ETL pipeline.
    input_source: file path (str) or pandas DataFrame or file-like object.
    """
    # 1. Extraction
    if isinstance(input_source, pd.DataFrame):
        raw_df = input_source.copy()
    elif isinstance(input_source, str):
        if not os.path.exists(input_source):
            raise FileNotFoundError(f"Input file not found: {input_source}")
        if input_source.endswith(".xlsx") or input_source.endswith(".xls"):
            raw_df = pd.read_excel(input_source)
        else:
            raw_df = pd.read_csv(input_source)
    else:
        # File-like object (BytesIO or UploadFile)
        try:
            raw_df = pd.read_csv(input_source)
        except Exception:
            if hasattr(input_source, "seek"):
                input_source.seek(0)
            raw_df = pd.read_excel(input_source)

    total_extracted = len(raw_df)

    # 2. Schema normalization
    df, col_mapping = standardize_dataframe_columns(raw_df)

    # Check for required schema columns
    missing_required_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required_cols:
        raise ValueError(f"Dataset is missing mandatory columns: {missing_required_cols}")

    # Initialize tracking collections
    clean_records: List[Dict[str, Any]] = []
    rejected_records: List[Dict[str, Any]] = []
    seen_transaction_keys = set()
    rejection_reasons_counter: Dict[str, int] = {
        "missing_required_field": 0,
        "missing_price": 0,
        "invalid_date_format": 0,
        "invalid_quantity": 0,
        "invalid_discount": 0,
        "duplicate_transaction": 0
    }

    # Iterate through rows and validate
    for idx, row in df.iterrows():
        row_num = idx + 1  # 1-indexed for business reporting
        raw_row_dict = row.to_dict()

        order_id = row.get("order_id")
        customer_id = row.get("customer_id")
        order_date_raw = row.get("order_date")
        product = row.get("product")
        qty_raw = row.get("quantity")
        unit_price_raw = row.get("unit_price")

        # 1. Missing required field validation (order_id, customer_id, product)
        missing_fields = []
        if pd.isna(order_id) or str(order_id).strip() == "":
            missing_fields.append("order_id")
        if pd.isna(customer_id) or str(customer_id).strip() == "":
            missing_fields.append("customer_id")
        if pd.isna(product) or str(product).strip() == "":
            missing_fields.append("product")

        if missing_fields:
            reason = f"Missing required field(s): {', '.join(missing_fields)}"
            rejection_reasons_counter["missing_required_field"] += 1
            rejected_records.append({
                "row_number": row_num,
                "order_id": str(order_id) if not pd.isna(order_id) else "",
                "product": str(product) if not pd.isna(product) else "",
                "rejection_reason": reason,
                "raw_data": json.dumps(raw_row_dict, default=str)
            })
            continue

        # 2. Missing price validation
        if pd.isna(unit_price_raw) or str(unit_price_raw).strip() == "":
            reason = "Missing required price: unit_price cannot be null or empty"
            rejection_reasons_counter["missing_price"] += 1
            rejected_records.append({
                "row_number": row_num,
                "order_id": str(order_id),
                "product": str(product),
                "rejection_reason": reason,
                "raw_data": json.dumps(raw_row_dict, default=str)
            })
            continue

        # 3. Date parsing validation
        parsed_date = None
        if pd.isna(order_date_raw) or str(order_date_raw).strip() == "":
            reason = "Missing required field: order_date"
            rejection_reasons_counter["missing_required_field"] += 1
            rejected_records.append({
                "row_number": row_num,
                "order_id": str(order_id),
                "product": str(product),
                "rejection_reason": reason,
                "raw_data": json.dumps(raw_row_dict, default=str)
            })
            continue

        try:
            parsed_date_obj = pd.to_datetime(order_date_raw, errors="coerce")
            if pd.isna(parsed_date_obj) or parsed_date_obj.year < 2000 or parsed_date_obj.year > 2100:
                reason = f"Invalid date format or out of bounds: '{order_date_raw}'"
                rejection_reasons_counter["invalid_date_format"] += 1
                rejected_records.append({
                    "row_number": row_num,
                    "order_id": str(order_id),
                    "product": str(product),
                    "rejection_reason": reason,
                    "raw_data": json.dumps(raw_row_dict, default=str)
                })
                continue
            parsed_date = parsed_date_obj.strftime("%Y-%m-%d")
        except Exception as e:
            reason = f"Failed to parse date: '{order_date_raw}' ({str(e)})"
            rejection_reasons_counter["invalid_date_format"] += 1
            rejected_records.append({
                "row_number": row_num,
                "order_id": str(order_id),
                "product": str(product),
                "rejection_reason": reason,
                "raw_data": json.dumps(raw_row_dict, default=str)
            })
            continue

        # 4. Numeric validation: Quantity
        try:
            quantity = int(qty_raw)
            if quantity <= 0:
                raise ValueError("Quantity must be greater than 0")
        except Exception:
            reason = f"Invalid quantity: '{qty_raw}' must be an integer greater than 0"
            rejection_reasons_counter["invalid_quantity"] += 1
            rejected_records.append({
                "row_number": row_num,
                "order_id": str(order_id),
                "product": str(product),
                "rejection_reason": reason,
                "raw_data": json.dumps(raw_row_dict, default=str)
            })
            continue

        # 5. Numeric validation: Unit Price
        try:
            unit_price = float(unit_price_raw)
            if unit_price < 0 or np.isnan(unit_price):
                raise ValueError("Unit price must be non-negative")
        except Exception:
            reason = f"Invalid unit price: '{unit_price_raw}' must be a non-negative number"
            rejection_reasons_counter["missing_price"] += 1
            rejected_records.append({
                "row_number": row_num,
                "order_id": str(order_id),
                "product": str(product),
                "rejection_reason": reason,
                "raw_data": json.dumps(raw_row_dict, default=str)
            })
            continue

        # 6. Numeric validation: Cost Price
        cost_price_raw = row.get("cost_price", 0.0)
        try:
            cost_price = float(cost_price_raw) if not pd.isna(cost_price_raw) else 0.0
            if cost_price < 0:
                cost_price = 0.0
        except Exception:
            cost_price = 0.0

        # 7. Numeric validation: Discount
        discount_raw = row.get("discount", 0.0)
        try:
            discount = float(discount_raw) if not pd.isna(discount_raw) else 0.0
            if discount < 0.0 or discount > 1.0 or np.isnan(discount):
                reason = f"Invalid discount: '{discount_raw}' must be between 0.0 and 1.0"
                rejection_reasons_counter["invalid_discount"] += 1
                rejected_records.append({
                    "row_number": row_num,
                    "order_id": str(order_id),
                    "product": str(product),
                    "rejection_reason": reason,
                    "raw_data": json.dumps(raw_row_dict, default=str)
                })
                continue
        except Exception:
            reason = f"Invalid discount format: '{discount_raw}'"
            rejection_reasons_counter["invalid_discount"] += 1
            rejected_records.append({
                "row_number": row_num,
                "order_id": str(order_id),
                "product": str(product),
                "rejection_reason": reason,
                "raw_data": json.dumps(raw_row_dict, default=str)
            })
            continue

        # 8. Stable transaction key & Duplicate detection
        tx_key = generate_transaction_key(order_id, product)
        if tx_key in seen_transaction_keys:
            reason = f"Duplicate transaction detected: transaction key '{tx_key}' already processed"
            rejection_reasons_counter["duplicate_transaction"] += 1
            rejected_records.append({
                "row_number": row_num,
                "order_id": str(order_id),
                "product": str(product),
                "rejection_reason": reason,
                "raw_data": json.dumps(raw_row_dict, default=str)
            })
            continue
        seen_transaction_keys.add(tx_key)

        # 9. Financial Calculations
        gross_sales = round(quantity * unit_price, 2)
        discount_amount = round(gross_sales * discount, 2)
        net_sales = round(gross_sales - discount_amount, 2)
        total_cost = round(quantity * cost_price, 2)
        profit = round(net_sales - total_cost, 2)

        clean_record = {
            "transaction_key": tx_key,
            "order_id": str(order_id).strip(),
            "order_date": parsed_date,
            "customer_id": str(customer_id).strip(),
            "customer_name": str(row.get("customer_name", "Unknown")).strip() or "Unknown",
            "region": str(row.get("region", "Unassigned")).strip() or "Unassigned",
            "category": str(row.get("category", "Uncategorized")).strip() or "Uncategorized",
            "product": str(product).strip(),
            "quantity": quantity,
            "unit_price": round(unit_price, 2),
            "cost_price": round(cost_price, 2),
            "discount": round(discount, 4),
            "payment_method": str(row.get("payment_method", "Other")).strip() or "Other",
            "gross_sales": gross_sales,
            "discount_amount": discount_amount,
            "net_sales": net_sales,
            "total_cost": total_cost,
            "profit": profit
        }
        clean_records.append(clean_record)

    # 10. Create Clean & Rejected DataFrames
    clean_df = pd.DataFrame(clean_records)
    rejected_df = pd.DataFrame(rejected_records)

    accepted_count = len(clean_df)
    rejected_count = len(rejected_df)
    reconciliation_passed = (total_extracted == accepted_count + rejected_count)

    # Calculate financial aggregates for summary
    total_gross_sales = float(clean_df["gross_sales"].sum()) if not clean_df.empty else 0.0
    total_net_sales = float(clean_df["net_sales"].sum()) if not clean_df.empty else 0.0
    total_profit = float(clean_df["profit"].sum()) if not clean_df.empty else 0.0
    total_units_sold = int(clean_df["quantity"].sum()) if not clean_df.empty else 0
    distinct_orders = int(clean_df["order_id"].nunique()) if not clean_df.empty else 0
    profit_margin = round((total_profit / total_net_sales * 100), 2) if total_net_sales > 0 else 0.0
    avg_order_value = round((total_net_sales / distinct_orders), 2) if distinct_orders > 0 else 0.0

    summary_report = {
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_extracted_rows": total_extracted,
        "valid_rows_count": accepted_count,
        "rejected_rows_count": rejected_count,
        "reconciliation_passed": reconciliation_passed,
        "data_quality_score_pct": round((accepted_count / total_extracted * 100), 2) if total_extracted > 0 else 0.0,
        "rejection_breakdown": rejection_reasons_counter,
        "financial_aggregates": {
            "total_gross_sales": round(total_gross_sales, 2),
            "total_net_sales": round(total_net_sales, 2),
            "total_profit": round(total_profit, 2),
            "total_units_sold": total_units_sold,
            "distinct_orders": distinct_orders,
            "average_order_value": avg_order_value,
            "profit_margin_pct": profit_margin
        }
    }

    # 11. Persist artifacts if paths provided
    if clean_output_path:
        os.makedirs(os.path.dirname(clean_output_path), exist_ok=True)
        clean_df.to_csv(clean_output_path, index=False)

    if rejected_output_path:
        os.makedirs(os.path.dirname(rejected_output_path), exist_ok=True)
        rejected_df.to_csv(rejected_output_path, index=False)

    if report_output_path:
        os.makedirs(os.path.dirname(report_output_path), exist_ok=True)
        with open(report_output_path, "w", encoding="utf-8") as f:
            json.dump(summary_report, f, indent=2)

    return {
        "summary": summary_report,
        "clean_df": clean_df,
        "rejected_df": rejected_df
    }


if __name__ == "__main__":
    import sys
    src_file = "data/raw/sales_data.csv"
    if len(sys.argv) > 1:
        src_file = sys.argv[1]

    print(f"Running SalesPulse ETL Pipeline on '{src_file}'...")
    result = run_etl(src_file)
    sum_data = result["summary"]
    print(f"Extraction & Quality Summary:")
    print(f"  Total Extracted: {sum_data['total_extracted_rows']}")
    print(f"  Accepted Rows:   {sum_data['valid_rows_count']}")
    print(f"  Rejected Rows:   {sum_data['rejected_rows_count']}")
    print(f"  Reconciliation:  {'PASSED' if sum_data['reconciliation_passed'] else 'FAILED'}")
    print(f"  Quality Score:   {sum_data['data_quality_score_pct']}%")
    print(f"  Rejection breakdown: {sum_data['rejection_breakdown']}")
    print(f"  Clean data saved to: data/processed/clean_sales.csv")
    print(f"  Rejected data saved to: data/processed/rejected_sales.csv")
    print(f"  Audit report saved to: reports/data_quality_summary.json")
