# JEV-VLNS: M20 Local Test Handoff — Expected-Value Landscape

> **Audience:** local AI agent working inside a local clone of `designfordrink/jev-vlns`.
>
> **Purpose:** provide the exact local validation sequence for M20 before spending money on Live JEV.
>
> **Important:** PR #19 is already merged. It changed the M20 research protocol/documentation, but the Expected-Value implementation must be validated separately. This document is the local test gate.

## 1. M20 research question

M19 compared Real JEV Destroy + Random Repair against Random Destroy + Random Repair and produced a negative result.

The previous choice-quality metric used a best-possible-Repair Oracle. M20 corrects that mismatch.

The aligned target is:

```
current state
    ↓
Destroy candidate
    ↓
Random Repair
    ↓
deterministic greedy completion
    ↓
final executable move count
```

For candidate `d`:

```
EV_N(d) = mean(final_moves_1 ... final_moves_N)
```

Lower is better.

The key question is:

> Does Real JEV remain poor when its Destroy choices are evaluated against the downstream Random Repair policy it actually controls?

M20 is a **measurement/alignment experiment**, not a prompt-tuning experiment.

---

## 2. M20 protocol lock

Do not change:

- JEV prompt;
- candidate serializer;
- candidate IDs;
- candidate ordering;
- K;
- `destroy_include_non_adjacent`;
- Random Repair semantics;
- deterministic greedy completion;
- acceptance rule;
- initial-state generation;
- iteration budget;
- seed protocol;
- primary `final_moves` metric.

Required neighborhood:

```
K = 2 exactly
destroy_include_non_adjacent = true
```

Primary seeds:

```
1 2 3 4 5
```

Primary iterations:

```
50
```

Primary Monte-Carlo sample count:

```
N = 64
```

Fast validation:

```
N = 32
```

Robustness check:

```
N = 128
```

---

## 3. Preconditions

Run from the repository root.

### 3.1 Working tree

```powershell
git status
git branch --show-current
git log -1 --oneline
```

The working tree should be clean.

### 3.2 Update repository

```powershell
git fetch origin
git pull --ff-only
```

### 3.3 Verify branch and implementation

Before running M20, confirm that the Expected-Value implementation and tests actually exist:

```powershell
Test-Path src/jev_vlns/search/expected_value.py
Test-Path tests/test_expected_value_landscape.py
```

If either returns `False`, **STOP**.

Do not invent a local workaround. The implementation stage is not complete.

---

## 4. Full unit-test gate

Run:

```powershell
python -m pytest -q
```

Do not start any M20 experiment if the test suite fails.

### PASS condition

```
M20 UNIT TESTS: PASS
```

### FAIL condition

Any failing test:

```
M20 UNIT TESTS: FAIL — do not run live M20
```

Record:

- failing test;
- exception;
- whether failure is implementation, test-harness, or environment related.

---

## 5. Expected-Value evaluator contract

The evaluator must:

1. Start from an immutable/frozen decision state.
2. Apply exactly one Destroy candidate.
3. Use an explicit deterministic sample seed.
4. Execute exactly one existing Random Repair outcome.
5. Run the existing deterministic greedy completion.
6. Validate the executable plan.
7. Record `final_moves`.
8. Repeat exactly N times.
9. Aggregate the samples.
10. Never call JEV.
11. Never mutate the actual solver state.
12. Never expose EV results to JEV.

The evaluator must reproduce the M19 downstream policy, not a new Repair implementation.

---

## 6. Required random-seed protocol

For every decision state define:

- `run_seed`: 1..5;
- `iteration`: zero-based;
- `state_key`: deterministic identifier of the frozen state;
- `sample_index`: 0..N-1.

Sample seed:

```text
sample_seed = uint64(SHA256(
  "m20-ev-v1|" + run_seed + "|" + iteration + "|" + state_key + "|" + sample_index
)[0:16])
```

Candidate ID must **not** be part of the seed.

This gives every candidate the same sample-index seed at a given decision state.

The evaluator must create a fresh RNG instance for every candidate/sample.

---

## 7. Mandatory evaluator tests

The test suite must cover all of the following.

### A. Reproducibility

Same:

- state;
- candidate;
- run seed;
- iteration;
- sample schedule;
- N

must produce identical raw samples and aggregates.

### B. Evaluation-order invariance

Evaluating:

```
A, B, C
```

must produce exactly the same results as:

```
C, A, B
```

### C. Candidate isolation

Changing candidate A must not change candidate B's sampled result.

### D. State immutability

The frozen input state must be byte-for-byte/logically unchanged after evaluation.

### E. Objective consistency

Every reported `final_moves` must equal the move count of the validated deterministic executable completion.

### F. No JEV dependency

The evaluator must run without a JEV API key.

### G. No leakage

Expected values, Oracle scores, ranks and regrets must not occur in:

- JEV prompt;
- JEV request payload;
- candidate serializer;
- selection context.

### H. Flat landscape

If all candidate EVs are equal:

- every candidate is best/tied;
- Top-1 is true for any selected candidate;
- regret = 0;
- normalized regret = 0.

### I. Prefix consistency

The first 32 samples of N=64 must equal the N=32 samples.

The first 64 samples of N=128 must equal the N=64 samples.

---

## 8. First local smoke experiment — OFFLINE ONLY

Do **not** use Real JEV for this test.

Purpose: validate that the evaluator can actually complete Random Repair + greedy completion across a small number of states.

Recommended smoke configuration:

```
seeds: 1
iterations: 3
K: 2
non-adjacent: true
samples: 32
```

Use the repository's M20 offline evaluator command if available.

If a dedicated command is not yet available, **STOP** rather than creating an ad-hoc command that changes the protocol.

### Smoke acceptance

For every decision state:

- legal K=2 candidates exist;
- every candidate has exactly 32 samples;
- every sample is successful;
- every sample has a valid executable move count;
- no input state is mutated;
- results are reproducible.

Expected:

```
decision states = 3
candidate sample count = sum(candidate_count × 32)
failed samples = 0
```

If any candidate has incomplete samples:

```
M20 SMOKE: FAIL — incomplete candidate landscape
```

Do not silently drop or impute samples.

---

## 9. Full offline validation — N=32

After the smoke test passes, run the full matched offline validation:

```
seeds: 1 2 3 4 5
iterations: 50
K: 2
non-adjacent: true
N: 32
```

This produces:

```
5 × 50 = 250 decision states
```

The exact number of candidate-level samples must be calculated from the generated artifact:

```
total_samples = Σ(candidate_count_per_decision × 32)
```

Do not estimate this from the M18 average.

### Required validation

For all 250 decision states:

- all candidate sets are legal;
- K=2 is fixed;
- non-adjacent is enabled;
- all requested samples exist;
- all samples are valid;
- no candidate has missing data;
- state immutability holds;
- results are reproducible;
- EV is not used by the decision path.

### Primary PASS condition

```
M20 OFFLINE N=32: PASS
```

If any candidate has a missing/invalid sample:

```
M20 OFFLINE N=32: FAIL — protocol violation
```

---

## 10. Primary offline validation — N=64

Only after N=32 passes, run:

```
seeds: 1 2 3 4 5
iterations: 50
K: 2
non-adjacent: true
N: 64
```

The same 250 decision states must be used.

The N=64 sample stream must extend the N=32 stream rather than creating an unrelated Monte-Carlo experiment.

Verify:

```
samples[0:32]_N64 == samples_N32
```

for every candidate/decision state.

### Primary PASS condition

```
M20 OFFLINE N=64: PASS
```

---

## 11. Optional robustness validation — N=128

If runtime is acceptable:

```
seeds: 1 2 3 4 5
iterations: 50
K: 2
non-adjacent: true
N: 128
```

Verify:

```
samples[0:64]_N128 == samples_N64
```

Then compare:

- best-candidate identity;
- complete candidate ordering;
- selected-candidate rank;
- regret;
- normalized regret.

Do not treat N=32, N=64 and N=128 as unrelated experiments.

---

## 12. Required candidate-level statistics

For every candidate report:

- candidate ID;
- position;
- serialization;
- sample count;
- feasible count;
- error count;
- raw `final_moves[]` where practical;
- mean;
- median;
- sample standard deviation;
- min;
- max;
- p10;
- p90.

A candidate is rankable only if all requested samples are valid.

Rank:

```
lower mean EV = better candidate
```

Tie tolerance:

```
1e-9
```

Do not break Top-1 ties by candidate ID.

---

## 13. Required choice-quality metrics

For each decision state, after all candidate evaluations:

```
best_EV = min(candidate_mean_EV)
worst_EV = max(candidate_mean_EV)
selected_EV = EV(selected_candidate)

regret = selected_EV - best_EV

normalized_regret =
    regret / (worst_EV - best_EV)
```

If:

```
worst_EV == best_EV
```

then:

```
normalized_regret = 0
regret = 0
Top-1 = true
```

Report:

- Top-1;
- mean rank;
- median rank;
- mean regret;
- median regret;
- mean normalized regret;
- median normalized regret;
- number/fraction of flat or near-flat landscapes.

---

## 14. Only after offline validation: Live M20

Do **not** run Live JEV until:

```
M20 UNIT TESTS: PASS
M20 SMOKE: PASS
M20 OFFLINE N=32: PASS
M20 OFFLINE N=64: PASS
```

Then the live experiment may use:

```
seeds = 1..5
iterations = 50
K = 2
non-adjacent = true
N = 64
```

Causal order for every decision must be:

```
freeze state
    ↓
generate candidates
    ↓
send unchanged JEV request
    ↓
receive JEV selection
    ↓
evaluate every candidate with EV
    ↓
record rank/regret
    ↓
continue actual solver using JEV selection
```

EV evaluation must never occur before the JEV response.

---

## 15. Required live M20 artifacts

Expected:

```
Output/m20-expected-value-landscape.json
Output/M20_EXPECTED_VALUE_LANDSCAPE.md
```

If the live experiment uses a separate filename, document the exact filename in the final report.

The Markdown report must contain:

### Protocol

| Parameter | Value |
|---|---|
| Seeds | 1..5 |
| Iterations | 50 |
| K | 2 |
| Non-adjacent | true |
| Samples | 64 |
| Repair | Random |
| Completion | deterministic greedy |
| Acceptance | unchanged from M19 |

### Coverage

| Metric | Value |
|---|---:|
| Decision states | ... |
| Candidate evaluations | ... |
| Candidate-level samples | ... |
| Successful samples | ... |
| Failed samples | ... |
| Feasible decisions | ... |

### Choice quality

| Metric | M19 best-repair Oracle | M20 Random-Repair EV |
|---|---:|---:|
| Top-1 | 0.004 | ... |
| Mean rank | 9.84 | ... |
| Mean regret | ... | ... |
| Mean normalized regret | 0.972 | ... |

Do not copy M19 values for metrics that were not actually recomputed.

---

## 16. Reproducibility

For every offline experiment, run the same command twice.

Write separate outputs for the repeat:

```
...-repeat.json
...-repeat.md
```

Compare the JSON artifacts.

Expected:

```
no meaningful differences
```

If live JEV is involved, exact decision outcomes may differ because JEV is stochastic. In that case compare protocol invariants and statistical direction, not byte-for-byte identity.

---

## 17. M20 interpretation gate

### Outcome A — alignment explains M19 failure

If JEV looks substantially better under Random-Repair EV than under the best-Repair Oracle:

```
M20 STATUS: DIAGNOSTIC — objective/oracle mismatch confirmed
```

Do not tune the prompt yet.

### Outcome B — JEV remains poor

If Top-1 remains low, rank remains poor and regret remains high:

```
M20 STATUS: CONFIRMED — poor selection under aligned downstream objective
```

Then the next stage should investigate state representation/context.

### Outcome C — EV is unstable

If best candidate/order changes materially between N=32, 64 and 128:

```
M20 STATUS: INCONCLUSIVE — EV sampling too noisy
```

Increase N or introduce a predeclared confidence-aware comparison.

### Outcome D — implementation/protocol failure

If any of the following occurs:

- missing samples;
- invalid executable plans;
- non-reproducibility;
- state mutation;
- leakage;
- wrong Repair semantics;
- wrong candidate set;
- wrong K;
- wrong seed schedule;

then:

```
M20 STATUS: FAIL — fix measurement/implementation before interpretation
```

---

## 18. What the local agent must NOT do

Do not:

1. Tune the JEV prompt.
2. Change candidate serialization.
3. Change candidate ordering.
4. Change K.
5. Change Random Repair.
6. Change acceptance.
7. Remove difficult seeds.
8. Increase iterations after seeing an unfavorable result.
9. Drop failed Monte-Carlo samples.
10. Impute missing candidate outcomes.
11. Send EV/Oracle information to JEV.
12. Treat greedy completion as the exact optimum.
13. Claim statistical significance from five seeds.
14. Run expensive Live JEV before the offline evaluator passes.
15. Change the protocol until Top-1 improves.

---

## 19. Final local report format

At the end of the local run, return a Markdown report containing:

### Protocol

Exact:

- commit SHA;
- branch;
- seeds;
- iterations;
- K;
- non-adjacent flag;
- N;
- Repair;
- completion;
- acceptance.

### Test gate

```
Unit tests: PASS/FAIL
Evaluator smoke: PASS/FAIL
Offline N=32: PASS/FAIL
Offline N=64: PASS/FAIL
Offline N=128: PASS/FAIL/SKIPPED
```

### Coverage

| Metric | Value |
|---|---:|
| Decision states | ... |
| Candidate evaluations | ... |
| Requested samples | ... |
| Successful samples | ... |
| Failed samples | ... |

### Choice quality

| Metric | Value |
|---|---:|
| Top-1 | ... |
| Mean rank | ... |
| Median rank | ... |
| Mean regret | ... |
| Mean normalized regret | ... |
| Flat landscapes | ... |

### N stability

| Comparison | Best candidate stable | JEV Top-1 status changed |
|---|---:|---:|
| N=32 → N=64 | ... | ... |
| N=64 → N=128 | ... | ... |

### Decision

Return exactly one:

```
M20 STATUS: PASS — proceed to matched Live JEV N=64
```

or

```
M20 STATUS: FAIL — <specific reason>
```

or

```
M20 STATUS: INCONCLUSIVE — <specific reason>
```

---

## 20. Research boundary

M20 Expected-Value Landscape is **not** an exact solver.

It answers:

> Which Destroy candidate has the best expected downstream result under the actual Random Repair policy?

A later exact small-instance solver answers:

> What is the true minimum executable move count?

Do not merge these claims.

The intended research sequence is:

```
M19 negative baseline
        ↓
M20 objective/oracle alignment
        ↓
Expected-Value Landscape
        ↓
Exact small-instance reference
        ↓
JEV representation/context diagnostics
        ↓
JEV Top-K → deterministic rollout
```

The purpose of the local gate is to make sure every subsequent conclusion is based on a valid and reproducible measurement.
