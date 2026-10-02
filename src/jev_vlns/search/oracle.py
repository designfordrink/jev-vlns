"""Oracle selectors and exact local-neighborhood landscape analysis.

The oracle is an experiment control, not a production solver. It enumerates the
small repair neighborhood that the current Container Stack MVP can represent
and chooses the candidate with the lowest greedy-completion objective.
"""

from dataclasses import dataclass
from collections.abc import Sequence

from jev_vlns.container_stack.state import ContainerStackState, MAX_STACK_HEIGHT
from .destroy import DestroyCandidate, PartialSolution, apply_destroy
from .repair import RepairCandidate, apply_repair, generate_repair_candidates
from .vlns import projected_objective


@dataclass(frozen=True)
class RepairPlan:
    choices: tuple[RepairCandidate, ...]
    score: float


@dataclass(frozen=True)
class DestroyLandscapeEntry:
    candidate: DestroyCandidate
    score: float


def _enumerate_plans(
    partial: PartialSolution,
    removed: Sequence[str],
    repairs: Sequence[RepairCandidate],
    index: int = 0,
    choices: tuple[RepairCandidate, ...] = (),
):
    if index >= len(removed):
        yield RepairPlan(choices=choices, score=projected_objective(apply_repair(partial, choices)))
        return

    container_id = removed[index]
    used_capacity = {
        stack_index: sum(
            choice.destination_stack == stack_index for choice in choices
        )
        for stack_index in range(len(partial.state.stacks))
    }
    options = [
        candidate
        for candidate in repairs
        if candidate.container_id == container_id
        and len(partial.state.stacks[candidate.destination_stack])
        + used_capacity[candidate.destination_stack]
        < MAX_STACK_HEIGHT
    ]
    for candidate in options:
        yield from _enumerate_plans(
            partial,
            removed,
            repairs,
            index + 1,
            choices + (candidate,),
        )


def best_repair_plan(partial: PartialSolution) -> RepairPlan:
    """Enumerate every legal full repair plan and return the lowest score."""
    repairs = generate_repair_candidates(partial)
    plans = list(_enumerate_plans(partial, partial.removed, repairs))
    if not plans:
        return RepairPlan(choices=(), score=float("inf"))
    return min(plans, key=lambda plan: (plan.score, tuple(c.id for c in plan.choices)))


def destroy_landscape(
    state: ContainerStackState,
    candidates: Sequence[DestroyCandidate],
) -> list[DestroyLandscapeEntry]:
    """Score every destroy candidate by its best possible full repair."""
    entries: list[DestroyLandscapeEntry] = []
    for candidate in candidates:
        partial = apply_destroy(state, candidate)
        entries.append(
            DestroyLandscapeEntry(
                candidate=candidate,
                score=best_repair_plan(partial).score,
            )
        )
    return entries


class OracleDestroySelector:
    """Choose the destroy neighborhood with the best downstream potential."""

    def __init__(self):
        self.last_landscape: list[DestroyLandscapeEntry] = []

    def select(
        self,
        state: ContainerStackState,
        candidates: Sequence[DestroyCandidate],
    ) -> DestroyCandidate:
        if not candidates:
            raise ValueError("cannot select from an empty candidate list")
        self.last_landscape = destroy_landscape(state, candidates)
        return min(
            self.last_landscape,
            key=lambda entry: (entry.score, entry.candidate.id),
        ).candidate


class OracleRepairSelector:
    """Choose the complete repair plan with the best downstream objective."""

    def __init__(self):
        self.last_plan = RepairPlan(choices=(), score=float("inf"))

    def select_all(
        self,
        partial: PartialSolution,
        candidates: Sequence[RepairCandidate],
        removed: Sequence[str],
    ) -> list[RepairCandidate]:
        if not removed:
            return []
        self.last_plan = best_repair_plan(partial)
        return list(self.last_plan.choices)

    def select_for_container(
        self,
        state,
        candidates: Sequence[RepairCandidate],
        container_id: str,
    ) -> RepairCandidate:
        scoped = [c for c in candidates if c.container_id == container_id]
        if not scoped:
            raise ValueError(f"no repair candidates for {container_id}")
        # This method is retained for selector-interface compatibility. The
        # guided VLNS runner uses select_all() so the oracle can optimize the
        # whole repair rather than making a myopic per-container choice.
        return min(scoped, key=lambda candidate: candidate.id)
