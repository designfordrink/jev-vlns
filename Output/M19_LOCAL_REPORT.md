# M19 — Local Execution Report (Real JEV, K=2)

Executed locally against `main` at `1506bdc` following
`docs/M19_REAL_JEV_K2.md`. Live calls went through OpenRouter using
`typesafe/jev-1.13`. No credentials are stored in the repository.

## Protocol as executed

| Dimension | Value |
|---|---|
| Destroy | Real JEV (treatment) / Random (control) |
| Destroy neighborhood | exactly K=2 stacks, non-adjacent enabled |
| Repair | Random |
| Acceptance | strict improvement |
| Iteration budget | 50 |
| Seeds | 1, 2, 3, 4, 5 |
| Oracle | diagnostic only, never sent to JEV |

Protocol checks: 5 result rows; `iterations = 50` for every seed;
`destroy_min_stacks = destroy_max_stacks = 2`; `destroy_include_non_adjacent = true`;
250 JEV calls, 250 successful, 0 fallbacks; all runs feasible in both arms.

## M12 choice quality (K=2)

250 decisions measured against the local Oracle landscape.

| Metric | Value |
|---|---|
| Top-1 rate | 0.004 |
| Mean rank | 9.84 |
| Mean regret | 1.72 |
| Mean normalized regret | 0.972 |
| JEV calls / successes / failures | 250 / 250 / 0 |
| Fallbacks | 0 |
| Cost | $0.029216 |

Mean normalized regret 0.972 on a 0–1 scale where 0 is best means live JEV
choices sat near the **worst** end of the local candidate landscape almost
everywhere: it picked the best candidate in 1 of 250 decisions.

## M19 end-to-end (K=2)

| Seed | Random moves | Real JEV moves | Δ (JEV−Random) | Feasible | Fallbacks | Calls | Latency ms |
|---:|---:|---:|---:|:--:|---:|---:|---:|
| 1 | 17 | 18 | +1 | yes | 0 | 50 | 1349.1 |
| 2 | 15 | 18 | +3 | yes | 0 | 50 | 843.8 |
| 3 | 15 | 16 | +1 | yes | 0 | 50 | 1343.6 |
| 4 | 17 | 19 | +2 | yes | 0 | 50 | 884.4 |
| 5 | 15 | 16 | +1 | yes | 0 | 50 | 928.1 |

| Comparison | Wins | Ties | Losses | Mean Δ | Median Δ | Min / Max Δ |
|---|---:|---:|---:|---:|---:|---:|
| Real JEV vs Random (K=2) | 0 | 0 | 5 | +1.600 | +1 | +1 / +3 |

- Random mean moves: **15.800**
- Real JEV mean moves: **17.400**
- All runs feasible: **yes** (both arms)
- Total calls: **250**, successes **250**, fallbacks **0**
- Mean latency: **1069.8 ms**
- Tokens in/out: **588316 / 35500**
- Total API cost: **$0.024709**

## Interpretation

Real JEV lost on all five paired seeds and never tied. Feasibility was intact
and there was no fallback activity, so this is not a protocol or reliability
failure: JEV made real, successful selections that were measurably worse than
random selection under the same K=2 candidate set.

The M12 choice-quality result explains the direction. Random Destroy picks
uniformly among the K=2 candidates, so its expected rank is middling; JEV's mean
rank of 9.84 and normalized regret of 0.972 indicate its selections were
systematically toward the poor end of the landscape the local Oracle scores.
The end-to-end loss is therefore consistent with, and not independent of, the
measured choice quality.

Per the M19 interpretation rules, this must **not** be turned into a prompt or
neighborhood change made after seeing the result. The next step indicated by the
document is to inspect the trace and choice-quality data before changing the
prompt or neighborhood, keeping K=2, Repair, acceptance, seeds and objective fixed.

## Reproducibility boundary

Live JEV responses are **not** deterministic. Re-running the identical command
produced different per-seed outcomes across three executions, while the protocol
and per-run cost stayed stable:

| Run | Seed 1 Δ | Seed 2 Δ | Seed 3 Δ | Seed 4 Δ | Seed 5 Δ | Mean Δ | Wins |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0 | +1 | 0 | +2 | 0 | +0.6 | 0/5 |
| 2 | +1 | 0 | 0 | +2 | +2 | +1.0 | 0/5 |
| 3 (reported) | +1 | +3 | +1 | +2 | +1 | +1.6 | 0/5 |

The direction was consistent across all three runs — Real JEV never won a seed
and never beat Random on the mean — but the exact deltas differ. Any claim here
rests on that consistency, not on a single run.

## Scope

This is **projected-search / greedy-completion evidence**. It does not establish
performance under a physically executable reconfiguration path, nor against an
exact optimum.

## Defects found while running M19

Three implementation defects blocked or invalidated the documented runs. They are
fixed separately from the result, in commit `a109c4d`.

1. `experiments/run_real_jev_choice_quality.py` crashed with
   `KeyError: 'jev_stats'` — `summarize_choice_metrics` never placed `jev_stats`
   into `per_run`, but `render_report` read it there. The pre-existing test passed
   only because it hand-built that field, so the real pipeline crash was invisible
   to CI.
2. `experiments/run_m13_real_jev_end_to_end.py` recorded only six fields per seed,
   so feasibility, latency, token usage and successful-call accounting required by
   the M19 document were unavailable. `BenchmarkResult` already exposed all of them.
3. `JevClient` computed latency per call but never added it to
   `stats.total_latency_ms`, so `average_latency_ms` was always reported as 0.0.

No protocol, seed, Repair, acceptance, objective or K=2 logic was changed.
