"""
generate_sales_data.py
----------------------
Generates a realistic synthetic sales dataset for SalesPulse ETL pipeline testing.
Total rows: 1,501
12 source columns:
  OrderID, OrderDate, CustomerID, CustomerName, Region, Category, Product,
  Quantity, UnitPrice, CostPrice, Discount, PaymentMethod

Intentionally introduced anomalies (exactly 6 rejected rows):
  1. Missing required field (CustomerID is blank)
  2. Missing price (UnitPrice is blank/null)
  3. Invalid date ("2026-15-45")
  4. Invalid quantity (-4)
  5. Invalid discount (1.65, > 1.0)
  6. Duplicate record (duplicate of an existing row)
"""

import os
import random
from datetime import datetime, timedelta, timezone
import pandas as pd

def generate_dataset(output_path: str = "data/raw/sales_data.csv", seed: int = 42):
    random.seed(seed)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    regions = ["North", "South", "East", "West", "Central"]
    categories = {
        "Electronics": [
            ("Laptop Pro 15", 999.99, 650.00),
            ("Ultra HD Monitor 27\"", 349.99, 210.00),
            ("Wireless Mouse", 29.99, 12.50),
            ("Mechanical Keyboard", 89.99, 45.00),
            ("Noise-Cancelling Headphones", 199.99, 110.00),
            ("USB-C Multiport Dock", 69.99, 32.00),
            ("Smartwatch Series 5", 249.99, 150.00),
        ],
        "Furniture": [
            ("Ergonomic Mesh Chair", 279.99, 140.00),
            ("Standing Desk 55\"", 429.99, 230.00),
            ("Bookshelf 5-Tier", 119.99, 58.00),
            ("Filing Cabinet 3-Drawer", 149.99, 75.00),
            ("Desk Lamp LED", 39.99, 18.00),
        ],
        "Office Supplies": [
            ("Heavy-Duty Stapler", 19.99, 8.50),
            ("Ballpoint Pens (Pack of 50)", 14.99, 5.00),
            ("Printer Paper (5 Reams)", 44.99, 22.00),
            ("Expanding File Organizer", 16.99, 6.50),
            ("Dry Erase Board 36x24", 49.99, 24.00),
        ],
        "Apparel": [
            ("Corporate Polo Shirt", 34.99, 15.00),
            ("Lightweight Windbreaker", 59.99, 28.00),
            ("Canvas Laptop Backpack", 49.99, 21.00),
            ("Running Sneakers", 89.99, 42.00),
        ],
        "Home & Kitchen": [
            ("Stainless Steel Travel Mug", 24.99, 9.50),
            ("Compact Espresso Machine", 159.99, 90.00),
            ("Electric Kettle 1.7L", 39.99, 17.50),
            ("Air Purifier HEPA", 129.99, 65.00),
        ]
    }

    first_names = [
        "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Logan",
        "Sam", "Dakota", "Reese", "Quinn", "Cameron", "Skyler", "Peyton", "Hayden",
        "Jesse", "Kendall", "Harper", "Rowan", "Revanth", "Elena", "Liam", "Sophia",
        "Marcus", "Chloe", "Devon", "Aria", "Kai", "Zara"
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia",
        "Rodriguez", "Wilson", "Martinez", "Anderson", "Taylor", "Thomas", "Hernandez",
        "Moore", "Martin", "Jackson", "Thompson", "White", "Lopez", "Lee", "Gonzalez",
        "Harris", "Clark", "Lewis", "Robinson", "Walker", "Perez", "Hall"
    ]

    payment_methods = ["Credit Card", "PayPal", "Debit Card", "Bank Transfer"]
    discounts = [0.0, 0.0, 0.0, 0.05, 0.05, 0.10, 0.10, 0.15, 0.20]

    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 6, 30)
    day_span = (end_date - start_date).days

    rows = []
    # Generate exactly 1,495 valid records with guaranteed distinct order_id + product keys
    # To support multiple line items per order without collision, each order can have up to 3 distinct products
    current_order_num = 10001
    items_in_current_order = 0
    max_items_this_order = 2
    used_products_in_order = set()
    current_cust_num = 1001
    current_date = (start_date + timedelta(days=5)).strftime("%Y-%m-%d")
    current_region = "North"

    for i in range(1, 1496):
        if items_in_current_order >= max_items_this_order:
            current_order_num += 1
            items_in_current_order = 0
            max_items_this_order = random.choice([1, 2, 3])
            used_products_in_order.clear()
            current_cust_num = 1000 + (current_order_num % 300)
            rand_days = random.randint(0, day_span)
            current_date = (start_date + timedelta(days=rand_days)).strftime("%Y-%m-%d")
            current_region = random.choice(regions)

        order_id = f"ORD-{current_order_num}"
        cust_id = f"CUST-{current_cust_num}"
        fn = first_names[current_cust_num % len(first_names)]
        ln = last_names[(current_cust_num * 7) % len(last_names)]
        cust_name = f"{fn} {ln}"

        # Choose a product category and a product not yet in this order
        cat_choices = list(categories.keys())
        random.shuffle(cat_choices)
        chosen_cat = cat_choices[0]
        chosen_prod_tuple = None
        for cat in cat_choices:
            for item in categories[cat]:
                if item[0] not in used_products_in_order:
                    chosen_cat = cat
                    chosen_prod_tuple = item
                    break
            if chosen_prod_tuple:
                break

        product_name = chosen_prod_tuple[0]
        base_price = chosen_prod_tuple[1]
        cost_price = chosen_prod_tuple[2]
        used_products_in_order.add(product_name)
        items_in_current_order += 1

        quantity = random.randint(1, 10)
        discount = random.choice(discounts)
        payment = random.choice(payment_methods)

        rows.append({
            "OrderID": order_id,
            "OrderDate": current_date,
            "CustomerID": cust_id,
            "CustomerName": cust_name,
            "Region": current_region,
            "Category": chosen_cat,
            "Product": product_name,
            "Quantity": quantity,
            "UnitPrice": round(base_price, 2),
            "CostPrice": round(cost_price, 2),
            "Discount": discount,
            "PaymentMethod": payment
        })

    # Now inject exactly the 6 designated anomalous records:
    # 1. Missing required field (CustomerID is blank)
    rows.append({
        "OrderID": "ORD-99001",
        "OrderDate": "2025-05-12",
        "CustomerID": "",  # Missing CustomerID
        "CustomerName": "Ghost Customer",
        "Region": "North",
        "Category": "Electronics",
        "Product": "Wireless Mouse",
        "Quantity": 2,
        "UnitPrice": 29.99,
        "CostPrice": 12.50,
        "Discount": 0.0,
        "PaymentMethod": "Credit Card"
    })

    # 2. Missing price (UnitPrice is blank/null)
    rows.append({
        "OrderID": "ORD-99002",
        "OrderDate": "2025-06-18",
        "CustomerID": "CUST-1099",
        "CustomerName": "Taylor Swift",
        "Region": "East",
        "Category": "Furniture",
        "Product": "Desk Lamp LED",
        "Quantity": 1,
        "UnitPrice": None,  # Missing UnitPrice
        "CostPrice": 18.00,
        "Discount": 0.05,
        "PaymentMethod": "PayPal"
    })

    # 3. Invalid Date ("2026-15-45")
    rows.append({
        "OrderID": "ORD-99003",
        "OrderDate": "2026-15-45",  # Invalid Date
        "CustomerID": "CUST-1042",
        "CustomerName": "Marcus Davis",
        "Region": "West",
        "Category": "Office Supplies",
        "Product": "Printer Paper (5 Reams)",
        "Quantity": 3,
        "UnitPrice": 44.99,
        "CostPrice": 22.00,
        "Discount": 0.10,
        "PaymentMethod": "Debit Card"
    })

    # 4. Invalid Quantity (negative)
    rows.append({
        "OrderID": "ORD-99004",
        "OrderDate": "2025-09-22",
        "CustomerID": "CUST-1115",
        "CustomerName": "Elena Rostova",
        "Region": "South",
        "Category": "Apparel",
        "Product": "Corporate Polo Shirt",
        "Quantity": -4,  # Invalid quantity <= 0
        "UnitPrice": 34.99,
        "CostPrice": 15.00,
        "Discount": 0.0,
        "PaymentMethod": "Credit Card"
    })

    # 5. Invalid Discount (> 1.0)
    rows.append({
        "OrderID": "ORD-99005",
        "OrderDate": "2025-11-04",
        "CustomerID": "CUST-1201",
        "CustomerName": "Aria Stark",
        "Region": "Central",
        "Category": "Home & Kitchen",
        "Product": "Compact Espresso Machine",
        "Quantity": 1,
        "UnitPrice": 159.99,
        "CostPrice": 90.00,
        "Discount": 1.65,  # Invalid discount > 1.0
        "PaymentMethod": "Bank Transfer"
    })

    # 6. Duplicate record (exact duplicate of row index 50)
    dup_row = dict(rows[50])
    rows.append(dup_row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} rows into {output_path}")
    return df

if __name__ == "__main__":
    generate_dataset()
