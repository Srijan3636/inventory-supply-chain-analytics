"""
Download the Northwind PostgreSQL sample database dump.

Source verified before use: github.com/pthom/northwind_psql — a commonly
referenced Postgres port of the classic Northwind sample database. No login
required.

Usage: py -3.10 scripts/download_northwind.py
"""
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql"
OUT_PATH = Path(__file__).parent.parent / "data" / "raw" / "northwind.sql"


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {URL} ...")
    urllib.request.urlretrieve(URL, OUT_PATH)
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"Saved {size_kb:.0f} KB -> {OUT_PATH}")


if __name__ == "__main__":
    main()
