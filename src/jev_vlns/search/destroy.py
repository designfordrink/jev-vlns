from dataclasses import dataclass
from collections.abc import Sequence
from itertools import combinations

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
    state: ContainerStackState,
    max_stacks: int = 2,
    *,
    min_stacks: int = 1,
    include_non_adjacent: bool = True,
) -> list[DestroyCandidate]:
    """Generate deterministic variable-size destroy neighborhoods.

    A candidate removes the top container from each selected non-empty stack.
    Candidate generation is purely combinatorial: legality is determined by
    the current state, and applying a candidate never charges physical moves.

    min_stacks and max_stacks define the neighborhood-size family.
    When include_non_adjacent is true, all stack combinations in that
    size range are considered, not only adjacent stacks.
    """
    if min_stacks < 1:
        raise ValueError("min_stacks must be at least 1")
    if max_stacks < min_stacks:
        raise ValueError("max_stacks must be >= min_stacks")

    non_empty = tuple(i for i, stack in enumerate(state.stacks) if stack)
    if not non_empty:
        return []

    upper = min(max_stacks, len(non_empty))
    candidates: list[DestroyCandidate] = []

    for size in range(min_stacks, upper + 1):
        if include_non_adjacent:
            groups = combinations(non_empty, size)
        else:
            groups = (
                tuple(non_empty[start : start + size])
                for start in range(len(non_empty) - size + 1)
            )

        for indices in groups:
            stack_indices = tuple(indices)
            label = ",".join(map(str, stack_indices))
            if size == 1:
                candidate_id = f"stack:{label}"
                description = f"destroy top of stack {label}"
            else:
                candidate_id = f"stacks:{label}"
                description = f"destroy tops of stacks {label}"
            candidates.append(
                DestroyCandidate(
                    id=candidate_id,
                    stack_indices=stack_indices,
                    description=description,
                )
            )
    return candidates


def apply_destroy(
    state: ContainerStackState, candidate: DestroyCandidate
) -> PartialSolution:
    stacks = [list(stack) for stack in state.stacks]
    removed: list[str] = []

    for index in candidate.stack_indices:
        if not 0 <= index < len(stacks):
            raise ValueError("destroy candidate stack index out of range")
        if not stacks[index]:
            raise ValueError("destroy candidate references an empty stack")
        removed.append(stacks[index].pop())

    return PartialSolution(
        state=state.with_stacks(tuple(tuple(stack) for stack in stacks)),
        removed=tuple(removed),
    )
