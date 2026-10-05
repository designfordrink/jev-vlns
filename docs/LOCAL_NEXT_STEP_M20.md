# JEV-VLNS: M20 Local Execution Handoff — Objective & Oracle Alignment

> Audience: local AI agent working inside a local clone of `designfordrink/jev-vlns`.
> Purpose: repair the methodological mismatch exposed by M19 before diagnosing or tuning the JEV prompt.
>
> **M20 is not a prompt-optimization stage. It is an objective/oracle-alignment stage.**

## 1. Why M20 changed

M19 established a real negative result under a controlled K=2 protocol:

- K=2 fixed; non-adjacent neighborhoods enabled.
- Real JEV Destroy + Random Repair.
- Strict-improvement acceptance.
- 50 iterations; seeds 1..5.
- 250/250 JEV calls successful; 0 fallbacks; all runs feasible.
- Real JEV lost all 5 paired seeds.
- One reported run: Random mean = 15.8, Real JEV mean = 17.4, mean paired delta = +1.6.
- Choice-quality report: Top-1 = 0.004, mean rank = 9.84, mean normalized regret = 0.972.
- Repeated live runs changed exact per-seed deltas because JEV is stochastic, but all repeated runs had 0/5 JEV wins and a positive mean delta.

M19 is therefore a useful negative baseline.

However, the previous M12/M19 choice-quality analysis used an **Oracle with best possible Repair**, while the actual M19 solver uses **Random Repair**. That means the measured Oracle landscape does not exactly represent the downstream objective that JEV is actually optimizing in M19.

This is the central methodological problem M20 must address.

## 2. M20 research question

> **When each Destroy candidate is evaluated under the same downstream Random Repair + deterministic greedy completion process that M19 actually uses, does Real JEV still select poor candidates?**

More formally, for a current state (s) and Destroy candidate (d), define the M19-aligned target as:

```
EV_N(s, d) =
    mean over N Random-Repair outcomes of:
        final executable moves after deterministic greedy completion
```

Lower is better.

M20 must determine whether the very poor M19 choice-quality result survives when candidates are scored against this **expected downstream landscape** rather than against best possible Repair.

## 3. Research objective hierarchy

M20 must explicitly distinguish three different objectives.

### 3.1 Projected search objective

The current VLNS search operates on virtual Destroy/Repair configurations. This is the objective used by the existing search machinery.

It is useful for comparing search configurations, but it is **not automatically equivalent to physical container-rehandling cost**.

### 3.2 Executable objective

The deterministic greedy completion produces an executable plan and a concrete move count.

This is currently the closest executable outcome used by the benchmark.

M20 must continue to call this a **greedy-completion / executable proxy**, not an exact optimum.

### 3.3 Exact optimum

For sufficiently small instances, the true minimum executable move count should eventually be obtained with an exact solver such as BFS/A*/DP.

M20 does **not** need to implement the exact solver unless it is already available and required for validation. Exact optimum is a later reference layer.

## 4. M20 target landscape

The target used for JEV choice-quality must match the actual M19 downstream policy:

```
state
  ↓
Destroy candidate d
  ↓
Random Repair
  ↓
deterministic greedy completion
  ↓
final executable move count
```

For each candidate:

```
EV_N(d) = mean(final_moves_1 ... final_moves_N)
```

Recommended N values:

- N=32 — fast diagnostic.
- N=64 — primary M20 setting if runtime is acceptable.
- N=128 — robustness check.

The same candidate, state, and repair policy must be used for every compared selector.

Report at least:

- mean;
- median;
- standard deviation;
- p10/p90 or another clearly documented spread measure;
- sample count N.

The mean is the primary expected-value target. Distributional statistics are diagnostics.

## 5. Critical anti-leakage rule

The expected-value / Oracle evaluation is **diagnostic only**.

JEV must receive:

- the current state-aware context;
- the legal candidate list;
- the existing M20/M19 prompt;
- the existing candidate serialization.

JEV must **not** receive:

- Random Repair outcomes;
- expected values;
- means/medians/quantiles;
- Oracle scores;
- candidate ranks;
- regrets;
- future iteration outcomes.

All downstream evaluation happens **after** the JEV decision.

The experiment must preserve the causal order:

```
JEV sees candidates → JEV selects → evaluator scores candidates
```

not:

```
evaluator scores candidates → JEV sees scores → JEV selects
```

## 6. What M20 must keep fixed

To make M20 a valid continuation of M19, keep all of the following unchanged:

- JEV model/API configuration;
- JEV prompt;
- candidate serializer;
- candidate IDs and ordering;
- K=2 exactly;
- `destroy_include_non_adjacent=True`;
- Random Repair policy;
- deterministic greedy completion;
- strict-improvement acceptance where applicable;
- seed set 1..5 for the matched M19 comparison;
- 50 search iterations;
- candidate-generation logic;
- state initialization;
- primary final-moves metric.

Do **not** tune the prompt or change the neighborhood based on M20 observations.

The only methodological addition is the M19-aligned expected-value evaluator and its diagnostics.

## 7. Why K=2 remains locked

M18 compared K=1, K=2 and K=3 under the same 50-iteration protocol and 10 seeds:

| K | Mean projected moves | Mean candidates |
|---:|---:|---:|
| 1 | 15.10 | 4.50 |
| 2 | 14.80 | 12.47 |
| 3 | 14.80 | 20.60 |

K=2 was selected as the smallest neighborhood showing the observed improvement over K=1 without the larger K=3 candidate expansion.

M20 is a methodological alignment experiment, not a neighborhood search. Therefore K=2 remains fixed.

## 8. Required implementation

Add the smallest reusable evaluator needed to compute the expected downstream value of a Destroy candidate.

A suitable location is:

```
src/jev_vlns/evaluation/expected_value.py
```

or another location consistent with the existing repository architecture.

The evaluator should conceptually provide:

```text
evaluate_destroy_candidate(
    state,
    candidate,
    repair_policy=RandomRepair,
    completion_policy=GreedyCompletion,
    samples=N,
    seed=...
) -> ExpectedValueStats
```

The exact API may follow existing project conventions.

### Required properties

1. Deterministic when the same seed, state, candidate and N are supplied.
2. Uses exactly the same Random Repair semantics as M19.
3. Uses exactly the same deterministic greedy completion.
4. Does not mutate the caller's state.
5. Does not change the actual M19 solver path.
6. Does not call JEV.
7. Does not expose its results to JEV.
8. Makes the random sampling seed explicit and reproducible.

## 9. Sampling protocol

For every decision state:

1. Generate the legal K=2 Destroy candidates exactly as M19 does.
2. Preserve the existing candidate ordering.
3. Ask JEV to select exactly one candidate.
4. After the JEV response, evaluate **every candidate** independently.
5. For each candidate, run N Random Repair samples.
6. Complete each repaired configuration with the deterministic greedy policy.
7. Record final executable move count.
8. Aggregate the N outcomes into expected-value statistics.
9. Rank candidates by mean expected value; lower is better.
10. Compare the JEV-selected candidate against this M19-aligned landscape.

Important: the JEV request must be constructed and sent **before** these candidate evaluations are performed.

## 10. Required choice-quality metrics

Recompute the previous choice-quality metrics using the new expected-value target.

### Primary

- **Top-1**: fraction of decisions where JEV selected a candidate tied for best expected value.
- **Mean rank**: rank of the selected candidate by expected value.
- **Mean regret**:

```
selected_EV - best_EV
```

- **Mean normalized regret**:

```
(selected_EV - best_EV) /
(max_EV - best_EV)
```

When all candidates have identical EV, normalized regret must be defined explicitly and reported as 0 for a tied/best decision rather than producing an artificial penalty.

### Additional recommended metrics

If inexpensive to compute:

- Top-3;
- Top-5;
- median rank;
- Spearman correlation between JEV ranking/proxy and expected-value ranking, if a JEV ranking is available;
- Kendall correlation, if appropriate.

JEV currently selects one candidate rather than returning a ranking, so ranking metrics must not be invented. Top-K metrics only apply if the protocol is explicitly extended to collect a ranking.

## 11. Required experiment

Create a focused M20 experiment, for example:

```
experiments/run_m20_expected_value_landscape.py
```

The experiment must support:

- `--samples 32|64|128`;
- fixed seeds 1..5 by default;
- 50 iterations;
- K=2 exactly;
- non-adjacent enabled;
- existing Real JEV configuration;
- deterministic output paths.

The experiment should produce:

```
Output/m20-expected-value-landscape.json
Output/M20_EXPECTED_VALUE_LANDSCAPE.md
```

If a separate implementation/audit report is useful, it may be added, but avoid producing redundant artifacts.

## 12. Required validation

Before running live JEV:

```bash
git status
git branch --show-current
git log -1 --oneline
git fetch origin
git pull --ff-only
python -m pytest -q
```

Then validate the evaluator offline.

Minimum tests:

### A. Reproducibility

Same state + candidate + seed + N → identical sample outcomes and aggregates.

### B. Candidate isolation

Changing candidate A must not change candidate B's sampled evaluation when both use their own explicit deterministic sampling seeds.

### C. State immutability

Evaluating a candidate must not mutate the input state.

### D. Objective consistency

Each sample's reported value must equal the move count of its deterministic executable completion.

### E. No JEV dependency

Expected-value evaluation must work without a JEV API key.

### F. No information leakage

The expected-value result must not be present in the JEV request payload, prompt, candidate serializer, or selection context.

### G. Flat-landscape handling

If all candidates have equal expected value:

- every candidate is best/tied;
- Top-1 counts the JEV choice as correct;
- regret = 0;
- normalized regret = 0.

## 13. Required M20 analyses

### A. M19 Oracle vs M20 expected-value landscape

Directly compare:

1. previous best-repair Oracle landscape;
2. new Random-Repair expected-value landscape.

The goal is to quantify how much the target landscape changes.

Do not silently substitute one for the other.

### B. JEV choice quality under the aligned target

Report:

| Metric | M19 / best-repair Oracle | M20 / Random-Repair EV |
|---|---:|---:|
| Top-1 | 0.004 | ... |
| Mean rank | 9.84 | ... |
| Mean regret | ... | ... |
| Mean normalized regret | 0.972 | ... |

Use exact values from the generated artifacts; do not copy numbers that are not recomputed.

### C. Landscape stability

Compare N=32, N=64 and N=128 if runtime permits.

For the same state/candidate, check whether:

- candidate ordering by EV is stable;
- the best candidate changes;
- JEV regret estimates change materially.

### D. End-to-end interpretation

Do **not** immediately rerun M19 with a changed prompt.

First answer:

> Does JEV remain poor when judged against the downstream objective it actually controls?

Possible outcomes:

**Outcome A — Alignment explains much of the failure**

The best-repair Oracle made JEV look worse than it actually was under Random Repair.

→ M20 identifies a measurement mismatch. Do not tune prompt yet.

**Outcome B — JEV remains poor under aligned EV**

Top-1 remains low, mean rank remains poor, and regret remains high.

→ The M19 negative result is strengthened. Proceed to representation/context diagnostics.

**Outcome C — EV landscape is too noisy at small N**

Ranks or best candidates change materially between N=32/64/128.

→ Increase N or use a confidence-aware comparison before drawing conclusions.

**Outcome D — Implementation/measurement failure**

Any leakage, non-reproducibility, state mutation, objective inconsistency or protocol drift.

→ M20 FAIL. Fix the measurement before interpreting results.

## 14. Exact solver is a separate reference layer

M20 must not claim that expected-value Oracle equals the global optimum.

The expected-value landscape answers:

> Which Destroy candidate has the best expected downstream result under the **actual Random Repair policy**?

The exact solver, to be developed later for small instances, answers:

> What is the true minimum executable move count?

These are different questions.

The intended future reference stack is:

```
Random Repair EV
        ↓
Exact small-instance optimum
        ↓
JEV choice / ranking
```

The exact solver should eventually allow us to quantify the gap between the policy-level landscape and the true problem optimum.

## 15. What M20 must NOT do

Do not:

- change the JEV prompt;
- change candidate serialization;
- change candidate ordering;
- change candidate IDs;
- change K;
- change Random Repair;
- change acceptance;
- change seeds;
- change iteration budget;
- send EV/Oracle scores to JEV;
- use future search outcomes as JEV input;
- claim statistical significance from five seeds;
- treat greedy completion as the exact optimum;
- call the expected-value evaluator an exact Oracle;
- tune the system until Top-1 improves.

## 16. Security

Never write:

- API keys;
- Authorization headers;
- raw `.env` contents;
- private credentials

to experiment outputs, traces, JSON artifacts or Git history.

Sanitize request/response diagnostics before persisting them.

## 17. Definition of done

M20 is complete when all of the following are true:

- [ ] The M19-vs-M20 objective mismatch is explicitly documented.
- [ ] A reproducible Random-Repair expected-value evaluator exists.
- [ ] The evaluator uses the same downstream policy as M19.
- [ ] Unit tests cover reproducibility, isolation, immutability, objective consistency, leakage and flat landscapes.
- [ ] At least one matched live M20 run is completed with N=64, or a documented reason is given if N=64 is computationally impractical.
- [ ] N=32/64/128 stability is evaluated when feasible.
- [ ] Choice quality is recomputed against the aligned EV target.
- [ ] The report distinguishes policy-level expected value from exact optimum.
- [ ] No prompt/neighborhood/Repair tuning is introduced.
- [ ] The next research step is selected from the M20 outcome, not assumed in advance.

## 9A. Exact Expected-Value Landscape protocol

### 9A.1 Experimental unit

The fundamental unit is one frozen JEV decision state: one outer run seed at one VLNS iteration. All legal K=2 Destroy candidates at that state form one matched candidate set.

For each decision state and each candidate, run exactly N independent Random-Repair samples followed by the existing deterministic greedy completion. With N=64, a decision containing C candidates produces C × 64 candidate-level samples.

The primary experiment is 5 seeds × 50 iterations = exactly 250 decision states, assuming no protocol failure. The actual total number of candidate-level samples must be reported from the artifact.

### 9A.2 Causal ordering

For every decision the order is mandatory:

1. Freeze the current decision state.
2. Generate the legal K=2 candidates in the existing order.
3. Build and send the unchanged JEV request.
4. Receive and validate exactly one selected candidate.
5. Only after the JEV response, evaluate every candidate with Random Repair + Greedy Completion.
6. Aggregate candidate samples and calculate EV/rank/regret.
7. Continue the actual solver from the original state using the JEV-selected candidate.

EV results must never be available to JEV. This is a diagnostic evaluator, not part of the decision path.

### 9A.3 Random-seed derivation

Do not use process-global RNG state. Define:

- `run_seed`: outer experiment seed, 1..5;
- `iteration`: zero-based VLNS iteration;
- `state_key`: deterministic identifier of the frozen decision state;
- `sample_index`: zero-based sample index, 0..N-1.

Derive each sample seed deterministically from:

```text
sample_seed = uint64(SHA256(
  "m20-ev-v1|" + run_seed + "|" + iteration + "|" + state_key + "|" + sample_index
)[0:16])
```

The exact encoding must be unambiguous. **Candidate ID must not be included in the seed.**

This creates a matched/common-random-number design: candidate A and candidate B at the same decision use the same sample-index seeds. Each candidate/sample still receives a fresh RNG instance, so evaluation order cannot affect results.

If the existing Random Repair implementation cannot accept an explicit RNG, introduce the smallest boundary change needed to make the diagnostic evaluator deterministic without changing M19 solver semantics.

### 9A.4 Sample execution

For each candidate and sample:

1. Start from an immutable copy of the frozen decision state.
2. Apply exactly that Destroy candidate.
3. Initialize a fresh RNG from the prescribed sample seed.
4. Execute exactly one existing Random Repair outcome.
5. Run the existing deterministic greedy completion.
6. Validate the executable plan.
7. Record the resulting `final_moves`.

No diagnostic evaluation may mutate the state used by the actual solver.

### 9A.5 Aggregation

For candidate d with outcomes x1..xN, calculate:

```text
mean   = sum(x) / N
median = median(x)
std    = sample standard deviation(x)
min    = min(x)
max    = max(x)
p10    = 10th percentile(x)
p90    = 90th percentile(x)
```

The raw sample vector must be retained in JSON when practical so aggregate numbers are auditable.

A candidate is rankable only when all N requested samples are successful and produce valid executable move counts. Do not silently impute, drop, or replace failed samples. A missing sample in the primary run is a protocol failure unless a predeclared missing-data rule is added before execution.

Rank candidates by ascending mean EV. Lower is better.

### 9A.6 Tie rule

Use a predeclared tolerance of `1e-9` when comparing floating-point mean EVs. Candidates within that tolerance of the minimum are tied for best.

Do not break a tie by candidate ID for Top-1 correctness. Every tied-best candidate counts as Top-1.

If all candidates are tied, regret and normalized regret are both zero.

### 9A.7 Choice-quality metrics

For selected candidate j:

```text
best_EV = min(candidate_mean_EV)
worst_EV = max(candidate_mean_EV)
regret = selected_EV - best_EV
normalized_regret = regret / (worst_EV - best_EV)
```

If `worst_EV == best_EV`, normalized regret = 0.

Use competition ranking: equal EVs share the same rank. Report Top-1, mean rank, median rank, mean regret, median regret, mean normalized regret and median normalized regret.

### 9A.8 N stability protocol

N=64 is the primary setting. Run N=32 and N=128 as stability checks when feasible.

All three runs must use the same decision states and the same seed schedule. N=32 must be the first 32 samples of N=64; N=64 must be the first 64 samples of N=128.

Compare per decision:

- best-candidate identity 32→64 and 64→128;
- selected-candidate rank;
- selected-candidate regret;
- Top-1 status;
- complete candidate ordering where meaningful.

Report best-candidate stability and the fraction of decisions whose JEV Top-1 status changes between N values. Do not treat N=32/64/128 as unrelated Monte-Carlo experiments.

### 9A.9 Mandatory evaluator tests

Before the live experiment, tests must verify:

- same state + candidate + seed schedule + N gives identical raw samples;
- evaluating candidates A,B,C gives identical results to C,A,B;
- changing candidate A does not alter candidate B's result;
- the input state is unchanged after evaluation;
- each reported `final_moves` equals the executable completion move count;
- evaluator works without JEV credentials;
- EV never appears in the JEV request/context;
- flat landscapes produce Top-1=true, regret=0 and normalized regret=0;
- the first 32 samples of N=64 equal the N=32 samples, and the first 64 of N=128 equal N=64.

## Final instruction to the local agent

Treat M20 as a **methodological correction**, not as another attempt to make JEV win.

The key question is:

> **Was JEV actually making bad decisions, or were we measuring its decisions against the wrong downstream landscape?**

Only after this question is answered should the project move to state-representation/context diagnostics, exact small-instance reference solving, or a JEV Top-K → deterministic rollout architecture.