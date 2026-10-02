# Experiments

## Baseline protocol

For every comparison keep fixed:
- initial instance;
- instance seed;
- initial state;
- search seed;
- iteration budget;
- time budget.

The first baseline selectors are RandomSelector and GreedySelector. The solver must not call JEV for these baselines.

## JEV/VLNS matrix

| Mode | Destroy | Repair | Research question |
|---|---|---|---|
| random-random | Random | Random | reference control |
| jev-random | JEV | Random | effect of choosing where to rebuild |
| random-jev | Random | JEV | effect of choosing how to rebuild |
| jev-jev | JEV | JEV | combined pipeline |

JEV here means the System-1 selector: it chooses one item from a finite, code-generated candidate set. It does not generate arbitrary actions, validate them, or execute them.

For the current offline benchmark, FakeJevClient is used. Its deterministic first/last strategies are plumbing stand-ins, not evidence that real JEV improves search. This stage verifies that the four experimental conditions are mechanically isolated and reproducible.

## Running

From the repository root:

    python experiments/run_benchmark.py
    python experiments/run_benchmark.py --seeds 1 2 3 4 5 --iterations 50
    python experiments/run_benchmark.py --seeds 1 2 3 4 5 --iterations 50 --output experiments/runs/matrix.json

The JSON output is the raw experiment artifact. Do not manually edit result files.

## Metrics

Record at minimum: feasible, objective/total moves, projected objective, delivered count, blocked containers, iterations.

For JEV-enabled runs also record JEV calls, latency, failures, fallback count, cost, and destroy/repair choice distributions.

The current benchmark exposes JEV call counts. The remaining operational metrics will be added with structured decision logging.

## Interpreting the first run

The primary outcome is the final completed solution objective (moves) under the same instance and iteration budget.

projected_objective is a search-time estimate used to compare candidate neighborhoods before final greedy completion. It should not replace the final objective when reporting solver quality.

Do not average different seeds into a single claim before inspecting per-seed results. Use multiple seeds and report the distribution rather than one lucky run.

## Research discipline

No claim about JEV improvement should be made until controlled runs compare the same instances, seeds and budgets.

A FakeJevClient result is a software-integration/control result, not a result about the quality of the real JEV model.
