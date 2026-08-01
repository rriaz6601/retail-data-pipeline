"""Load raw CSVs into the `raw` schema in Postgres, preserving source
fidelity. Column typing/cleanup happens in dbt staging models, not here."""
from __future__ import annotations

from pathlib import Path

import psycopg

TABLES = {
    "online_orders": (
        "order_id", "customer_email", "order_timestamp", "item_sku",
        "quantity", "unit_price", "channel", "fulfillment_type",
    ),
    "pos_transactions": (
        "txn_id", "cust_email", "txn_datetime", "product_code",
        "qty", "price_each", "store_id",
    ),
    "loyalty_members": (
        "member_id", "email", "full_name", "signup_date", "loyalty_tier",
    ),
}


def load_raw(csv_dir: Path, dsn: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS raw")
            for table, columns in TABLES.items():
                cur.execute(f"DROP TABLE IF EXISTS raw.{table}")
                cols_ddl = ", ".join(f'"{c}" TEXT' for c in columns)
                cur.execute(f"CREATE TABLE raw.{table} ({cols_ddl})")

                csv_path = csv_dir / f"{table}.csv"
                with csv_path.open() as f, cur.copy(
                    f"COPY raw.{table} ({', '.join(columns)}) FROM STDIN WITH CSV HEADER"
                ) as copy:
                    copy.write(f.read())

                cur.execute(f"SELECT count(*) FROM raw.{table}")
                counts[table] = cur.fetchone()[0]
    return counts


if __name__ == "__main__":
    import sys

    dsn = sys.argv[1] if len(sys.argv) > 1 else "postgresql://retail:retail@localhost:55432/retail"
    print(load_raw(Path("data/raw"), dsn))
