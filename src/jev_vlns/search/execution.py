"""Executable plans produced by the deterministic environment policy."""

from dataclasses import dataclass

from jev_vlns.container_stack.actions import apply_legal_action, legal_actions
from jev_vlns.container_stack.state import ContainerStackState
from jev_vlns.core.action import Action
from jev_vlns.selectors.greedy import GreedySelector


@dataclass(frozen=True)
class ExecutablePlan:
    """A complete legal action sequence with its replayed final state."""

    actions: tuple[Action, ...]
    final_state: ContainerStackState

    @property
    def moves(self) -> int:
        return len(self.actions)


def greedy_plan(
    initial_state: ContainerStackState,
    *,
    max_steps: int | None = None,
) -> ExecutablePlan:
    """Build a deterministic executable plan from an initial state.

    This is an executable baseline, not a reconstruction of a virtual
    Destroy/Repair trajectory.
    """
    selector = GreedySelector()
    state = initial_state
    actions: list[Action] = []
    limit = max_steps or max(1, len(state.containers) * len(state.stacks) * 20)

    for _ in range(limit):
        if state.is_complete:
            return ExecutablePlan(tuple(actions), state)
        candidates = legal_actions(state)
        if not candidates:
            raise ValueError("no legal action before reaching a complete state")
        action = selector.select(state, candidates)
        actions.append(action)
        state = apply_legal_action(state, action)

    raise ValueError("greedy plan exceeded execution step limit")


def assert_executable_plan(
    initial_state: ContainerStackState,
    plan: ExecutablePlan,
) -> ContainerStackState:
    """Independently replay a plan and require exact final-state agreement."""
    state = initial_state
    for action in plan.actions:
        state = apply_legal_action(state, action)

    if not state.is_complete:
        raise ValueError("executable plan does not reach a complete state")
    if state != plan.final_state:
        raise ValueError("plan final state differs from replayed final state")
    if state.moves != len(plan.actions):
        raise ValueError("reported moves differ from executable action count")
    return state
