# M20 — Real JEV Choice Quality vs Random-Repair Expected Value

| Decisions | Top-1 | Mean rank | Median rank | Mean regret | Mean normalized regret | Flat landscapes |
|---:|---:|---:|---:|---:|---:|---:|
| 250 | 0.004 | 7.48 | 8.00 | 1.412 | 0.733 | 0 |

## Protocol

- JEV chooses first; EV evaluation happens only after the JEV response.
- Every legal K=2 non-adjacent Destroy candidate is evaluated.
- Random Repair samples per candidate: 64.
- Greedy completion is deterministic.
- Common random-number seeds are shared across candidates at each decision.
- EV is never included in the JEV request.
- Primary objective is expected final executable move count.

## JEV telemetry

- Calls: 250
- Successful calls: 250
- Fallbacks: 0
- Cost USD: 0.024681
