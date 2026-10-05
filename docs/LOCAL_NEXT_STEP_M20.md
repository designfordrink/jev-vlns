# JEV-VLNS: M20 Local Execution Handoff — Diagnose Real JEV Choice Failure

> Audience: local AI agent working inside a local clone of designfordrink/jev-vlns.
> Purpose: explain why Real JEV performed worse than Random in M19 before changing prompt, neighborhood, Repair or objective.

## 1. M19 finding

M19 is merged and protocol-valid.

- K=2 fixed; non-adjacent neighborhoods enabled.
- Random Repair; strict-improvement acceptance; 50 iterations; seeds 1..5.
- 250/250 JEV calls successful; 0 fallbacks; all runs feasible.
- Real JEV lost all 5 paired seeds.
- Random mean = 15.8; Real JEV mean = 17.4; mean paired delta = +1.6.
- Choice quality: Top-1 = 0.004; mean rank = 9.84; mean normalized regret = 0.972.
- Three identical live executions changed exact per-seed deltas, but all had 0/5 JEV wins and positive mean delta.

Conclusion supported by M19: Real JEV made successful legal decisions, but its selections were systematically poor on the current K=2 candidate landscape.

Do not yet conclude why.

## 2. M20 research question

Determine which mechanism best explains the poor selections. Candidate hypotheses:

1. Objective misunderstanding.
2. State-aware context lacks useful information.
3. Candidate serialization is confusing or insufficient.
4. JEV has a harmful feature preference.
5. Candidate IDs/order create positional bias.
6. Relevant information is present but difficult for JEV to use.
7. Textual objective and local Oracle objective are misaligned.
8. Rank/regret measurement has a tie/flat-landscape artifact.
9. Live JEV is stochastic but has a stable harmful bias.
10. What is sent to JEV differs from what is scored afterward.

Do not choose a hypothesis before inspecting decision-level evidence.

## 3. Methodological lock

M20 must NOT change: JEV prompt, candidate serializer, K=2, non-adjacent=True, Random Repair, acceptance, seeds, iteration budget, objective, or candidate generation.

The only new capability is diagnostic recording.
Oracle scores may be computed after the JEV response, but must NEVER be included in the JEV request.

## 4. Preconditions

Run from repository root:

    git status
    git branch --show-current
    git log -1 --oneline
    git fetch origin
    git pull --ff-only
    python -m pytest -q

Use current main containing merged M19. Stop if tests fail.

## 5. Diagnostic live run

Repeat the M19 protocol: seeds 1..5, 50 iterations, K=2 exactly, non-adjacent enabled, Real JEV Destroy, Random Repair, strict-improvement acceptance.

Run a diagnostic version of the M19 choice-quality/end-to-end experiment that records EVERY JEV decision. Prefer existing M10 replay/trace infrastructure. If insufficient, add the smallest instrumentation necessary without changing solver behavior.

## 6. Required decision trace

For every JEV decision record:

### State/protocol
- seed; iteration; state hash/identifier if available; candidate count; K; accepted/rejected phase if available.

### Every candidate
- candidate ID; operation; affected stack indices; stack destination/height; top container ID/destination/priority; exposed-after-destroy container ID/destination/priority; exact serialized candidate text sent to JEV.

### JEV decision
- selected candidate ID; selected list position; success/failure; fallback; latency; token usage/cost if available.

### Post-response diagnostic data
For EVERY candidate, computed only after the response:
- local/Oracle projected objective; rank; regret; normalized regret; best/worst/tie flags.

For the selected candidate also record rank, normalized regret, objective and available candidate features.

## 7. Security

Never write API keys, Authorization headers or raw .env files into the trace or repository. Sanitize request objects if necessary.

## 8. Mandatory validation

Expected decision count: 5 × 50 = 250.

Verify for every decision:
- selected candidate ID is one of the supplied candidate IDs;
- K=2 protocol is unchanged;
- no Oracle value appears in the JEV request;
- candidate serialization in the trace is exactly what was sent.

If any of these fail, stop and report an implementation/measurement failure.

## 9. Required analyses

### A. Recompute choice quality
From the trace calculate Top-1, mean rank, mean regret and normalized regret. Break them down by seed, iteration range and candidate count.

### B. Positional bias
Calculate selection frequency by candidate position and ID. Calculate mean Oracle rank by candidate position. Check whether JEV disproportionately selects first/last/small subsets of positions or IDs.

Do not change candidate ordering during this diagnostic.

### C. Feature bias
Compare selected candidates with all candidates for available features: affected stack count, stack height, top priority, top destination, exposed destination, shared destination, adjacency/non-adjacency, and candidate position.

Report correlations as diagnostics, not causal claims.

### D. Search-phase linkage
For each decision record whether its selected candidate led to an accepted iteration, rejected iteration, improved projected objective or unchanged/worse objective.

Use this only to explain the existing M19 result; do not replace the primary M19 metric.

## 10. Required artifacts

Create:

    Output/M20_JEV_FAILURE_ANALYSIS.md
    Output/m20-jev-decision-trace.json

If the raw trace is too large, keep it local and commit only a sanitized/aggregated report.

The report must contain:

1. Protocol validation.
2. Decision count and legality.
3. M19 vs M20 choice-quality comparison.
4. Candidate-position/ID bias table.
5. Feature diagnostics.
6. State/iteration/candidate-count breakdown.
7. Accepted/rejected linkage.
8. Evidence assessment for every hypothesis.

## 11. Decision rule

Case A — implementation/measurement issue:
M20 STATUS: FAIL — measurement/implementation issue

Case B — positional/formatting bias:
M20 STATUS: DIAGNOSTIC — positional/formatting bias detected

Case C — objective/context mismatch suspected:
M20 STATUS: DIAGNOSTIC — objective/context mismatch suspected

Case D — sound measurement and systematic poor selection:
M20 STATUS: CONFIRMED — systematic poor selection

Case E — no clear cause:
M20 STATUS: INCONCLUSIVE — additional controlled diagnostic needed

Do not change the prompt automatically for any case.

## 12. What NOT to do

Do not change prompt, K, candidate ordering, serializer, Repair, acceptance, objective or seeds. Do not send Oracle scores to JEV. Do not remove bad seeds. Do not optimize until Top-1 improves. Do not claim statistical significance from this sample. Do not invent missing telemetry.

## Final instruction

Run M20 as a controlled diagnostic of the already-observed M19 failure. The goal is not to make JEV better yet; the goal is to identify the most plausible mechanism behind the poor decisions with decision-level evidence.