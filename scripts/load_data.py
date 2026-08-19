"""
Load the Northwind SQL dump into Postgres database `inventory_analytics`.
The dump is raw DDL+INSERT SQL (not a pandas-cleaned dataset) — Northwind's
schema is already relational and well-formed, so this project's real work is
in sql/analysis/, not in cleaning.

Usage: py -3.10 scripts/load_data.py
Requires DATABASE_URL in .env (see .env.example).
"""
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set. Copy .env.example to .env and fill in your password.")

ROOT = Path(__file__).parent.parent
DUMP_SQL = ROOT / "data" / "raw" / "northwind.sql"

if not DUMP_SQL.exists():
    raise SystemExit(
        f"{DUMP_SQL} not found. Download it first:\n"
        "  py -3.10 scripts/download_northwind.py"
    )


def ensure_database_exists(database_url: str) -> None:
    """CREATE DATABASE cannot run inside a transaction, and the target DB
    (inventory_analytics) doesn't exist on a fresh Postgres install — only
    the default `postgres` maintenance DB does. Connect there first, at
    AUTOCOMMIT isolation, and create the target DB if missing."""
    target_db = urlparse(database_url).path.lstrip("/")
    maintenance_url = database_url.rsplit("/", 1)[0] + "/postgres"

    engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": target_db},
        ).scalar()
        if not exists:
            print(f"Database '{target_db}' does not exist — creating it.")
            conn.execute(text(f'CREATE DATABASE "{target_db}"'))
        else:
            print(f"Database '{target_db}' already exists.")
    engine.dispose()


def main():
    ensure_database_exists(DATABASE_URL)
    engine = create_engine(DATABASE_URL)
    sql_text = DUMP_SQL.read_text(encoding="utf-8", errors="ignore")

    print("Loading Northwind dump (DROP + recreate all tables)...")
    with engine.begin() as conn:
        # The dump file is one big script with many statements separated by
        # blank-line-delimited blocks; psycopg2/sqlalchemy's raw connection
        # can execute the whole multi-statement script in one call via the
        # DBAPI cursor, which is simpler and safer than trying to split on
        # semicolons ourselves (COPY blocks and string literals can contain
        # semicolons, which would break naive splitting).
        raw_conn = conn.connection
        cursor = raw_conn.cursor()
        cursor.execute(sql_text)
        cursor.close()

    print("Load complete. Row counts:")
    with engine.connect() as conn:
        for tbl in ["orders", "order_details", "products", "suppliers", "categories"]:
            n = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            print(f"  {tbl}: {n} rows")


if __name__ == "__main__":
    main()
