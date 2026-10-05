# JEV State-Aware Decision Context

## Purpose

Real JEV Destroy decisions must be made from the current state and the meaning of each legal candidate, not from opaque candidate IDs or generic descriptions.

The project therefore provides two layers of context:

1. **Global state** — the current Container Stack arrangement and metadata.
2. **Candidate context** — a compact, state-derived description of what each candidate changes or exposes.

This keeps the candidate-first boundary intact while reducing the amount of state JEV must reconstruct mentally.

## Destroy candidate context

For a Destroy candidate, the context contains:

- operation type (`destroy_top`);
- affected stack index;
- stack destination;
- stack height before destruction;
- top container ID, destination and priority;
- container exposed after destruction, when one exists.

The context is derived immediately before the JEV decision and is different for each candidate.

It does **not** contain:

- Oracle scores;
- downstream candidate rankings;
- regret;
- future evaluations;
- results of repair or completion.

Example:

    {
      "operation": "destroy_top",
      "affected_stacks": [
        {
          "index": 2,
          "destination": "C",
          "height_before": 3,
          "top": {
            "id": "C9",
            "destination": "A",
            "priority": 2
          },
          "exposed_after_destroy": {
            "id": "C3",
            "destination": "C",
            "priority": 1
          }
        }
      ]
    }

## JEV instructions

The Destroy prompt is intentionally explicit about the environment semantics:

- a container is delivered when it is on top of the stack whose destination matches the container destination;
- Destroy removes top containers;
- removal exposes the next container below;
- removed containers are repaired onto legal non-full stacks;
- the solver can then greedily complete the arrangement;
- JEV must choose exactly one locally generated candidate.

All runtime instructions sent to JEV are in English. Human-facing reports may be translated separately.

## Why this is methodologically safe

State-aware candidate context improves observability and reduces hidden inference, but it does not give JEV information that would be unavailable to a selector at decision time. It is computed from the same current state used by the solver.

The change also does not move legality, execution, validation, objective calculation, or Oracle scoring into JEV.

## Repair context

The same pattern should be used if a future experiment re-enables JEV Repair: a repair candidate should include only the current-state facts relevant to that placement decision. It must not include downstream outcome scores or future search results.
