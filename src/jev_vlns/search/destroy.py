from dataclasses import dataclass
from collections.abc import Sequence

from jev_vlns.container_stack.state import ContainerStackState


@dataclass(frozen=True)
class DestroyCandidate:
    id: str
    stack_indices: tuple[int, ...]
    description: str


@dataclass(frozen=True)
class PartialSolution:
    state: ContainerStackState
    removed: tuple[str, ...]


def generate_destroy_candidates(
    state: ContainerStackState, max_stacks: int = 2
) -> list[DestroyCandidate]:
    """Generate deterministic, small neighborhoods.

    Destroy candidates identify stacks whose top portions will be removed.
    The operation itself is pure and does not charge moves.
    """

    non_empty = [i for i, stack in enumerate(state.stacks) if stack]
    if not non_empty:
        return []

    candidates: list[DestroyCandidate] = []
    for index in non_empty:
        candidates.append(
            DestroyCandidate(
                id=f"stack:{index}",
                stack_indices=(index,),
                description=f"destroy top of stack {index}",
            )
        )

    if max_stacks >= 2 and len(non_empty) >= 2:
        for left, right in zip(non_empty, non_empty[1:]):
            candidates.append(
                DestroyCandidate(
                    id=f"stacks:{left},{right}",
                    stack_indices=(left, right),
                    description=f"destroy tops of stacks {left} and {right}",
                )
            )
    return candidates


def apply_destroy(
    state: ContainerStackState, candidate: DestroyCandidate
) -> PartialSolution:
    stacks = [list(stack) for stack in state.stacks]
    removed: list[str] = []

    for index in candidate.stack_indices:
        if stacks[index]:
            removed.append(stacks[index].pop())

    return PartialSolution(
        state=state.with_stacks(tuple(tuple(stack) for stack in stacks)),
        removed=tuple(removed),
    )
