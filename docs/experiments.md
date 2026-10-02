# Experiments

## Baseline protocol

For every comparison keep fixed:

- initial instance;
- instance seed;
- initial state;
- search seed;
- iteration budget;
- time budget.

The first baseline selectors are:

1. RandomSelector
2. GreedySelector

The solver must not call JEV for these baselines.

## Metrics

Record at minimum:

- feasible;
- objective (total moves);
- delivered count;
- blocked containers;
- iterations.

Later experiments will add:

- JEV calls;
- JEV latency;
- JEV failures;
- fallback count;
- cost;
- destroy/repair choice distributions.

## Research discipline

No claim about JEV improvement should be made until controlled runs compare the same instances, seeds and budgets.
