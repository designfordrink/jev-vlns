from dataclasses import dataclass
from typing import Callable, Protocol

from jev_vlns.container_stack.actions import apply_legal_action, legal_actions
from jev_vlns.container_stack.evaluator import evaluate
from jev_vlns.container_stack.state import ContainerStackState
from jev_vlns.core.action import Action
from jev_vlns.core.evaluator import Evaluation


class SelectorLike(Protocol):
    def select(
        self, state: ContainerStackState, candidates: list[Action]
    ) -> Action:
        ...


@dataclass(frozen=True)
class SolveResult:
    state: ContainerStackState
    evaluation: Evaluation
    iterations: int


def solve(
    initial_state: ContainerStackState,
    selector: SelectorLike,
    *,
    max_iterations: int = 10_000,
    on_step: Callable[[ContainerStackState, Action], None] | None = None,
) -> SolveResult:
    """Run a deterministic environment loop with an interchangeable selector."""

    state = initial_state
    for iteration in range(max_iterations):
        if state.is_complete:
            break
        candidates = legal_actions(state)
        if not candidates:
            break
        action = selector.select(state, candidates)
        if action.id not in {candidate.id for candidate in candidates}:
            raise ValueError("selector returned an action outside candidate set")
        state = apply_legal_action(state, action)
        if on_step:
            on_step(state, action)

    return SolveResult(
        state=state,
        evaluation=evaluate(state),
        iterations=state.moves,
    )
