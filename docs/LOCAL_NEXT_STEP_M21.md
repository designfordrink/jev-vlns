# M21 — Local Next Step: State Representation / Information Sufficiency

## Question

M20 confirmed poor Real JEV selection under the aligned Random-Repair expected-value objective. M21 asks:

Does the failure come from insufficient state/candidate representation available to JEV at decision time?

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

Expected: 4 x 5 x 50 = 1000 decisions.

## Variants

### A_compact — M20 control

Exact existing M20 state and candidate serializers.

### B_full_state

Every stack is expanded with index, destination, height, ordered container IDs, and each container's destination and priority. Candidate context remains the M20 context.

This tests whether reconstructing relationships between stack IDs and a separate container metadata table is a bottleneck.

### C_consequence

The candidate context explicitly shows each affected stack before Destroy, the top container removed, the exposed container, and the resulting stack after Destroy. Global state remains compact.

This tests whether mentally simulating the immediate Destroy effect is the bottleneck.

No variant contains EV, Oracle scores, regret, future evaluation results, or final outcomes.

### D_decision_ready — arithmetic-light context

This variant is added because JEV is known to be weak at explicit counting and relational arithmetic. The environment therefore precomputes small, local, decision-relevant facts such as whether a top/exposed container matches its stack destination and the count of such matches.

This is intentionally **not** the EV objective. It contains no repair outcome, Oracle score, regret, final move count, or future evaluation. The hypothesis is narrower: if JEV cannot reliably perform the simple bookkeeping required to compare candidates, removing that arithmetic burden may improve selection quality.

D is therefore the most direct test of the distinction between **information insufficiency** and **reasoning/computation insufficiency**.

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

## Interpretation

Outcome A: one representation materially improves Top-1/rank/regret. The information-bottleneck hypothesis gains support. Next isolate the winning addition.

Outcome B: all remain near M20. Straightforward context enrichment is insufficient. Next test whether single-step categorical choice is the wrong abstraction and move toward ranking or rollout.

Outcome C: final VLNS moves change but choice quality does not. Treat this as search-dynamics evidence; choice quality remains primary.

## Prohibited

Do not change prompt, model, K, Random Repair, greedy completion, EV evaluator, candidate set, or seeds. Do not send EV/Oracle data to JEV. Do not add Top-K or rollout selection during M21.
