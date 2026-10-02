from dataclasses import dataclass
import random
from collections.abc import Sequence

from jev_vlns.container_stack.actions import apply_legal_action, legal_actions
from jev_vlns.container_stack.evaluator import evaluate
from jev_vlns.container_stack.state import ContainerStackState, MAX_STACK_HEIGHT
from jev_vlns.selectors.greedy import GreedySelector
from .destroy import DestroyCandidate, apply_destroy, generate_destroy_candidates
from .repair import RepairCandidate, apply_repair, generate_repair_candidates


@dataclass(frozen=True)
class VlnsResult:
    state: ContainerStackState
    evaluation: object
    iterations: int
    best_projected_objective: float
    mean_destroy_candidates: float = 0.0
    mean_repair_candidates: float = 0.0
    mean_destroy_regret: float = 0.0
    mean_repair_regret: float = 0.0


def projected_objective(state: ContainerStackState) -> float:
    """Estimate total solution cost by greedily completing this arrangement."""
    selector = GreedySelector()
    working = state
    guard = max(1, len(state.containers) * len(state.stacks) * 20)

    for _ in range(guard):
        if working.is_complete:
            return float(working.moves)
        candidates = legal_actions(working)
        if not candidates:
            return float("inf")
        action = selector.select(working, candidates)
        working = apply_legal_action(working, action)

    return float("inf")


def estimated_objective(state: ContainerStackState) -> float:
    """Backward-compatible name for the projected completion objective."""
    return projected_objective(state)


def _available_repairs(
    partial,
    repairs: Sequence[RepairCandidate],
    container_id: str,
    planned: Sequence[RepairCandidate],
) -> list[RepairCandidate]:
    """Return candidates still legal after earlier repair choices."""
    reserved = {choice.destination_stack for choice in planned}
    counts = {
        index: reserved_count
        for index, reserved_count in (
            (stack_index, sum(c.destination_stack == stack_index for c in planned))
            for stack_index in range(len(partial.state.stacks))
        )
    }
    return [
        candidate
        for candidate in repairs
        if candidate.container_id == container_id
        and len(partial.state.stacks[candidate.destination_stack])
        + counts[candidate.destination_stack]
        < MAX_STACK_HEIGHT
    ]


def _repair_randomly(
    partial,
    removed: Sequence[str],
    repairs: Sequence[RepairCandidate],
    rng: random.Random,
) -> list[RepairCandidate]:
    choices: list[RepairCandidate] = []
    for container_id in removed:
        options = _available_repairs(partial, repairs, container_id, choices)
        if not options:
            return []
        choices.append(rng.choice(options))
    return choices


def _finish_greedily(state: ContainerStackState) -> ContainerStackState:
    selector = GreedySelector()
    working = state
    guard = max(1, len(state.containers) * len(state.stacks) * 20)
    for _ in range(guard):
        if working.is_complete:
            return working
        candidates = legal_actions(working)
        if not candidates:
            return working
        working = apply_legal_action(working, selector.select(working, candidates))
    return working


def random_vlns(
    initial_state: ContainerStackState,
    *,
    seed: int = 0,
    iterations: int = 100,
) -> VlnsResult:
    """Random Destroy + Random Repair VLNS baseline."""
    rng = random.Random(seed)
    current = initial_state
    current_score = projected_objective(current)

    for _ in range(iterations):
        destroys = generate_destroy_candidates(current)
        if not destroys:
            break

        destroy = rng.choice(destroys)
        partial = apply_destroy(current, destroy)
        repairs = generate_repair_candidates(partial)
        choices = _repair_randomly(partial, partial.removed, repairs, rng)
        if not choices:
            continue

        repaired = apply_repair(partial, choices)
        candidate_score = projected_objective(repaired)

        if candidate_score < current_score:
            current = repaired
            current_score = candidate_score

    final_state = _finish_greedily(current)
    return VlnsResult(
        state=final_state,
        evaluation=evaluate(final_state),
        iterations=iterations,
        best_projected_objective=current_score,
    )


class _RandomDestroy:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def select(self, state, candidates):
        if not candidates:
            raise ValueError("no destroy candidates")
        return self.rng.choice(list(candidates))


class _RandomRepair:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def select_for_container(self, state, candidates, container_id):
        scoped = [c for c in candidates if c.container_id == container_id]
        if not scoped:
            raise ValueError(f"no repair candidates for {container_id}")
        return self.rng.choice(scoped)


def guided_vlns(
    initial_state: ContainerStackState,
    destroy_selector,
    repair_selector,
    *,
    iterations: int = 100,
) -> VlnsResult:
    """VLNS with injectable Destroy and Repair selectors.

    Also collect exact local-neighborhood diagnostics. These diagnostics answer
    a narrow question: how much objective quality was available inside the
    current neighborhood but missed by the selected candidate?
    """
    from .oracle import best_repair_plan, destroy_landscape

    current = initial_state
    current_score = projected_objective(current)
    destroy_counts: list[int] = []
    repair_counts: list[int] = []
    destroy_regrets: list[float] = []
    repair_regrets: list[float] = []

    for _ in range(iterations):
        destroys = generate_destroy_candidates(current)
        if not destroys:
            break

        destroy_land = destroy_landscape(current, destroys)
        finite_destroy = [
            entry.score for entry in destroy_land if entry.score != float("inf")
        ]
        best_destroy_score = min(finite_destroy) if finite_destroy else float("inf")
        destroy_counts.append(len(destroys))

        destroy = destroy_selector.select(current, destroys)
        selected_destroy_score = next(
            entry.score for entry in destroy_land if entry.candidate.id == destroy.id
        )
        if selected_destroy_score != float("inf") and best_destroy_score != float("inf"):
            destroy_regrets.append(selected_destroy_score - best_destroy_score)

        partial = apply_destroy(current, destroy)
        repairs = generate_repair_candidates(partial)
        repair_counts.append(len(repairs))

        # OracleRepairSelector can optimize the whole repair combination.
        select_all = getattr(repair_selector, "select_all", None)
        if callable(select_all):
            choices = list(select_all(partial, repairs, partial.removed))
        else:
            choices = []
            for container_id in partial.removed:
                options = _available_repairs(
                    partial, repairs, container_id, choices
                )
                if not options:
                    choices = []
                    break
                choice = repair_selector.select_for_container(
                    partial.state, options, container_id
                )
                choices.append(choice)

        if not choices:
            continue

        best_repair_score = best_repair_plan(partial).score
        repaired = apply_repair(partial, choices)
        candidate_score = projected_objective(repaired)
        if candidate_score != float("inf") and best_repair_score != float("inf"):
            repair_regrets.append(candidate_score - best_repair_score)

        if candidate_score < current_score:
            current = repaired
            current_score = candidate_score

    final_state = _finish_greedily(current)
    n = len(destroy_counts)
    return VlnsResult(
        state=final_state,
        evaluation=evaluate(final_state),
        iterations=iterations,
        best_projected_objective=current_score,
        mean_destroy_candidates=sum(destroy_counts) / n if n else 0.0,
        mean_repair_candidates=(
            sum(repair_counts) / len(repair_counts) if repair_counts else 0.0
        ),
        mean_destroy_regret=(
            sum(destroy_regrets) / len(destroy_regrets)
            if destroy_regrets else 0.0
        ),
        mean_repair_regret=(
            sum(repair_regrets) / len(repair_regrets)
            if repair_regrets else 0.0
        ),
    )

def make_random_vlns_selectors(seed: int = 0):
    """Return reproducible Random Destroy and Random Repair selectors."""
    return _RandomDestroy(seed), _RandomRepair(seed + 1)
