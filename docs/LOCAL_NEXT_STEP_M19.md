# JEV-VLNS: M19 Local Execution Handoff — Real JEV with Fixed K=2

> **Audience:** local AI agent working inside a local clone of `designfordrink/jev-vlns`.
>
> **Purpose:** execute and analyze the M19 live Real JEV experiment after the M18 neighborhood gate. This document is the exact local hand-off. Do not silently change the protocol.

## 1. Current state

M18 has passed its protocol gate and selected **K=2** as the most reasonable neighborhood for the next Real JEV experiment.

M19 is now a **live API experiment**:

> Can Real JEV select useful Destroy neighborhoods when the legal candidate set is fixed to K=2, the state-aware context is supplied, and all other solver conditions are matched?

Important objective boundary:

- The current result is still a **projected-search / greedy-completion objective**.
- Virtual Destroy/Repair operations are not physical container moves.
- Do not describe M19 results as physical reconfiguration performance.
- Oracle scores are diagnostics only and must never be sent to JEV.

## 2. Required checkout / preconditions

Work from the repository root.

First inspect the repository:

```powershell
git status
git branch --show-current
git log -1 --oneline
```

The M19 implementation is on branch:

```m19-real-jev-k2-protocol
```

If M19 has already been merged into `main`, use current `main` instead. Otherwise checkout the M19 branch:

```powershell
git fetch origin
git checkout m19-real-jev-k2-protocol
git pull --ff-only
```

The working tree must be clean before the experiment.

Verify the test suite:

```powershell
python -m pytest -q
```

At the time this handoff was prepared, the M19 compatibility fix was CI-green. If local tests fail, **STOP and report the failure before running the live experiment**.

## 3. Required API configuration

M19 uses the real JEV API.

For OpenRouter, configure the local environment only:

```dotenv
OPENROUTER_API_KEY=...
TYPESAFE_BASE_URL=https://openrouter.ai/api
JEV_MODEL=typesafe/jev-1.13
```

Do not commit credentials.

Before running, verify that the local environment exposes the required key without printing its value.

If credentials are unavailable, do not invent results. Report:

```
M19 STATUS: BLOCKED — live JEV credentials unavailable
```

## 4. Fixed M19 protocol

Do not change these values:

| Dimension | Required value |
|---|---|
| Destroy selector | Real JEV |
| Control selector | Random |
| Destroy min stacks | 2 |
| Destroy max stacks | 2 |
| Non-adjacent neighborhoods | enabled |
| Repair | Random |
| Acceptance | strict improvement |
| Iterations | 50 |
| Seeds | 1, 2, 3, 4, 5 |
| Candidate generation | deterministic local code |
| Objective | projected final moves after Random Repair + greedy completion |
| Oracle | diagnostic only |
| JEV context | state-aware English prompt already in repository |

The critical isolation rule is:

> **Treatment and control must use the same seeds, initial states, iteration budget, candidate-generation protocol, Repair, acceptance policy and objective. Only the Destroy selector changes.**

Do not change K after seeing results.

## 5. Run 1 — Real JEV choice quality

Run this first:

```powershell
python experiments/run_real_jev_choice_quality.py `
  --seeds 1 2 3 4 5 `
  --iterations 50 `
  --destroy-min-stacks 2 `
  --destroy-max-stacks 2 `
  --destroy-include-non-adjacent `
  --output experiments/runs/m19-real-jev-choice-quality
```

The repository code should enforce the fixed K=2 protocol. If the command rejects the protocol unexpectedly, investigate the implementation rather than changing the parameters.

### Inspect the choice-quality output

Do not assume that a live JEV call succeeded merely because a row exists.

Inspect:

- number of decisions;
- successful JEV calls;
- failures;
- fallback decisions;
- candidate counts;
- selected candidate IDs;
- rank / regret fields if present;
- latency;
- token usage;
- provider-reported cost;
- seed and iteration metadata.

Important:

- Oracle information may be used for **offline diagnostic measurement**.
- Oracle information must not be included in the JEV prompt/request.
- A fallback decision is not evidence that JEV successfully selected a candidate.

Report choice-quality measurements separately from end-to-end solver performance.

## 6. Run 2 — M19 end-to-end

Only after the choice-quality run completes successfully, execute:

```powershell
python experiments/run_m13_real_jev_end_to_end.py `
  --seeds 1 2 3 4 5 `
  --iterations 50 `
  --destroy-min-stacks 2 `
  --destroy-max-stacks 2 `
  --destroy-include-non-adjacent `
  --output experiments/runs/m19-real-jev-k2
```

This is the primary M19 experiment.

The implementation should reject any Destroy range other than exactly K=2. Do not bypass that guard.

## 7. Required output inspection

Locate the generated JSON and Markdown files under:

```text
experiments/runs/m19-real-jev-k2/
experiments/runs/m19-real-jev-choice-quality/
```

Use the actual filenames produced by the scripts; do not invent filenames if the implementation uses a different layout.

Inspect the JSON before making any conclusion.

Verify:

### 7.1 Matched seeds

Both treatment and control must cover:

```text
1, 2, 3, 4, 5
```

### 7.2 Matched iterations

Every end-to-end result must use:

```text
iterations = 50
requested_iterations = 50
```

If not, **FAIL** the experiment.

### 7.3 Fixed neighborhood

Verify metadata explicitly shows:

```text
destroy_min_stacks = 2
destroy_max_stacks = 2
destroy_include_non_adjacent = true
```

If not, **FAIL** the experiment.

### 7.4 Feasibility

Report feasibility separately for Random and Real JEV.

Unexpected infeasibility must be investigated before interpreting final moves.

### 7.5 Fallbacks

Report:

- total JEV calls;
- successful calls;
- failed calls;
- fallback count;
- fallback rate.

A result dominated by fallback is **not strong evidence about Real JEV selection quality**.

Do not hide fallback behavior inside an aggregate score.

## 8. Primary end-to-end comparison

For every seed calculate:

```text
delta = RealJEV_moves - Random_moves
```

Interpretation:

- negative = Real JEV better;
- zero = tie;
- positive = Real JEV worse.

Report:

- wins;
- ties;
- losses;
- mean delta;
- median delta;
- minimum delta;
- maximum delta.

The primary outcome is **lower final projected move count**.

Do not use an unpaired comparison as the primary evidence because the same seed must provide the matched control.

## 9. Required human-readable report

Return this table:

| Seed | Random moves | Real JEV moves | Δ (JEV-Random) | JEV calls | Failures | Fallbacks |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | ... | ... | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... | ... | ... |
| 3 | ... | ... | ... | ... | ... | ... |
| 4 | ... | ... | ... | ... | ... | ... |
| 5 | ... | ... | ... | ... | ... | ... |

Then:

| Metric | Value |
|---|---:|
| Random mean moves | ... |
| Real JEV mean moves | ... |
| Mean paired Δ | ... |
| Median paired Δ | ... |
| Wins | ... |
| Ties | ... |
| Losses | ... |
| JEV calls | ... |
| Successful calls | ... |
| Failed calls | ... |
| Fallbacks | ... |
| Fallback rate | ... |
| Mean latency | ... |
| Total/provider cost | ... |

Also report choice-quality metrics from Run 1, using the fields actually produced by the implementation.

## 10. Interpretation rules

Do not claim Real JEV is better because:

- it wins on one seed;
- its unpaired mean happens to be lower;
- it made more API calls;
- it produced more candidate choices;
- the fallback path happened to perform well.

The first question is whether the **matched paired deltas** support a useful signal.

Then inspect:

1. successful JEV decisions;
2. fallback rate;
3. choice quality;
4. consistency across seeds;
5. latency;
6. cost.

### Stronger positive evidence

A positive result is more credible when:

- the treatment/control protocol is fully matched;
- fallback is low;
- most decisions are successful JEV choices;
- paired deltas favor JEV across multiple seeds;
- choice-quality metrics show signal rather than random behavior;
- the improvement is not explained by an implementation artifact.

### Negative result

If Real JEV loses, do not immediately modify the prompt or K=2 neighborhood.

First determine whether the loss is associated with:

- poor choice quality;
- high fallback;
- API/provider failures;
- insufficient context;
- candidate serialization problems;
- genuinely poor JEV decisions.

Do not rerun with altered parameters merely to obtain a better result.

## 11. Reproducibility

Live JEV responses may be provider-nondeterministic, so do not require byte-identical JSON as in M18.

Instead verify:

- same code revision;
- same seeds;
- same iterations;
- same K=2 protocol;
- same candidate-generation rules;
- same Repair and acceptance;
- same objective;
- same model/configuration.

If you perform a repeat run, clearly label it as a repeat/live-provider run rather than silently replacing the original output.

Do not delete the first result because the repeat is more favorable.

## 12. What the local agent must NOT do

Do not:

1. Change K=2.
2. Change Repair.
3. Change acceptance.
4. Change seed set.
5. Increase the iteration budget after seeing results.
6. Remove an unfavorable seed.
7. Change the JEV prompt during the experiment.
8. Send Oracle scores or future evaluation results to JEV.
9. Replace failed JEV calls with invented successful responses.
10. Hide fallback decisions.
11. Present projected moves as physical movement cost.
12. Commit API credentials.
13. Rewrite the benchmark until Real JEV wins.
14. Claim statistical significance from five seeds.
15. Invent missing cost/token/latency data.

If an implementation defect is found, stop and report it separately.

## 13. Repository updates after successful execution

After the experiment is complete and the protocol has passed, preserve the raw outputs.

At minimum, retain:

```text
experiments/runs/m19-real-jev-k2/
experiments/runs/m19-real-jev-choice-quality/
```

Also prepare Markdown summaries suitable for committing to the repository under `Output/` if that is the project's established convention.

Suggested names:

```text
Output/m19-real-jev-k2.md
Output/m19-real-jev-k2.json
Output/m19-real-jev-choice-quality.md
Output/m19-real-jev-choice-quality.json
```

Do not overwrite prior experiments.

If the scripts already emit the final files in another canonical format, preserve that format rather than duplicating data unnecessarily.

## 14. Final status

Return exactly one of these statuses:

### Successful protocol and usable result

```text
M19 STATUS: PASS — Real JEV result is valid for analysis
```

### Protocol/implementation failure

```text
M19 STATUS: FAIL — do not interpret results; investigate <specific issue>
```

### No live credentials

```text
M19 STATUS: BLOCKED — live JEV credentials unavailable
```

The status must reflect the protocol, not whether Real JEV won.

## 15. Research boundary after M19

Even a successful M19 result does **not** establish:

- physical container reconfiguration efficiency;
- superiority over an exact optimum;
- generalization to other datasets;
- statistical significance from five seeds.

If M19 passes, the next research step should be chosen from the actual evidence. Likely directions are:

1. stronger matched-state JEV choice-quality evaluation;
2. exact small-instance reference solver;
3. physical/executable reconfiguration objective;
4. broader seed/dataset validation.

Do not implement the next stage automatically unless explicitly instructed.

## 16. Final instruction to the local AI agent

**Your immediate task is M19 execution and analysis only.**

Run the fixed K=2 choice-quality experiment, then the fixed K=2 end-to-end experiment, verify the protocol, inspect fallback/call/cost behavior, compute paired seed-level outcomes, preserve raw outputs, and return the actual measurements.

Do not modify the experimental protocol to improve the outcome.
