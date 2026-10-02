from typing import Sequence

from jev_vlns.core.action import Action

from .state import ContainerStackState, MAX_STACK_HEIGHT


def legal_actions(state: ContainerStackState) -> list[Action]:
    """Generate legal actions in a deterministic order."""

    actions: list[Action] = []

    # Delivery is listed first so simple greedy selectors can make progress.
    for source, stack in enumerate(state.stacks):
        if not stack:
            continue
        container_id = stack[-1]
        container = state.container(container_id)
        if container.destination == state.stack_destinations[source]:
            actions.append(
                Action(
                    id=f"deliver:{container_id}:{source}",
                    kind="deliver",
                    payload={"container_id": container_id, "stack": source},
                )
            )

    # Move actions are deterministic: source stack, destination stack.
    for source, stack in enumerate(state.stacks):
        if not stack:
            continue
        container_id = stack[-1]
        for destination in range(len(state.stacks)):
            if source == destination:
                continue
            if len(state.stacks[destination]) >= MAX_STACK_HEIGHT:
                continue
            actions.append(
                Action(
                    id=f"move:{container_id}:{source}:{destination}",
                    kind="move",
                    payload={
                        "container_id": container_id,
                        "source": source,
                        "destination": destination,
                    },
                )
            )
    return actions


def apply_action(state: ContainerStackState, action: Action) -> ContainerStackState:
    """Apply one legal action; reject malformed or illegal actions."""

    stacks = [list(stack) for stack in state.stacks]

    if action.kind == "deliver":
        source = int(action.payload["stack"])
        container_id = str(action.payload["container_id"])
        if not stacks[source] or stacks[source][-1] != container_id:
            raise ValueError("container is not the top item of the source stack")
        container = state.container(container_id)
        if container.destination != state.stack_destinations[source]:
            raise ValueError("container destination does not match stack")
        stacks[source].pop()
        return state.with_stacks(
            tuple(tuple(stack) for stack in stacks),
            moves=state.moves + 1,
            delivered=state.delivered + (container_id,),
        )

    if action.kind == "move":
        source = int(action.payload["source"])
        destination = int(action.payload["destination"])
        container_id = str(action.payload["container_id"])
        if source == destination:
            raise ValueError("source and destination must differ")
        if not 0 <= source < len(stacks) or not 0 <= destination < len(stacks):
            raise ValueError("stack index out of range")
        if not stacks[source] or stacks[source][-1] != container_id:
            raise ValueError("container is not the top item of the source stack")
        if len(stacks[destination]) >= MAX_STACK_HEIGHT:
            raise ValueError("destination stack is full")
        stacks[source].pop()
        stacks[destination].append(container_id)
        return state.with_stacks(
            tuple(tuple(stack) for stack in stacks),
            moves=state.moves + 1,
        )

    raise ValueError(f"unknown action kind: {action.kind}")


def action_is_legal(state: ContainerStackState, action: Action) -> bool:
    return action.id in {candidate.id for candidate in legal_actions(state)}


def apply_legal_action(
    state: ContainerStackState, action: Action
) -> ContainerStackState:
    if not action_is_legal(state, action):
        raise ValueError(f"illegal action: {action.id}")
    return apply_action(state, action)


def action_ids(actions: Sequence[Action]) -> list[str]:
    return [action.id for action in actions]
