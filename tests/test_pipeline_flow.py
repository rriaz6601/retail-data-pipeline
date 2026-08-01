"""Unit test for the pipeline's data-quality check, run without Prefect's
runtime or a real database (using a fake cursor/connection)."""
import pytest

from flows.pipeline_flow import check_no_duplicate_sales


class _FakeCursor:
    def __init__(self, count: int):
        self._count = count

    def execute(self, *_args, **_kwargs):
        pass

    def fetchone(self):
        return (self._count,)

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


class _FakeConn:
    def __init__(self, count: int):
        self._count = count

    def cursor(self):
        return _FakeCursor(self._count)

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def test_check_passes_when_count_matches_expected(monkeypatch):
    monkeypatch.setattr("psycopg.connect", lambda *_a, **_kw: _FakeConn(150))

    check_no_duplicate_sales.fn(expected_online=100, expected_pos_unique=50)


def test_check_raises_when_count_indicates_duplicates(monkeypatch):
    monkeypatch.setattr("psycopg.connect", lambda *_a, **_kw: _FakeConn(158))

    with pytest.raises(ValueError, match="dedup logic may be broken"):
        check_no_duplicate_sales.fn(expected_online=100, expected_pos_unique=50)
