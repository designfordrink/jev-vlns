# M21 — Local Next Step: State Representation / Information Sufficiency

## Question

M20 confirmed poor Real JEV selection under the aligned Random-Repair expected-value objective. M21 asks:

Does the failure come from insufficient state/candidate representation available to JEV at decision time, or from JEV having difficulty performing simple counting/bookkeeping?

This is not prompt tuning. Only serialization changes.

## Frozen protocol

All variants use the same:

- Real typesafe/jev-1.13.
- Existing English JEV_DESTROY_QUESTION and JEV_DESTROY_OBJECTIVE.
- K=2 non-adjacent Destroy candidates.
- Random Repair and deterministic greedy completion.
- M20 Expected-Value Landscape evaluator.
- N=64 samples.
- Seeds 1 2 3 4 5.
- 50 iterations per seed.
- Same fallback and confidence threshold.
- EV/Oracle information is computed after the JEV response and never sent to JEV.

Expected: **4 x 5 x 50 = 1,000 decisions**.

## Variants

### A_compact — M20 control

Exact existing M20 state and candidate serializers.

### B_full_state

Every stack is expanded with index, destination, height, ordered container IDs, and each container's destination and priority. Candidate context remains the M20 context.

This tests whether reconstructing relationships between stack IDs and a separate container metadata table is a bottleneck.

### C_consequence

The candidate context explicitly shows each affected stack before Destroy, the top container removed, the exposed container, and the resulting stack after Destroy. Global state remains compact.

This tests whether mentally simulating the immediate Destroy effect is the bottleneck.

### D_decision_ready — arithmetic-light context

The environment computes small local relations that JEV would otherwise have to count or compare:

- whether each top container matches its stack destination;
- number of immediately deliverable top containers;
- remaining capacity per stack;
- whether the removed top and exposed container match the affected stack destination;
- counts of removed/exposed matches;
- sum of exposed-container priorities.

D contains only facts derived from the current state and the current Destroy candidate. It does **not** contain EV, Oracle values, regret, repair outcomes, final move counts, or any future evaluation.

This variant specifically tests the hypothesis:

> The information may already be available, but JEV may be weak at the simple arithmetic/bookkeeping required to extract it.

The environment performs the bookkeeping; JEV only consumes the resulting categorical/local facts.

## Why D is scientifically useful

B and C increase the amount of raw information available to JEV. D changes something different: it keeps the information local but precomputes elementary relations and counts.

Therefore:

- If B/C improve, the main bottleneck is likely representation/context reconstruction.
- If D improves while B/C do not, the main bottleneck is more likely arithmetic/bookkeeping.
- If none improve, straightforward context enrichment is insufficient and the single-step categorical-choice abstraction becomes the stronger suspect.

D is not intended as a production heuristic or as a new objective. It is a diagnostic intervention.

## Metrics

Primary:
1. Top-1 against the aligned EV target.
2. Mean rank.
3. Mean normalized regret.

Secondary:
- median rank;
- mean regret;
- fallback count;
- latency;
- input/output tokens;
- cost;
- final executable moves.

Do not claim statistical significance from five seeds.

## Gate

From repository root:

    python -m pytest -q

Then:

    python -m pytest -q tests/test_context_variants.py

Do not start live collection if either gate fails.

## Live command

    python experiments/run_m21_context_diagnostics.py --seeds 1 2 3 4 5 --iterations 50 --samples 64 --output experiments/runs/m21-context-diagnostics

The runner obtains its variant list from `context_variant_names()`, so the expected collection is four variants / 1,000 decisions.

## Interpretation

### Outcome A — representation bottleneck

One of B/C materially improves Top-1/rank/regret relative to A. The information-bottleneck hypothesis gains support. Next isolate the winning addition.

### Outcome B — bookkeeping bottleneck

D materially improves while B/C do not. This supports the hypothesis that JEV can use the information once elementary counting/comparison is externalized.

### Outcome C — no context intervention helps

A/B/C/D remain near the M20 baseline. Straightforward context enrichment is insufficient. Next test whether single-step categorical choice is the wrong abstraction and move toward ranking or rollout.

### Outcome D — search dynamics differ without choice-quality improvement

Final VLNS moves change but choice quality does not. Treat this as search-dynamics evidence; choice quality remains primary.

These are directional research outcomes, not claims of statistical significance.

## Prohibited

Do not change prompt, model, K, Random Repair, greedy completion, EV evaluator, candidate set, or seeds. Do not send EV/Oracle data to JEV. Do not add Top-K or rollout selection during M21.
