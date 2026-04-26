"""
Generate transaction-level POS data for the ODSC coffee shop DES tutorial.

One row per customer. Six months of weekdays. Arrivals follow a piecewise
Poisson process with the same five rate windows used by the SimPy simulation
in Chapter 5 of Simulation Models for Data Science. Service times are
lognormal with parameters that depend on order type. The intent is that
participants who fit exp() to inter-arrival times and lognorm() to service
times with scipy.stats recover the canonical parameters within a small
tolerance.

Run:
    python generate_coffee_shop_pos.py

Outputs (next to this script):
    coffee_shop_pos.csv          one row per customer
    coffee_shop_pos_codebook.md  field-by-field description

Determinism: seeded with rng(42). Re-running produces the same file.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Canonical parameters. These match the SimPy reference implementation in
# coffee_shop_des.py. Fits to the generated data should recover these values
# to within a few percent.
# ---------------------------------------------------------------------------

# Each tuple: (start_minute_from_open, end_minute_from_open, rate_per_hour)
ARRIVAL_WINDOWS: list[tuple[int, int, float]] = [
    (0, 120, 30.0),    # 7:00 - 9:00 AM, morning rush
    (120, 240, 14.0),  # 9:00 - 11:00 AM
    (240, 360, 18.0),  # 11:00 AM - 1:00 PM, lunch bump
    (360, 480, 9.0),   # 1:00 - 3:00 PM, afternoon lull
    (480, 600, 12.0),  # 3:00 - 5:00 PM, late afternoon
]

OPEN_TIME = time(7, 0)
CLOSE_TIME = time(17, 0)

# Order-type mix and lognormal(mu, sigma) parameters in log-space.
# Real-space mean = exp(mu + sigma**2 / 2).
ORDER_TYPES: dict[str, dict[str, float]] = {
    "drip":     {"prob": 0.30, "mu": 0.7, "sigma": 0.30},
    "espresso": {"prob": 0.50, "mu": 1.2, "sigma": 0.35},
    "blended":  {"prob": 0.20, "mu": 1.5, "sigma": 0.30},
}

# Six months of weekdays starting from a Monday so we always start on a
# day the shop is open. Any weekday-only span produces ~130 days; that is
# enough samples to fit distributions cleanly without producing a CSV that
# is annoyingly large to load in a workshop.
START_DATE = datetime(2025, 10, 6)  # Monday
N_WEEKDAYS = 130                    # ~ six months of weekdays

SEED = 42

OUTPUT_CSV = Path(__file__).parent / "coffee_shop_pos.csv"
OUTPUT_CODEBOOK = Path(__file__).parent / "coffee_shop_pos_codebook.md"


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

@dataclass
class Transaction:
    transaction_id: str
    arrival_timestamp: datetime
    order_type: str
    service_duration_min: float


def weekdays_from(start: datetime, n: int) -> list[datetime]:
    """Return n consecutive weekdays starting at `start`."""
    days: list[datetime] = []
    cursor = start
    while len(days) < n:
        if cursor.weekday() < 5:  # Mon-Fri
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


def sample_arrivals_for_window(
    rng: np.random.Generator,
    start_min: int,
    end_min: int,
    rate_per_hour: float,
) -> np.ndarray:
    """
    Sample arrival times within [start_min, end_min) under a homogeneous
    Poisson process with the given hourly rate. Returns minute offsets
    from the start of the simulated day (i.e., from `start_min`).

    Implementation: draw exponential inter-arrival gaps in minutes
    (mean = 60 / rate_per_hour) and accumulate until we exceed the
    window length. The first arrival in the window is offset by an
    exponential gap as well, which preserves the memoryless property
    across window boundaries when concatenated.
    """
    window_length = end_min - start_min
    if rate_per_hour <= 0:
        return np.empty(0, dtype=float)
    mean_gap_min = 60.0 / rate_per_hour
    # Generate generously, then trim. Expected count is rate * hours; we
    # multiply by 3 to make the buffer effectively never overflow.
    expected = rate_per_hour * (window_length / 60.0)
    buffer = max(int(expected * 3), 32)
    gaps = rng.exponential(scale=mean_gap_min, size=buffer)
    cum = np.cumsum(gaps)
    in_window = cum[cum < window_length]
    return start_min + in_window


def sample_order_type(rng: np.random.Generator) -> str:
    names = list(ORDER_TYPES.keys())
    probs = [ORDER_TYPES[n]["prob"] for n in names]
    return rng.choice(names, p=probs)


def sample_service_time(rng: np.random.Generator, order_type: str) -> float:
    p = ORDER_TYPES[order_type]
    return float(rng.lognormal(mean=p["mu"], sigma=p["sigma"]))


def generate_day(rng: np.random.Generator, day: datetime) -> list[Transaction]:
    """Generate all transactions for a single business day."""
    open_dt = datetime.combine(day.date(), OPEN_TIME)

    # Concatenate arrivals from all windows, in order.
    all_offsets: list[float] = []
    for start_min, end_min, rate in ARRIVAL_WINDOWS:
        offsets = sample_arrivals_for_window(rng, start_min, end_min, rate)
        all_offsets.extend(offsets.tolist())
    all_offsets.sort()

    txns: list[Transaction] = []
    for i, offset_min in enumerate(all_offsets):
        arrival = open_dt + timedelta(minutes=float(offset_min))
        order_type = sample_order_type(rng)
        service = sample_service_time(rng, order_type)
        txn_id = f"{day.strftime('%Y%m%d')}-{i:04d}"
        txns.append(Transaction(txn_id, arrival, order_type, service))

    return txns


def generate_dataset() -> list[Transaction]:
    rng = np.random.default_rng(SEED)
    days = weekdays_from(START_DATE, N_WEEKDAYS)
    out: list[Transaction] = []
    for day in days:
        out.extend(generate_day(rng, day))
    return out


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

CODEBOOK = """\
# coffee_shop_pos.csv — Codebook

Transaction-level point-of-sale data for the ODSC tutorial coffee shop. One row
per customer transaction. Six months of weekdays. Each business day runs
7:00 AM to 5:00 PM.

The data is synthetic. It is generated by `generate_coffee_shop_pos.py`
using a piecewise Poisson arrival process and lognormal service-time
distributions whose parameters match the SimPy reference simulation in
Chapter 5 of *Simulation Models for Data Science*. Participants who fit
distributions to this data with `scipy.stats` should recover those
parameters to within a few percent.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `transaction_id` | string | Unique identifier. Format: `YYYYMMDD-NNNN`. |
| `arrival_timestamp` | ISO 8601 datetime | When the customer joined the line. Local time, no timezone. |
| `order_type` | enum | One of `drip`, `espresso`, `blended`. Drives the service-time distribution. |
| `service_duration_min` | float | Time the customer spent being served, in minutes. Lognormal in log-space with parameters that vary by `order_type`. |

## Generation parameters (canonical)

Arrival rates by window (customers per hour):

| Window | Rate |
|--------|------|
| 7:00 - 9:00 AM | 30.0 |
| 9:00 - 11:00 AM | 14.0 |
| 11:00 AM - 1:00 PM | 18.0 |
| 1:00 - 3:00 PM | 9.0 |
| 3:00 - 5:00 PM | 12.0 |

Order-type mix and lognormal(mu, sigma) parameters (log-space):

| Order | Probability | mu | sigma | Real-space mean (min) |
|-------|-------------|----|-------|----------------------|
| drip | 0.30 | 0.70 | 0.30 | 2.10 |
| espresso | 0.50 | 1.20 | 0.35 | 3.53 |
| blended | 0.20 | 1.50 | 0.30 | 4.69 |

Weighted-mean service time across the order mix is approximately 3.33
minutes, which is the value used in the workshop's M/M/c utilization
sanity check.

## Reproducibility

The generator is seeded with `numpy.random.default_rng(42)`. Re-running
`generate_coffee_shop_pos.py` produces the same file byte-for-byte.
"""


def write_csv(transactions: list[Transaction], path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["transaction_id", "arrival_timestamp", "order_type", "service_duration_min"]
        )
        for t in transactions:
            writer.writerow(
                [
                    t.transaction_id,
                    t.arrival_timestamp.isoformat(timespec="seconds"),
                    t.order_type,
                    f"{t.service_duration_min:.4f}",
                ]
            )


def main() -> None:
    txns = generate_dataset()
    write_csv(txns, OUTPUT_CSV)
    OUTPUT_CODEBOOK.write_text(CODEBOOK)
    print(f"Wrote {len(txns):,} transactions to {OUTPUT_CSV}")
    print(f"Wrote codebook to {OUTPUT_CODEBOOK}")


if __name__ == "__main__":
    main()
