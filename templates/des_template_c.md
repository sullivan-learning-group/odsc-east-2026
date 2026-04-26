# DES Template C: Validation and Results

## [Your Simulation Title]

Run these checks after the simulation produces results. Each section verifies a different aspect of model correctness and output quality. A simulation that produces plausible-looking numbers is not the same as a simulation you can trust. This template provides the structured protocol that separates the two.

**Key difference from Monte Carlo validation:** DES validation adds warm-up assessment and scenario comparison. Convergence is measured across replications (independent simulation runs) rather than within a single run's iteration count.

---

## Section 1: Sanity Checks

The purpose of sanity checks is to confirm that the code actually implements the spec. You're comparing simulated outputs against the input parameters from Template A to catch coding errors, distribution misconfigurations, and unit mismatches.

### Arrival Rate Verification

Do the simulated arrival rates match the rates specified in Template A? Measure across 20+ replications to average out sampling noise.

| Time Window | Expected Arrivals/hr | Simulated Arrivals/hr | Diff % | Pass? |
|-------------|---------------------|----------------------|--------|-------|
| [Window 1] | [from spec] | [measured] | [%] | [Y/N] |
| [Window 2] | [from spec] | [measured] | [%] | [Y/N] |
| [Window 3] | [from spec] | [measured] | [%] | [Y/N] |
| ... | ... | ... | ... | ... |

**Pass criterion:** All windows within 10% of the specified rate. Deviations up to 10% are expected from sampling variability, especially with exponential inter-arrival times (coefficient of variation = 1). If any window exceeds 10%, investigate whether the rate parameter is using the wrong units (per-hour vs. per-minute is the most common error).

### Service Time Verification

Do the simulated service times match the distribution parameters from Template A?

| Entity Category | Expected Mean | Simulated Mean | Diff % | Pass? |
|----------------|--------------|----------------|--------|-------|
| [Category_1] | [from spec] | [measured] | [%] | [Y/N] |
| [Category_2] | [from spec] | [measured] | [%] | [Y/N] |
| [Category_3] | [from spec] | [measured] | [%] | [Y/N] |

**Pass criterion:** All categories within 5% of the specified mean. Service time distributions with high variance (e.g., lognormal with large σ) may require more replications to converge. If a category is consistently biased in one direction, check whether the distribution parameterisation uses the log-space or real-space convention (this is the most frequent source of service time errors with lognormal distributions).

### Analytical Benchmark

Compare the bottleneck time window against a standard queueing theory approximation as an independent sanity check. Use M/M/c (exponential arrivals and service) or M/G/c (exponential arrivals, general service) depending on your service time distribution.

| Metric | Queueing Theory | Simulated | Reasonable? |
|--------|----------------|-----------|-------------|
| Utilisation (ρ) | [calculated] | [measured] | [Y/N] |
| Mean wait time | [calculated] | [measured] | [Y/N — see note if divergent] |
| P(waiting) | [calculated] | [measured] | [Y/N] |

```
[If the simulated wait time diverges from the queueing theory
prediction, explain why. Common reasons:

1. Transient vs. steady state: queueing formulas assume the system
   has been running at the given arrival rate forever. If your
   high-demand window is short (1–3 hours), the queue hasn't
   reached steady-state, and simulated waits will be LOWER than
   the formula predicts.

2. Non-exponential service times: M/M/c assumes exponential
   service (CV = 1). Lognormal and other distributions have
   different CVs, which affects wait times. Higher CV generally
   increases waits.

3. Time-varying rates: the formula assumes a constant arrival
   rate. If rates change mid-window, the formula doesn't apply
   cleanly.

Utilisation and P(waiting) are more robust comparisons than mean
wait because they depend less on steady-state assumptions. If
utilisation and P(waiting) match but mean wait diverges, the
divergence is almost certainly explained by transient effects,
and the model passes the sanity check.]
```

---

## Section 2: Warm-Up Assessment

The warm-up period exists to remove the startup artifact from summary statistics. Every simulation starts from an artificial initial condition (empty queues, idle resources), and the first batch of entities experiences unrealistically short waits. The warm-up discards this transient.

### Context for your system type

```
[Classify your system and explain the implications for warm-up:

Stationary systems (constant arrival and service rates):
  The warm-up removes the initial transient so that statistics
  reflect steady-state performance. Standard guidance applies:
  run for 5–10× the warm-up period.

Non-stationary systems (time-varying rates):
  The warm-up removes only the "empty at t=0" artifact. Be careful
  not to discard the time-dependent dynamics you want to study.
  If your peak period starts at the beginning of the day, an
  aggressive warm-up will cut into peak data.

Terminating systems (fixed start and end, like a single business day):
  Warm-up is typically short, just long enough for the queue to
  start building naturally. The system is inherently transient,
  and the transient IS the phenomenon of interest.]
```

### Queue stabilisation

From a single baseline replication, report the queue length behaviour during the warm-up period:

```
Queue rolling average (0 to [warm-up end]):     [value]
Queue rolling average ([warm-up end] to [2× warm-up end]): [value]
```

*The queue should reach its operating pattern within the warm-up period. "Operating pattern" does not mean steady state; it means the queue is responding to arrival dynamics rather than to the empty-system startup.*

### Sensitivity test

Do summary statistics change meaningfully if you extend the warm-up by 50%?

| Warm-up (min) | Mean Wait | P90 Wait | Utilisation |
|---------------|-----------|----------|-------------|
| [0.5× specified] | [value] | [value] | [value] |
| **[specified]** | **[value]** | **[value]** | **[value]** |
| [1.5× specified] | [value] | [value] | [value] |

**Pass criterion:** Extending the warm-up by 50% changes the primary KPI by less than 5%. If the change exceeds 5%, determine whether the warm-up is too short (startup artifact still present) or too long (discarding meaningful data from the period of interest).

```
Warm-up period specified: [N] minutes
Queue reaches operating pattern by: ~[M] minutes
Adequate? [Y/N — explain reasoning]
```

---

## Section 3: Convergence Across Replications

Run increasing numbers of replications for the Baseline scenario. A metric is converged when doubling the replication count changes the mean by less than 2%.

| Replications | Mean Wait | [Primary Percentile] | Utilisation | Stable? |
|--------------|-----------|---------------------|-------------|---------|
| [N/5] | [value] | [value] | [value] | — |
| [N/2] | [value] | [value] | [value] | [Y/N (% changes)] |
| [N] | [value] | [value] | [value] | [Y/N (% changes)] |
| [2N] | [value] | [value] | [value] | [Y/N (% changes)] |

```
[Document observations:

1. Which metrics converge first? Means converge faster than
   percentiles. Utilisation converges fastest of all because it
   depends on rates, not individual observations.

2. Which metrics converge last? Tail statistics (P90, P95, max)
   converge slowly because they depend on rare events. If your
   primary KPI is a percentile, you may need more replications
   than if it were a mean.

3. What is the 95% CI width for the primary KPI at your chosen
   replication count? Is it narrow enough to distinguish between
   scenarios? If the smallest scenario difference you expect is
   D units, the CI half-width should be well under D/2.]
```

**Final replication count:** [N] — [justify the choice. State the CI width for the primary KPI and confirm it's adequate for distinguishing scenarios.]

---

## Section 4: Scenario Comparison

All results from [N] replications per scenario. Bold the best performer per metric.

| Metric | Baseline | Scenario A | Scenario B | Scenario C |
|--------|----------|-----------|-----------|-----------|
| Mean wait (min) | [value] | [value] | [value] | [value] |
| [Primary percentile] wait (min) | [value] | [value] | [value] | [value] |
| Max wait (min) | [value] | [value] | [value] | [value] |
| Abandonment rate (%) | [value] | [value] | [value] | [value] |
| Mean utilisation | [value] | [value] | [value] | [value] |
| Entities served/day | [value] | [value] | [value] | [value] |
| Daily cost ($) | [value] | [value] | [value] | [value] |
| Cost per [KPI unit] reduced | — | [value] | [value] | [value] |

### Confidence interval overlap check

Scenarios whose CIs overlap on the primary KPI may not be statistically distinguishable at the 95% level.

| Comparison | CIs Overlap? | Interpretation |
|-----------|-------------|----------------|
| Baseline vs. A | [Yes/No] | [Significant or not] |
| Baseline vs. B | [Yes/No] | [Significant or not] |
| Baseline vs. C | [Yes/No] | [Significant or not] |

```
[For any overlapping CIs, discuss:
  - Is the improvement real but noisy, requiring more replications?
  - Would a paired comparison (same seeds) sharpen the estimate?
  - Is the practical difference large enough to matter even if
    statistical significance is borderline?

Overlapping CIs do not mean "no difference." They mean you can't
rule out that the difference is zero with 95% confidence at this
replication count.]
```

### Cost-effectiveness analysis

| Scenario | Extra Cost vs. Baseline | Primary KPI Improvement | Cost per Unit Improved | Rating |
|----------|------------------------|------------------------|----------------------|--------|
| A | [+$X/day] | [−Y min or −Z%] | [$X/unit] | [Best / Moderate / Poor] |
| B | [+$X/day] | [−Y min or −Z%] | [$X/unit] | [Rating] |
| C | [+$X/day] | [−Y min or −Z%] | [$X/unit] | [Rating] |

```
[Interpret the cost-effectiveness ratios:
  - Which scenario delivers the most improvement per dollar?
  - Is there a clear "knee" where additional spending produces
    sharply diminishing returns?
  - Does any scenario achieve improvement at zero cost (process
    change, demand management)?
  - Frame the comparison as a decision with trade-offs, not a
    single "winner."]
```

---

## Section 5: Results Summary

### One-Paragraph Finding

```
[Write 3–5 sentences that a decision-maker can read in 30 seconds.
Include: the recommended scenario, the primary KPI improvement
(before and after with percentage), the cost, and a brief mention
of the runner-up. Avoid jargon. Use concrete numbers.]
```

### Key Numbers

| Metric | Value | What It Means |
|--------|-------|---------------|
| Best scenario | [Name] | [One-line description] |
| Primary KPI improvement | [Before → After (−X%)] | [Plain-language interpretation] |
| Cost of improvement | [+$X/day or $X/period] | [What this buys] |
| Abandonment change | [Before → After] | [Entities recovered per day] |
| Cost-effectiveness | [$X per KPI-unit reduced] | [Best ratio of all scenarios] |
| Zero-cost alternative | [Name, if applicable] | [What it achieves] |

### Recommendation

```
[Frame the recommendation as a set of options with trade-offs,
not a single mandate. Decision-makers need to choose based on
their risk tolerance, budget, and strategic priorities.

Good format: "Implement [cheapest effective option] first. If
[specific condition], add [next option] at [incremental cost].
[Expensive option] is only justified if [specific strategic
priority]."

Bad format: "Scenario A is the best." (No trade-offs, no
context for the decision.)]
```

### Limitations

```
[List 4–6 limitations that a decision-maker should weigh when
acting on these results. Each limitation should name what was
excluded and how its inclusion might change the conclusion.

Common limitations to consider:
  1. Arrival data representativeness (sample period, seasonality)
  2. Resource homogeneity assumption (skill variation, training)
  3. Patience model simplicity (fixed vs. distributed thresholds)
  4. External factors not modelled (weather, competition, events)
  5. Intangible benefits not quantified (satisfaction, retention)
  6. Single-day vs. multi-day effects (fatigue, learning curves)
]
```

---

## Validation Checklist

Before presenting results to the decision-maker, confirm:

- [ ] Arrival rates match spec targets within 10% across all time windows
- [ ] Service time means match distribution parameters within 5%
- [ ] Utilisation aligns with queueing theory benchmark
- [ ] Any divergence from queueing theory is explained (transient, non-exponential service, etc.)
- [ ] Warm-up period removes startup artifact without discarding data from the period of interest
- [ ] Extending warm-up by 50% does not change the primary KPI by more than 5%
- [ ] Chosen replication count produces a CI width narrow enough to distinguish between scenarios
- [ ] Scenario rankings are stable across replication counts (no rank reversals)
- [ ] All key scenario differences are assessed for statistical significance (CI overlap)
- [ ] Cost-effectiveness calculated per unit of primary KPI improvement
- [ ] Results framed as trade-offs with actionable recommendations
- [ ] Limitations documented with directional impact on conclusions
