from dataclasses import dataclass
import random

from jev_vlns.container_stack.evaluator import evaluate
from jev_vlns.container_stack.state import ContainerStackState
from .acceptance import strict_improvement
from .destroy import apply_destroy, generate_destroy_candidates
from .repair import apply_repair, generate_repair_candidates


@dataclass(frozen=True)
class VlnsResult:
    state: ContainerStackState
    evaluation: object
    iterations: int


def estimated_objective(state: ContainerStackState) -> float:
    """Simple admissible-style lower bound plus accumulated moves.

    Every undelivered container requires at least one future action.
    This is deliberately simple for the first VLNS milestone.
    """

    return float(state.moves + state.remaining_count)


def random_vlns(
    initial_state: ContainerStackState,
    *,
    seed: int = 0,
    iterations: int = 100,
) -> VlnsResult:
    """Minimal VLNS baseline: random destroy + random repair.

    Destroy is free because it changes the candidate solution, not the
    executed history. Repair actions increment the solution's move count.
    """

    rng = random.Random(seed)
    current = initial_state
    current_eval = evaluate(current)

    for _ in range(iterations):
        destroys = generate_destroy_candidates(current)
        if not destroys:
            break

        destroy = rng.choice(destroys)
        partial = apply_destroy(current, destroy)
        repairs = generate_repair_candidates(partial)
        if not repairs:
            continue

        # A repair candidate represents a placement. For multiple removed
        # containers, shuffle then place each once.
        chosen = []
        remaining = list(partial.removed)
        for container_id in remaining:
            options = [
                candidate
                for candidate in repairs
                if candidate.container_id == container_id
            ]
            chosen.append(rng.choice(options))

        repaired = apply_repair(partial, chosen)
        repaired = repaired.with_stacks(
            repaired.stacks,
            moves=current.moves + len(chosen),
        )

        # M4 uses the simple evaluator plus a future-work estimate.
        candidate_score = estimated_objective(repaired)
        current_score = estimated_objective(current)
        if candidate_score < current_score and repaired.is_complete:
            candidate_eval = evaluate(repaired)
            if strict_improvement(current_eval, candidate_eval):
                current = repaired
                current_eval = candidate_eval

    return VlnsResult(
        state=current,
        evaluation=current_eval,
        iterations=iterations,
    )
