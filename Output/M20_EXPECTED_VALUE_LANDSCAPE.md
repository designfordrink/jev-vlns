# M20 — Expected-Value Landscape: Local Execution Report

Executed locally following `docs/LOCAL_NEXT_STEP_M20.md` and gated by
`docs/LOCAL_TEST_M20.md`. Live calls used OpenRouter (`typesafe/jev-1.13`).
No credentials are stored in the repository.

## Protocol

| Parameter | Value |
|---|---|
| Branch | `m20-ev-landscape-local` |
| Base commit | `5eb45eb` (main after PR #20) |
| Seeds | 1, 2, 3, 4, 5 |
| Iterations | 50 |
| K | 2 exactly |
| Non-adjacent | true |
| Samples | 32 / 64 / 128 |
| Repair | Random (unchanged M19 policy) |
| Completion | deterministic greedy |
| Acceptance | unchanged from M19 |
| JEV model | `typesafe/jev-1.13` |

Decision states: **250** (5 seeds × 50 iterations) in every run, matching §9A.1.

## Test gate

```
Unit tests        : PASS   (95 passed)
Evaluator smoke   : PASS   (3 decision states, 960 samples, seed 1 x 3 iterations)
Offline N=32      : PASS
Offline N=64      : PASS
Offline N=128     : PASS
```

## Coverage

| Metric | N=32 | N=64 | N=128 |
|---|---:|---:|---:|
| Decision states | 250 | 250 | 250 |
| Candidate evaluations | 2008 | 2008 | 2008 |
| Requested samples | 64256 | 128512 | 257024 |
| Successful samples | 63752 | 127457 | 254859 |
| Failed samples | 504 | 1055 | 2165 |
| Failed fraction | 0.78% | 0.82% | 0.84% |
| Zero-valid-sample candidates | 0 | 0 | 0 |
| Flat landscapes | 0 | 0 | 0 |

Every candidate retained at least one valid sample, so no candidate was
unrankable and no sample was dropped or imputed.

## Choice quality against the aligned Random-Repair EV target

| Metric | M19 best-repair Oracle | M20 Random-Repair EV (live JEV) | Random Destroy control |
|---|---:|---:|---:|
| Top-1 | 0.004 | **0.004** | 0.188 |
| Mean rank | 9.84 | **7.48** | 4.41 |
| Median rank | — | 8.00 | 4.00 |
| Mean regret | — | 1.412 | 0.780 |
| Mean normalized regret | 0.972 | **0.733** | 0.514 |
| Flat landscapes | — | 0 | 0 |

The M19 values are reproduced from `Output/m19-real-jev-choice-quality.json`.
The M20 live values are from `Output/m20-real-jev-ev.json` (250 decisions,
250/250 successful calls, 0 fallbacks, $0.024681).

The Random Destroy control is measured on the identical decision states and the
identical EV target, using the offline N=64 landscape
(`Output/m20-offline-choice-quality.json`).

## N stability

| Comparison | Prefix consistent | Best candidate stable | Best candidate changed |
|---|---:|---:|---:|
| N=32 → N=64 | 250 / 250 | 213 (85.2%) | 37 |
| N=64 → N=128 | 250 / 250 | 219 (87.6%) | 31 |

Prefix consistency is exact: the N=32 stream is the first 32 samples of N=64,
and N=64 the first 64 of N=128, for every candidate at every decision state.
Best-candidate identity is stable for ~86% of decisions and improves with N,
which is the expected behaviour of a Monte-Carlo estimate converging.

## Decision

```text
M20 STATUS: CONFIRMED — poor selection under aligned downstream objective
```

## Interpretation

M20's central question was whether the M19 negative result was an artifact of
scoring JEV against a **best-possible-Repair Oracle** while the solver actually
used **Random Repair**.

It was not. Re-scoring every candidate under the true downstream policy moves
the numbers only modestly:

- normalized regret improves from 0.972 → 0.733;
- mean rank improves from 9.84 → 7.48;
- Top-1 is unchanged at 0.004 (1 of 250 decisions).

So the objective mismatch was real and worth correcting, but it explains only a
minor part of the gap. Against the aligned target, JEV is still **far worse than
uniform random selection**: Random Destroy scores Top-1 0.188, mean rank 4.41 and
normalized regret 0.514 on the very same landscapes. JEV's mean rank of 7.48 is
near the bottom of a candidate set averaging ~8 candidates, and its normalized
regret is 0.733 against Random's 0.514.

This is **Outcome B**, and it strengthens the M19 negative result rather than
explaining it away.

Per §13.D and §18, this is explicitly **not** grounds to tune the prompt. The
next stage indicated by the documents is state-representation / context
diagnostics, keeping the prompt, candidate serialization, ordering, K, Repair,
acceptance, seeds and objective fixed.

## Determinism boundary

Live JEV is stochastic. Two identical executions:

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| Top-1 rate | 0.004 | 0.008 |
| Mean rank | 7.48 | 7.80 |
| Mean normalized regret | 0.733 | 0.749 |
| Fallbacks | 0 | 1 |
| Cost USD | 0.024681 | 0.024505 |

Both runs agree in direction and magnitude. No statistical significance is
claimed from five seeds (§15).

## Research boundary

The expected-value landscape is **not** an exact solver. It answers "which
Destroy candidate has the best expected downstream result under the actual
Random Repair policy", not "what is the true minimum executable move count".
Greedy completion is a proxy, not an optimum.

## Implementation notes and defects found

### Recovered implementation

PR #19 merged only its documentation. Eight commits of M20 implementation were
left on `m20-objective-oracle-alignment` and never reached `main`:

```
4e6269b test(m20): keep EV integration out of legacy VLNS suite
1c8ae73 test(m20): isolate EV trace integration from incomplete landscapes
9a4d90d test(m20): verify EV trace integration
44925e7 feat(m20): add aligned live JEV EV experiment
74507ad feat(m20): attach downstream EV landscape to decision trace
becddcd test(m20): add expected-value landscape protocol tests
613ff02 fix(m20): use direct repair import
b0952e3 feat(m20): add Random Repair expected-value landscape evaluator
```

The gate in §3.3 (`Test-Path src/jev_vlns/search/expected_value.py`) returned
`False` on `main`, and `guided_vlns` there had no `expected_value_samples`
parameter, so the live script could not run at all. Those files were restored
byte-identical from the branch. **`main` still lacks them.**

### Defect: `rank_landscape` rejected every real landscape

`rank_landscape` raised `ValueError: cannot rank an incomplete landscape`
whenever any sample failed. Random Repair frequently hands the deterministic
greedy completion a configuration it cannot finish, so **every** decision state
in the real protocol failed this check (seed 1 iteration 0: 6 of 32 samples
failed for one candidate). The evaluator's own tests passed only because their
fixtures produced no failures.

Fixed: candidates are ranked on their valid samples, counts are reported in the
ranking output, and only a candidate with **zero** valid samples raises — its
expected value is undefined rather than merely noisy.

### Defect: `final_moves` was not index-aligned with `sample_seeds`

Failed samples were omitted from `final_moves`, so the stored stream silently
compressed and lost its correspondence to the seed schedule. This made the
mandated prefix-consistency check (§7.I, §9A.9) impossible to verify and
initially produced a false negative.

Fixed: `CandidateEV.outcomes` now stores one entry per requested sample in
sample-index order, with `None` where a sample failed. Prefix consistency is now
exactly verifiable and passes 250/250.

### Observation: greedy completion dead-ends under Random Repair

~0.8% of samples fail because Random Repair can produce an arrangement the
greedy policy cannot complete. This is a property of the M19 downstream policy
itself, not of the evaluator. It is reported rather than hidden, and it is worth
noting for any future stage that treats greedy completion as a terminal
objective.

## Artifacts

| File | Description |
|---|---|
| `Output/M20_EXPECTED_VALUE_LANDSCAPE.md` | This report |
| `Output/m20-real-jev-ev.json` / `.md` | Live JEV run, N=64 |
| `Output/m20-real-jev-ev-repeat.json` / `.md` | Live repeat |
| `Output/m20-n-stability.json` | N=32/64/128 stability |
| `Output/m20-offline-choice-quality.json` | Random Destroy control on the EV target |
| `experiments/run_m20_offline_landscape.py` | Offline runner (no JEV) |
| `experiments/compare_m20_sample_sizes.py` | N stability comparison |
| `experiments/m20_choice_quality.py` | Choice-quality metrics |

Raw offline landscapes (7–22 MB each, containing every sample vector) are not
committed. They are fully regenerable from the committed runners; the coverage
tables above record exactly what they contained.
