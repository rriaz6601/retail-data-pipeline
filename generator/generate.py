"""Synthetic multi-source retail data generator.

Produces three CSVs that mimic a retailer's real source systems: online
orders, POS transactions, and loyalty members. A configurable fraction of
online "pickup" orders are deliberately mirrored into the POS feed under a
different ID, simulating an order-online-pickup-in-store flow that
double-counts the sale unless reconciled downstream.
"""
from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

SKUS = [f"SKU-{i:04d}" for i in range(1, 51)]


@dataclass
class GenerateResult:
    online_orders: int
    pos_transactions: int
    loyalty_members: int
    pickup_matched: int

    @property
    def pickup_rate_actual(self) -> float:
        return self.pickup_matched / self.online_orders


def _sku_prices(rng: random.Random) -> dict[str, float]:
    return {sku: round(rng.uniform(5.0, 150.0), 2) for sku in SKUS}


def generate(
    output_dir: Path,
    seed: int = 42,
    n_customers: int = 200,
    n_online_orders: int = 1000,
    pickup_rate: float = 0.08,
    n_pos_only: int = 500,
    n_loyalty_members: int = 150,
) -> GenerateResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    fake = Faker()
    Faker.seed(seed)

    prices = _sku_prices(rng)
    customers = [fake.unique.email() for _ in range(n_customers)]
    store_ids = ["STORE-01", "STORE-02", "STORE-03"]

    start = datetime(2026, 1, 1)

    online_rows = []
    pos_rows = []
    pickup_matched = 0

    for i in range(1, n_online_orders + 1):
        order_id = f"WEB-{i:06d}"
        customer_email = rng.choice(customers)
        sku = rng.choice(SKUS)
        quantity = rng.randint(1, 4)
        unit_price = prices[sku]
        order_ts = start + timedelta(
            days=rng.randint(0, 180), hours=rng.randint(0, 23), minutes=rng.randint(0, 59)
        )
        is_pickup = rng.random() < pickup_rate
        fulfillment_type = "pickup" if is_pickup else "shipped"

        online_rows.append(
            {
                "order_id": order_id,
                "customer_email": customer_email,
                "order_timestamp": order_ts.isoformat(),
                "item_sku": sku,
                "quantity": quantity,
                "unit_price": unit_price,
                "channel": "online",
                "fulfillment_type": fulfillment_type,
            }
        )

        if is_pickup:
            pickup_matched += 1
            txn_ts = order_ts + timedelta(hours=rng.randint(1, 47))
            pos_rows.append(
                {
                    "txn_id": f"POS-{len(pos_rows) + 1:06d}",
                    "cust_email": customer_email,
                    "txn_datetime": txn_ts.isoformat(),
                    "product_code": sku,
                    "qty": quantity,
                    "price_each": unit_price,
                    "store_id": rng.choice(store_ids),
                }
            )

    for _ in range(n_pos_only):
        sku = rng.choice(SKUS)
        txn_ts = start + timedelta(
            days=rng.randint(0, 180), hours=rng.randint(0, 23), minutes=rng.randint(0, 59)
        )
        pos_rows.append(
            {
                "txn_id": f"POS-{len(pos_rows) + 1:06d}",
                "cust_email": rng.choice(customers),
                "txn_datetime": txn_ts.isoformat(),
                "product_code": sku,
                "qty": rng.randint(1, 4),
                "price_each": prices[sku],
                "store_id": rng.choice(store_ids),
            }
        )

    loyalty_customers = rng.sample(customers, k=min(n_loyalty_members, len(customers)))
    loyalty_rows = []
    for i, email in enumerate(loyalty_customers, start=1):
        loyalty_rows.append(
            {
                "member_id": f"LOY-{i:05d}",
                "email": email,
                "full_name": fake.name(),
                "signup_date": (start - timedelta(days=rng.randint(30, 900))).date().isoformat(),
                "loyalty_tier": rng.choice(["bronze", "silver", "gold"]),
            }
        )

    _write_csv(output_dir / "online_orders.csv", online_rows)
    _write_csv(output_dir / "pos_transactions.csv", pos_rows)
    _write_csv(output_dir / "loyalty_members.csv", loyalty_rows)

    return GenerateResult(
        online_orders=len(online_rows),
        pos_transactions=len(pos_rows),
        loyalty_members=len(loyalty_rows),
        pickup_matched=pickup_matched,
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"no rows to write for {path}")
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    result = generate(Path("data/raw"))
    print(result)
