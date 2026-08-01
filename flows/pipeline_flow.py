"""End-to-end orchestration: generate synthetic data, load it into Postgres,
run dbt, and check the result isn't obviously broken."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from prefect import flow, task

from flows.load_raw import load_raw
from generator.generate import generate

DEFAULT_DSN = "postgresql://retail:retail@localhost:55432/retail"
DATA_DIR = Path("data/raw")
DBT_DIR = Path("dbt")


@task
def generate_data(seed: int = 42) -> dict:
    result = generate(DATA_DIR, seed=seed)
    return {
        "online_orders": result.online_orders,
        "pos_transactions": result.pos_transactions,
        "loyalty_members": result.loyalty_members,
        "pickup_matched": result.pickup_matched,
    }


@task
def load_data(dsn: str = DEFAULT_DSN, schema: str = "raw") -> dict:
    return load_raw(DATA_DIR, dsn, schema=schema)


@task
def run_dbt() -> None:
    env = {**os.environ, "DBT_PROFILES_DIR": str((DBT_DIR / "profiles").resolve())}
    subprocess.run(["dbt", "run"], cwd=DBT_DIR, env=env, check=True)
    subprocess.run(["dbt", "test"], cwd=DBT_DIR, env=env, check=True)


@task
def check_no_duplicate_sales(
    dsn: str = DEFAULT_DSN, expected_online: int = 0, expected_pos_unique: int = 0
) -> None:
    import psycopg

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select count(*) from dbt_marts.fct_sales")
        (count,) = cur.fetchone()
        expected = expected_online + expected_pos_unique
        if count != expected:
            raise ValueError(
                f"fct_sales has {count} rows, expected {expected} "
                f"(online + non-pickup POS) — dedup logic may be broken"
            )


@flow(name="retail-data-pipeline")
def run_pipeline(seed: int = 42, dsn: str = DEFAULT_DSN) -> None:
    gen_result = generate_data(seed=seed)
    load_data(dsn=dsn)
    run_dbt()
    check_no_duplicate_sales(
        dsn=dsn,
        expected_online=gen_result["online_orders"],
        expected_pos_unique=gen_result["pos_transactions"] - gen_result["pickup_matched"],
    )


if __name__ == "__main__":
    run_pipeline()
