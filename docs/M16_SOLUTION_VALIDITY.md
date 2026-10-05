# M16 — Solution Validity

## Goal

Make the distinction between a VLNS search configuration and an executable
solution explicit in the data model.

## What changed

VlnsResult now exposes:

- state: the final state after deterministic greedy completion;
- search_state: the best virtual configuration selected by VLNS before that
  completion.

search_state is explicitly **not** an executable trajectory from the initial
state.

A new ExecutablePlan represents an actual sequence of legal environment
actions. greedy_plan(initial_state) creates a deterministic executable
baseline, and assert_executable_plan independently replays it.

## Why this matters

The old result shape made it easy to interpret a complete final state as if it
were reached by physical actions from the initial state. That is false while
Destroy/Repair remain virtual search operators.

M16 therefore does not pretend to solve the reconfiguration problem. It makes
the semantic boundary explicit so the next stage can address it.

## Required next step

The physical benchmark still needs a deterministic way to convert a selected
virtual configuration into an executable action sequence from the original
initial state, or the benchmark must explicitly adopt a different objective
that does not claim physical reconfiguration cost.

That decision belongs to the next research stage; it is not hidden inside
M16.
