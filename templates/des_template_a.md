# DES Template A: Process and Resource Specification

## [Your Simulation Title]

Everything the simulation needs to know about entities, resources, queues, and process flow. This completed specification is the authoritative reference for the SimPy code generated in DES Template B.

**Key difference from Monte Carlo specs:** Monte Carlo specifications define inputs and a formula. DES specifications define a process flow with resources, queues, and time-dependent behavior. The "model" is a process, not an equation.

---

## Section 1: Problem Definition

**Business Question**

```
[State the specific question the simulation will answer. Include a
measurable target or constraint. Good business questions name both
the performance metric to optimise and the cost or resource constraint
that limits the solution space.

Examples:
  - "What staffing level minimises patient wait time while keeping
    daily labour cost under $X?"
  - "How many checkout lanes should be open per hour to keep P90
    wait below Y minutes during peak traffic?"
  - "Which maintenance schedule minimises machine downtime without
    exceeding Z hours of technician labour per week?"
]
```

**Key Performance Indicators (KPIs)**

```
Primary KPI:    [The single most important metric, with a specific
                target. Examples: P90 wait time < 5 min, throughput
                > 200 units/hr, utilisation between 70–85%.]
Secondary KPIs: [2–4 additional metrics that provide context.
                Examples: mean wait time, abandonment/walkaway rate,
                resource utilisation, queue length.]
Cost metric:    [How cost is measured per scenario. Examples: daily
                labour cost, hourly operating cost, cost per unit
                produced.]
```

**Key Assumptions**

```
[List 4–8 assumptions that bound the simulation. Each should be
specific enough that someone could challenge it. Good assumptions
name the data source ("based on 2 weeks of transaction logs") and
acknowledge what is NOT modelled ("no seasonal effects").

Common categories to address:
  1. Arrival pattern data source and representativeness
  2. Service time data source and fitting method
  3. Resource homogeneity (are all servers equally skilled?)
  4. External factors excluded (weather, holidays, competitors)
  5. Operating hours and boundary conditions
  6. Entity patience or tolerance behaviour
]
```

---

## Section 2: Entity Definition

**Entity type:** [e.g., Customer, Patient, Order, Vehicle, Job]

**Entity attributes:**

| Attribute | Type | Description | Set When |
|-----------|------|-------------|----------|
| arrival_time | Float (minutes from start) | Clock time the entity enters the system | Arrival |
| [attribute_2] | [Type: categorical, float, integer] | [What it represents and what it affects] | [Arrival / During service / etc.] |
| [attribute_3] | [Type] | [Description] | [When assigned] |

*Include every attribute that influences routing, service time, or queue behaviour. If an attribute determines which service time distribution to use, say so explicitly. If an attribute controls a balking or reneging decision, state the threshold or distribution here.*

---

## Section 3: Process Flow

```
Entity arrives (inter-arrival time drawn from [distribution]
for the current time window)

  → Assign [attribute]: [category_1] (X%), [category_2] (Y%), ...

  → [Decision point 1: describe the condition]
      → If [condition met]: [ACTION]. Entity leaves immediately.
        Record: [list of fields to capture]

      → Else: [ACTION — e.g., JOIN QUEUE]
        → Wait for available [resource] ([queue discipline])
        → Record: wait_time = service_start_time − arrival_time
        → [Resource] processes entity
            Service time drawn from [distribution]
            conditional on [attribute]:
              [category_1]: [Distribution(params)] → mean X min
              [category_2]: [Distribution(params)] → mean Y min
              [category_3]: [Distribution(params)] → mean Z min
        → Entity departs
          Record: wait_time, service_time,
                  total_time = wait_time + service_time,
                  outcome = "[completed/served/processed]"

[If the process has multiple stages (e.g., triage → treatment →
discharge), document each stage as a separate block with its own
resource, queue, and service time distribution. Show routing logic
between stages.]
```

*The process flow is the single most important section of this template. Every decision point, every queue, every resource interaction must appear here. If the code generator has to guess about routing logic or recording rules, the spec is incomplete.*

---

## Section 4: Resource Definitions

| Resource | Base Capacity | Schedule (if time-varying) | Notes |
|----------|--------------|---------------------------|-------|
| [Resource_1] | [integer] | [Yes/No — describe schedule] | [What this resource does, any constraints] |
| [Resource_2] | [integer] | [Yes/No — describe schedule] | [Notes] |

**Baseline schedule:**

| Resource | Time Window | Capacity |
|----------|-------------|----------|
| [Resource_1] | [Start–End] | [n] |
| [Resource_1] | [Start–End] | [n] |
| [Resource_1] | [Start–End] | [n] |

**Cost calculation:**

```
[Unit cost: $/hr per resource unit, or $/shift, or however cost
is measured in your domain.

Show the arithmetic for the baseline scenario:
  Window 1: n units × h hours = nh unit-hours
  Window 2: n units × h hours = nh unit-hours
  ...
  Total: N unit-hours × $/unit-hour = $X/day

This calculation anchors all scenario cost comparisons.]
```

---

## Section 5: Arrival Process

[Describe the arrival model. Most DES models use a non-homogeneous Poisson process (exponential inter-arrival times with rates that change by time window). State the distribution family, how rates were estimated, and the data source.]

| Time Window | Arrival Rate (entities/hr) | Inter-arrival Distribution | Mean Inter-arrival (min) | Window Total |
|-------------|---------------------------|--------------------------|-------------------------|-------------|
| [Window 1] | [rate] | [Distribution(params)] | [mean] | [total] |
| [Window 2] | [rate] | [Distribution(params)] | [mean] | [total] |
| [Window 3] | [rate] | [Distribution(params)] | [mean] | [total] |
| ... | ... | ... | ... | ... |
| **Total** | | | | **[daily total]** |

**Calibration note:** [Explain how the arrival rates connect to your data source. If you have historical daily totals, confirm that the sum across windows matches. If the rates come from a sample period, state the period and any adjustments made.]

---

## Section 6: Service Process

[Describe the service time model. State the distribution family and why it was chosen (e.g., "lognormal because service times are strictly positive and right-skewed"). State how parameters were estimated (time study, historical logs, expert judgment).]

| Entity Category | Probability | Service Time Distribution | Mean (min) | Median (min) | Source |
|----------------|------------|--------------------------|-----------|-------------|--------|
| [Category_1] | [p] | [Distribution(μ, σ)] | [mean] | [median] | [source] |
| [Category_2] | [p] | [Distribution(μ, σ)] | [mean] | [median] | [source] |
| [Category_3] | [p] | [Distribution(μ, σ)] | [mean] | [median] | [source] |

**Derived metrics:**

```
Weighted average service time: [calculation]
Service rate per resource unit: 60 / [weighted avg] = [rate] entities/hr
Max throughput ([n] units):    [n × rate] entities/hr
```

**Distribution choice justification:** [1–2 sentences explaining why this distribution family fits the data. Reference any goodness-of-fit tests, Q-Q plots, or domain knowledge that supports the choice.]

---

## Section 7: Queue Behaviour

```
Queue discipline:     [FIFO / Priority / other]
Maximum queue length: [Unlimited / physical cap of N]
Balking rule:         [e.g., entity leaves if queue length ≥ threshold.
                      State the threshold and whether it is fixed or
                      drawn from a distribution.]
Reneging rule:        [e.g., entity leaves after waiting X minutes.
                      State the patience distribution or "None".]
Jockeying:            [If multiple queues exist, can entities switch?
                      State the rule or "Not applicable".]
```

*If queue behaviour is simple (FIFO, no balking, no reneging), this section is short. If you have complex patience models or priority classes, document every rule. The code generator needs unambiguous logic.*

---

## Section 8: Simulation Parameters

```
Run length:      [Duration in hours/minutes, representing what real-world
                 period (one shift, one day, one week). State what happens
                 to entities in progress when the run ends.]
Warm-up period:  [Duration to discard. Explain why this value was chosen.
                 For systems that start empty, the warm-up removes the
                 startup transient. For non-stationary systems, be careful
                 not to discard the very dynamics you want to study.]
Replications:    [Number of independent runs per scenario. 30–100 is
                 typical. More replications produce tighter confidence
                 intervals but take longer to run.]
Random seeds:    [Seeding strategy. Common approach: sequential from a
                 base seed (e.g., seed_i = 42 + i). All scenarios should
                 use the same seed sequence so that differences reflect
                 design changes, not random variation.]
```

**Why [N] replications?** [Justify the replication count. How many entity-level observations does this produce? Is that sufficient for stable percentile estimates (P90, P95)? Template C will verify convergence by checking that doubling replications changes the mean by less than 2%.]

---

## Section 9: Scenarios to Compare

| Scenario | Description | What Changes | [Window 1] | [Window 2] | [Window 3] | Daily Cost |
|----------|-------------|-------------|-----------|-----------|-----------|-----------|
| Baseline | Current operations | Nothing (reference) | [config] | [config] | [config] | $[X] |
| A: [name] | [description] | [specific change] | [config] | [config] | [config] | $[X] |
| B: [name] | [description] | [specific change] | [config] | [config] | [config] | $[X] |
| C: [name] | [description] | [specific change] | [config] | [config] | [config] | $[X] |

**Scenario design rationale:**

```
[For each scenario, explain:
  1. What utilisation level it produces at the bottleneck
  2. Why this scenario is interesting (targeted fix vs. brute force
     vs. process improvement vs. demand management)
  3. The cost delta vs. baseline

Good scenario sets include:
  - A baseline (current state)
  - A targeted intervention at the bottleneck
  - A broader intervention for comparison
  - A process or demand-side change that avoids adding resources

Avoid testing only "add more resources" scenarios. Include at least
one scenario that changes the process rather than the capacity.]
```

**Expected outcome (to be verified by simulation):**

```
[State your hypothesis for which scenario will win and why. Include
back-of-envelope calculations. The simulation will confirm or
challenge these expectations. If the simulation disagrees with the
hand calculation, that divergence itself is informative.]
```

---

## Analytical Pre-Check

Before running the simulation, verify the spec is internally consistent with quick hand calculations.

**Utilisation by window (Baseline):**

| Window | Arrival Rate | Resources | Service Rate (per unit) | Utilisation (ρ) | Interpretation |
|--------|-------------|-----------|------------------------|----------------|----------------|
| [Window 1] | [rate] | [n] | [rate] | [ρ = λ/(n×μ)] | [Qualitative assessment] |
| [Window 2] | [rate] | [n] | [rate] | [ρ] | [Assessment] |
| ... | ... | ... | ... | ... | ... |

```
[Run at least these checks:

1. Utilisation at the bottleneck window: is it high enough to produce
   queuing (ρ > 0.7) or so high that the system is unstable (ρ > 1.0)?

2. Daily totals: does the sum of window arrivals match your expected
   daily volume? Is it consistent with your historical data?

3. Scenario deltas: does the proposed intervention actually change
   utilisation enough to matter? A 2% drop in utilisation won't produce
   a meaningful difference in waits.

4. Revenue/cost sanity: if the business question involves cost, verify
   that the daily revenue and cost numbers are internally consistent.

If any check fails, revise the spec before moving to Template B.]
```

---

## Data Source Summary

| Spec Element | Data Source | Notes |
|-------------|-----------|-------|
| [Arrival rates] | [Source and collection period] | [Any adjustments or caveats] |
| [Service times] | [Source and sample size] | [Distribution fitting method] |
| [Entity mix] | [Source] | [How probabilities were estimated] |
| [Queue thresholds] | [Source] | [Observation, survey, or assumption] |
| [Resource costs] | [Source] | [Wage rates, overhead, etc.] |
| [Revenue per entity] | [Source] | [Used for ROI calculations] |

*Every number in the spec should trace back to a data source. If a number is an assumption rather than a measurement, say so. Decision-makers need to know which inputs are grounded in data and which are judgment calls.*

---

## Checklist

Before moving to DES Template B (code generation), confirm:

- [ ] Business question is precise and includes a measurable target and constraint
- [ ] All KPIs defined with specific numeric targets
- [ ] Entity type and all relevant attributes specified
- [ ] Process flow documented with every decision point and recording rule
- [ ] Resources defined with time-varying schedules (if applicable)
- [ ] Arrival rates specified per time window with distributions
- [ ] Service times specified per entity category with distributions
- [ ] Queue behaviour documented (discipline, balking, reneging)
- [ ] Simulation parameters set (run length, warm-up, replications, seeds)
- [ ] At least 3 scenarios defined with cost calculations
- [ ] Analytical pre-check confirms internal consistency
- [ ] Bottleneck utilisation is high enough to produce observable queuing
- [ ] Scenario interventions change utilisation enough to produce measurable differences
- [ ] Data sources documented for every numeric input
