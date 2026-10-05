# M13 — Real JEV End-to-End Validation

Paired comparison of real JEV Destroy + Random Repair against Random Destroy + Random Repair.

- seeds: [1, 2, 3, 4, 5]
- iterations: 50
- destroy neighborhood: K=2..2, non-adjacent=True

## Paired results

| Seed | Random moves | Real JEV moves | Delta (JEV-Random) | Fallbacks | Calls | Cost USD |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 17 | 18 | 1 | 0 | 50 | 0.004829 |
| 2 | 15 | 18 | 3 | 0 | 50 | 0.004941 |
| 3 | 15 | 16 | 1 | 0 | 50 | 0.005009 |
| 4 | 17 | 19 | 2 | 0 | 50 | 0.004938 |
| 5 | 15 | 16 | 1 | 0 | 50 | 0.004992 |

## Aggregate

- Random mean moves: **15.800**
- Real JEV mean moves: **17.400**
- Mean paired delta (JEV − Random): **1.600**
- Median paired delta: **1.000**
- Min / max paired delta: **+1 / +3**
- Real JEV wins / ties / losses: **0 / 0 / 5** of 5 (0.0% wins)
- All runs feasible: **True**
- Total JEV calls: **250**, successes **250**, fallbacks **0**
- Mean latency: **1069.8 ms**
- Tokens in/out: **588316** / **35500**
- Total API cost: **$ 0.024709**

## Paired deltas

delta = JEV moves − Random moves; negative favours Real JEV.

| Comparison | Wins | Ties | Losses | Mean Δ | Median Δ |
|---|---:|---:|---:|---:|---:|
| Real JEV vs Random (K=2) | 0 | 0 | 5 | +1.600 | +1.000 |

## Interpretation rule

Negative delta means real JEV used fewer final moves and therefore won that paired seed.
This experiment tests end-to-end search quality under the fixed Random Repair protocol.
It does not establish that JEV is universally better, nor does it replace M12 local choice-quality measurements.
Fallbacks are reported separately and must be considered when interpreting the result.
