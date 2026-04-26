# Spec-Driven Simulation Modeling

**Building and Validating Decision Support Models with Python and LLMs**

Workshop materials for ODSC East 2026 — a hands-on tutorial on using simulation, rather than prediction, to support decisions about systems, processes, and policies.

## What this workshop is about

Data scientists regularly build predictive models, but these are not always the best tool for decision support. Problems that involve system dynamics, process flows, capacity constraints, or emergent behaviors are better approached with simulation. Simulations let you explore "what-if" scenarios, quantify uncertainty, and test strategies before changing anything in production.

This workshop walks through a spec-driven approach to building and validating simulation models in Python, using LLMs as a collaborator throughout the modeling lifecycle.

## What you'll learn

- **Four simulation approaches** for decision support: Monte Carlo (uncertainty), discrete event (queues, processes, resource constraints), system dynamics (feedback loops, policy effects), and agent-based modeling (emergent behavior).
- **Statistical foundations** — the distribution families that show up most often in business modeling (normal, lognormal, exponential, triangular, Poisson) and how to fit them to data with SciPy.
- **Spec-driven model development** using prompt templates that turn a fuzzy business question into a clear model specification before any code gets written.
- **Discrete event simulation in SimPy** — built around a running coffee-shop scenario where the owner is deciding whether hiring an extra barista during the morning rush is worth the cost.
- **LLMs across the modeling lifecycle** — generating initial code from specs, reviewing logic, verifying spec compliance, validating against reality, generating test scenarios, and documenting assumptions.

## Repository layout

```
.
├── SETUP.md                  Pre-workshop setup instructions (do this first)
├── requirements.txt          Python dependencies
├── notebooks/                Workshop notebooks — work through these in order
│   ├── 00_verify_setup.ipynb
│   ├── block2_distribution_fitting.ipynb
│   ├── block5_llm_validation.ipynb
│   ├── bonus_llm_lifecycle.ipynb
│   └── llm_responses/        Saved LLM outputs (used by the offline-friendly cells)
├── code/                     Reference SimPy models for the coffee-shop scenario
├── data/                     Coffee-shop POS dataset, codebook, and generator
└── templates/                Spec prompt templates (A, B, C) plus a completed example
```

## Getting started

1. **Run the setup before the workshop.** See [SETUP.md](SETUP.md) — there are two paths (local Jupyter or Google Colab). Allow about 15 minutes.
2. **Verify your environment.** Open `notebooks/00_verify_setup.ipynb` and run all cells. Every cell should pass.
3. **The other notebooks are worked through together during the session.** You don't need to pre-run them.

## Prerequisites

- Intermediate Python skills.
- A laptop with Jupyter installed (or a Google account for Colab).
- No prior simulation experience required.

## The live LLM cell

Block 5 contains one cell that calls Anthropic's API for a spec-compliance review. It ships with a saved-response fallback, which is the default and recommended path — the exercise produces identical output without any network dependency. See [SETUP.md](SETUP.md#optional--the-live-llm-cell) if you want to run the live call.

## Contact

Questions about setup or materials: dan@sullivanlearninggroup.com
