"""Integration test — requires `docker compose up -d postgres` first.

Loads into `raw_test`, not `raw`, so this never touches (or drops-CASCADE)
the pipeline's real `raw` schema and the dbt views built on top of it."""
from pathlib import Path

import psycopg
import pytest

from flows.load_raw import load_raw
from generator.generate import generate

DSN = "postgresql://retail:retail@localhost:55432/retail"


def _postgres_available() -> bool:
    try:
        with psycopg.connect(DSN, connect_timeout=2):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_available(),
    reason="postgres not running — start with `docker compose up -d postgres`",
)


def test_load_raw_creates_tables_with_correct_row_counts(tmp_path: Path):
    result = generate(tmp_path, seed=1, n_online_orders=100, n_pos_only=50, n_loyalty_members=30)

    counts = load_raw(tmp_path, DSN, schema="raw_test")

    assert counts["online_orders"] == result.online_orders
    assert counts["pos_transactions"] == result.pos_transactions
    assert counts["loyalty_members"] == result.loyalty_members
