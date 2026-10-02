from dataclasses import dataclass
from collections.abc import Sequence

from jev_vlns.container_stack.state import ContainerStackState, MAX_STACK_HEIGHT
from .destroy import PartialSolution


@dataclass(frozen=True)
class RepairCandidate:
    id: str
    container_id: str
    destination_stack: int
    description: str


def generate_repair_candidates(
    partial: PartialSolution,
) -> list[RepairCandidate]:
    candidates: list[RepairCandidate] = []
    for container_id in partial.removed:
        for stack_index, stack in enumerate(partial.state.stacks):
            if len(stack) >= MAX_STACK_HEIGHT:
                continue
            candidates.append(
                RepairCandidate(
                    id=f"place:{container_id}:{stack_index}",
                    container_id=container_id,
                    destination_stack=stack_index,
                    description=(
                        f"place {container_id} on stack {stack_index}"
                    ),
                )
            )
    return candidates


def apply_repair(
    partial: PartialSolution, choices: Sequence[RepairCandidate]
) -> ContainerStackState:
    stacks = [list(stack) for stack in partial.state.stacks]

    for choice in choices:
        if choice.container_id not in partial.removed:
            raise ValueError("repair contains a container not removed by destroy")
        if len(stacks[choice.destination_stack]) >= MAX_STACK_HEIGHT:
            raise ValueError("repair destination is full")
        if choice.container_id in [item for stack in stacks for item in stack]:
            raise ValueError("container already placed")
        stacks[choice.destination_stack].append(choice.container_id)

    placed = {choice.container_id for choice in choices}
    if placed != set(partial.removed):
        raise ValueError("repair must place every removed container")

    return partial.state.with_stacks(tuple(tuple(stack) for stack in stacks))
