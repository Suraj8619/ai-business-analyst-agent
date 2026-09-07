"""
Loads the sales CSV into a local SQLite database.
Run this once before starting the app: python db_setup.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

CSV_PATH = Path("data/sales_data.csv")
DB_PATH = Path("business.db")


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"{CSV_PATH} not found. Run `python data/generate_sample_data.py` first, "
            "or replace it with your own CSV at that path."
        )

    df = pd.read_csv(CSV_PATH, parse_dates=["order_date"])

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("sales", conn, if_exists="replace", index=False)

    # Sanity check: print schema and row count so you know it worked.
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(sales)")
    print("Columns:", [row[1] for row in cursor.fetchall()])

    cursor.execute("SELECT COUNT(*) FROM sales")
    print("Row count:", cursor.fetchone()[0])

    conn.close()
    print(f"Database ready at {DB_PATH}")


if __name__ == "__main__":
    main()
