# Objective Semantics

## Status

M15 research reset. This document defines the distinction between the current
VLNS search objective and an executable physical-move objective.

## The problem

Destroy and Repair are currently search operators. They mutate a candidate
configuration without calling the physical action executor and therefore do
not increase the state's moves counter.

Consequently:

- projected_objective(state) is the number of moves required by the
  deterministic greedy completion from that state;
- it is not, by itself, the number of physical moves required to transform the
  original initial state into that state;
- a candidate configuration can therefore be reached by the search with zero
  recorded physical cost.

This is a real semantic distinction, not merely an implementation detail.

## Decision for the research reset

The main benchmark will use **physical-move semantics** for its final reported
solution quality.

The VLNS Destroy/Repair operators remain search perturbations, but their
virtual mutation must never be presented as an executable physical action
sequence.

Therefore the project will maintain three explicitly different quantities:

1. **Search projected objective** — the current greedy-completion proxy used
   while developing the VLNS search.
2. **Executable objective** — the cost of a legal action sequence replayed from
   the original initial state.
3. **Exact optimum** — the minimum executable objective for small instances,
   supplied by the exact reference solver.

Only (2) is the primary end-to-end benchmark metric after the M15 migration.
(1) remains a diagnostic heuristic metric. (3) is the reference on instances
where exact search is feasible.

## Required validity contract

A result is not an executable solution merely because:

- state.is_complete is true; or
- evaluate(state).feasible is true.

A solution is executable only if an independent validator can replay its full
action sequence from the original initial state and confirm that every action
was legal and that the final state is complete.

## Transition policy

Until the executable objective is wired into the solver, existing historical
benchmark numbers must be treated as **configuration-search / greedy-proxy
results**, not as validated physical-move results.

No new live JEV conclusion should be drawn from the old objective.

## Audit

experiments/audit_objective_semantics.py constructs a deliberately
pre-marshalled configuration at zero recorded moves and measures its greedy
completion objective. If that objective reaches the delivery lower bound, the
audit demonstrates why the old metric cannot be interpreted as the physical
cost from the initial state.

## Next implementation steps

1. Make solver results carry an explicit executable plan or a clearly marked
   non-executable search state.
2. Add independent replay validation.
3. Introduce an exact small-instance reference.
4. Only then replace the end-to-end benchmark metric with the validated
   executable objective.
