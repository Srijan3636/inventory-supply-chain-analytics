"""
Run every sql/analysis/*.sql file and write results to exports/*.csv,
plus dimension tables for the Power BI model.

Usage: py -3.10 scripts/export_data.py
Requires DATABASE_URL in .env and the DB already loaded (run load_data.py first).
"""
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set. Copy .env.example to .env and fill in your password.")

ROOT = Path(__file__).parent.parent
ANALYSIS_DIR = ROOT / "sql" / "analysis"
EXPORT_DIR = ROOT / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


def main():
    engine = create_engine(DATABASE_URL)

    sql_files = sorted(ANALYSIS_DIR.glob("*.sql"))
    print(f"Running {len(sql_files)} analysis queries...\n")

    for sql_file in sql_files:
        query = sql_file.read_text()
        try:
            df = pd.read_sql(text(query), engine)
        except Exception as e:
            print(f"  FAILED: {sql_file.name} -> {e}")
            continue

        out_path = EXPORT_DIR / f"{sql_file.stem}.csv"
        df.to_csv(out_path, index=False)
        print(f"  {sql_file.name}: {len(df)} rows -> {out_path.name}")

    # Dimension tables for the Power BI star schema
    with engine.connect() as conn:
        dim_product = pd.read_sql(
            "SELECT p.product_id, p.product_name, c.category_name, s.company_name AS supplier_name, "
            "p.unit_price, p.units_in_stock, p.reorder_level "
            "FROM products p "
            "JOIN categories c ON c.category_id = p.category_id "
            "JOIN suppliers s ON s.supplier_id = p.supplier_id", conn)
        dim_supplier = pd.read_sql(
            "SELECT supplier_id, company_name, country FROM suppliers", conn)

    dim_product.to_csv(EXPORT_DIR / "dim_product.csv", index=False)
    dim_supplier.to_csv(EXPORT_DIR / "dim_supplier.csv", index=False)
    print(f"\n  dim_product: {len(dim_product)} rows")
    print(f"  dim_supplier: {len(dim_supplier)} rows")

    print(f"\nAll exports written to {EXPORT_DIR}")


if __name__ == "__main__":
    main()
