# Research Remediation Plan — M15+

## Purpose

This plan resets the experimental protocol before any live JEV conclusion is treated as evidence. The required order is:

1. Objective semantics
2. Solution validity
3. Real VLNS
4. Exact reference
5. Correct choice-quality benchmark
6. Live JEV M12
7. End-to-end M13

The key rule is: do not advance to a later stage while an earlier stage has an unresolved methodological blocker.

## 1. Objective semantics

### Problem

The current Destroy/Repair operators mutate the configuration without increasing moves. The evaluator therefore measures greedy completion from a virtually rearranged configuration, not necessarily the cost of an executable plan from the initial state.

### Decision

The benchmark will distinguish two concepts:

- search-state transformation: internal Destroy/Repair perturbation used by VLNS;
- physical execution cost: cost of a legal action sequence from the original initial state.

The primary research objective must be explicitly defined before new results are collected.

### Work

- Add a formal objective contract to the TRD.
- Define whether the benchmark is physical-move optimization or pre-marshalled configuration optimization.
- Prefer physical-move semantics for the main benchmark.
- Keep any virtual/pre-marshalling interpretation as a separate diagnostic experiment.
- Add an objective audit experiment that demonstrates the difference.
- Record initial objective, search objective, and final executable objective separately.

### Done when

A reader can answer: “What exactly does one unit of moves mean, and can the reported final solution be executed from the initial state?”

## 2. Solution validity

### Problem

VlnsResult currently returns a final state but not a complete executable action sequence. Feasibility checks completion, not replayability from the initial state.

### Work

- Introduce an explicit execution/replay representation.
- Store the initial state and final action sequence for validated solutions.
- Add a validator that replays every action from the initial state using the legal-action boundary.
- Verify legality, container conservation, delivery validity, completeness, and reported physical cost.
- Add tests for successful replay and deliberately invalid/tampered traces.
- Do not call a solution valid merely because state.is_complete is true.

### Done when

Every reported solution can be independently replayed from initial_state and either passes validation or is rejected.

## 3. Real VLNS

### Problem

The current neighborhood is small and fixed: one stack or two adjacent stacks. This is not a convincing Variable Large Neighborhood Search.

### Work

- Replace the fixed neighborhood generator with configurable neighborhood families.
- Support k=1, k=2, k>=3, non-adjacent stack combinations, and configurable/adaptive k.
- Make neighborhood size a search parameter.
- Record candidate counts and neighborhood size per iteration.
- Keep candidate generation deterministic and legality outside JEV.
- Separate the small MVP neighborhood from the actual VLNS benchmark.
- Add tests for coverage, determinism, and preservation of container multiset.
- Keep Oracle diagnostics behind an explicit measurement mode.

### Done when

The benchmark genuinely varies neighborhood size/structure and JEV chooses among a materially non-trivial candidate set.

## 4. Exact reference

### Problem

Current Oracle/regret uses greedy rollout, so it is only optimal relative to the greedy proxy.

### Work

- Implement an exact solver/reference for small instances.
- Define the exact state transition model and objective.
- Cross-check exact solver against replay validation.
- Use exact downstream cost where computationally feasible.
- Keep greedy rollout as a separate heuristic baseline.
- Compare greedy baseline, exact optimum, local Oracle choice, Random choice, and JEV choice.
- Measure the gap between greedy proxy and exact optimum.

### Done when

The project can state when Oracle means exact and when it only means best according to greedy rollout.

## 5. Correct choice-quality benchmark

### Problem

Current choice-quality metrics can hide failures, over-credit ties/flat landscapes, and compare decisions reached on different trajectories.

### Work

- Define a fixed decision-state benchmark.
- At each sampled state, expose exactly the same candidate set to Random, JEV, heuristic controls, and reference evaluators.
- Handle inf explicitly; never silently drop invalid/worst choices.
- Define tie-aware Top-1 and top-k metrics.
- Add a chance-corrected or tie-aware Random baseline.
- Report flat-landscape rate separately.
- Report mean rank, regret, normalized regret, and exact-optimal choice where available.
- Distinguish matched-state decision quality from end-to-end solver quality.
- Preserve the Oracle diagnostic boundary: future outcomes are never sent to JEV.

### Done when

Choice quality is measured on matched decision states and cannot improve merely because the landscape is flat or a bad choice is omitted.

## 6. Live JEV M12

### Gate

Do not run live M12 until stages 1–5 are green.

### Protocol

- Fix model/version, prompt, candidate order policy, seeds, instance set, and budget.
- All JEV prompts/context remain English.
- Run multiple seeds and multiple instance difficulties.
- Record success, timeout, API error, malformed response, invalid choice, low confidence, fallback, latency, tokens, and provider cost.
- Do not silently classify fallback as JEV success.
- Run matched-state choice-quality evaluation first.
- Analyze per-seed and per-instance variance.

### Done when

There is an auditable live dataset showing what JEV selected, at what cost, and how often it failed or fell back.

## 7. End-to-end M13

### Gate

Run only after live M12 has passed the interpretation and telemetry checks.

### Protocol

Treatment: Real JEV Destroy + fixed Repair.

Control: Random Destroy + same fixed Repair.

Keep identical: initial state, instance, seed, iteration budget, acceptance, candidate generator, objective, and validator.

Primary metric: validated executable objective.

Secondary metrics: paired delta, wins/ties/losses, fallback rate, latency, token usage, USD cost, feasibility/validation failures.

Use enough seeds/instances for uncertainty estimates. Do not claim superiority from a single series.

## Engineering hygiene after the methodological gates

These are important but do not replace the seven research gates:

- fix API-key repr leakage;
- bind credential usage to configured host;
- align timeout defaults;
- add .gitignore and license;
- add ruff/type checking;
- remove dead acceptance code;
- fix actual iteration count;
- use an enum/registry for benchmark modes;
- improve CI permissions and dependency caching;
- remove stale roadmap/documentation contradictions.

## Decision rule

No live JEV result becomes a project conclusion until:

objective semantics → replay validity → real VLNS → exact reference → matched-state choice quality → live M12 → end-to-end M13

has been completed in this order.
