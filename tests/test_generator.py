import hashlib
from pathlib import Path

from generator.generate import generate

GENERATED_FILES = ("online_orders.csv", "pos_transactions.csv", "loyalty_members.csv")


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pickup_overlap_rate_within_expected_band(tmp_path: Path):
    result = generate(tmp_path, seed=42, n_online_orders=1000, pickup_rate=0.08)

    assert 0.05 <= result.pickup_rate_actual <= 0.10


def test_pos_transactions_include_both_matched_and_organic(tmp_path: Path):
    result = generate(
        tmp_path, seed=42, n_online_orders=1000, pickup_rate=0.08, n_pos_only=500
    )

    assert result.pos_transactions == result.pickup_matched + 500


def test_generate_is_deterministic_for_a_given_seed(tmp_path: Path):
    run1_dir = tmp_path / "run1"
    run2_dir = tmp_path / "run2"
    first = generate(run1_dir, seed=7, n_online_orders=200)
    second = generate(run2_dir, seed=7, n_online_orders=200)

    assert first == second

    # GenerateResult equality above only proves the row *counts* match — it
    # can't catch content drift (emails, SKUs, timestamps, prices). Hash the
    # actual CSV bytes from each run to prove the generated content itself is
    # identical, not just its shape.
    first_hashes = {name: _hash_file(run1_dir / name) for name in GENERATED_FILES}
    second_hashes = {name: _hash_file(run2_dir / name) for name in GENERATED_FILES}
    assert first_hashes == second_hashes
