from pathlib import Path

from generator.generate import generate


def test_pickup_overlap_rate_within_expected_band(tmp_path: Path):
    result = generate(tmp_path, seed=42, n_online_orders=1000, pickup_rate=0.08)

    assert 0.05 <= result.pickup_rate_actual <= 0.10


def test_pos_transactions_include_both_matched_and_organic(tmp_path: Path):
    result = generate(
        tmp_path, seed=42, n_online_orders=1000, pickup_rate=0.08, n_pos_only=500
    )

    assert result.pos_transactions == result.pickup_matched + 500


def test_generate_is_deterministic_for_a_given_seed(tmp_path: Path):
    first = generate(tmp_path / "run1", seed=7, n_online_orders=200)
    second = generate(tmp_path / "run2", seed=7, n_online_orders=200)

    assert first == second
