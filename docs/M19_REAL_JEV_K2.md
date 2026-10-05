# M19 — Real JEV with the Selected K=2 Destroy Neighborhood

## Purpose

M19 is the next live experiment after the M18 neighborhood protocol gate.

M18 compared K=1, K=2 and K=3 Destroy neighborhoods under the same Random Destroy + Random Repair protocol. K=2 was selected for the next stage because it matched K=3 on mean final moves while using substantially fewer candidates.

M19 therefore tests **Real JEV as the Destroy selector with K=2 fixed**.

## Fixed protocol

| Dimension | M19 |
|---|---|
| Destroy | Real JEV |
| Destroy neighborhood | exactly K=2 stacks |
| Non-adjacent neighborhoods | enabled |
| Repair | Random |
| Acceptance | strict improvement |
| Iteration budget | 50 |
| Seeds | 1, 2, 3, 4, 5 |
| Candidate generation | local deterministic code |
| Objective | projected final moves after Random Repair + greedy completion |
| Oracle | diagnostic only; never sent to JEV |

The control is **Random Destroy + Random Repair** with exactly the same K=2 candidate-generation protocol.

The treatment differs only in the Destroy selector.

## M12 choice-quality run

Run the local choice-quality measurement first:

```powershell
python experiments/run_real_jev_choice_quality.py `
  --seeds 1 2 3 4 5 `
  --iterations 50 `
  --output experiments/runs/m19-real-jev-choice-quality
```

This measures whether live JEV choices align with the offline local landscape. It is not an end-to-end solver result.

## M19 end-to-end run

After the choice-quality run, execute:

```powershell
python experiments/run_m13_real_jev_end_to_end.py `
  --seeds 1 2 3 4 5 `
  --iterations 50 `
  --destroy-min-stacks 2 `
  --destroy-max-stacks 2 `
  --destroy-include-non-adjacent `
  --output experiments/runs/m19-real-jev-k2
```

The script rejects any Destroy range other than exactly K=2. This is intentional: the M19 treatment must not silently drift to another neighborhood size.

## Required environment

For OpenRouter:

```dotenv
OPENROUTER_API_KEY=...
TYPESAFE_BASE_URL=https://openrouter.ai/api
JEV_MODEL=typesafe/jev-1.13
```

No credentials belong in the repository.

## Primary measurements

For each seed record:

- Random final moves
- Real JEV final moves
- paired delta = JEV - Random
- feasibility
- number of JEV calls
- successful calls / failures
- fallback count
- latency
- token usage
- provider-reported cost

Primary outcome:

**lower final move count is better.**

A negative paired delta means Real JEV used fewer final moves than the matched Random control.

## Interpretation rules

Do not claim that Real JEV is better from a single seed.

First inspect:

1. Whether the two treatments used the same seeds and iteration counts.
2. Whether K=2 and non-adjacent neighborhoods were fixed.
3. Whether fallbacks occurred.
4. Whether Real JEV actually made successful choices rather than relying on fallback.
5. Paired deltas across all seeds.
6. Mean and median delta.
7. Win/tie/loss counts.
8. API cost and latency.

M19 remains **projected-search / greedy-completion evidence**. It does not yet establish performance under a physically executable reconfiguration path or against an exact optimum.

## Expected next decision

- If Real JEV is competitive and the live choices show meaningful signal, continue to a stronger matched-state choice-quality analysis and exact-reference work.
- If Real JEV loses clearly, inspect the trace and choice-quality data before changing the prompt or neighborhood.
- Do not change K=2, Repair, acceptance, seeds or objective after seeing the result.

## Reproducibility

The experiment output should contain enough metadata to reconstruct the protocol. The repeat run should use the same seeds and parameters; provider nondeterminism may still affect live JEV responses.
