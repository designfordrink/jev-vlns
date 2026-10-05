"""Audit the semantic gap between virtual Destroy/Repair and physical moves.

This is intentionally diagnostic: it does not change the solver. It shows how
a zero-cost configuration mutation can make the projected objective reach the
delivery lower bound without replaying physical moves from the initial state.
"""

import argparse

from jev_vlns.container_stack.state import ContainerStackState, make_seeded_state
from jev_vlns.search.vlns import projected_objective


def make_pre_marshalled_state(state: ContainerStackState) -> ContainerStackState:
    """Place every container on a stack matching its destination, at zero moves."""
    by_destination = {destination: [] for destination in state.stack_destinations}
    for container in state.containers:
        by_destination.setdefault(container.destination, []).append(container.id)

    stacks = tuple(
        tuple(by_destination[destination])
        for destination in state.stack_destinations
    )
    return ContainerStackState(
        stacks=stacks,
        containers=state.containers,
        stack_destinations=state.stack_destinations,
        moves=0,
        delivered=(),
    )


def audit_seed(seed: int) -> dict[str, float | int | bool]:
    initial = make_seeded_state(seed)
    marshalled = make_pre_marshalled_state(initial)
    return {
        "seed": seed,
        "container_count": len(initial.containers),
        "initial_moves": initial.moves,
        "initial_projected_objective": projected_objective(initial),
        "marshalled_moves": marshalled.moves,
        "marshalled_projected_objective": projected_objective(marshalled),
        "delivery_lower_bound": len(initial.containers),
        "teleport_reaches_lower_bound": (
            projected_objective(marshalled) == len(initial.containers)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    args = parser.parse_args()

    print("Objective semantics audit")
    print("=========================")
    for seed in args.seeds:
        row = audit_seed(seed)
        print(row)


if __name__ == "__main__":
    main()
