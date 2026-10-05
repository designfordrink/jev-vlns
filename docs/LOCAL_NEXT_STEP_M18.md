# JEV-VLNS: Current Research Gate and Local Execution Plan

> **Audience:** local AI agent working inside a local clone of `designfordrink/jev-vlns`.
>
> **Purpose:** this document is the exact hand-off point for the next local experiment. Do not skip the M18 gate and do not start Real JEV experiments until the acceptance criteria below are satisfied.

## 1. Where the project is now

The project is currently **after M18 Protocol Gate**.

### Completed and merged

- **M9 — Real JEV Destroy**
  - Real JEV can select Destroy candidates.
  - Repair is Random in the isolation experiment.
  - Real JEV is optional/live and is not required for CI.

- **M10 — Visualization / Replay**
  - Added observational traces for individual VLNS runs.
  - Trace capture must not change solver behavior.

- **M11 — JEV Choice vs Local Landscape**
  - Measures Top-1, mean rank, regret and normalized regret.

- **M12 — Real JEV Choice Quality**
  - Real `typesafe/jev-1.13` uses the same candidate/seed/budget protocol as the offline choice-quality benchmark.
  - Live/API experiment is optional and must not be used as a CI requirement.

- **M13 — Real JEV End-to-End Validation**
  - Treatment: Real JEV Destroy + Random Repair.
  - Control: Random Destroy + Random Repair.
  - Same seed, initial state, iteration budget and acceptance policy.

- **M14 — State-aware JEV Destroy context**
  - JEV receives an English state-aware candidate context.
  - JEV selects exactly one legal candidate ID.
  - The prompt contains current stack/container information and exposed-after-destroy information.
  - JEV must not invent actions or use future Oracle scores.

- **M15 — Objective semantics / research validity reset**
  - Explicitly documented that the current search objective is a **projected-search / greedy-completion proxy**.
  - Virtual Destroy/Repair operations are not physical container moves.
  - Historical numbers must not be presented as physical reconfiguration results.

- **M16 — Executable solution validity**
  - Added deterministic executable-plan validation.
  - `VlnsResult.search_state` is the best virtual search configuration before deterministic final completion.
  - This does **not** claim that the virtual search state is physically reachable at the reported move cost.

- **M17 — Real variable Destroy neighborhoods**
  - Destroy candidates can cover K=1..K stacks.
  - Non-adjacent stack combinations are supported.
  - Default behavior remains backward compatible.
  - Destroy remains a virtual search transformation.

- **M18 — Neighborhood protocol gate**
  - Actual executed iteration count is recorded.
  - Random Destroy candidate counts are recorded.
  - Matched K=1/K=2/K=3 comparison is implemented.
  - Reproducibility and zero-budget protocol tests exist.
  - **PR #14 is merged.**
  - The last CI failure was fixed; the merged M18 code is CI-green.

## 2. The exact current research question

Before testing Real JEV again, determine whether a larger variable Destroy neighborhood is actually useful.

The question is:

> **Does allowing Destroy to affect more stacks improve the resulting solution under a strictly matched offline protocol?**

Compare:

- **K=1:** Destroy affects exactly one stack.
- **K=2:** Destroy may affect one or two stacks.
- **K=3:** Destroy may affect one, two or three stacks.

The experiment is deliberately **offline** and uses:

- Random Destroy;
- Random Repair;
- the same initial state per seed;
- the same iteration budget;
- the same acceptance behavior;
- the same candidate generation rules except for maximum K.

Do **not** use Real JEV for this gate.

## 3. Important objective boundary

The current M18 result uses the existing project objective:

- final `evaluation.moves`;
- `best_projected_objective`;
- deterministic greedy completion.

This is **not yet a physical container-reconfiguration cost**.

Therefore:

- Do not call M18 evidence of real-world physical move reduction.
- Do not claim that K=2 or K=3 is physically better.
- M18 only answers whether the larger **virtual search neighborhood** is useful under the current projected-search protocol.

A later research stage must address physical/executable reconfiguration separately.

## 4. Preconditions for the local agent

Run from the repository root.

First verify the working tree and branch:

```powershell
git status
git branch --show-current
git log -1 --oneline
```

The working tree should be clean before running the benchmark.

Update the repository if necessary:

```powershell
git fetch origin
git pull --ff-only
```

Create/activate the project's normal Python environment according to the repository documentation.

Then verify the test suite:

```powershell
python -m pytest -q
```

**Do not continue to interpretation if the test suite fails.**

## 5. Run the M18 experiment locally

Use **10 matched seeds**, not the default 5-seed smoke configuration.

From the repository root:

```powershell
python experiments/compare_neighborhood_sizes.py `
  --seeds 1 2 3 4 5 6 7 8 9 10 `
  --iterations 50 `
  --max-k 3 `
  --output experiments/runs/m18-neighborhood-comparison.json `
  --report experiments/runs/m18-neighborhood-comparison.md
```

This command runs:

- 10 seeds;
- 50 requested iterations per seed and K;
- K=1, K=2, K=3;
- non-adjacent Destroy neighborhoods enabled;
- Random Destroy + Random Repair;
- no Real JEV;
- JSON and Markdown output.

The experiment itself is deterministic/reproducible for a given seed.

## 6. Required output files

After a successful run, these files must exist:

```text
experiments/runs/m18-neighborhood-comparison.json
experiments/runs/m18-neighborhood-comparison.md
```

The JSON contains:

- `seeds`;
- `iterations`;
- `max_k`;
- `adjacent_only`;
- one result row for every seed × K;
- summary statistics for every K;
- paired K-vs-K=1 deltas.

Each result row contains at least:

- `seed`;
- `k`;
- `iterations`;
- `requested_iterations`;
- `moves`;
- `projected_objective`;
- `feasible`;
- `mean_destroy_candidates`.

## 7. First protocol checks

The local agent must inspect the JSON before making any research conclusion.

### 7.1 Expected number of result rows

With 10 seeds and K=1,2,3:

```text
10 × 3 = 30 result rows
```

There must be exactly 30 rows.

### 7.2 Expected iterations

Every row must have:

```text
iterations = 50
requested_iterations = 50
```

If any row has fewer actual iterations, treat the experiment as **FAIL** and investigate before interpreting results.

### 7.3 Feasibility

Calculate feasibility separately for K=1, K=2 and K=3.

Expected:

```text
feasible_rate = 100%
```

If feasibility drops for a larger K, this is a serious finding. Do not declare the larger neighborhood better merely because its move count is lower.

### 7.4 Candidate count

`mean_destroy_candidates` should increase as K grows.

Do not require a particular numeric value; inspect the actual values.

The expected qualitative relationship is:

```text
K=1 < K=2 < K=3
```

If candidate counts do not behave this way, investigate the candidate-generation protocol before interpreting solution quality.

## 8. The main research comparison

The primary comparison is **paired by seed**.

For each seed:

```text
delta(K) = moves(K) - moves(K=1)
```

Interpretation:

- negative delta = K is better than K=1;
- zero delta = tie;
- positive delta = K is worse than K=1.

The JSON already contains `paired_deltas`.

For each of K=2 and K=3, calculate/report:

- number of wins;
- number of ties;
- number of losses;
- mean delta;
- median delta;
- minimum delta;
- maximum delta.

## 9. Decision rule

Do **not** choose K=2 or K=3 because it has:

- more candidates;
- a lower result on one seed;
- a lower unpaired mean alone.

A larger neighborhood is useful only if the paired results provide evidence that the larger neighborhood improves the search outcome without damaging protocol validity.

### Candidate interpretation

#### Case A — K=2 or K=3 clearly improves

If a larger K shows:

- all/most runs feasible;
- more candidates as expected;
- consistently favorable paired deltas;
- meaningful wins over K=1;
- no obvious protocol violation;

then select the best-supported K for the next stage.

The next stage is **Real JEV choice-quality / end-to-end testing using that neighborhood family**.

Do not silently change the protocol. Record the selected K explicitly.

#### Case B — larger K is mostly neutral

If K=2/K=3 produce mostly ties and no meaningful improvement:

- keep K=1 as the baseline;
- do not increase search complexity without evidence;
- proceed using K=1 unless a separate research question justifies another neighborhood.

#### Case C — larger K is worse

If K=2 or K=3 consistently worsens paired outcomes:

- keep K=1;
- document that larger neighborhoods did not help under this protocol;
- do not proceed with Real JEV using the worse neighborhood merely because it gives JEV more choices.

#### Case D — feasibility or protocol failure

If:

- actual iterations are not 50;
- result rows are missing;
- reproducibility fails;
- feasibility unexpectedly drops;
- candidate counts are inconsistent with K;

then **STOP**.

Fix the protocol/implementation first. Do not interpret the experiment.

## 10. What the local agent must NOT do

Do not:

1. Modify the JEV prompt during M18.
2. Add Real JEV calls.
3. Change Repair.
4. Change the acceptance rule.
5. Change the initial-state generator.
6. Change the random seed protocol.
7. Increase iterations after seeing unfavorable results.
8. Remove seeds because they look anomalous.
9. Select K based only on mean moves.
10. Present projected `moves` as physical container movement cost.
11. Invent or estimate missing results.
12. Rewrite the experiment until it produces a preferred outcome.

If an implementation problem is found, report it separately from the experimental result.

## 11. Reproducibility check

After the first successful run, run the exact same command again.

Compare the two JSON outputs.

The experiment is reproducible if the generated measurements are identical for the same code, seeds and parameters.

A simple PowerShell comparison is:

```powershell
python experiments/compare_neighborhood_sizes.py `
  --seeds 1 2 3 4 5 6 7 8 9 10 `
  --iterations 50 `
  --max-k 3 `
  --output experiments/runs/m18-neighborhood-comparison-repeat.json `
  --report experiments/runs/m18-neighborhood-comparison-repeat.md

Compare-Object `
  (Get-Content experiments/runs/m18-neighborhood-comparison.json) `
  (Get-Content experiments/runs/m18-neighborhood-comparison-repeat.json)
```

Expected: no meaningful differences.

If there are differences, investigate before proceeding.

## 12. Required local report for the human

After running the experiment, the local agent should report the following compact table:

| K | N | Feasible | Mean moves | Median moves | Mean candidates |
|---:|---:|---:|---:|---:|---:|
| 1 | 10 | ... | ... | ... | ... |
| 2 | 10 | ... | ... | ... | ... |
| 3 | 10 | ... | ... | ... | ... |

Then provide:

| Comparison | Wins | Ties | Losses | Mean Δ | Median Δ |
|---|---:|---:|---:|---:|---:|
| K=2 vs K=1 | ... | ... | ... | ... | ... |
| K=3 vs K=1 | ... | ... | ... | ... | ... |

Then give exactly one protocol decision:

```text
M18 STATUS: PASS — use K=<value> for next stage
```

or:

```text
M18 STATUS: PASS — keep K=1 baseline
```

or:

```text
M18 STATUS: FAIL — do not proceed; investigate <specific issue>
```

## 13. What happens after M18

### If M18 passes

The next research step is **M19: Real JEV under the validated neighborhood protocol**.

M19 should use the neighborhood family selected by M18.

The purpose is not merely to show that JEV can make API calls. The purpose is to test:

> Can Real JEV select useful Destroy neighborhoods when given the same legal candidate set and state-aware context, under a matched protocol?

The comparison must keep constant:

- seed;
- initial state;
- iteration budget;
- Repair;
- acceptance;
- candidate-generation protocol;
- objective/evaluation;
- fallback accounting.

Only the Destroy selector should differ when comparing Real JEV with its control.

### M19 should then lead to

1. Real JEV choice-quality measurement.
2. Real JEV vs Random Destroy end-to-end comparison.
3. Fallback/call/cost accounting.
4. Analysis of whether JEV decisions are actually useful.
5. Only after that, broader research conclusions.

## 14. Physical-objective warning for all future stages

The current project still has an important boundary:

```text
virtual VLNS search state
        ≠
physically executed container rearrangement
```

The current executable-plan validation proves that a final state can be completed by the deterministic executor, but it does not establish the physical cost of transforming the original state into every virtual intermediate search state.

Therefore future documentation must distinguish:

- **projected-search objective**;
- **executable greedy completion cost**;
- **physical reconfiguration cost**, if/when implemented;
- **exact optimum**, if/when an exact solver is implemented.

Do not merge these concepts into a single "moves" claim.

## 15. Current roadmap

```text
M14  State-aware JEV context                 DONE
M15  Objective semantics / validity reset    DONE
M16  Executable solution validity             DONE
M17  Variable Destroy neighborhoods           DONE
M18  Matched K=1/K=2/K=3 protocol gate        DONE (code + CI)
     |
     v
LOCAL STEP NOW:
     Run M18 with 10 seeds × 50 iterations
     Validate protocol + feasibility
     Analyze paired K=2/K=3 vs K=1
     |
     +---- FAIL --> fix protocol, rerun M18
     |
     +---- PASS --> select K
                    |
                    v
M19  Real JEV with validated neighborhood
                    |
                    v
Real JEV choice quality + end-to-end result
                    |
                    v
Further physical-objective / exact-reference work
```

## 16. Final instruction to the local AI agent

**Your immediate task is only M18 execution and analysis.**

Do not implement M19 yet.

Do not change the benchmark to obtain better results.

Run the exact 10-seed command, verify the protocol, perform the paired analysis, repeat once for reproducibility, and return the actual numbers.

The next implementation decision must be made from those measured results, not from expectations.
