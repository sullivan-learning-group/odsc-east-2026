# What the simulation found, in plain English

*Prepared for: the coffee shop owner. One page. No statistics jargon.*

## The question we set out to answer

You wanted to know whether hiring a third barista during the morning rush would reduce wait times enough to be worth the extra labor cost. The short answer: it would, and the cheaper alternative — speeding up the rush workflow without adding labor — gets you most of the way there for free.

## What we did

We built a simulation of a typical day at the shop using six months of point-of-sale data. The simulation tracks every customer from the moment they arrive to the moment they leave — including the people who walk out without ordering because the line is too long. We ran each staffing scenario fifty times to see how it performs across a range of mornings, not just one.

## What we found

Today, on a normal morning, customers wait about two minutes on average. That sounds fine, but the average hides the problem you actually feel: the slowest customer in ten waits more than six minutes, and during the busiest stretches the line gets long enough that roughly 1% of customers turn around and leave. Adding utilization arithmetic to that — the baristas are busy about 83% of the time during the rush — explains why a 30%-per-hour customer load feels like it does, even though the math says you have plenty of capacity. Coffee shop queues do not behave linearly. Going from 50% busy to 83% busy makes the wait dramatically worse, not modestly worse.

We tested three changes against today's setup:

**Adding a third barista from 7 to 9 AM only** brings the slowest-customer-in-ten wait down to about three and a half minutes and cuts walkaways close to zero. It costs about $34 per day in additional labor — roughly $9,000 a year, less the revenue you recover from the customers who currently walk out.

**Adding a third barista all day** does not produce meaningfully better results than the rush-only fix. The afternoon already has plenty of capacity. You would be paying about $170 per day for an improvement that lands almost entirely in the morning two hours. Not worth it.

**Speeding up the morning workflow by 15%** — through a dedicated order-taking position, pre-staged ingredients, or workflow reorganization, with no extra labor — gets you most of the wait-time improvement of adding a barista, at zero additional daily cost. Not all the way to the rush-staffed numbers, but close. If you can pull this off operationally, it is the highest-leverage move available.

## What we recommend

Try the workflow change first. It is the cheapest experiment you can run, and if it works it solves the problem without touching payroll. Give it two to four weeks of consistent execution before judging it. If wait times during the rush still feel long after that, add the third barista from 7 to 9 AM as a second-line fix. The combined effect — faster workflow plus an extra body during the rush — should comfortably handle even the busier-than-typical mornings the simulation showed could happen.

## What this analysis cannot tell you

The simulation assumes today's customer mix and weather pattern continues. If a competitor opens nearby, or you start drawing a different crowd because of the workflow changes, the numbers will shift and we should rerun. It also doesn't model customers who leave after waiting (a separate behavior from walking out at the door). Most coffee shop customers will tolerate a five-minute wait; if your customers are different, that's worth a separate conversation.

We modeled what could happen, not what we know happened. Use these numbers to size the bet, not as exact predictions.
