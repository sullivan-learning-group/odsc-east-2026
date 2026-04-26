# Modeling assumptions — for the record

*Companion to the simulation results. Plain-English version of the assumption list in Template A. Read this before relying on the simulation for a decision that costs more than the simulation cost to build.*

The simulation's answers are only as good as the assumptions it rests on. If any of these stops being true, the conclusions need to be revisited. We have organized the assumptions by how much they would change the answer if they were wrong.

## Assumptions that would change the answer most if wrong

**Customer arrivals are random and independent.** We assumed that customers arrive without coordinating with each other — one customer's decision to come in does not influence another's. This is the standard assumption behind exponential inter-arrival times and is what makes random clustering happen. *If wrong:* the simulation would understate wait times during predictable bursts (e.g., a meeting next door that lets out at 8:30 AM), because the simulation cannot distinguish "30 customers per hour evenly random" from "30 customers per hour with a 10-minute pulse."

**Service times follow a lognormal distribution per drink type.** We fit lognormal curves to historical service times for drip, espresso, and blended drinks. *If wrong:* if a barista trained differently, or new equipment changes the shape of the service-time distribution, the simulation's tail predictions (slowest 10%) become unreliable. The averages would still be roughly right.

**Customers walk away if the line has eight or more people in it at the moment they arrive.** This is the balking threshold. *If wrong:* a higher threshold (more patient customers) would mean longer queues but lower walkaway rates; a lower threshold the reverse. We picked 8 based on physical capacity of the entryway and the owner's observation. Worth re-checking by recording walkaway-trigger queue lengths over a week.

**The staffing schedules in each scenario are followed exactly.** No late starts, no early leaves, no breaks during the rush. *If wrong:* real-world deviations from the staffing plan are likely the largest source of "the simulation said X but reality showed Y."

## Assumptions that would change the answer modestly if wrong

**The order-type mix stays at 30% drip, 50% espresso, 20% blended.** If the mix shifts toward more blended drinks, average service time rises, capacity falls, and the wait-time results worsen. *If wrong:* a 5-percentage-point shift toward blended drinks would push morning utilization from 0.83 toward 0.86 — visibly worse waits.

**No reneging.** Customers who join the queue do not leave before being served. In reality some do, after about 8 to 10 minutes of waiting. *If wrong:* the simulated wait distribution overstates the long tail because in real life those customers would have left. Walkaway counts would be higher than what we currently report.

**All baristas are equally skilled.** Service-time distributions do not vary by barista. *If wrong:* a slower-than-average barista on the morning shift would push P90 wait higher than the simulation predicts, and a faster-than-average one would do the opposite. The simulation reflects the average barista, not the morning shift specifically.

**Weather and seasonality are not modeled.** The arrival rates are based on a six-month average and assume the next quarter looks like the past two. *If wrong:* a heat wave that drives blended-drink demand, or a colder-than-usual season that drives drip demand, would shift the order mix and the answer along with it.

## Assumptions that would change the answer least if wrong

**Hourly wage is $17.** Used only for the daily-cost comparison. Easily updated; does not affect wait times.

**Warm-up period is 30 minutes.** We discard the first 30 minutes of each simulated day to avoid the artifact of starting with an empty queue. *If wrong:* a longer warm-up throws away meaningful rush data; a shorter one introduces empty-queue bias. Tested and 30 minutes is the right balance for this system.

**Number of replications is 50.** Each scenario is simulated 50 times to produce stable averages. *If wrong:* fewer replications would widen confidence intervals; more would tighten them but rarely change conclusions.

## What is *not* in the simulation

For honesty, here is what the simulation does *not* model:

- Special events (free coffee day, a popular author signing books).
- Competitors (a new shop opening across the street).
- Menu changes (introducing a faster drink, dropping a slow one).
- Equipment failures or stockouts.
- Customer behavior outside the door (people who see a long line through the window and don't enter).

If a decision turns on any of these, this simulation alone is not enough to make it.

## When to rerun

Rerun the simulation if any of the following becomes true:

1. The order-type mix shifts by more than 5 percentage points in any direction.
2. Average service time changes by more than 30 seconds.
3. Daily customer count shifts by more than 15%.
4. Staffing rules change (different break patterns, different number of baristas on shift).
5. A new operational pattern emerges that was not in the historical data — for example, mobile pre-orders becoming a meaningful fraction of arrivals.

The simulation is not a forecast. It is a tool for thinking through what could happen under specific assumptions. Treat it accordingly.
