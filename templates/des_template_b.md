# DES Template B: Code Generation Prompt

Generate a discrete event simulation in Python using SimPy based
on the following spec.

===============================================================
PROCESS AND RESOURCE SPEC
===============================================================

[Paste the completed DES Template A here. The code generator needs
the full specification as context: problem definition, entity
attributes, process flow, resource definitions, arrival rates,
service time distributions, queue behaviour, simulation parameters,
and scenario definitions.

Do not summarise or abbreviate. The code generator will reference
specific distribution parameters, threshold values, and recording
rules directly from the spec.]

===============================================================
TECHNICAL REQUIREMENTS
===============================================================

Libraries: simpy, numpy, scipy.stats, pandas, matplotlib
Random seed: [base seed from Template A] (increment per replication)
Store per-replication summary statistics in a DataFrame

Additional library notes:

```
[If your simulation requires specialised libraries beyond the
standard set, list them here with a brief justification:
  - networkx: for routing through a network topology
  - scipy.optimize: for parameter fitting or optimisation
  - seaborn: for specific plot types

If your entity categories or service time distributions require
scipy.stats distributions beyond lognormal and exponential, name
them explicitly so the code generator imports the right modules.]
```

===============================================================
CODE ARCHITECTURE
===============================================================

Organise the code into these functions:

1. entity_process(env, name, resources, metrics)
   - The entity lifecycle from arrival through departure
   - Implement every decision point from the process flow
     (balking, reneging, routing, priority)
   - Record wait time, service time, total time in system
   - Record outcome for every entity (served, balked, reneged,
     or any other terminal state from the process flow)

2. entity_generator(env, resources, metrics)
   - Generates entity arrivals with time-varying rates
   - Draws inter-arrival times from the correct distribution
     for the current time window
   - Assigns entity attributes (category, patience, priority)
     according to the probabilities in the spec
   - Stops generating arrivals after the run length is reached

3. run_single_replication(scenario, seed)
   - Creates SimPy environment and resources
   - Initialises resource capacities from the scenario's
     staffing/capacity schedule
   - Starts background processes for:
     a. Dynamic capacity changes (if resources are time-varying)
     b. Queue length monitoring (sample every minute for plotting)
   - Runs one complete simulation
   - Returns per-entity metrics as a DataFrame and a queue trace
     for plotting

4. run_scenario(scenario, n_replications)
   - Outer loop over replications with sequential seeds
   - Calls run_single_replication for each seed
   - Computes per-replication summary statistics (see Required
     Outputs below)
   - Stores the first replication's entity-level data and queue
     trace for diagnostic plots
   - Returns a summary DataFrame with one row per replication

5. compare_scenarios(results_dict)
   - Accepts a dict mapping scenario name → summary DataFrame
   - Builds a side-by-side comparison table with 95% confidence
     intervals for every KPI
   - Computes cost-effectiveness metrics (cost per unit of
     primary KPI improvement)
   - Calls visualisation functions

Supporting structures:

```
[Define a Scenario dataclass or dictionary structure that holds:
  - name and description
  - capacity schedule: list of (start_time, end_time, capacity)
  - service time multipliers (if any scenario modifies service
    speed rather than capacity)
  - a method to compute daily/shift cost from the schedule

This structure should make it trivial to add new scenarios without
changing the simulation logic.]
```

===============================================================
REQUIRED OUTPUTS
===============================================================

Per-replication statistics:

```
For each independent run, compute and store:
  - Mean wait time
  - Median (P50) wait time
  - P90 wait time (or whichever percentile is your primary KPI)
  - Maximum wait time
  - Total entities arrived (after warm-up)
  - Total entities served
  - Total entities that balked/reneged (by outcome type)
  - Abandonment rate (balked + reneged) / total arrived
  - Resource utilisation by time window:
      utilisation = total busy time / (capacity × window duration)
  - Mean service time (as a sanity check against the spec)
```

Cross-replication statistics:

```
For each metric above, compute across all replications:
  - Mean
  - 95% confidence interval (using t-distribution with n-1 df)
  - Min and max across replications

Present these in a summary table, one row per scenario.
```

Plots (required):

```
1. Queue length over time (single representative run)
   - One line per scenario, overlaid on the same axes
   - Mark the balking threshold (if applicable) as a dashed
     horizontal line
   - Shade the high-demand time window(s)
   - X-axis: clock time (not minutes from zero)

2. Wait time histogram by scenario
   - One panel per scenario (2×2 or similar grid)
   - Mark the mean and P90 as vertical lines
   - Use consistent x-axis limits across panels

3. Scenario comparison bar chart with error bars
   - One panel per KPI (mean wait, P90 wait, abandonment rate,
     entities served)
   - 95% CI error bars on each bar
   - Mark any KPI target as a dashed horizontal line

4. Resource utilisation by time window
   - Heatmap or grouped bar chart
   - Scenarios on one axis, time windows on the other
   - Annotate cells with utilisation percentages
```

Plots (optional, include if relevant):

```
- Utilisation heatmap by time-of-day and scenario
- Abandonment rate vs. threshold sensitivity analysis
- Wait time by entity category (box plot or violin plot)
- Cost-effectiveness frontier (cost on x-axis, primary KPI on
  y-axis, one point per scenario)
```

===============================================================
CODE QUALITY GUIDELINES
===============================================================

```
1. Warm-up filtering: apply the warm-up cutoff when computing
   summary statistics, not during the simulation run itself.
   Entities that arrive during warm-up should still flow through
   the system (they occupy resources and affect queue lengths),
   but their individual metrics are excluded from reporting.

2. End-of-run drain: after the arrival generator stops (end of
   operating hours), let the simulation continue until all
   entities in service or in queue have completed. Do not
   truncate mid-service.

3. Reproducibility: every random draw must use the replication's
   seeded RNG, never the global numpy random state. Pass the
   RNG object explicitly to all functions that draw random numbers.

4. Resource capacity changes: SimPy's Resource does not natively
   support dynamic capacity. Use a background process that
   modifies resource._capacity at schedule boundaries and
   triggers the resource to re-evaluate its queue.

5. Recording: capture every entity outcome, including those that
   balk or renege. These records are essential for computing
   abandonment rates and for debugging.

6. Scenario isolation: each replication creates a fresh SimPy
   environment. No state carries over between replications.

7. Print progress: print a brief summary after each scenario
   completes (mean wait, P90 wait, abandonment rate, cost) so
   the user can monitor long runs.
```

===============================================================
MAIN EXECUTION
===============================================================

```
The main() function should:
  1. Loop over all scenarios defined in the spec
  2. Run each scenario for the specified number of replications
  3. Print per-scenario summaries as they complete
  4. Build and print the cross-scenario comparison table
  5. Compute cost-effectiveness metrics
  6. Generate and save all required plots
  7. Save the per-replication summary data to CSV
  8. Return all results for interactive exploration

The script should be runnable with `python simulation.py` and
produce all outputs (console summary, CSV, plots) in a single run.
```
