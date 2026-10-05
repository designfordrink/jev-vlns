# Offline VLNS neighborhood comparison

Seeds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
Iterations: 50
Adjacent only: False

## Summary

| K | N | Feasible | Mean moves | Median | Stdev | Mean candidates |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10 | 100% | 15.10 | 15.00 | 0.99 | 4.50 |
| 2 | 10 | 100% | 14.80 | 15.00 | 1.03 | 12.47 |
| 3 | 10 | 100% | 14.80 | 15.00 | 1.14 | 20.60 |

## Paired deltas

delta = moves(K) - moves(K=1); negative is better.

| Seed | K | K=1 | K | Delta |
|---:|---:|---:|---:|---:|
| 1 | 2 | 17 | 16 | -1 |
| 1 | 3 | 17 | 17 | +0 |
| 2 | 2 | 15 | 15 | +0 |
| 2 | 3 | 15 | 16 | +1 |
| 3 | 2 | 14 | 14 | +0 |
| 3 | 3 | 14 | 14 | +0 |
| 4 | 2 | 16 | 16 | +0 |
| 4 | 3 | 16 | 14 | -2 |
| 5 | 2 | 15 | 14 | -1 |
| 5 | 3 | 15 | 15 | +0 |
| 6 | 2 | 14 | 13 | -1 |
| 6 | 3 | 14 | 13 | -1 |
| 7 | 2 | 14 | 15 | +1 |
| 7 | 3 | 14 | 14 | +0 |
| 8 | 2 | 16 | 16 | +0 |
| 8 | 3 | 16 | 15 | -1 |
| 9 | 2 | 15 | 15 | +0 |
| 9 | 3 | 15 | 15 | +0 |
| 10 | 2 | 15 | 14 | -1 |
| 10 | 3 | 15 | 15 | +0 |

## Interpretation boundary

- Offline Random Destroy + Random Repair control only.
- Seeds, initial states, iteration budget, Repair, and acceptance are matched.
- Only the Destroy neighborhood family changes.
- The current projected-search semantics are used; this is not physical reconfiguration evidence.
- A useful neighborhood should improve paired outcomes, not merely increase candidate count.
