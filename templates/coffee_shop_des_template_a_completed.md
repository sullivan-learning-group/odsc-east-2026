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
