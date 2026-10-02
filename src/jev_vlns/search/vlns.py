from dataclasses import dataclass
import random
from collections.abc import Sequence

from jev_vlns.container_stack.actions import apply_legal_action, legal_actions
from jev_vlns.container_stack.evaluator import evaluate
from jev_vlns.container_stack.state import ContainerStackState
from jev_vlns.selectors.greedy import GreedySelector
from .destroy import DestroyCandidate, apply_destroy, generate_destroy_candidates
from .repair import RepairCandidate, apply_repair, generate_repair_candidates


@dataclass(frozen=True)
class VlnsResult:
    state: ContainerStackState
    evaluation: object
    iterations: int
    best_projected_objective: float


def projected_objective(state: ContainerStackState) -> float:
    """Estimate total solution cost by greedily completing this arrangement.

    Destroy/repair are hypothetical search operations and therefore do not
    increment state.moves. The objective is the number of moves already
    committed plus the moves needed by a deterministic greedy completion.
    """
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


def _repair_randomly(
    partial_state: ContainerStackState,
    removed: Sequence[str],
    repairs: Sequence[RepairCandidate],
    rng: random.Random,
) -> list[RepairCandidate]:
    choices: list[RepairCandidate] = []
    for container_id in removed:
        options = [c for c in repairs if c.container_id == container_id]
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
    """Random Destroy + Random Repair VLNS baseline.

    The search compares complete-solution cost estimates rather than
    accumulating hypothetical repair operations into the move count.
    """
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
        choices = _repair_randomly(partial.state, partial.removed, repairs, rng)
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

    This is the experiment harness: selectors may be Random, Greedy or JEV.
    Candidate generation, legality, objective and execution remain local.
    """
    current = initial_state
    current_score = projected_objective(current)

    for _ in range(iterations):
        destroys = generate_destroy_candidates(current)
        if not destroys:
            break

        destroy = destroy_selector.select(current, destroys)
        partial = apply_destroy(current, destroy)
        repairs = generate_repair_candidates(partial)

        choices: list[RepairCandidate] = []
        for container_id in partial.removed:
            choice = repair_selector.select_for_container(
                partial.state, repairs, container_id
            )
            choices.append(choice)

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


def make_random_vlns_selectors(seed: int = 0):
    """Return reproducible Random Destroy and Random Repair selectors."""
    return _RandomDestroy(seed), _RandomRepair(seed + 1)
