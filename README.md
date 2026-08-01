# retail-data-pipeline

A small, self-contained data pipeline that consolidates three messy synthetic
"source systems" — online orders, POS transactions, and loyalty members —
into one clean, deduplicated sales mart. Prefect orchestrates it, dbt
transforms it, Postgres stores it.

All data is synthetic and generated locally. No client data, no proprietary
logic — this demonstrates the same multi-source consolidation pattern used
in production data warehouse work, safe to run and read end to end.

## The problem it solves

Real retailers often have online orders and in-store POS as separate
systems. When a customer orders online for in-store pickup, the sale can
get recorded twice — once online, once when the store scans it at pickup.
This pipeline generates that exact scenario (a configurable ~5-10% of online
orders are mirrored into the POS feed) and then reconciles it in dbt, so the
final `fct_sales` mart has exactly one row per real sale.

## Architecture

```
generator/generate.py          synthetic data (seeded, deterministic)
        |
        v
data/raw/*.csv
        |
        v (flows/load_raw.py)
Postgres: raw.online_orders, raw.pos_transactions, raw.loyalty_members
        |
        v (dbt: models/staging/)
staging: stg_online_orders, stg_pos_transactions, stg_loyalty_members
        |
        v (dbt: models/marts/)
marts: int_pos_matched -> fct_sales (deduped), dim_customers
        |
        v (flows/pipeline_flow.py)
Prefect flow ties it all together + a final data-quality check
```

## Running it

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
git clone https://github.com/rriaz6601/retail-data-pipeline
cd retail-data-pipeline
uv sync
docker compose up -d postgres
uv run python -m flows.pipeline_flow
```

This generates ~1000 online orders + ~580 POS transactions + 150 loyalty
members, loads them into Postgres, builds every dbt model, runs all dbt
tests, and checks that `fct_sales` has exactly one row per real sale.

## Running the tests

```bash
uv run pytest                          # generator + flow unit tests
docker compose up -d postgres          # required for the loader test
uv run pytest tests/test_load_raw.py   # integration test
cd dbt && DBT_PROFILES_DIR=./profiles uv run dbt test   # dbt tests
```

## Why this exists

This is one of a few small portfolio projects, each demonstrating a specific
data engineering pattern with fully synthetic data — no client work, safe to
read and run end to end.
