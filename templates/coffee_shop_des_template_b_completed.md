# DES Template B: Code Generation Prompt (Completed)

## Coffee Shop Staffing Simulation

This is the prompt you would hand to an LLM (or use as a brief for a human engineer) to produce the SimPy implementation of the Coffee Shop Staffing Simulation. It is the "completed" version of `des_template_b.md` — every placeholder has been filled in with the specifics of the coffee shop case study, and it is internally consistent with the completed Template A spec (`coffee_shop_des_template_a_completed.md`) and with the canonical implementation in `code/coffee_shop_des.py`.

The prompt is presented in two layers. The **Prompt body** is the literal text you would paste into an LLM. The **Facilitator notes** explain the choices behind each section so you can adapt the prompt to a different DES problem without losing the structure.

---

## Prompt body — paste this into the LLM

```
Generate a discrete event simulation in Python using SimPy based
on the following spec.

===============================================================
PROCESS AND RESOURCE SPEC
===============================================================
```

# DES Template A: Process and Resource Spec (Completed)

## Coffee Shop Staffing Simulation

Everything the simulation needs to know about entities, resources, queues, and process flow. This completed specification is the authoritative reference for the SimPy code generated in DES Template B.

**Key difference from MC Template A:** Monte Carlo specs define inputs and a formula. DES specs define a process flow with resources, queues, and time-dependent behavior. The "model" is a process, not an equation.

---

## Section 1: Problem Definition

**Business Question**

```
What staffing configuration minimizes customer wait time during the
morning rush while keeping daily labor cost under $350?
```

**Key Performance Indicators (KPIs)**

```
Primary KPI:    P90 wait time — the wait that 90% of customers experience
                or less. Target: under 5 minutes.
Secondary KPIs: Average wait time, walkaway rate (% of arriving customers
                who leave because the line is too long), barista utilization
                (fraction of time each barista is actively making drinks).
Cost metric:    Daily labor cost per scenario (baristas × hours × $17/hr).
```

**Key Assumptions**

```
1. Arrival patterns are based on two weeks of POS hourly traffic reports
   collected during a typical (non-holiday) period. The daily total of
   166 customers is consistent with a busy Friday or Saturday in the
   Chapter 4 dataset (Friday mean: 147, Saturday mean: 170).
2. Service times are based on a 3-day stopwatch study of ~200 orders,
   with lognormal distributions fit using the techniques from Chapter 3.
3. All baristas are equally skilled. Service time distributions do not
   vary by barista.
4. No holidays, special events, or competitor effects during the
   simulation period.
5. Weather is not modeled. The simulation represents a typical sunny/
   cloudy day. (Weather conditioning is reserved as an exercise.)
6. The shop operates from 7 AM to 5 PM (10-hour day). No customers
   arrive before 7 AM or after 5 PM, but customers already in the queue
   or being served at 5 PM complete their service.
```

---

## Section 2: Entity Definition

**Entity type:** Customer

**Entity attributes:**

| Attribute | Type | Description | Set When |
|-----------|------|-------------|----------|
| arrival_time | Float (minutes from 7 AM) | Clock time the customer enters the shop | Arrival |
| order_type | Categorical: drip / espresso / blended | Determines which service time distribution to draw from | Arrival (random draw based on order mix probabilities) |
| patience_threshold | Integer (queue length) | Fixed at 8 for all customers. If queue length ≥ 8 at arrival, customer balks. | Arrival (constant) |

---

## Section 3: Process Flow

```
Customer arrives (inter-arrival time drawn from exponential distribution
for the current time window)

  → Assign order_type: drip (30%), espresso (50%), blended (20%)

  → Check queue length
      → If queue length ≥ 8: BALK. Customer leaves immediately.
        Record: arrival_time, order_type, outcome = "walkaway"

      → Else: JOIN QUEUE
        → Wait for available barista (FIFO)
        → Record: wait_time = service_start_time − arrival_time
        → Barista prepares order
            Service time drawn from lognormal distribution
            conditional on order_type:
              drip:     Lognormal(μ=0.7, σ=0.3)   → mean 2.1 min
              espresso: Lognormal(μ=1.2, σ=0.35)  → mean 3.5 min
              blended:  Lognormal(μ=1.5, σ=0.3)   → mean 4.7 min
        → Customer departs
          Record: wait_time, service_time,
                  total_time = wait_time + service_time,
                  outcome = "served"
```

---

## Section 4: Resource Definitions

| Resource | Base Capacity | Schedule (if time-varying) | Notes |
|----------|--------------|---------------------------|-------|
| Barista | 2 | Yes — varies by time window and scenario | Single resource type. Each barista handles the full service process (take order + prepare drink). |

**Baseline staffing schedule:**

| Resource | Time Window | Capacity |
|----------|-------------|----------|
| Barista | 7:00–9:00 AM | 2 |
| Barista | 9:00 AM–2:00 PM | 2 |
| Barista | 2:00–5:00 PM | 1 |

**Labor cost calculation:**

```
Hourly wage: $17/hr per barista
Baseline daily cost: (2 × 2hrs) + (2 × 5hrs) + (1 × 3hrs) = 17 barista-hours
                     17 × $17 = $289/day

Wait — let me recompute. The midday window is 9 AM–2 PM = 5 hours.
  Morning:   2 baristas × 2 hours  =  4 barista-hours
  Midday:    2 baristas × 5 hours  = 10 barista-hours
  Afternoon: 1 barista  × 3 hours  =  3 barista-hours
  Total:     17 barista-hours × $17/hr = $289/day
```

*Note: The original outline listed $306/day for baseline because it used a different time-window split (9–2 as two separate windows). With the consolidated 5-window arrival schedule mapped to a 3-shift staffing model, the baseline cost is $289/day. The scenarios below use this corrected arithmetic.*

**Corrected labor costs:**

| Scenario | Morning (7–9) | Midday (9–2) | Afternoon (2–5) | Barista-Hours | Daily Cost |
|----------|--------------|-------------|-----------------|--------------|-----------|
| Baseline | 2 | 2 | 1 | 17 | $289 |
| A: Rush boost | 3 | 2 | 1 | 19 | $323 |
| B: All-day 3 | 3 | 3 | 2 | 27 | $459 |
| C: Rush+reg (simplified) | 2 | 2 | 1 | 17 | $289 |

---

## Section 5: Arrival Process

Arrivals follow a Poisson process (exponential inter-arrival times) with rates that change by time of day. Rates are derived from two weeks of POS hourly traffic reports. The daily total of 166 customers is consistent with a busy Friday or Saturday in the Chapter 4 dataset.

| Time Window | Arrival Rate (customers/hr) | Inter-arrival Distribution | Mean Inter-arrival (min) | Window Total |
|-------------|---------------------------|--------------------------|-------------------------|-------------|
| 7:00–9:00 AM | 30 | Exponential(λ = 30/hr) | 2.0 | 60 |
| 9:00–11:00 AM | 14 | Exponential(λ = 14/hr) | 4.3 | 28 |
| 11:00 AM–1:00 PM | 18 | Exponential(λ = 18/hr) | 3.3 | 36 |
| 1:00–3:00 PM | 9 | Exponential(λ = 9/hr) | 6.7 | 18 |
| 3:00–5:00 PM | 12 | Exponential(λ = 12/hr) | 5.0 | 24 |
| **Total** | | | | **166** |

**Calibration note:** The Chapter 4 dataset contains 2 years of daily customer counts with weekday mean = 136, Friday mean = 147, and Saturday mean = 170. A daily total of 166 falls between Friday and Saturday, representing a typical busy day. The morning rush (7–9 AM) accounts for 36% of daily traffic, which is consistent with observed patterns in coffee shop POS data.

---

## Section 6: Service Process

Service times follow lognormal distributions, conditional on order type. Parameters were estimated by fitting lognormal distributions to ~200 timed observations collected over a 3-day stopwatch study, using the distribution fitting techniques from Chapter 3.

| Order Type | Probability | Service Time Distribution | Mean (min) | Median (min) | Source |
|-----------|------------|--------------------------|-----------|-------------|--------|
| Drip coffee | 0.30 | Lognormal(μ = 0.7, σ = 0.3) | 2.1 | 2.0 | Stopwatch study |
| Espresso drink | 0.50 | Lognormal(μ = 1.2, σ = 0.35) | 3.5 | 3.3 | Stopwatch study |
| Blended/specialty | 0.20 | Lognormal(μ = 1.5, σ = 0.3) | 4.7 | 4.5 | Stopwatch study |

**Derived metrics:**

```
Weighted average service time: 0.30(2.1) + 0.50(3.5) + 0.20(4.7) = 3.33 min
Service rate per barista:      60 / 3.33 = 18.0 customers/hr
Max throughput (2 baristas):   36.0 customers/hr
Max throughput (3 baristas):   54.0 customers/hr
```

**Why lognormal?** Service times are strictly positive and right-skewed — most drinks take close to the median time, but occasional complex orders or equipment delays produce a long right tail. Lognormal captures this shape. The stopwatch data confirmed the fit via Q-Q plots (Chapter 3 techniques).

---

## Section 7: Queue Behavior

```
Queue discipline:     FIFO (first-in, first-out)
Maximum queue length: Unlimited (no physical cap on the line)
Balking rule:         Customer leaves immediately if queue length ≥ 8
                      at time of arrival. Recorded as a walkaway.
Reneging rule:        None. Once a customer joins the queue, they wait
                      until served. (A patience distribution is reserved
                      as an end-of-chapter exercise.)
```

---

## Section 8: Simulation Parameters

```
Run length:      10 hours (7:00 AM to 5:00 PM), representing one business day.
                 Customers in service or in queue at 5:00 PM complete
                 normally; no new arrivals after 5:00 PM.
Warm-up period:  30 minutes. Discard all events before 7:30 AM to avoid
                 startup bias (empty queue, idle servers at t=0 are not
                 representative of steady-state operations).
Replications:    50 independent runs per scenario. Each replication uses
                 a different random seed to produce an independent sample
                 of the day's operations.
Random seeds:    Sequential from base seed 42. Replication i uses seed
                 42 + i. All scenarios use the same seed sequence so that
                 differences between scenarios reflect staffing changes,
                 not random variation.
```

**Why 50 replications?** Each replication simulates one day with ~166 customer arrivals. With 50 replications, we have ~8,300 simulated customer experiences per scenario, which is sufficient to produce tight 95% confidence intervals on mean wait time (typically ±0.3 minutes) and stable P90 estimates. Convergence will be verified in DES Template C by checking that doubling replications changes the mean by less than 2%.

---

## Section 9: Scenarios to Compare

| Scenario | Description | What Changes | Morning (7–9) | Midday (9–2) | Afternoon (2–5) | Daily Cost |
|----------|-------------|-------------|--------------|-------------|-----------------|-----------|
| Baseline | Current operations | Nothing — this is the reference | 2 baristas | 2 baristas | 1 barista | $289 |
| A: Rush boost | Add one barista during morning rush only | +1 barista for 2 hours (7–9 AM) | 3 baristas | 2 baristas | 1 barista | $323 |
| B: All-day three | Full staffing increase across all windows | +1 barista in every window | 3 baristas | 3 baristas | 2 baristas | $459 |
| C: Process improvement | Streamline morning workflow (dedicated register, prep staging) | Service times reduced by 15% during 7–9 AM only. No additional labor. | 2 baristas (faster) | 2 baristas | 1 barista | $289 |

**Scenario design rationale:**

- **Baseline** establishes the reference point. Morning rush utilization = 30 / (2 × 18.0) = 83%. At this level, random arrival bursts will regularly push the queue past the balking threshold.
- **Scenario A** is the targeted fix: one extra barista during the 2-hour rush window only. Morning utilization drops to 30 / (3 × 18.0) = 56%. Cost increase: $34/day.
- **Scenario B** is the "throw resources at it" approach. Eliminates queuing everywhere but at significant cost (+$170/day over baseline). Tests whether the additional investment beyond Scenario A is justified.
- **Scenario C** tests whether a process change (no extra labor cost) can achieve similar results to Scenario A. The 15% service time reduction represents operational improvements like a dedicated order-taking position, pre-staged ingredients, or workflow reorganization. This keeps service time distributions identical to baseline except that during the 7–9 AM window, each drawn service time is multiplied by 0.85.

**Expected outcome (to be verified by simulation):**

```
Scenario A is expected to be the cost-effective winner. At $34/day in
additional labor, even a modest reduction in walkaways (from ~14% to
~2%) would recover ~$147 × (0.14 − 0.02) / 0.14 ≈ $126/day in revenue
at $7.00 per lost customer. Net benefit: ~$92/day.

Scenario C is the interesting comparison — can process improvement match
the effect of additional labor? If the 15% service time reduction brings
morning utilization from 83% to approximately 71%, waits will decrease
but may not drop as dramatically as adding a full barista.
```

---

## Analytical Pre-Check

Before running the simulation, verify the spec is internally consistent with quick hand calculations.

**Utilization by window (Baseline):**

| Window | Arrival Rate | Baristas | Service Rate (per barista) | Utilization (ρ) | Interpretation |
|--------|-------------|----------|---------------------------|----------------|----------------|
| 7–9 AM | 30/hr | 2 | 18.0/hr | 0.83 | Heavy load. Queues will build during arrival bursts. |
| 9–11 AM | 14/hr | 2 | 18.0/hr | 0.39 | Light. Queues from morning rush will drain quickly. |
| 11 AM–1 PM | 18/hr | 2 | 18.0/hr | 0.50 | Moderate. Occasional short waits. |
| 1–3 PM | 9/hr | 2 | 18.0/hr | 0.25 | Very light. Near-zero waits. |
| 3–5 PM | 12/hr | 1 | 18.0/hr | 0.67 | Moderate. Single barista handles it but has less slack than midday. |

**Daily totals check:**

```
Expected customers served (no balking): 166
Expected customers served (with balking): 166 × (1 − walkaway_rate)
  Walkaway rate will be determined by simulation, but at ρ = 0.83 with
  exponential arrivals and lognormal service times, we expect occasional
  queue lengths exceeding 8 during the morning rush.
Expected daily revenue (no balking): 166 × $7.00 = $1,162
  Consistent with Ch04 Saturday mean revenue of $1,206.
```

**Scenario A morning rush check:**

```
Utilization: 30 / (3 × 18.0) = 0.56
At ρ = 0.56, queue buildup is rare. P90 wait should be well under 5 min.
Cost increase: $323 − $289 = $34/day
Revenue recovery if walkaways drop from ~14% to ~1%:
  (0.14 − 0.01) × 166 × $7.00 = $151/day
Net benefit: ~$117/day
```

---

## Data Source Summary

| Spec Element | Data Source | Chapter Reference |
|-------------|-----------|-------------------|
| Daily customer volume (anchor) | Ch04 coffee_shop_daily_operations.csv | Chapter 4 EDA |
| Revenue per customer ($7.00) | Ch04 coffee_shop_daily_operations.csv | Chapter 4 EDA |
| Operating costs / break-even | Ch04 coffee_shop_daily_operations.csv | Chapter 4 simulation |
| Hourly arrival rates | POS hourly traffic reports (2 weeks) | Introduced in Chapter 5 |
| Order type mix (30/50/20) | POS product mix report | Introduced in Chapter 5 |
| Service time distributions | Stopwatch time study (~200 orders, 3 days) | Introduced in Chapter 5, fit using Chapter 3 techniques |
| Balking threshold (queue > 8) | Owner observation | Introduced in Chapter 5 |
| Barista hourly wage ($17/hr) | Stated operating assumption | Introduced in Chapter 5 |

---

## Checklist

Before moving to DES Template B (code generation), confirm:

- [x] Business question is precise and includes a specific cost threshold ($350/day)
- [x] All KPIs defined with clear targets (P90 wait < 5 min)
- [x] Entity type and attributes specified
- [x] Process flow documented with decision points (balking logic)
- [x] Resources defined with time-varying schedules
- [x] Arrival rates specified per time window with distributions
- [x] Service times specified per order type with distributions
- [x] Queue behavior documented (FIFO, balking at 8, no reneging)
- [x] Simulation parameters set (10 hrs, 30 min warmup, 50 reps, seed 42)
- [x] Scenarios defined with cost calculations
- [x] Analytical pre-check confirms internal consistency
- [x] Data sources documented with chapter references
- [x] Daily totals consistent with Chapter 4 data (166 ≈ busy Fri/Sat)
- [x] Morning rush utilization (83%) high enough to demonstrate queuing effects
- [x] Scenario A utilization (56%) low enough to show clear improvement


```
===============================================================
TECHNICAL REQUIREMENTS
===============================================================

Libraries: simpy, numpy, scipy.stats, pandas, matplotlib
Random seed: base seed 42 (increment per replication: replication i uses seed 42 + i)
Store per-replication summary statistics in a DataFrame.

Additional library notes:

  - Only the standard set above is required. No networkx (single resource type),
    no scipy.optimize (no parameter fitting at runtime — fits were done offline
    in Block 2 and the parameters are already in the spec), no seaborn.
  - The lognormal service-time distributions use scipy.stats.lognorm with the
    real-space mean reported as exp(mu + sigma**2 / 2). Verify this convention
    in the implementation — it is the most frequent source of service-time
    errors. The reference implementation uses numpy.random.Generator.lognormal
    directly, which takes (mean, sigma) of the underlying normal in log-space
    (matching the spec's μ and σ).
  - Inter-arrival times are exponential at the rate that applies to the
    current simulation clock. Use np.random.Generator.exponential with
    scale = 60 / rate_per_hour to get inter-arrival times in minutes.

===============================================================
CODE ARCHITECTURE
===============================================================

Organise the code into these functions:

1. customer_process(env, name, baristas, scenario, rng, metrics)
   - The customer lifecycle from arrival through departure.
   - Implements the balking decision (queue length >= 8 -> walkaway).
   - Records wait_time, service_time, total_time, and outcome
     ('served' or 'walkaway') for every customer that enters the shop.
   - The order_type is assigned at arrival based on the 30/50/20 mix
     and determines which lognormal distribution the service time
     is drawn from.
   - Service time is multiplied by scenario.service_time_multiplier
     for the current time window (used by Scenario C: 0.85 multiplier
     during 7:00-9:00 AM, 1.0 elsewhere).

2. customer_generator(env, baristas, scenario, rng, metrics)
   - Generates customer arrivals with time-varying rates per the
     ARRIVAL_WINDOWS schedule (30/14/18/9/12 cust/hr by 2-hour window).
   - Draws inter-arrival times from Exponential(scale = 60 / current_rate).
   - Stops generating arrivals at simulation minute 600 (5 PM close).
     Customers in queue or in service at minute 600 finish normally.

3. run_single_replication(scenario, seed)
   - Creates a fresh SimPy environment and Resource(capacity=initial)
     for the baristas.
   - Initialises capacity from the first window of scenario.staffing_schedule.
   - Starts background processes for:
     a. Dynamic capacity changes — at each schedule boundary, modify
        baristas._capacity to the new value and call baristas._trigger_get
        so any waiting requests are reconsidered. (SimPy's Resource does
        not natively support dynamic capacity; this is the standard
        workaround.)
     b. Queue length monitoring — sample (env.now, len(baristas.queue))
        every 1.0 simulated minutes for the queue trace plot.
   - Runs for 600 simulated minutes plus a drain phase (run until all
     customers have departed).
   - Returns (per-customer DataFrame, queue trace list).

4. summarise_replication(df, scenario)
   - Filters df to served and walkaway customers with arrival_time >= 30
     (the warm-up cutoff).
   - Returns a dict with: mean_wait, p50_wait, p90_wait, max_wait,
     n_arrivals, n_served, n_walkaways, walkaway_rate, daily_cost,
     and util_<start>_<end> per staffing window
     (computed as total busy time / (capacity * window duration)).

5. run_scenario(scenario, n_replications)
   - Outer loop over replications with sequential seeds (42, 43, ..., 91).
   - Calls run_single_replication and summarise_replication for each seed.
   - Stores the FIRST replication's per-customer DataFrame and queue trace
     for diagnostic plots; later replications keep only the summary row.
   - Returns (summary_df with one row per replication, first_customer_df,
     first_queue_trace).

6. compare_scenarios(results_dict)
   - results_dict: {scenario_name: summary_df, ...}
   - Builds a side-by-side comparison table with mean and 95% CI for:
     mean_wait, p90_wait, walkaway_rate, n_served, daily_cost.
   - Computes cost-effectiveness metrics:
     - Extra labour cost vs. Baseline ($/day).
     - Walkaway reduction vs. Baseline (% and customers/day at 166 daily).
     - Estimated revenue gain at $7.00 per recovered customer.
     - Net daily benefit.
     - Pass flags for the two budget/KPI gates: cost <= $350/day and
       p90_wait < 5 min.

Supporting structures:

  Use a `@dataclass` named Scenario with fields:
    name: str
    description: str
    staffing_schedule: List[Tuple[int, int, int]]   # (start_min, end_min, n)
    service_time_multiplier: Dict[Tuple[int,int], float] = field(
        default_factory=lambda: {})
  with a property `daily_cost` that computes
    sum((end - start) / 60 * n_baristas * 17 for (start, end, n) in schedule)

  Define the four scenarios as a module-level dict, SCENARIOS, keyed by
  the scenario name string used in the spec. Schedule tuples use minutes
  from 7 AM open: 0 = 7 AM, 120 = 9 AM, 420 = 2 PM, 600 = 5 PM. The three
  staffing windows are therefore 7-9 AM (0-120), 9 AM-2 PM (120-420),
  and 2-5 PM (420-600). This matches the prose schedule in Section 4
  of the Template A spec and the canonical implementation in
  code/coffee_shop_des.py.
    "Baseline":              [(0,120,2), (120,420,2), (420,600,1)]   $289
    "A: Rush boost":         [(0,120,3), (120,420,2), (420,600,1)]   $323
    "B: All-day 3":          [(0,120,3), (120,420,3), (420,600,2)]   $459
    "C: Process improvement": same schedule as Baseline, plus
                              service_time_multiplier {(0,120): 0.85} $289

  These cost numbers must match the labour-cost arithmetic in Section 4
  of the Template A spec exactly. If the generated code's daily_cost
  differs from the spec, the code is wrong. The most likely cause of
  a $306 baseline (instead of $289) is using 480 as the second-window
  boundary in minutes, which would encode 9 AM-3 PM and 3-5 PM rather
  than the spec's 9 AM-2 PM and 2-5 PM.

===============================================================
REQUIRED OUTPUTS
===============================================================

Per-replication statistics (one row per replication, four scenarios = 200 rows total at N=50):

  - Mean wait time (minutes)
  - P50 (median) wait time (minutes)
  - P90 wait time (minutes) — primary KPI
  - Max wait time (minutes)
  - Number of arrivals after the warm-up cutoff
  - Number of customers served
  - Number of walkaways
  - Walkaway rate = n_walkaways / n_arrivals
  - Mean barista utilisation per staffing window (3 columns:
    util_0_120, util_120_420, util_420_600)
  - Mean service time (sanity check against the spec's 3.33 min weighted mean)
  - Daily labour cost ($) — copied from the Scenario object

Cross-replication statistics (one row per scenario in the comparison table):

  For each metric above, compute across the 50 replications:
    - Mean
    - 95% confidence interval using t.ppf(0.975, n-1) * stderr.
      Use scipy.stats.t (not normal — n=50 is borderline).
    - Min and max across replications

Plots (required, save as PNGs at 150 DPI):

  1. queue_over_time.png — single representative replication, one line per
     scenario overlaid. Mark the BALK_THRESHOLD (queue=8) as a dashed
     horizontal line. Shade the 7-9 AM rush window. X-axis labelled in
     clock time (7-9-11-13-15-17), not minutes from zero.

  2. wait_histograms.png — one panel per scenario (2x2 grid), histogram of
     all served customers' wait times. Mark the per-scenario mean and P90
     as vertical lines. X-axis limit fixed at 0-12 minutes across all
     panels for direct visual comparison.

  3. scenario_comparison.png — four-panel bar chart, one panel per KPI
     (Mean Wait, P90 Wait, Walkaway Rate, Customers Served / Day).
     95% CI error bars on each bar. P90 panel shows the 5-minute target
     as a dashed red line. Walkaway panel uses a percentage formatter
     on the y-axis.

  4. utilisation_heatmap.png — 4 scenarios × 3 windows heatmap. Annotate
     each cell with the utilisation percentage. Use YlOrRd colormap with
     0.0-1.0 fixed colour range so cross-scenario comparisons are visually
     valid.

Plots (optional):

  - Wait time by order type (boxplot — drip / espresso / blended).
  - Cost vs. P90 wait scatter (one point per scenario), to display the
    cost-effectiveness frontier.

===============================================================
CODE QUALITY GUIDELINES
===============================================================

  1. Warm-up filtering. Apply the 30-minute cutoff when computing
     summary statistics, NOT during the run. Customers that arrive
     before minute 30 still occupy resources and affect queue lengths,
     but their individual wait/service records are excluded from the
     reported metrics.

  2. End-of-run drain. The arrival generator stops at minute 600.
     Let the simulation continue until all customers in queue or in
     service have departed. Do not call env.run(until=600); call
     env.run() (no until) and let the processes terminate naturally.

  3. Reproducibility. Every random draw must use the replication's
     seeded numpy.random.Generator (np.random.default_rng(seed)).
     Never use np.random.<func>() directly. Pass the rng object to
     every function that draws random numbers (assign_order_type,
     draw_service_time, generate inter-arrival).

  4. Resource capacity changes. SimPy's Resource does not natively
     support dynamic capacity. Implement a background process
     `staffing_manager(env, baristas, schedule)` that yields env.timeout
     to each schedule boundary, then mutates baristas._capacity. This
     is the standard SimPy idiom for time-varying staffing.

  5. Recording. Capture every customer outcome — both 'served' and
     'walkaway'. Walkaways have wait_time = NaN, service_time = NaN.
     Filter to outcome == 'served' before computing mean/percentile
     wait stats; count walkaways separately for the walkaway rate.

  6. Scenario isolation. Each replication creates a fresh SimPy
     environment, fresh Resource, fresh metrics list, fresh rng.
     No state carries over between replications. The seed sequence
     is the same across scenarios so that scenario differences
     reflect staffing changes, not RNG noise.

  7. Print progress. After each scenario finishes its 50 replications,
     print a one-line summary:
       "Mean wait: X min, P90: Y min, walkaways: Z%, cost: $W/day"
     with 95% CIs. This lets the user monitor the run and catch
     obvious errors (e.g., zero walkaways for the Baseline would
     indicate a balking-logic bug).

===============================================================
MAIN EXECUTION
===============================================================

The main() function should:

  1. Loop over all four scenarios in SCENARIOS dict order
     (Baseline, A: Rush boost, B: All-day 3, C: Process improvement).
  2. For each, run 50 replications with seeds 42, 43, ..., 91.
  3. Print the per-scenario one-line summary as it completes.
  4. Build and print the cross-scenario comparison table (formatted
     with pandas.DataFrame.to_string(index=False)).
  5. Compute and print the cost-effectiveness analysis: for each
     non-baseline scenario, print extra cost, walkaway reduction,
     estimated revenue gain (at $7.00/customer × 166 customers/day),
     net daily benefit, and the two pass/fail gates (under $350?
     P90 < 5 min?).
  6. Generate and save all four required plots.
  7. Save the per-replication summary data to replication_summaries.csv
     (200 rows × ~15 columns).
  8. Return all_summaries, all_traces, all_customers as a tuple for
     interactive exploration in Jupyter or REPL.

The script must be runnable from the command line:
    python coffee_shop_des.py

and produce all outputs (console summary, CSV, four PNGs) in a single
end-to-end run with no further user input. The expected run time on
modern laptops is 30-60 seconds for the full 4 scenarios × 50 reps.

Expected baseline summary (from a verified run, useful as a sanity
check while developing):
  Mean wait:     1.97 min  (95% CI ~ 1.68 to 2.26)
  P90 wait:      6.38 min  (95% CI ~ 5.44 to 7.31)
  Walkaway rate: 0.8%      (95% CI ~ 0.3% to 1.3%)
  Avg served:    149.4 / day
  Daily cost:    $289

If your generated code produces materially different baseline
numbers, you have a bug. The most likely culprits, in order:

  1. Wrong inter-arrival distribution (uniform instead of exponential,
     or wrong rate).
  2. Lognormal parameterisation mismatch (treating μ as the real-space
     mean instead of the log-space parameter).
  3. Balking check in the wrong place (after yield req instead of
     before — this is the seeded-bug variant for Block 5).
  4. Warm-up applied during the run instead of in post-processing.
  5. Resource capacity not actually changing at schedule boundaries.
```

---

## Facilitator notes — why this prompt is structured this way

### Why paste the entire Template A rather than summarise it

The blank Template B says "do not summarise or abbreviate." The completed Template B follows the same rule. LLMs are very good at code generation when given precise numerical specs and very bad at it when given prose summaries. Pasting the full Template A gives the LLM the exact distribution parameters, time windows, and balking threshold values to reference — and it gives you a paper trail when you later want to ask *why does the espresso service time distribution use μ=1.2?* The answer is in the spec the prompt embedded.

### Why the technical-requirements section names specific failure modes

The bullet about lognormal real-space-vs-log-space convention is there because that is the single most common source of service-time bugs. By naming the failure mode in the prompt, you bias the generator toward writing the conversion correctly the first time, and you make the bug easy to spot if it does occur — you can grep the generated code for `lognormal` and check the call signature. The same logic applies to the inter-arrival exponential parameterisation: scipy and numpy use `scale = 1/rate`, but it's easy for an LLM to flip the convention if not warned.

### Why the architecture section names exact function signatures

The reference implementation `code/coffee_shop_des.py` uses these exact names. Specifying them in the prompt makes the generated code match the reference closely enough that participants can swap snippets between the two without renaming half the variables. It also gives the simulation a clean separation of concerns — you can substitute a different `customer_process` (for example, one with reneging) without touching the generator or replication driver.

### Why the SCENARIOS dict and dataclass are dictated rather than left to the LLM

The four scenarios are the experiment, and the experiment design is fixed in the spec. If the LLM invents its own scenario representation, every downstream piece of code has to be inspected for whether it uses the right fields. Dictating the dataclass keeps the API stable and lets a participant who copies the LLM-generated code into a notebook see the same `Scenario(name=..., staffing_schedule=...)` calls they would see in the reference implementation.

### Why the expected-baseline summary is included

This is the single most important block in the prompt for catching errors fast. A participant who runs the LLM-generated code and sees baseline mean wait of 0.3 min knows immediately that something is wrong with arrival rates or balking — they don't have to wait until Block 5 to discover that the model is broken. The numbers are taken from a verified production run of the canonical implementation. If you ever change the spec, regenerate them.

### Why "the most likely culprits" list is at the end of the prompt

Negative knowledge is more compressible than positive knowledge. Telling the LLM "make sure the balking check is BEFORE the resource request" is one bullet. Telling it the same thing positively requires reproducing the entire process flow. The numbered list also doubles as a triage checklist for the human running the prompt: when the run produces wrong numbers, walk down the list and check each candidate.

### What this prompt deliberately does NOT include

It does not include the validation protocol from Template C. Code generation and validation are different tasks for different reasons. The code-generation step produces something that runs; the validation step proves the run is trustworthy. Mixing the two in one prompt produces code that hardcodes its own validation thresholds — a bad pattern, because the thresholds belong with the analysis, not with the simulation engine.

It also does not include the LLM-assisted spec-compliance review from Block 5. That is a separate prompt against the *generated code*, not a part of generating the code. Keeping Block 4 (generation) and Block 5 (validation against the spec) separate is the entire point of the spec-driven workflow.

---

## Cross-references

- Spec: `coffee_shop_des_template_a_completed.md`
- Reference implementation: `../code/coffee_shop_des.py`
- Validation results: `coffee_shop_des_template_c_completed.md`
- Bug-seeded variant (used in Block 5): `../code/coffee_shop_des_buggy.py`
