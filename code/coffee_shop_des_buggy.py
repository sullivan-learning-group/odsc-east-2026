"""
Coffee Shop Staffing Simulation — Discrete Event Simulation with SimPy
======================================================================

Business question:
    What staffing configuration minimises customer wait time during the
    morning rush while keeping daily labour cost under $350?

Primary KPI : P90 wait time (target < 5 min)
Secondary   : mean wait, walkaway rate, barista utilisation
Cost metric : daily labour cost = barista-hours × $17/hr

Four scenarios are compared:
    Baseline   — current operations (2 / 2 / 1 baristas)
    A (Rush)   — +1 barista during 7–9 AM only
    B (Full)   — +1 barista in every window
    C (Process)— 15% faster service 7–9 AM, no extra labour
"""

# ── imports ──────────────────────────────────────────────────────────
import simpy
import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# ── configuration ────────────────────────────────────────────────────

OPEN_HOUR = 7          # 7 AM
CLOSE_HOUR = 17        # 5 PM
SIM_DURATION = (CLOSE_HOUR - OPEN_HOUR) * 60  # 600 minutes
WARMUP = 30            # minutes — discard events before 7:30 AM

HOURLY_WAGE = 17       # $/hr per barista
REVENUE_PER_CUSTOMER = 7.00

BALK_THRESHOLD = 8     # customer leaves if queue length >= 8

BASE_SEED = 42
N_REPLICATIONS = 50

# ── arrival rates by time window (customers / hour) ──────────────────
# Each tuple: (start_minute, end_minute, rate_per_hour)
ARRIVAL_WINDOWS = [
    (0,   120, 30),   # 7:00–9:00 AM
    (120, 240, 14),   # 9:00–11:00 AM
    (240, 360, 18),   # 11:00 AM–1:00 PM
    (360, 480,  9),   # 1:00–3:00 PM
    (480, 600, 12),   # 3:00–5:00 PM
]

# ── order-type mix and service-time parameters ───────────────────────
# Lognormal(μ, σ) in log-space → real-space mean = exp(μ + σ²/2)
ORDER_TYPES = {
    "drip":     {"prob": 0.30, "mu": 0.7, "sigma": 0.3},
    "espresso": {"prob": 0.50, "mu": 1.2, "sigma": 0.35},
    "blended":  {"prob": 0.20, "mu": 1.5, "sigma": 0.3},
}

# cumulative probabilities for sampling
_order_names = list(ORDER_TYPES.keys())
_order_cum_probs = np.cumsum([ORDER_TYPES[n]["prob"] for n in _order_names])


# ── scenario definitions ─────────────────────────────────────────────

@dataclass
class Scenario:
    """Defines a staffing scenario."""
    name: str
    description: str
    # staffing_schedule: list of (start_min, end_min, n_baristas)
    staffing_schedule: List[Tuple[int, int, int]]
    # service_time_multiplier: dict mapping (start_min, end_min) → multiplier
    # (default 1.0 everywhere; Scenario C uses 0.85 for 7–9 AM)
    service_multipliers: Dict[Tuple[int, int], float] = field(default_factory=dict)

    @property
    def daily_cost(self) -> float:
        total_hours = sum(
            n * (end - start) / 60
            for start, end, n in self.staffing_schedule
        )
        return total_hours * HOURLY_WAGE

    def baristas_at(self, t: float) -> int:
        """Return number of baristas on duty at time t (minutes from open)."""
        for start, end, n in self.staffing_schedule:
            if start <= t < end:
                return n
        # after closing — return last window's staffing for drain-out
        return self.staffing_schedule[-1][2]

    def service_multiplier_at(self, t: float) -> float:
        """Return service-time multiplier at time t."""
        for (start, end), m in self.service_multipliers.items():
            if start <= t < end:
                return m
        return 1.0


SCENARIOS = {
    "Baseline": Scenario(
        name="Baseline",
        description="Current operations (2/2/1)",
        staffing_schedule=[(0, 120, 2), (120, 420, 2), (420, 600, 1)],
    ),
    "A: Rush boost": Scenario(
        name="A: Rush boost",
        description="+1 barista during morning rush (3/2/1)",
        staffing_schedule=[(0, 120, 3), (120, 420, 2), (420, 600, 1)],
    ),
    "B: All-day 3": Scenario(
        name="B: All-day 3",
        description="+1 barista every window (3/3/2)",
        staffing_schedule=[(0, 120, 3), (120, 420, 3), (420, 600, 2)],
    ),
    "C: Process improvement": Scenario(
        name="C: Process improvement",
        description="15% faster service 7–9 AM (2/2/1)",
        staffing_schedule=[(0, 120, 2), (120, 420, 2), (420, 600, 1)],
        service_multipliers={(0, 120): 0.85},
    ),
}


# ── helper: arrival rate at time t ───────────────────────────────────

def _arrival_rate(t: float) -> float:
    """Return arrival rate (customers/hr) at time t (minutes from open)."""
    for start, end, rate in ARRIVAL_WINDOWS:
        if start <= t < end:
            return rate
    return 0.0  # after last window — no new arrivals


# ── helper: draw service time ────────────────────────────────────────

def _draw_service_time(order_type: str, rng: np.random.Generator,
                       multiplier: float = 1.0) -> float:
    """Draw a lognormal service time (minutes) for the given order type."""
    params = ORDER_TYPES[order_type]
    raw = rng.lognormal(mean=params["mu"], sigma=params["sigma"])
    return raw * multiplier


# ── helper: assign order type ────────────────────────────────────────

def _assign_order_type(rng: np.random.Generator) -> str:
    u = rng.random()
    for i, cp in enumerate(_order_cum_probs):
        if u <= cp:
            return _order_names[i]
    return _order_names[-1]


# ── helper: current queue length ─────────────────────────────────────
# SimPy's PriorityResource / Resource exposes .count (in service) and
# len(.queue) for those waiting.  We use a plain Resource.

def _queue_length(resource: simpy.Resource) -> int:
    return len(resource.queue)


# ════════════════════════════════════════════════════════════════════
#  CORE SIMULATION FUNCTIONS
# ════════════════════════════════════════════════════════════════════

def entity_process(
    env: simpy.Environment,
    name: str,
    baristas: simpy.Resource,
    scenario: Scenario,
    rng: np.random.Generator,
    metrics: List[dict],
):
    """
    Entity lifecycle: arrive → check queue → (balk | wait → serve → depart).

    Parameters
    ----------
    env       : SimPy environment (clock in minutes from 7 AM).
    name      : unique customer identifier.
    baristas  : SimPy Resource representing the barista pool.
    scenario  : Scenario object (for service multiplier look-up).
    rng       : numpy random Generator for this replication.
    metrics   : mutable list that collects per-customer records.
    """
    arrival_time = env.now
    order_type = _assign_order_type(rng)

    # ── join queue & wait for barista ────────────────────────────────
    with baristas.request() as req:
        yield req

        # ── balking check ────────────────────────────────────────────
        if _queue_length(baristas) >= BALK_THRESHOLD:
            metrics.append({
                "customer": name,
                "arrival_time": arrival_time,
                "order_type": order_type,
                "wait_time": np.nan,
                "service_time": np.nan,
                "total_time": np.nan,
                "outcome": "walkaway",
            })
            return

        service_start = env.now
        wait_time = service_start - arrival_time

        # ── service ──────────────────────────────────────────────────
        multiplier = scenario.service_multiplier_at(arrival_time)
        service_time = _draw_service_time(order_type, rng, multiplier)
        yield env.timeout(service_time)

        metrics.append({
            "customer": name,
            "arrival_time": arrival_time,
            "order_type": order_type,
            "wait_time": wait_time,
            "service_time": service_time,
            "total_time": wait_time + service_time,
            "outcome": "served",
        })


def entity_generator(
    env: simpy.Environment,
    baristas: simpy.Resource,
    scenario: Scenario,
    rng: np.random.Generator,
    metrics: List[dict],
):
    """
    Generate customer arrivals using time-varying Poisson process.

    Uses thinning: inter-arrival time drawn from exponential with the
    *current* window's rate.  Rate changes are checked after each arrival.
    """
    customer_id = 0
    while True:
        rate = _arrival_rate(env.now)
        if rate <= 0:
            break  # past closing; no more arrivals

        # draw inter-arrival time (minutes)
        iat = rng.exponential(60.0 / rate)
        yield env.timeout(iat)

        # stop generating if we've passed the closing time
        if env.now >= SIM_DURATION:
            break

        customer_id += 1
        env.process(
            entity_process(env, f"C{customer_id}", baristas, scenario, rng, metrics)
        )


# ── staffing manager (adjusts resource capacity on schedule) ─────────

def staffing_manager(
    env: simpy.Environment,
    baristas: simpy.Resource,
    scenario: Scenario,
):
    """
    Adjust the barista resource capacity according to the scenario's
    staffing schedule.  Runs as a background SimPy process.

    SimPy's Resource doesn't support dynamic capacity changes natively,
    so we use a PriorityResource workaround — but the simplest robust
    approach is to manage capacity via the resource's `_capacity` attribute
    combined with releasing phantom requests.  Here we take the cleaner
    approach of checking capacity at each schedule boundary.
    """
    for start, end, n in scenario.staffing_schedule:
        # wait until the start of this window
        if env.now < start:
            yield env.timeout(start - env.now)
        baristas._capacity = n
        # wake up any waiting requests that can now be served
        # by triggering the resource to re-evaluate its queue
        baristas._trigger_put(None)


def run_single_replication(
    scenario: Scenario,
    seed: int,
) -> Tuple[pd.DataFrame, List[Tuple[float, int]]]:
    """
    Run one day of the coffee shop simulation.

    Returns
    -------
    df_customers : DataFrame with one row per customer.
    queue_trace  : list of (time, queue_length) snapshots for plotting.
    """
    rng = np.random.default_rng(seed)
    env = simpy.Environment()

    # start with the first window's capacity
    initial_capacity = scenario.staffing_schedule[0][2]
    baristas = simpy.Resource(env, capacity=initial_capacity)

    metrics: List[dict] = []
    queue_trace: List[Tuple[float, int]] = []

    # ── background process: adjust staffing ──────────────────────────
    env.process(staffing_manager(env, baristas, scenario))

    # ── background process: record queue length every minute ─────────
    def queue_monitor(env, resource, trace):
        while True:
            trace.append((env.now, len(resource.queue) + resource.count))
            yield env.timeout(1)  # sample every minute

    env.process(queue_monitor(env, baristas, queue_trace))

    # ── arrival generator ────────────────────────────────────────────
    env.process(entity_generator(env, baristas, scenario, rng, metrics))

    # run until all customers served (give extra time for drain-out)
    env.run(until=SIM_DURATION + 120)

    df = pd.DataFrame(metrics)
    return df, queue_trace


def summarise_replication(df: pd.DataFrame, scenario: Scenario) -> dict:
    """Compute summary statistics for one replication (post-warmup)."""
    # filter out warmup period
    df_warm = df[df["arrival_time"] >= WARMUP].copy()
    served = df_warm[df_warm["outcome"] == "served"]
    walkaways = df_warm[df_warm["outcome"] == "walkaway"]

    n_total = len(df_warm)
    n_served = len(served)
    n_walkaways = len(walkaways)

    summary = {
        "scenario": scenario.name,
        "n_arrivals": n_total,
        "n_served": n_served,
        "n_walkaways": n_walkaways,
        "walkaway_rate": n_walkaways / n_total if n_total > 0 else 0.0,
        "mean_wait": served["wait_time"].mean() if n_served > 0 else np.nan,
        "p50_wait": served["wait_time"].quantile(0.50) if n_served > 0 else np.nan,
        "p90_wait": served["wait_time"].quantile(0.90) if n_served > 0 else np.nan,
        "max_wait": served["wait_time"].max() if n_served > 0 else np.nan,
        "mean_service": served["service_time"].mean() if n_served > 0 else np.nan,
        "mean_total": served["total_time"].mean() if n_served > 0 else np.nan,
        "daily_cost": scenario.daily_cost,
    }

    # ── utilisation by time window ───────────────────────────────────
    # Utilisation = time baristas are busy / (n_baristas × window_duration)
    for start, end, n in scenario.staffing_schedule:
        window_served = served[
            (served["arrival_time"] >= start) & (served["arrival_time"] < end)
        ]
        busy_time = window_served["service_time"].sum()
        available_time = n * (end - start)
        label = f"util_{start}_{end}"
        summary[label] = busy_time / available_time if available_time > 0 else 0.0

    return summary


def run_scenario(
    scenario: Scenario,
    n_replications: int = N_REPLICATIONS,
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Tuple[float, int]]]:
    """
    Run all replications for one scenario.

    Returns
    -------
    df_summary      : DataFrame with one row per replication.
    df_all_customers: DataFrame with all customer records (rep 0 only saved
                      for queue trace).
    queue_trace     : queue trace from the first replication (for plotting).
    """
    summaries = []
    first_trace = None
    first_customers = None

    for i in range(n_replications):
        seed = BASE_SEED + i
        df_cust, trace = run_single_replication(scenario, seed)
        summary = summarise_replication(df_cust, scenario)
        summary["replication"] = i
        summary["seed"] = seed
        summaries.append(summary)

        if i == 0:
            first_trace = trace
            first_customers = df_cust.copy()
            first_customers["replication"] = 0

    df_summary = pd.DataFrame(summaries)
    return df_summary, first_customers, first_trace


# ════════════════════════════════════════════════════════════════════
#  ANALYSIS & VISUALISATION
# ════════════════════════════════════════════════════════════════════

def ci_95(series: pd.Series) -> Tuple[float, float]:
    """Return (lower, upper) of a 95% confidence interval for the mean."""
    n = len(series)
    m = series.mean()
    se = series.std(ddof=1) / np.sqrt(n)
    t_crit = stats.t.ppf(0.975, df=n - 1)
    return (m - t_crit * se, m + t_crit * se)


def compare_scenarios(results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Build a side-by-side comparison table across scenarios.

    Parameters
    ----------
    results : dict mapping scenario name → per-replication summary DataFrame.

    Returns
    -------
    DataFrame with one row per scenario and columns for each KPI with CIs.
    """
    rows = []
    for name, df in results.items():
        lo_wait, hi_wait = ci_95(df["mean_wait"])
        lo_p90, hi_p90 = ci_95(df["p90_wait"])
        lo_walk, hi_walk = ci_95(df["walkaway_rate"])

        rows.append({
            "Scenario": name,
            "Daily Cost": f"${df['daily_cost'].iloc[0]:.0f}",
            "Mean Wait (min)": f"{df['mean_wait'].mean():.2f}",
            "  95% CI": f"[{lo_wait:.2f}, {hi_wait:.2f}]",
            "P90 Wait (min)": f"{df['p90_wait'].mean():.2f}",
            "  95% CI ": f"[{lo_p90:.2f}, {hi_p90:.2f}]",
            "Walkaway Rate": f"{df['walkaway_rate'].mean():.1%}",
            "  95% CI  ": f"[{lo_walk:.1%}, {hi_walk:.1%}]",
            "Avg Served/Day": f"{df['n_served'].mean():.1f}",
        })

    return pd.DataFrame(rows)


# ── plotting functions ───────────────────────────────────────────────

def plot_queue_over_time(traces: Dict[str, List[Tuple[float, int]]],
                         save_path: Optional[str] = None):
    """Queue length over time for a single representative run per scenario."""
    fig, ax = plt.subplots(figsize=(12, 5))
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]

    for (name, trace), color in zip(traces.items(), colors):
        times = [t for t, _ in trace if t <= SIM_DURATION]
        lengths = [q for t, q in trace if t <= SIM_DURATION]
        ax.plot(times, lengths, alpha=0.7, label=name, color=color, linewidth=0.8)

    ax.axhline(y=BALK_THRESHOLD, color="red", linestyle="--", alpha=0.5,
               label=f"Balk threshold ({BALK_THRESHOLD})")
    ax.axvspan(0, 120, alpha=0.08, color="orange", label="Morning rush (7–9 AM)")

    # x-axis: clock times
    tick_positions = list(range(0, SIM_DURATION + 1, 60))
    tick_labels = [f"{OPEN_HOUR + m // 60}:00" for m in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right")

    ax.set_xlabel("Time of Day")
    ax.set_ylabel("Customers in System (queue + service)")
    ax.set_title("Queue Length Over Time — Single Representative Run")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_wait_histograms(customer_dfs: Dict[str, pd.DataFrame],
                         save_path: Optional[str] = None):
    """Wait time distribution histograms, one panel per scenario."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=True)
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]

    for ax, (name, df), color in zip(axes.flat, customer_dfs.items(), colors):
        served = df[(df["outcome"] == "served") & (df["arrival_time"] >= WARMUP)]
        waits = served["wait_time"].dropna()
        ax.hist(waits, bins=40, color=color, alpha=0.7, edgecolor="white")
        ax.axvline(waits.quantile(0.90), color="red", linestyle="--",
                   label=f"P90 = {waits.quantile(0.90):.1f} min")
        ax.axvline(waits.mean(), color="black", linestyle="-",
                   label=f"Mean = {waits.mean():.1f} min")
        ax.set_title(name, fontsize=10)
        ax.set_xlabel("Wait Time (min)")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    axes[0, 0].set_ylabel("Frequency")
    axes[1, 0].set_ylabel("Frequency")
    fig.suptitle("Wait Time Distributions (Single Representative Run)", fontsize=12)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_scenario_comparison(results: Dict[str, pd.DataFrame],
                             save_path: Optional[str] = None):
    """Bar chart comparing KPIs across scenarios with error bars."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 5))
    names = list(results.keys())
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]
    x = np.arange(len(names))

    metrics = [
        ("mean_wait", "Mean Wait (min)"),
        ("p90_wait", "P90 Wait (min)"),
        ("walkaway_rate", "Walkaway Rate"),
        ("n_served", "Customers Served / Day"),
    ]

    for ax, (col, title) in zip(axes, metrics):
        means = [results[n][col].mean() for n in names]
        ci_lo = [ci_95(results[n][col])[0] for n in names]
        ci_hi = [ci_95(results[n][col])[1] for n in names]
        errs = [[m - lo for m, lo in zip(means, ci_lo)],
                [hi - m for m, hi in zip(means, ci_hi)]]

        bars = ax.bar(x, means, color=colors, alpha=0.8, edgecolor="white")
        ax.errorbar(x, means, yerr=errs, fmt="none", ecolor="black",
                    capsize=4, linewidth=1.5)

        # add a target line for P90 wait
        if col == "p90_wait":
            ax.axhline(5, color="red", linestyle="--", alpha=0.6, label="Target (5 min)")
            ax.legend(fontsize=7)

        if col == "walkaway_rate":
            ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

        ax.set_xticks(x)
        ax.set_xticklabels([n.split(":")[0] if ":" in n else n[:8]
                            for n in names], rotation=30, ha="right", fontsize=8)
        ax.set_title(title, fontsize=10)
        ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle("Scenario Comparison (50 Replications, 95% CI)", fontsize=12)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_utilisation_by_window(results: Dict[str, pd.DataFrame],
                               save_path: Optional[str] = None):
    """Heatmap of barista utilisation by time window and scenario."""
    # identify utilisation columns
    sample_df = list(results.values())[0]
    util_cols = [c for c in sample_df.columns if c.startswith("util_")]

    window_labels = []
    for col in util_cols:
        parts = col.split("_")
        start, end = int(parts[1]), int(parts[2])
        s_hr = OPEN_HOUR + start // 60
        e_hr = OPEN_HOUR + end // 60
        window_labels.append(f"{s_hr}:00–{e_hr}:00")

    scenario_names = list(results.keys())
    data = np.zeros((len(scenario_names), len(util_cols)))

    for i, name in enumerate(scenario_names):
        for j, col in enumerate(util_cols):
            data[i, j] = results[name][col].mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    im = ax.imshow(data, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(len(window_labels)))
    ax.set_xticklabels(window_labels, rotation=30, ha="right")
    ax.set_yticks(range(len(scenario_names)))
    ax.set_yticklabels(scenario_names, fontsize=9)

    # annotate cells
    for i in range(len(scenario_names)):
        for j in range(len(util_cols)):
            ax.text(j, i, f"{data[i, j]:.0%}", ha="center", va="center",
                    fontsize=9, color="white" if data[i, j] > 0.6 else "black")

    fig.colorbar(im, ax=ax, label="Utilisation", shrink=0.8)
    ax.set_title("Barista Utilisation by Time Window and Scenario")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


# ════════════════════════════════════════════════════════════════════
#  MAIN EXECUTION
# ════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  COFFEE SHOP STAFFING DES — SimPy Simulation")
    print("=" * 70)

    all_summaries: Dict[str, pd.DataFrame] = {}
    all_traces: Dict[str, List[Tuple[float, int]]] = {}
    all_customers: Dict[str, pd.DataFrame] = {}

    for scenario_name, scenario in SCENARIOS.items():
        print(f"\n▶ Running scenario: {scenario_name} "
              f"(daily cost: ${scenario.daily_cost:.0f})")

        df_summary, df_cust, trace = run_scenario(scenario, N_REPLICATIONS)
        all_summaries[scenario_name] = df_summary
        all_traces[scenario_name] = trace
        all_customers[scenario_name] = df_cust

        # quick summary
        print(f"  Mean wait:     {df_summary['mean_wait'].mean():.2f} min "
              f"(95% CI: [{ci_95(df_summary['mean_wait'])[0]:.2f}, "
              f"{ci_95(df_summary['mean_wait'])[1]:.2f}])")
        print(f"  P90 wait:      {df_summary['p90_wait'].mean():.2f} min "
              f"(95% CI: [{ci_95(df_summary['p90_wait'])[0]:.2f}, "
              f"{ci_95(df_summary['p90_wait'])[1]:.2f}])")
        print(f"  Walkaway rate: {df_summary['walkaway_rate'].mean():.1%} "
              f"(95% CI: [{ci_95(df_summary['walkaway_rate'])[0]:.1%}, "
              f"{ci_95(df_summary['walkaway_rate'])[1]:.1%}])")
        print(f"  Avg served:    {df_summary['n_served'].mean():.1f} / day")

    # ── comparison table ─────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  SCENARIO COMPARISON")
    print("=" * 70)
    comparison = compare_scenarios(all_summaries)
    print(comparison.to_string(index=False))

    # ── cost-effectiveness ───────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  COST-EFFECTIVENESS ANALYSIS")
    print("=" * 70)
    baseline_walkaways = all_summaries["Baseline"]["walkaway_rate"].mean()
    baseline_served = all_summaries["Baseline"]["n_served"].mean()

    for name, df in all_summaries.items():
        if name == "Baseline":
            continue
        walk_reduction = baseline_walkaways - df["walkaway_rate"].mean()
        extra_customers = walk_reduction * 166  # approximate daily arrivals
        revenue_gain = extra_customers * REVENUE_PER_CUSTOMER
        cost_increase = df["daily_cost"].iloc[0] - all_summaries["Baseline"]["daily_cost"].iloc[0]
        net_benefit = revenue_gain - cost_increase
        print(f"\n  {name}:")
        print(f"    Additional labour cost:  ${cost_increase:+.0f}/day")
        print(f"    Walkaway reduction:      {walk_reduction:+.1%} "
              f"(≈ {extra_customers:+.1f} customers/day)")
        print(f"    Estimated revenue gain:  ${revenue_gain:+.0f}/day")
        print(f"    Net daily benefit:       ${net_benefit:+.0f}/day")
        meets_budget = df["daily_cost"].iloc[0] <= 350
        meets_p90 = df["p90_wait"].mean() < 5.0
        print(f"    Under $350 budget?       {'✓ Yes' if meets_budget else '✗ No'}")
        print(f"    P90 wait < 5 min?        {'✓ Yes' if meets_p90 else '✗ No'}")

    # ── generate plots ───────────────────────────────────────────────
    print("\n▶ Generating plots...")

    plot_queue_over_time(all_traces, save_path="queue_over_time.png")
    print("  Saved: queue_over_time.png")

    plot_wait_histograms(all_customers, save_path="wait_histograms.png")
    print("  Saved: wait_histograms.png")

    plot_scenario_comparison(all_summaries, save_path="scenario_comparison.png")
    print("  Saved: scenario_comparison.png")

    plot_utilisation_by_window(all_summaries, save_path="utilisation_heatmap.png")
    print("  Saved: utilisation_heatmap.png")

    # ── save raw data ────────────────────────────────────────────────
    all_rep_data = pd.concat(all_summaries.values(), ignore_index=True)
    all_rep_data.to_csv("replication_summaries.csv", index=False)
    print("  Saved: replication_summaries.csv")

    print("\n" + "=" * 70)
    print("  SIMULATION COMPLETE")
    print("=" * 70)

    return all_summaries, all_traces, all_customers


if __name__ == "__main__":
    main()
