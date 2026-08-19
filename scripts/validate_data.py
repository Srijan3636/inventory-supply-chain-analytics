"""
Data-quality validation for the loaded Northwind database: referential
integrity, null checks, and range sanity checks. Northwind arrives as an
already-clean relational dump (see load_data.py) so there's no messy-text
cleaning to do — but "already clean" is a claim that should be verified,
not assumed. This is that verification.

Usage: py -3.10 scripts/validate_data.py
Requires DATABASE_URL in .env and the DB already loaded.
"""
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set.")

CHECKS = {
    "orphaned_order_details_product": """
        SELECT COUNT(*) FROM order_details od
        LEFT JOIN products p ON p.product_id = od.product_id
        WHERE p.product_id IS NULL
    """,
    "orphaned_order_details_order": """
        SELECT COUNT(*) FROM order_details od
        LEFT JOIN orders o ON o.order_id = od.order_id
        WHERE o.order_id IS NULL
    """,
    "orphaned_products_supplier": """
        SELECT COUNT(*) FROM products p
        LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id
        WHERE p.supplier_id IS NOT NULL AND s.supplier_id IS NULL
    """,
    "orphaned_products_category": """
        SELECT COUNT(*) FROM products p
        LEFT JOIN categories c ON c.category_id = p.category_id
        WHERE p.category_id IS NOT NULL AND c.category_id IS NULL
    """,
    "orders_with_shipped_before_order_date": """
        SELECT COUNT(*) FROM orders
        WHERE shipped_date IS NOT NULL AND shipped_date < order_date
    """,
    "orders_missing_required_date": """
        SELECT COUNT(*) FROM orders WHERE required_date IS NULL
    """,
    "order_details_negative_or_zero_quantity": """
        SELECT COUNT(*) FROM order_details WHERE quantity <= 0
    """,
    "order_details_negative_unit_price": """
        SELECT COUNT(*) FROM order_details WHERE unit_price < 0
    """,
    "products_negative_units_in_stock": """
        SELECT COUNT(*) FROM products WHERE units_in_stock < 0
    """,
    "products_null_units_in_stock": """
        SELECT COUNT(*) FROM products WHERE units_in_stock IS NULL
    """,
}


def main():
    engine = create_engine(DATABASE_URL)
    print("=== Data quality validation: inventory_analytics ===\n")

    failures = []
    with engine.connect() as conn:
        for name, sql in CHECKS.items():
            n = conn.execute(text(sql)).scalar()
            status = "OK" if n == 0 else f"FOUND {n}"
            print(f"  [{status:>8}] {name}")
            if n > 0:
                failures.append((name, n))

        order_date_range = conn.execute(
            text("SELECT MIN(order_date), MAX(order_date) FROM orders")
        ).fetchone()
        print(f"\n  order_date range: {order_date_range[0]} to {order_date_range[1]}")

        unshipped = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE shipped_date IS NULL")
        ).scalar()
        total = conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        print(f"  unshipped orders: {unshipped}/{total} "
              f"({100*unshipped/total:.1f}%) — excluded from lead-time and "
              f"fulfilment calculations, see supplier_lead_time.sql")

    print(f"\n{'PASSED' if not failures else 'ISSUES FOUND'}: "
          f"{len(CHECKS)-len(failures)}/{len(CHECKS)} checks clean")
    if failures:
        print("Non-zero checks:", failures)


if __name__ == "__main__":
    main()
